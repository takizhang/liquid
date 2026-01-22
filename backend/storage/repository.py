"""Data access layer with repository pattern."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, delete, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert

from .models import Indicator, DataPointModel, AnalysisReport, SignalEvent
from backend.core import DataPoint, AnalysisResult


class IndicatorRepository:
    """Repository for indicator data operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Indicator Operations ====================

    async def upsert_indicator(self, indicator_config: dict) -> Indicator:
        """Insert or update indicator metadata."""
        stmt = insert(Indicator).values(
            id=indicator_config["id"],
            name=indicator_config["name"],
            name_en=indicator_config.get("name_en"),
            source=indicator_config["source"],
            series_id=indicator_config.get("series_id"),
            market=indicator_config["market"],
            category=indicator_config.get("category"),
            unit=indicator_config.get("unit"),
            unit_divisor=indicator_config.get("unit_divisor", 1.0),
            direction=indicator_config.get("direction"),
            impact_up=indicator_config.get("impact", {}).get("up"),
            impact_down=indicator_config.get("impact", {}).get("down"),
            description=indicator_config.get("description"),
            update_frequency=indicator_config.get("update_frequency"),
            is_primary=1 if indicator_config.get("is_primary") else 0,
            is_computed=1 if indicator_config.get("is_computed") else 0,
            enabled=0 if indicator_config.get("enabled") is False else 1,
            tags=indicator_config.get("tags", []),
            dependencies=indicator_config.get("dependencies", []),
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": indicator_config["name"],
                "name_en": indicator_config.get("name_en"),
                "source": indicator_config["source"],
                "series_id": indicator_config.get("series_id"),
                "market": indicator_config["market"],
                "category": indicator_config.get("category"),
                "unit": indicator_config.get("unit"),
                "unit_divisor": indicator_config.get("unit_divisor", 1.0),
                "direction": indicator_config.get("direction"),
                "impact_up": indicator_config.get("impact", {}).get("up"),
                "impact_down": indicator_config.get("impact", {}).get("down"),
                "description": indicator_config.get("description"),
                "update_frequency": indicator_config.get("update_frequency"),
                "is_primary": 1 if indicator_config.get("is_primary") else 0,
                "enabled": 0 if indicator_config.get("enabled") is False else 1,
                "tags": indicator_config.get("tags", []),
                "updated_at": datetime.utcnow(),
            }
        )
        await self.session.execute(stmt)
        await self.session.commit()

        result = await self.session.execute(
            select(Indicator).where(Indicator.id == indicator_config["id"])
        )
        return result.scalar_one()

    async def get_indicator(self, indicator_id: str) -> Optional[Indicator]:
        """Get indicator by ID."""
        result = await self.session.execute(
            select(Indicator).where(Indicator.id == indicator_id)
        )
        return result.scalar_one_or_none()

    async def get_indicators_by_market(self, market: str) -> list[Indicator]:
        """Get all indicators for a market."""
        result = await self.session.execute(
            select(Indicator).where(
                and_(Indicator.market == market, Indicator.enabled == 1)
            ).order_by(Indicator.is_primary.desc(), Indicator.id)
        )
        return list(result.scalars().all())

    async def get_all_indicators(self) -> list[Indicator]:
        """Get all enabled indicators."""
        result = await self.session.execute(
            select(Indicator).where(Indicator.enabled == 1).order_by(Indicator.market, Indicator.id)
        )
        return list(result.scalars().all())

    async def get_indicators_by_source(self, source: str) -> list[Indicator]:
        """Get all indicators for a specific data source."""
        result = await self.session.execute(
            select(Indicator).where(
                and_(Indicator.source == source, Indicator.enabled == 1)
            )
        )
        return list(result.scalars().all())

    # ==================== Data Point Operations ====================

    async def save_data_points(self, data_points: list[DataPoint]) -> int:
        """Save data points with upsert logic."""
        if not data_points:
            return 0

        count = 0
        for dp in data_points:
            stmt = insert(DataPointModel).values(
                indicator_id=dp.indicator_id,
                timestamp=dp.timestamp,
                value=dp.value,
                source=dp.source,
                market=dp.market,
                extra_data=dp.metadata,
            ).on_conflict_do_update(
                index_elements=["indicator_id", "timestamp"],
                set_={
                    "value": dp.value,
                    "source": dp.source,
                    "extra_data": dp.metadata,
                }
            )
            await self.session.execute(stmt)
            count += 1

        await self.session.commit()
        return count

    async def get_data_points(
        self,
        indicator_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500
    ) -> list[DataPointModel]:
        """Get data points for an indicator."""
        query = select(DataPointModel).where(
            DataPointModel.indicator_id == indicator_id
        )

        if start_date:
            query = query.where(DataPointModel.timestamp >= start_date)
        if end_date:
            query = query.where(DataPointModel.timestamp <= end_date)

        query = query.order_by(DataPointModel.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_data_point(self, indicator_id: str) -> Optional[DataPointModel]:
        """Get the most recent data point for an indicator."""
        result = await self.session.execute(
            select(DataPointModel)
            .where(DataPointModel.indicator_id == indicator_id)
            .order_by(DataPointModel.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_all_indicators(self, market: Optional[str] = None) -> dict:
        """Get latest data point for all indicators."""
        subq = (
            select(
                DataPointModel.indicator_id,
                func.max(DataPointModel.timestamp).label("max_ts")
            )
            .group_by(DataPointModel.indicator_id)
            .subquery()
        )

        query = (
            select(DataPointModel)
            .join(
                subq,
                and_(
                    DataPointModel.indicator_id == subq.c.indicator_id,
                    DataPointModel.timestamp == subq.c.max_ts
                )
            )
        )

        if market:
            query = query.where(DataPointModel.market == market)

        result = await self.session.execute(query)
        data_points = result.scalars().all()

        return {dp.indicator_id: dp for dp in data_points}

    async def calculate_change(
        self,
        indicator_id: str,
        days: int = 30
    ) -> Optional[dict]:
        """Calculate value change over specified days."""
        now = datetime.utcnow()
        start = now - timedelta(days=days)

        result = await self.session.execute(
            select(DataPointModel)
            .where(
                and_(
                    DataPointModel.indicator_id == indicator_id,
                    DataPointModel.timestamp >= start
                )
            )
            .order_by(DataPointModel.timestamp)
        )
        points = list(result.scalars().all())

        if len(points) < 2:
            return None

        first = points[0]
        last = points[-1]

        change = last.value - first.value
        change_pct = (change / first.value * 100) if first.value != 0 else 0

        return {
            "start_value": first.value,
            "end_value": last.value,
            "change": change,
            "change_pct": round(change_pct, 2),
            "start_date": first.timestamp.isoformat(),
            "end_date": last.timestamp.isoformat()
        }

    # ==================== Analysis Report Operations ====================

    async def save_analysis_report(
        self,
        market_id: str,
        report_type: str,
        result: AnalysisResult,
        data_snapshot: Optional[dict] = None,
        model_used: Optional[str] = None
    ) -> AnalysisReport:
        """Save an AI analysis report."""
        report = AnalysisReport(
            market_id=market_id,
            report_type=report_type,
            summary=result.summary,
            signals=result.signals,
            risk_level=result.risk_level,
            recommendations=result.recommendations,
            confidence=result.confidence,
            reasoning=result.reasoning,
            data_snapshot=data_snapshot,
            model_used=model_used
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_latest_analysis(
        self,
        market_id: str,
        report_type: str
    ) -> Optional[AnalysisReport]:
        """Get the most recent analysis report."""
        result = await self.session.execute(
            select(AnalysisReport)
            .where(
                and_(
                    AnalysisReport.market_id == market_id,
                    AnalysisReport.report_type == report_type
                )
            )
            .order_by(AnalysisReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_analysis_history(
        self,
        market_id: str,
        report_type: str,
        limit: int = 10
    ) -> list[AnalysisReport]:
        """Get analysis report history."""
        result = await self.session.execute(
            select(AnalysisReport)
            .where(
                and_(
                    AnalysisReport.market_id == market_id,
                    AnalysisReport.report_type == report_type
                )
            )
            .order_by(AnalysisReport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ==================== Signal Event Operations ====================

    async def save_signal(self, signal) -> SignalEvent:
        """Save a signal event."""
        event = SignalEvent(
            indicator_id=signal.indicator_id,
            indicator_name=signal.indicator_name,
            event_type=signal.signal_type,
            severity=signal.severity,
            description=signal.description,
            current_value=signal.current_value,
            threshold_value=signal.threshold_value,
            change_pct=signal.change_pct
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_signals(
        self,
        market_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50
    ) -> list[SignalEvent]:
        """Get signal events with filters."""
        query = select(SignalEvent)

        conditions = []
        if severity:
            conditions.append(SignalEvent.severity == severity)
        if acknowledged is not None:
            conditions.append(SignalEvent.acknowledged == (1 if acknowledged else 0))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(SignalEvent.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def acknowledge_signal(self, signal_id: int) -> bool:
        """Mark a signal as acknowledged."""
        stmt = (
            update(SignalEvent)
            .where(SignalEvent.id == signal_id)
            .values(acknowledged=1, acknowledged_at=datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
