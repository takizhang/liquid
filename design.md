# CLAUDE.md - Macroeconomic Liquidity Monitoring System

This document provides complete implementation details for rebuilding this project from scratch using Claude Code.

## Project Overview

**Type**: Full-stack web application (Python FastAPI backend + React TypeScript frontend)
**Purpose**: Monitor global liquidity indicators across US, China, and Crypto markets with real-time visualization
**Target User**: Individual researcher/investor needing macro liquidity insights for trading decisions

## Directory Structure

```
liquid/
├── backend/                          # Python-based data pipeline
│   ├── __init__.py                  # Empty package init
│   ├── config.py                    # Configuration management
│   ├── requirements.txt             # Python dependencies
│   ├── data/                        # SQLite database location
│   │   └── liquidity.db            # SQLite database file
│   ├── api/
│   │   ├── __init__.py             # Empty
│   │   └── main.py                 # FastAPI application
│   ├── collectors/
│   │   ├── __init__.py             # Exports BaseCollector, FREDCollector
│   │   ├── base.py                 # Base collector interface
│   │   └── fred.py                 # FRED API collector
│   ├── processors/
│   │   ├── __init__.py             # Exports LiquidityProcessor
│   │   └── liquidity.py            # Data processing logic
│   ├── storage/
│   │   ├── __init__.py             # Exports database, models, repository
│   │   ├── database.py             # SQLAlchemy async setup
│   │   ├── models.py               # ORM models
│   │   └── repository.py           # Data access layer
│   ├── scheduler/
│   │   └── __init__.py             # Empty (for future scheduled tasks)
│   └── scripts/
│       ├── init_data.py            # Initialize with real FRED data
│       └── generate_demo_data.py   # Generate demo data
├── frontend/                         # React TypeScript dashboard
│   ├── index.html                   # Entry HTML
│   ├── package.json                 # NPM dependencies
│   ├── tsconfig.json               # TypeScript config
│   ├── tsconfig.app.json           # App TypeScript config
│   ├── tsconfig.node.json          # Node TypeScript config
│   ├── vite.config.ts              # Vite build config
│   ├── postcss.config.js           # PostCSS config
│   ├── eslint.config.js            # ESLint config
│   └── src/
│       ├── main.tsx                # Entry point
│       ├── App.tsx                 # Main app with routing
│       ├── index.css               # Global styles + Tailwind
│       ├── vite-env.d.ts           # Vite type declarations
│       ├── api/
│       │   └── client.ts           # Axios HTTP client
│       ├── types/
│       │   └── index.ts            # TypeScript interfaces
│       ├── hooks/
│       │   └── useApi.ts           # React Query hooks
│       ├── components/
│       │   ├── Layout.tsx          # App layout & navigation
│       │   ├── IndicatorCard.tsx   # Single indicator card
│       │   ├── IndicatorChart.tsx  # ECharts visualization
│       │   ├── MarketCard.tsx      # Market overview card
│       │   └── StatusBadge.tsx     # Status emoji badge
│       └── pages/
│           ├── Overview.tsx        # Market overview page
│           ├── MarketDetail.tsx    # Market detail page
│           └── IndicatorDetail.tsx # Indicator detail page
├── config/
│   └── indicators.yaml             # Indicators configuration
├── start.sh                        # Unified start script
└── CLAUDE.md                       # This file
```

---

## Backend Implementation

### 1. requirements.txt

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pandas>=2.2.0
sqlalchemy>=2.0.25
aiosqlite>=0.19.0
httpx>=0.26.0
python-dotenv>=1.0.0
pydantic>=2.5.3
pydantic-settings>=2.1.0
apscheduler>=3.10.4
fredapi>=0.5.1
pyyaml>=6.0
greenlet>=3.0.0
```

### 2. backend/config.py

Configuration management using Pydantic Settings.

```python
import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # FRED API
    fred_api_key: str = Field(default="", alias="FRED_API_KEY")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/liquidity.db",
        alias="DATABASE_URL"
    )

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    config_dir: Path = base_dir / "config"
    data_dir: Path = base_dir / "backend" / "data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def load_indicators_config() -> dict:
    """Load indicators configuration from YAML file."""
    config_path = Path(__file__).parent.parent / "config" / "indicators.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


settings = Settings()
indicators_config = load_indicators_config()
```

### 3. backend/collectors/base.py

Base collector interface with DataPoint model.

```python
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Optional
import pandas as pd
from pydantic import BaseModel


class DataPoint(BaseModel):
    """Standardized data point format."""
    timestamp: datetime
    indicator_id: str
    value: float
    source: str
    market: str
    metadata: dict = {}
