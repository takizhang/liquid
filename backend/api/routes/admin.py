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

        # Process each market
        for market in config.get("markets", []):
            market_id = market["id"]

            for indicator_config in market.get("indicators", []):
                # Create indicator object
                indicator = Indicator(
                    id=indicator_config["id"],
                    name=indicator_config["name"],
                    name_en=indicator_config.get("name_en", indicator_config["name"]),
                    market=market_id,
                    source=indicator_config["source"],
                    series_id=indicator_config.get("series_id"),
                    unit=indicator_config.get("unit", ""),
                    description=indicator_config.get("description", ""),
                    is_primary=indicator_config.get("is_primary", False),
                    direction=indicator_config.get("direction", "up_is_loose")
                )

                # Save to database
                await repo.save_indicator(indicator)
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
