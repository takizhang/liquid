"""Admin routes for system management."""
from fastapi import APIRouter, HTTPException
from backend.storage import get_session, IndicatorRepository, init_db
from backend.storage.models import Indicator
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


@router.post("/collect-sync")
async def collect_data_sync():
    """Synchronously collect data for debugging."""
    import os
    from backend.core import CollectorRegistry
    from backend.storage import get_session, IndicatorRepository
    import backend.collectors  # noqa

    results = []
    errors = []

    # Check env vars
    fred_key = os.getenv("FRED_API_KEY", "")
    results.append(f"FRED_API_KEY configured: {bool(fred_key)}")

    session = await get_session()
    repo = IndicatorRepository(session)

    # Get all indicators
    indicators = await repo.get_all_indicators()
    results.append(f"Found {len(indicators)} indicators")

    # Try to collect data for first FRED indicator
    fred_indicators = [i for i in indicators if i.source == "FRED"]
    if fred_indicators:
        indicator = fred_indicators[0]
        results.append(f"Testing indicator: {indicator.id}, series_id: {indicator.series_id}")

        try:
            collector_class = CollectorRegistry.get_collector("FRED")
            if collector_class:
                collector = collector_class()
                data_points = await collector.fetch(
                    indicator_id=indicator.id,
                    series_id=indicator.series_id,
                    market=indicator.market
                )
                results.append(f"Fetched {len(data_points)} data points")

                if data_points:
                    await repo.save_data_points(data_points)
                    results.append(f"Saved {len(data_points)} data points")
            else:
                errors.append("FRED collector not found")
        except Exception as e:
            errors.append(f"Error: {str(e)}")

    await session.close()

    return {
        "results": results,
        "errors": errors
    }