class BaseCollector(ABC):
    """Base class for all data collectors."""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch raw data from the data source.
        Returns DataFrame with columns: date, value
        """
        pass

    def normalize(
        self,
        raw_data: pd.DataFrame,
        indicator_id: str,
        market: str,
        unit_divisor: float = 1.0,
        metadata: dict = {}
    ) -> list[DataPoint]:
        """Normalize raw data to standard format."""
        data_points = []
        for _, row in raw_data.iterrows():
            timestamp = row["date"]
            if isinstance(timestamp, date) and not isinstance(timestamp, datetime):
                timestamp = datetime.combine(timestamp, datetime.min.time())

            data_points.append(DataPoint(
                timestamp=timestamp,
                indicator_id=indicator_id,
                value=float(row["value"]) / unit_divisor,
                source=self.source_name,
                market=market,
                metadata=metadata
            ))
        return data_points

    def validate(self, data: list[DataPoint]) -> bool:
        """Validate data points - check for NaN values."""
        if not data:
            return True
        for point in data:
            if pd.isna(point.value):
                raise ValueError(f"NaN value found for {point.indicator_id} at {point.timestamp}")
        return True
```

### 4. backend/collectors/fred.py

FRED API collector implementation.

```python
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import httpx
import pandas as pd
from .base import BaseCollector, DataPoint
from backend.config import settings


class FREDCollector(BaseCollector):
    """Collector for Federal Reserve Economic Data (FRED)."""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self):
        super().__init__("FRED")
        self.api_key = settings.fred_api_key

    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Fetch data from FRED API."""
        if not self.api_key:
            raise ValueError("FRED API key not configured. Set FRED_API_KEY environment variable.")
