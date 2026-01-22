"""SQLAlchemy ORM models."""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Indicator(Base):
    """Indicator metadata table."""
    __tablename__ = "indicators"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    name_en = Column(String)
    source = Column(String, nullable=False)
    series_id = Column(String)
    market = Column(String, nullable=False)
    category = Column(String)
    unit = Column(String)
    unit_divisor = Column(Float, default=1.0)
    direction = Column(String)  # up_is_loose, down_is_loose
    impact_up = Column(String)
    impact_down = Column(String)
    description = Column(String)
    update_frequency = Column(String)
    is_primary = Column(Integer, default=0)
    enabled = Column(Integer, default=1)

    # New fields for v2
    tags = Column(JSON, default=[])
    dependencies = Column(JSON, default=[])
    api_endpoint = Column(String)
    transform_formula = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataPointModel(Base):
    """Time series data points table."""
    __tablename__ = "data_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    market = Column(String, nullable=False)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_data_points_indicator_timestamp", "indicator_id", "timestamp", unique=True),
    )


class AnalysisReport(Base):
    """AI analysis reports storage."""
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, nullable=False, index=True)
    report_type = Column(String, nullable=False)  # daily_summary, signal_alert, correlation

    summary = Column(Text)
    signals = Column(JSON, default=[])
    risk_level = Column(String)
    recommendations = Column(JSON, default=[])
    confidence = Column(Float)
    reasoning = Column(Text)

    data_snapshot = Column(JSON)  # Data used to generate this report
    prompt_version = Column(String)
    model_used = Column(String)

    user_rating = Column(Integer)  # 1-5
    user_feedback = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_analysis_reports_market_type", "market_id", "report_type"),
    )


class SignalEvent(Base):
    """Signal events record."""
    __tablename__ = "signal_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(String, nullable=False, index=True)
    indicator_name = Column(String)
    event_type = Column(String)  # threshold_breach, trend_change, divergence
    severity = Column(String)  # info, warning, critical

    description = Column(Text)
    current_value = Column(Float)
    threshold_value = Column(Float)
    change_pct = Column(Float)

    acknowledged = Column(Integer, default=0)
    acknowledged_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_signal_events_severity", "severity", "acknowledged"),
    )
