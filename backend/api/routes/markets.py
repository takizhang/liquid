"""Markets API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.storage import get_db, IndicatorRepository
from backend.processors import LiquidityProcessor
from backend.core import DataPoint

router = APIRouter(prefix="/api/markets", tags=["markets"])


def get_indicators_config():
    """Load indicators config."""
    import yaml
    from pathlib import Path
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "indicators.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"markets": [], "categories": [], "indicators": []}


@router.get("")
async def get_markets():
    """Get list of available markets."""
    config = get_indicators_config()
    return config.get("markets", [])


@router.get("/{market_id}")
async def get_market_detail(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get market detail with primary indicator."""
    repo = IndicatorRepository(db)
    config = get_indicators_config()

    market_config = next(
        (m for m in config.get("markets", []) if m["id"] == market_id),
        None
    )

    if not market_config:
        return {"error": "Market not found"}

    indicators = await repo.get_indicators_by_market(market_id)
    primary = next((i for i in indicators if i.is_primary), indicators[0] if indicators else None)

    result = {
        "market": market_config,
        "indicators_count": len(indicators),
        "primary_indicator": None
    }

    if primary:
        latest = await repo.get_latest_data_point(primary.id)
        if latest:
            result["primary_indicator"] = {
                "id": primary.id,
                "name": primary.name,
                "current_value": latest.value,
                "unit": primary.unit
            }

    return result


@router.get("/{market_id}/indicators")
async def get_market_indicators(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all indicators for a specific market with current values."""
    repo = IndicatorRepository(db)
    indicators = await repo.get_indicators_by_market(market_id)
    latest_data = await repo.get_latest_for_all_indicators(market_id)

    result = []
    for ind in indicators:
        item = {
            "id": ind.id,
            "name": ind.name,
            "name_en": ind.name_en,
            "source": ind.source,
            "market": ind.market,
            "category": ind.category,
            "unit": ind.unit,
            "direction": ind.direction,
            "impact_up": ind.impact_up,
            "impact_down": ind.impact_down,
            "description": ind.description,
            "is_primary": bool(ind.is_primary),
            "current_value": None,
            "current_date": None,
            "changes": {},
            "status": {"status": "neutral", "color": "yellow", "emoji": "🟡"}
        }

        if ind.id in latest_data:
            dp = latest_data[ind.id]
            item["current_value"] = dp.value
            item["current_date"] = dp.timestamp.isoformat()

            # Calculate changes
            data_points = await repo.get_data_points(ind.id, limit=365)
            if data_points:
                points = [
                    DataPoint(
                        timestamp=p.timestamp,
                        indicator_id=p.indicator_id,
                        value=p.value,
                        source=p.source,
                        market=p.market
                    )
                    for p in data_points
                ]
                stats = LiquidityProcessor.calculate_change_stats(points)
                item["changes"] = stats.get("changes", {})

                change_30d = item["changes"].get("30d", {}).get("change_pct")
                item["status"] = LiquidityProcessor.determine_status(
                    change_30d, ind.direction or "up_is_loose"
                )

        result.append(item)

    return result