# Default to last 2 years of data
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=730)

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date.isoformat(),
            "observation_end": end_date.isoformat(),
            "sort_order": "asc"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        observations = data.get("observations", [])

        if not observations:
            return pd.DataFrame(columns=["date", "value"])

        records = []
        for obs in observations:
            try:
                value = float(obs["value"])
                records.append({
                    "date": datetime.strptime(obs["date"], "%Y-%m-%d"),
                    "value": value
                })
            except (ValueError, KeyError):
                # Skip invalid entries (e.g., "." for missing data)
                continue

        return pd.DataFrame(records)

    async def fetch_multiple(
        self,
        indicators: list[dict],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict[str, list[DataPoint]]:
        """Fetch multiple indicators concurrently."""
        results = {}

        async def fetch_one(indicator: dict):
            indicator_id = indicator["id"]
            series_id = indicator["series_id"]
            market = indicator.get("market", "us")
            unit_divisor = indicator.get("unit_divisor", 1.0)

            try:
                df = await self.fetch(indicator_id, series_id, start_date, end_date)
                if df.empty:
                    return indicator_id, []

                data_points = self.normalize(df, indicator_id, market, unit_divisor)
                self.validate(data_points)
                return indicator_id, data_points
            except Exception as e:
                print(f"Error fetching {indicator_id}: {e}")
                return indicator_id, []

        tasks = [fetch_one(ind) for ind in indicators]
        completed = await asyncio.gather(*tasks)

        for indicator_id, data_points in completed:
            results[indicator_id] = data_points

        return results
```

### 5. backend/collectors/__init__.py

```python
from .base import BaseCollector
from .fred import FREDCollector

__all__ = ["BaseCollector", "FREDCollector"]
```

### 6. backend/storage/models.py

SQLAlchemy ORM models.

```python
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Index
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
    direction = Column(String)  # up_is_loose, down_is_loose
    impact_up = Column(String)
    impact_down = Column(String)
    description = Column(String)
    update_frequency = Column(String)
    is_primary = Column(Integer, default=0)
    enabled = Column(Integer, default=1)
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
```

### 7. backend/storage/database.py

Async SQLAlchemy database setup.

```python
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.config import settings
from .models import Base

# Ensure data directory exists
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 8. backend/storage/repository.py

Data access layer with upsert operations.

```python
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert
from .models import Indicator, DataPointModel
from backend.collectors.base import DataPoint


class IndicatorRepository:
    """Repository for indicator data operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Indicator metadata operations

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
            direction=indicator_config.get("direction"),
            impact_up=indicator_config.get("impact", {}).get("up"),
            impact_down=indicator_config.get("impact", {}).get("down"),
            description=indicator_config.get("description"),
            update_frequency=indicator_config.get("update_frequency"),
            is_primary=1 if indicator_config.get("is_primary") else 0,
            enabled=0 if indicator_config.get("enabled") is False else 1,
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
                "direction": indicator_config.get("direction"),
                "impact_up": indicator_config.get("impact", {}).get("up"),
                "impact_down": indicator_config.get("impact", {}).get("down"),
                "description": indicator_config.get("description"),
                "update_frequency": indicator_config.get("update_frequency"),
                "is_primary": 1 if indicator_config.get("is_primary") else 0,
                "enabled": 0 if indicator_config.get("enabled") is False else 1,
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
            ).order_by(Indicator.id)
        )
        return list(result.scalars().all())

    async def get_all_indicators(self) -> list[Indicator]:
        """Get all enabled indicators."""
        result = await self.session.execute(
            select(Indicator).where(Indicator.enabled == 1).order_by(Indicator.market, Indicator.id)
        )
        return list(result.scalars().all())

    # Data point operations

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
            "change_pct": change_pct,
            "start_date": first.timestamp,
            "end_date": last.timestamp
        }
```

### 9. backend/storage/__init__.py

```python
from .database import get_db, init_db, engine, async_session
from .models import Base, Indicator, DataPointModel
from .repository import IndicatorRepository

__all__ = [
    "get_db", "init_db", "engine", "async_session",
    "Base", "Indicator", "DataPointModel",
    "IndicatorRepository"
]
```

### 10. backend/processors/liquidity.py

Data processing and status calculation.

```python
from datetime import datetime
from typing import Optional
import pandas as pd
from backend.collectors.base import DataPoint


class LiquidityProcessor:
    """Processor for calculating liquidity metrics."""

    @staticmethod
    def calculate_net_liquidity(
        fed_balance: list[DataPoint],
        rrp: list[DataPoint],
        tga: list[DataPoint]
    ) -> list[DataPoint]:
        """
        Calculate US net liquidity.
        Net Liquidity = Fed Balance Sheet - RRP - TGA
        """
        def to_df(points: list[DataPoint], value_col: str) -> pd.DataFrame:
            if not points:
                return pd.DataFrame()
            data = [(p.timestamp.date(), p.value) for p in points]
            df = pd.DataFrame(data, columns=["date", value_col])
            return df.drop_duplicates(subset=["date"], keep="last")
df_fed = to_df(fed_balance, "fed")
        df_rrp = to_df(rrp, "rrp")
        df_tga = to_df(tga, "tga")

        if df_fed.empty:
            return []

        # Merge all data
        df = df_fed
        if not df_rrp.empty:
            df = df.merge(df_rrp, on="date", how="left")
        else:
            df["rrp"] = 0

        if not df_tga.empty:
            df = df.merge(df_tga, on="date", how="left")
        else:
            df["tga"] = 0

        # Forward fill missing values
        df = df.sort_values("date")
        df = df.fillna(method="ffill").fillna(0)

        # Calculate net liquidity
        df["net_liquidity"] = df["fed"] - df["rrp"] - df["tga"]

        # Convert back to DataPoints
        result = []
        for _, row in df.iterrows():
            result.append(DataPoint(
                timestamp=datetime.combine(row["date"], datetime.min.time()),
                indicator_id="net_liquidity",
                value=row["net_liquidity"],
                source="calculated",
                market="us",
                metadata={
                    "fed": row["fed"],
                    "rrp": row["rrp"],
                    "tga": row["tga"]
                }
            ))

        return result

    @staticmethod
    def calculate_change_stats(
        data_points: list[DataPoint],
        periods: list[int] = [7, 30, 90, 365]
    ) -> dict:
        """Calculate change statistics for various periods."""
        if not data_points:
            return {}

        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        latest = sorted_points[-1]
        latest_date = latest.timestamp

        stats = {
            "current_value": latest.value,
            "current_date": latest.timestamp.isoformat(),
            "changes": {}
        }

        for days in periods:
            target_date = latest_date - pd.Timedelta(days=days)

            # Find closest data point to target date
            closest = None
            min_diff = float("inf")
            for point in sorted_points:
                diff = abs((point.timestamp - target_date).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest = point

            if closest and closest.value != 0:
                change = latest.value - closest.value
                change_pct = (change / closest.value) * 100
                stats["changes"][f"{days}d"] = {
                    "change": round(change, 4),
                    "change_pct": round(change_pct, 2),
                    "from_value": closest.value,
                    "from_date": closest.timestamp.isoformat()
                }

        return stats

    @staticmethod
    def determine_status(
        change_pct_30d: Optional[float],
        direction: str
    ) -> dict:
        """
        Determine indicator status based on recent change and direction.
        Returns: status (bullish/slightly_bullish/neutral/slightly_bearish/bearish)
        """
        if change_pct_30d is None:
            return {"status": "neutral", "color": "yellow", "emoji": "🟡"}

        # Determine if change is positive for liquidity
        if direction == "up_is_loose":
            is_positive = change_pct_30d > 0
        else:  # down_is_loose
            is_positive = change_pct_30d < 0

        threshold = 2.0  # 2% threshold for significant change

        if is_positive:
            if abs(change_pct_30d) > threshold:
                return {"status": "bullish", "color": "green", "emoji": "🟢"}
            else:
                return {"status": "slightly_bullish", "color": "green", "emoji": "🟢"}
        else:
            if abs(change_pct_30d) > threshold:
                return {"status": "bearish", "color": "red", "emoji": "🔴"}
            else:
                return {"status": "slightly_bearish", "color": "red", "emoji": "🔴"}
```

### 11. backend/processors/__init__.py

```python
from .liquidity import LiquidityProcessor

__all__ = ["LiquidityProcessor"]
```

### 12. backend/api/main.py

FastAPI application with all endpoints.

```python
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.storage import get_db, init_db, IndicatorRepository
from backend.processors import LiquidityProcessor
from backend.config import indicators_config


# Pydantic models for API responses
class CategoryResponse(BaseModel):
    id: str
    name: str
    name_en: str
    description: str
    color: str

class IndicatorResponse(BaseModel):
    id: str
    name: str
    name_en: Optional[str]
    source: str
    market: str
    category: Optional[str]
    unit: Optional[str]
    direction: Optional[str]
    impact_up: Optional[str]
    impact_down: Optional[str]
    description: Optional[str]
    is_primary: bool


class DataPointResponse(BaseModel):
    timestamp: str
    value: float
    indicator_id: str


class IndicatorDataResponse(BaseModel):
    indicator: IndicatorResponse
    current_value: Optional[float]
    current_date: Optional[str]
    changes: dict
    status: dict
    data_points: list[DataPointResponse]


class MarketOverview(BaseModel):
    market_id: str
    market_name: str
    emoji: str
    status: dict
    primary_indicator: Optional[IndicatorDataResponse]
    indicators_count: int


class OverviewResponse(BaseModel):
    markets: list[MarketOverview]
    last_updated: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Liquidity Monitor API",
    description="Macroeconomic Liquidity Monitoring System API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_repository(db: AsyncSession = Depends(get_db)) -> IndicatorRepository:
    return IndicatorRepository(db)


@app.get("/")
async def root():
    return {"message": "Liquidity Monitor API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/markets")
async def get_markets():
    """Get list of available markets."""
    return indicators_config.get("markets", [])


@app.get("/api/categories")
async def get_categories():
    """Get list of macro factor categories."""
    return indicators_config.get("categories", [])


@app.get("/api/overview", response_model=OverviewResponse)
async def get_overview(repo: IndicatorRepository = Depends(get_repository)):
    """Get overview of all markets with status."""
    markets_config = indicators_config.get("markets", [])
    latest_data = await repo.get_latest_for_all_indicators()

    markets = []
    for market in markets_config:
        market_id = market["id"]
        indicators = await repo.get_indicators_by_market(market_id)
        primary = next((i for i in indicators if i.is_primary), None)
        if not primary and indicators:
            primary = indicators[0]

        primary_data = None
        status = {"status": "neutral", "color": "yellow", "emoji": "🟡"}

        if primary and primary.id in latest_data:
            dp = latest_data[primary.id]
            data_points = await repo.get_data_points(primary.id, limit=365)

            from backend.collectors.base import DataPoint as DP
            points = [
                DP(
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
            status = LiquidityProcessor.determine_status(change_30d, primary.direction or "up_is_loose")

            primary_data = IndicatorDataResponse(
                indicator=IndicatorResponse(
                    id=primary.id,
                    name=primary.name,
                    name_en=primary.name_en,
                    source=primary.source,
                    market=primary.market,
                    category=primary.category,
                    unit=primary.unit,
                    direction=primary.direction,
                    impact_up=primary.impact_up,
                    impact_down=primary.impact_down,
                    description=primary.description,
                    is_primary=bool(primary.is_primary)
                ),
                current_value=stats.get("current_value"),
                current_date=stats.get("current_date"),
                changes=stats.get("changes", {}),
                status=status,
                data_points=[]
            )

        markets.append(MarketOverview(
            market_id=market_id,
            market_name=market["name"],
            emoji=market["emoji"],
            status=status,
            primary_indicator=primary_data,
            indicators_count=len(indicators)
        ))

    return OverviewResponse(
        markets=markets,
        last_updated=datetime.utcnow().isoformat()
    )


@app.get("/api/markets/{market_id}/indicators")
async def get_market_indicators(
    market_id: str,
    repo: IndicatorRepository = Depends(get_repository)
):
    """Get all indicators for a specific market."""
    indicators = await repo.get_indicators_by_market(market_id)
    return [
        IndicatorResponse(
            id=i.id,
            name=i.name,
            name_en=i.name_en,
            source=i.source,
            market=i.market,
            category=i.category,
            unit=i.unit,
            direction=i.direction,
            impact_up=i.impact_up,
            impact_down=i.impact_down,
            description=i.description,
            is_primary=bool(i.is_primary)
        )
        for i in indicators
    ]


@app.get("/api/indicators/{indicator_id}", response_model=IndicatorDataResponse)
async def get_indicator_data(
    indicator_id: str,
    days: int = Query(default=365, ge=1, le=3650),
    repo: IndicatorRepository = Depends(get_repository)
):
    """Get indicator data with statistics."""
    indicator = await repo.get_indicator(indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    start_date = datetime.utcnow() - timedelta(days=days)
    data_points = await repo.get_data_points(indicator_id, start_date=start_date, limit=days * 2)

    from backend.collectors.base import DataPoint as DP
    points = [
        DP(
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

    return IndicatorDataResponse(
        indicator=IndicatorResponse(
            id=indicator.id,
            name=indicator.name,
            name_en=indicator.name_en,
            source=indicator.source,
            market=indicator.market,
            category=indicator.category,
            unit=indicator.unit,
            direction=indicator.direction,
            impact_up=indicator.impact_up,
            impact_down=indicator.impact_down,
            description=indicator.description,
            is_primary=bool(indicator.is_primary)
        ),
        current_value=stats.get("current_value"),
        current_date=stats.get("current_date"),
        changes=stats.get("changes", {}),
        status=status,
        data_points=[
            DataPointResponse(
                timestamp=p.timestamp.isoformat(),
                value=p.value,
                indicator_id=p.indicator_id
            )
            for p in sorted(data_points, key=lambda x: x.timestamp)
        ]
    )


@app.get("/api/indicators/{indicator_id}/data")
async def get_indicator_raw_data(
    indicator_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=500, ge=1, le=5000),
    repo: IndicatorRepository = Depends(get_repository)
): """Get raw data points for an indicator."""
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
```

### 13. backend/api/__init__.py

```python
# Empty file
```

### 14. backend/__init__.py

```python
# Empty file
```

### 15. backend/scheduler/__init__.py

```python
# Empty file (placeholder for future scheduled tasks)
```

---

## Frontend Implementation

### 1. package.json

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tailwindcss/postcss": "^4.1.18",
    "@tanstack/react-query": "^5.90.19",
    "axios": "^1.13.2",
    "echarts": "^6.0.0",
    "echarts-for-react": "^3.0.5",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.12.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.1",
    "@types/node": "^24.10.1",
    "@types/react": "^19.2.5",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^5.1.1",
    "autoprefixer": "^10.4.23",
    "eslint": "^9.39.1",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.4.24",
    "globals": "^16.5.0",
    "postcss": "^8.5.6",
    "tailwindcss": "^4.1.18",
    "typescript": "~5.9.3",
    "typescript-eslint": "^8.46.4",
    "vite": "^7.2.4"
  }
}
```

### 2. vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

### 3. frontend/src/main.tsx

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### 4. frontend/src/index.css

```css
@import "tailwindcss";

