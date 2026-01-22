"""Indicators API routes."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.storage import get_db, IndicatorRepository
from backend.processors import LiquidityProcessor
from backend.core import DataPoint

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("")
async def list_indicators(
    market: Optional[str] = None,
    source: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all indicators with optional filters."""
    repo = IndicatorRepository(db)

    if market:
        indicators = await repo.get_indicators_by_market(market)
    elif source:
        indicators = await repo.get_indicators_by_source(source)
    else:
        indicators = await repo.get_all_indicators()

    return [
        {
            "id": i.id,
            "name": i.name,
            "name_en": i.name_en,
            "source": i.source,
            "market": i.market,
            "category": i.category,
            "unit": i.unit,
            "is_primary": bool(i.is_primary)
        }
        for i in indicators
    ]


@router.get("/{indicator_id}")
async def get_indicator_data(
    indicator_id: str,
    days: int = Query(default=365, ge=1, le=3650),
    db: AsyncSession = Depends(get_db)
):
    """Get indicator data with statistics."""
    repo = IndicatorRepository(db)
    indicator = await repo.get_indicator(indicator_id)

    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    start_date = datetime.utcnow() - timedelta(days=days)
    data_points = await repo.get_data_points(indicator_id, start_date=start_date, limit=days * 2)

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
    change_30d = stats.get("changes", {}).get("30d", {}).get("change_pct")
    status = LiquidityProcessor.determine_status(change_30d, indicator.direction or "up_is_loose")

    # Apply unit_divisor to display value
    unit_divisor = indicator.unit_divisor or 1.0
    current_value = stats.get("current_value")
    if current_value is not None:
        current_value = round(current_value / unit_divisor, 2)

    return {
        "indicator": {
            "id": indicator.id,
            "name": indicator.name,
            "name_en": indicator.name_en,
            "source": indicator.source,
            "market": indicator.market,
            "category": indicator.category,
            "unit": indicator.unit,
            "direction": indicator.direction,
            "impact_up": indicator.impact_up,
            "impact_down": indicator.impact_down,
            "description": indicator.description,
            "is_primary": bool(indicator.is_primary)
        },
        "current_value": current_value,
        "current_date": stats.get("current_date"),
        "changes": stats.get("changes", {}),
        "status": status,
        "data_points": [
            {
                "timestamp": p.timestamp.isoformat(),
                "value": round(p.value / unit_divisor, 4),
                "indicator_id": p.indicator_id
            }
            for p in sorted(data_points, key=lambda x: x.timestamp)
        ]
    }


@router.get("/{indicator_id}/data")
async def get_indicator_raw_data(
    indicator_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db)
):
    """Get raw data points for an indicator."""
    repo = IndicatorRepository(db)
    indicator = await repo.get_indicator(indicator_id)

    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    data_points = await repo.get_data_points(indicator_id, start, end, limit)

    return {
        "indicator_id": indicator_id,
        "count": len(data_points),
        "data": [
            {
                "timestamp": p.timestamp.isoformat(),
                "value": p.value
            }
            for p in sorted(data_points, key=lambda x: x.timestamp)
        ]
    }
