"""Admin routes for system management."""
from fastapi import APIRouter, HTTPException
from backend.storage import get_session, IndicatorRepository, init_db
from backend.storage.models import Indicator
from backend.core import CollectorRegistry
import yaml
from pathlib import Path

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/init-indicators")
async def initialize_indicators():
    """Initialize indicators from config file."""
    try:
        # Load config
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "indicators.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        session = await get_session()
        repo = IndicatorRepository(session)

        indicators_created = 0

        # Process indicators (they're at top level, not under markets)
        for indicator_config in config.get("indicators", []):
            # Save to database using upsert_indicator
            await repo.upsert_indicator(indicator_config)
            indicators_created += 1

        await session.close()

        return {
            "status": "success",
            "message": f"Initialized {indicators_created} indicators",
            "indicators_count": indicators_created
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-data")
async def trigger_data_collection():
    """Manually trigger data collection for all indicators."""
    try:
        from backend.scheduler import collect_all_data
        import asyncio

        # Run data collection in background
        asyncio.create_task(collect_all_data())

        return {
            "status": "success",
            "message": "Data collection started in background"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/{indicator_id}")
async def debug_indicator(indicator_id: str):
    """Debug indicator unit_divisor."""
    from backend.storage import get_session, IndicatorRepository
    session = await get_session()
    repo = IndicatorRepository(session)
    indicator = await repo.get_indicator(indicator_id)
    await session.close()

    if not indicator:
        return {"error": "not found"}

    return {
        "id": indicator.id,
        "name": indicator.name,
        "unit": indicator.unit,
        "unit_divisor": indicator.unit_divisor,
        "unit_divisor_type": str(type(indicator.unit_divisor))
    }


@router.get("/env-check")
async def check_env():
    """Check environment variables."""
    import os
    return {
        "FRED_API_KEY": bool(os.getenv("FRED_API_KEY")),
        "COINGECKO_API_KEY": bool(os.getenv("COINGECKO_API_KEY")),
        "collectors": list(CollectorRegistry._collectors.keys()) if hasattr(CollectorRegistry, '_collectors') else []
    }


@router.post("/collect-all-sync")
async def collect_all_sync():
    """Synchronously collect ALL data for debugging."""
    import os
    import traceback
    from backend.storage import get_session, IndicatorRepository

    results = []
    errors = []

    try:
        import backend.collectors  # noqa
        from backend.core import CollectorRegistry
        results.append(f"Collectors loaded: {list(CollectorRegistry._collectors.keys())}")
    except Exception as e:
        errors.append(f"Failed to load collectors: {str(e)}")
        return {"results": results, "errors": errors}

    try:
        session = await get_session()
        repo = IndicatorRepository(session)

        indicators = await repo.get_all_indicators()
        results.append(f"Found {len(indicators)} indicators")

        for indicator in indicators:
            if indicator.is_computed:
                results.append(f"Skipping computed: {indicator.id}")
                continue

            try:
                collector = CollectorRegistry.get(indicator.source)
                data_points = await collector.fetch(
                    indicator_id=indicator.id,
                    series_id=indicator.series_id,
                    market=indicator.market
                )

                if data_points:
                    await repo.save_data_points(data_points)
                    results.append(f"✓ {indicator.id}: {len(data_points)} points")
                else:
                    errors.append(f"✗ {indicator.id}: no data")

            except Exception as e:
                errors.append(f"✗ {indicator.id}: {str(e)[:80]}")

        await session.close()

    except Exception as e:
        errors.append(f"DB error: {str(e)}")
        errors.append(traceback.format_exc()[:500])

    return {"results": results, "errors": errors}