:root {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: light;
  color: #213547;
  background-color: #f9fafb;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

.card {
  background-color: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  border: 1px solid #f3f4f6;
  padding: 1.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: color 0.15s, background-color 0.15s;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}
btn-secondary:hover {
  background-color: #e5e7eb;
}
```

### 5. frontend/src/App.tsx

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { Overview } from './pages/Overview';
import { MarketDetail } from './pages/MarketDetail';
import { IndicatorDetail } from './pages/IndicatorDetail';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="market/:marketId" element={<MarketDetail />} />
            <Route path="indicator/:indicatorId" element={<IndicatorDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

### 6. frontend/src/types/index.ts

```typescript
export interface Market {
  id: string;
  name: string;
  emoji: string;
}

export interface Category {
  id: string;
  name: string;
  name_en: string;
  description: string;
  color: string;
}

export interface Indicator {
  id: string;
  name: string;
  name_en?: string;
  source: string;
  market: string;
  category?: string;
  unit?: string;
  direction?: string;
  impact_up?: string;
  impact_down?: string;
  description?: string;
  is_primary: boolean;
}

export interface DataPoint {
  timestamp: string;
  value: number;
  indicator_id: string;
}

export interface ChangeStats {
  change: number;
  change_pct: number;
  from_value: number;
  from_date: string;
}

export interface Status {
  status: string;
  color: string;
  emoji: string;
}

export interface IndicatorData {
  indicator: Indicator;
  current_value?: number;
  current_date?: string;
  changes: Record<string, ChangeStats>;
  status: Status;
  data_points: DataPoint[];
}

export interface MarketOverview {
  market_id: string;
  market_name: string;
  emoji: string;
  status: Status;
  primary_indicator?: IndicatorData;
  indicators_count: number;
}

export interface OverviewResponse {
  markets: MarketOverview[];
  last_updated: string;
}
```

### 7. frontend/src/api/client.ts

```typescript
import axios from 'axios';
import type { OverviewResponse, IndicatorData, Indicator, Market, Category } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  health: async () => {
    const { data } = await client.get('/api/health');
    return data;
  },

  getMarkets: async (): Promise<Market[]> => {
    const { data } = await client.get('/api/markets');
    return data;
  },

  getCategories: async (): Promise<Category[]> => {
    const { data } = await client.get('/api/categories');
    return data;
  },

  getOverview: async (): Promise<OverviewResponse> => {
    const { data } = await client.get('/api/overview');
    return data;
  },

  getMarketIndicators: async (marketId: string): Promise<Indicator[]> => {
    const { data } = await client.get(`/api/markets/${marketId}/indicators`);
    return data;
  },

  getIndicatorData: async (indicatorId: string, days: number = 365): Promise<IndicatorData> => {
    const { data } = await client.get(`/api/indicators/${indicatorId}`, {
      params: { days },
    });
    return data;
  },

  getIndicatorRawData: async (
    indicatorId: string,
    startDate?: string,
    endDate?: string,
    limit: number = 500
  ) => {
    const { data } = await client.get(`/api/indicators/${indicatorId}/data`, {
      params: { start_date: startDate, end_date: endDate, limit },
    });
    return data;
  },
};

export default api;
```

### 8. frontend/src/hooks/useApi.ts

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

export const useOverview = () => {
  return useQuery({
    queryKey: ['overview'],
    queryFn: api.getOverview,
    refetchInterval: 60000,
  });
};

export const useMarkets = () => {
  return useQuery({
    queryKey: ['markets'],
    queryFn: api.getMarkets,
  });
};

export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: api.getCategories,
  });
};

export const useMarketIndicators = (marketId: string) => {
  return useQuery({
    queryKey: ['market-indicators', marketId],
    queryFn: () => api.getMarketIndicators(marketId),
    enabled: !!marketId,
  });
};

export const useIndicatorData = (indicatorId: string, days: number = 365) => {
  return useQuery({
    queryKey: ['indicator', indicatorId, days],
    queryFn: () => api.getIndicatorData(indicatorId, days),
    enabled: !!indicatorId,
  });
};
```

### 9. frontend/src/components/Layout.tsx

```typescript
import { Link, Outlet, useLocation } from 'react-router-dom';

export const Layout = () => {
  const location = useLocation();
return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="flex items-center gap-2">
              <span className="text-2xl">🌊</span>
              <h1 className="text-xl font-bold text-gray-900">
                Liquidity Monitor
              </h1>
            </Link>
            <nav className="flex gap-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === '/'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Overview
              </Link>
              <Link
                to="/market/us"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname.startsWith('/market/us')
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🇺🇸 US
              </Link>
              <Link
                to="/market/china"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname.startsWith('/market/china')
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🇨🇳 China
              </Link>
              <Link
                to="/market/crypto"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname.startsWith('/market/crypto')
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🪙 Crypto
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          Macroeconomic Liquidity Monitoring System
        </div>
      </footer>
    </div>
  );
};
```

### 10. frontend/src/components/StatusBadge.tsx

```typescript
import type { Status } from '../types';

interface StatusBadgeProps {
  status: Status;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge = ({ status, size = 'md' }: StatusBadgeProps) => {
  const sizeClasses = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-4xl',
  };

  return (
    <span className={sizeClasses[size]} title={status.status}>
      {status.emoji}
    </span>
  );
};
```

### 11. frontend/src/components/IndicatorChart.tsx

```typescript
import ReactECharts from 'echarts-for-react';
import type { DataPoint } from '../types';

interface IndicatorChartProps {
  dataPoints: DataPoint[];
  title?: string;
  unit?: string;
  height?: number;
  mini?: boolean;
}

export const IndicatorChart = ({
  dataPoints,
  title,
  unit = '',
  height = 300,
  mini = false,
}: IndicatorChartProps) => {
  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-gray-400"
      >
        No data available
      </div>
    );
  }

  const sortedData = [...dataPoints].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const dates = sortedData.map((d) =>
    new Date(d.timestamp).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    })
  );
  const values = sortedData.map((d) => d.value);

  const firstValue = values[0];
  const lastValue = values[values.length - 1];
  const trendColor = lastValue >= firstValue ? '#10b981' : '#ef4444';

  const option = {
    title: title && !mini
      ? {
          text: title,
          left: 'center',
          textStyle: { fontSize: 14, fontWeight: 500 },
        }
      : undefined,
    tooltip: mini
      ? undefined
      : {
          trigger: 'axis',
          formatter: (params: any) => {
            const data = params[0];
            const date = new Date(sortedData[data.dataIndex].timestamp);
            const formattedDate = date.toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            });
            return `${formattedDate}<br/>${data.value.toFixed(2)} ${unit}`;
          },
        },
    grid: {
      left: mini ? 0 : 60,
      right: mini ? 0 : 20,
      top: mini ? 5 : title ? 40 : 20,
      bottom: mini ? 0 : 30,
      containLabel: !mini,
    },
    xAxis: {
      type: 'category',
      data: dates,
      show: !mini,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      show: !mini,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
        formatter: (value: number) => {
          if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
          }
          return value.toFixed(1);
        },
      },
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: mini ? 'none' : 'circle',
        symbolSize: 4,
        lineStyle: { color: trendColor, width: mini ? 1.5 : 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: trendColor + '40' },
              { offset: 1, color: trendColor + '05' },
            ],
          },
        },
        itemStyle: { color: trendColor },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
};
```

### 12. frontend/src/components/IndicatorCard.tsx

```typescript
import { useNavigate } from 'react-router-dom';
import { IndicatorChart } from './IndicatorChart';
import { StatusBadge } from './StatusBadge';
import type { IndicatorData } from '../types';

interface IndicatorCardProps {
  data: IndicatorData;
  showChart?: boolean;
}

export const IndicatorCard = ({ data, showChart = true }: IndicatorCardProps) => {
  const navigate = useNavigate();
  const { indicator, current_value, changes, status, data_points } = data;

  const formatValue = (value: number | undefined, unit?: string) => {
    if (value === undefined) return '-';
    if (unit === 'T') return `$${value.toFixed(2)}T`;
    if (unit === 'B') return `$${value.toFixed(1)}B`;
    if (unit === '%') return `${value.toFixed(2)}%`;
    return value.toFixed(2);
  };

  const formatChange = (change: number | undefined) => {
    if (change === undefined) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const change30d = changes['30d']?.change_pct;
  const change7d = changes['7d']?.change_pct;
return (
    <div
      className="card cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => navigate(`/indicator/${indicator.id}`)}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">{indicator.name}</h3>
          {indicator.name_en && (
            <p className="text-xs text-gray-500">{indicator.name_en}</p>
          )}
        </div>
        <StatusBadge status={status} size="sm" />
      </div>

      <div className="mb-4">
        <p className="text-2xl font-bold text-gray-900">
          {formatValue(current_value, indicator.unit)}
        </p>
        <div className="flex gap-4 mt-1">
          {change7d !== undefined && (
            <span className={`text-sm ${change7d >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              7d: {formatChange(change7d)}
            </span>
          )}
          {change30d !== undefined && (
            <span className={`text-sm ${change30d >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              30d: {formatChange(change30d)}
            </span>
          )}
        </div>
      </div>

      {showChart && data_points.length > 0 && (
        <div className="mb-4 -mx-2">
          <IndicatorChart dataPoints={data_points.slice(-90)} height={80} mini />
        </div>
      )}

      <div className="border-t pt-3 mt-auto">
        <p className="text-xs font-medium text-gray-500 mb-1">
          {indicator.direction === 'up_is_loose' ? '↑ 上升' : '↓ 下降'}
        </p>
        <p className="text-xs text-gray-600">
          {indicator.direction === 'up_is_loose' ? indicator.impact_up : indicator.impact_down}
        </p>
      </div>
    </div>
  );
};
```

### 13. frontend/src/components/MarketCard.tsx

```typescript
import { useNavigate } from 'react-router-dom';
import { StatusBadge } from './StatusBadge';
import type { MarketOverview } from '../types';

interface MarketCardProps {
  market: MarketOverview;
}

export const MarketCard = ({ market }: MarketCardProps) => {
  const navigate = useNavigate();
  const { market_id, market_name, emoji, status, primary_indicator, indicators_count } = market;

  const formatValue = (value: number | undefined, unit?: string) => {
    if (value === undefined) return '-';
    if (unit === 'T') return `$${value.toFixed(2)}T`;
    if (unit === 'B') return `$${value.toFixed(1)}B`;
    if (unit === '%') return `${value.toFixed(2)}%`;
    return value.toFixed(2);
  };

  const formatChange = (change: number | undefined) => {
    if (change === undefined) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const change30d = primary_indicator?.changes['30d']?.change_pct;

  return (
    <div
      className="card cursor-pointer hover:shadow-lg transition-all transform hover:-translate-y-1"
      onClick={() => navigate(`/market/${market_id}`)}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{emoji}</span>
          <h2 className="text-xl font-bold text-gray-900">{market_name}</h2>
        </div>
        <StatusBadge status={status} size="lg" />
      </div>

      {primary_indicator ? (
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-1">{primary_indicator.indicator.name}</p>
          <p className="text-3xl font-bold text-gray-900">
            {formatValue(primary_indicator.current_value, primary_indicator.indicator.unit)}
          </p>
          {change30d !== undefined && (
            <p className={`text-sm font-medium mt-1 ${change30d >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              30d: {formatChange(change30d)}{change30d >= 0 ? ' ↑' : ' ↓'}
            </p>
          )}
        </div>
      ) : (
        <div className="mb-4">
          <p className="text-gray-400">No data available</p>
        </div>
      )}

      <div className="border-t pt-3">
        <p className="text-sm text-gray-600">
          {status.status === 'bullish' && '流动性充裕，利好风险资产'}
          {status.status === 'slightly_bullish' && '流动性边际改善'}
          {status.status === 'neutral' && '流动性中性'}
          {status.status === 'slightly_bearish' && '流动性边际收紧'}
          {status.status === 'bearish' && '流动性收紧，风险资产承压'}
        </p>
        <p className="text-xs text-gray-400 mt-2">{indicators_count} indicators tracked</p>
      </div>

      <div className="mt-4 text-center">
        <span className="text-sm text-blue-600 hover:text-blue-800">View Details →</span>
      </div>
    </div>
  );
};
```

### 14. frontend/src/pages/Overview.tsx

```typescript
import { useOverview } from '../hooks/useApi';
import { MarketCard } from '../components/MarketCard';

export const Overview = () => {
  const { data, isLoading, error } = useOverview();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-500 mb-2">Error loading data</p>
          <p className="text-sm text-gray-500">Make sure the backend server is running on port 8000</p>
        </div>
      </div>
    );
  }

  if (!data || data.markets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-500 mb-2">No data available</p>
          <p className="text-sm text-gray-400">Run the data initialization script to fetch data</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Global Liquidity Overview</h1>
        <p className="text-gray-600">Monitor liquidity conditions across major markets</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {data.markets.map((market) => (
          <MarketCard key={market.market_id} market={market} />
        ))}
      </div>

      <div className="card bg-gradient-to-r from-blue-50 to-indigo-50">
        <h3 className="font-semibold text-gray-900 mb-4">Quick Reference</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="font-medium text-gray-700">🟢 Bullish Signal</p>
            <p className="text-gray-600">Liquidity expanding, favorable for risk assets</p>
          </div>
          <div>
            <p className="font-medium text-gray-700">🟡 Neutral</p>
            <p className="text-gray-600">Mixed signals, watch for trend changes</p>
          </div>
          <div>
            <p className="font-medium text-gray-700">🔴 Bearish Signal</p>
            <p className="text-gray-600">Liquidity tightening, caution advised</p>
          </div>
        </div>
      </div>

      <div className="mt-4 text-right text-xs text-gray-400">
        Last updated: {new Date(data.last_updated).toLocaleString()}
      </div>
    </div>
  );
};
```

### 15. frontend/src/pages/MarketDetail.tsx

See the complete implementation in the codebase. Key features:
- Displays market info header with emoji
- Primary indicator section with large chart
- Category legend showing available categories
- Indicators grouped by category with lazy loading
- Skeleton placeholders for loading states

### 16. frontend/src/pages/IndicatorDetail.tsx

See the complete implementation in the codebase. Key features:
- Large historical chart (1 year)
- Current value and change stats (7d, 30d, 90d)
- Impact boxes for up/down movements
- Metadata: source, market, unit, direction
- Breadcrumb navigation

---

## Configuration
### config/indicators.yaml

The configuration file defines:
1. **Categories** (8 total): liquidity, inflation, growth, rates, dollar, credit, sentiment, positioning
2. **Markets** (3 total): us, china, crypto
3. **Indicators** (50+ total): Each with id, name, source, series_id, market, category, unit, direction, impact, description

Key indicator structure:
```yaml
indicators:
  - id: "fed_balance_sheet"
    name: "Fed资产负债表"
    name_en: "Fed Balance Sheet"
    source: "FRED"
    series_id: "WALCL"
    market: "us"
    category: "liquidity"
    update_frequency: "weekly"
    unit: "T"
    unit_divisor: 1000000
    direction: "up_is_loose"
    impact:
      up: "QE/扩表 = 利好风险资产"
      down: "QT/缩表 = 利空风险资产"
    description: "美联储总资产，反映货币政策松紧程度"
    is_primary: true  # Only for primary indicators
```

---

## Start Script (start.sh)

```bash
#!/bin/bash

# Liquidity Monitor - Start Script
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================"
echo "  Liquidity Monitor - Starting..."
echo "========================================"

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "Setting up backend virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Activate venv and generate demo data if database doesn't exist
cd backend
source venv/bin/activate

if [ ! -f "data/liquidity.db" ]; then
    echo ""
    echo "Generating demo data..."
    PYTHONPATH="$PROJECT_DIR" python scripts/generate_demo_data.py
fi

# Start backend
echo ""
echo "Starting backend server on http://localhost:8000..."
PYTHONPATH="$PROJECT_DIR" uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ../frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo ""
echo "Starting frontend server on http://localhost:5173..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Servers started!"
echo "  - Backend:  http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
```

---

## Running the Application

### Quick Start
```bash
chmod +x start.sh
./start.sh
```

### Manual Start

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=".." python scripts/generate_demo_data.py  # Generate demo data
PYTHONPATH=".." uvicorn api.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

**Backend (.env):**
```
FRED_API_KEY=your_key_here  # Optional, for real data
DATABASE_URL=sqlite+aiosqlite:///./data/liquidity.db
API_HOST=0.0.0.0
API_PORT=8000
```

**Frontend:**
```
VITE_API_URL=http://localhost:8000
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check root |
| GET | `/api/health` | Health status |
| GET | `/api/markets` | List available markets |
| GET | `/api/categories` | List macro factor categories |
| GET | `/api/overview` | Market overview with status |
| GET | `/api/markets/{market_id}/indicators` | Get market indicators |
| GET | `/api/indicators/{indicator_id}` | Get indicator data with stats |
| GET | `/api/indicators/{indicator_id}/data` | Get raw data points |

---
## Database Schema

### Indicators Table
- id (PK), name, name_en, source, series_id, market, category, unit, direction
- impact_up, impact_down, description, update_frequency, is_primary, enabled
- created_at, updated_at

### Data Points Table
- id (PK), indicator_id (FK, indexed), timestamp, value, source, market, extra_data
- Unique constraint on (indicator_id, timestamp)

---

## Key Architecture Decisions

1. **Pluggable Collectors**: Easy to add new data sources
2. **Async/Await**: Non-blocking I/O for high performance
3. **SQLite**: Simple for development (upgradeable to PostgreSQL)
4. **React Query**: Efficient data fetching and caching
5. **ECharts**: Rich, performant charting
6. **Tailwind CSS**: Utility-first styling
7. **Configuration-driven**: YAML-based indicator setup

---

## Future Expansion Points

- New collectors: PBOC, ECB, CoinGecko, Glassnode
- New macro dimensions: Inflation, Growth, Rates, Credit spreads
- Advanced analytics: Factor correlation matrices, regime detection
- Scheduler for automated data collection
- Export features: PDF reports, data export, custom alerts
