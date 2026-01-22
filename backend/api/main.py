"""FastAPI main application."""
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.storage import init_db
from backend.api.routes import markets, indicators, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()

    # Start scheduler in background (optional)
    try:
        from backend.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        yield
        stop_scheduler()
    except Exception as e:
        import logging
        logging.error(f"Scheduler failed to start: {e}")
        yield


app = FastAPI(
    title="Liquidity Monitor API",
    description="Macroeconomic Liquidity Monitoring System with AI Analysis",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://liquid-pi.vercel.app",
        "http://localhost:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(markets.router)
app.include_router(indicators.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Liquidity Monitor API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/categories")
async def get_categories():
    """Get list of macro factor categories."""
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent / "config" / "indicators.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("categories", [])
    return []


@app.get("/api/overview")
async def get_overview():
    """Get overview of all markets with status."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from backend.storage import get_session, IndicatorRepository
    from backend.processors import LiquidityProcessor
    from backend.core import DataPoint
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent / "config" / "indicators.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {"markets": []}

    markets_config = config.get("markets", [])

    session = await get_session()
    try:
        repo = IndicatorRepository(session)
        latest_data = await repo.get_latest_for_all_indicators()

        markets = []
        for market in markets_config:
            market_id = market["id"]
            indicators = await repo.get_indicators_by_market(market_id)
            primary = next((i for i in indicators if i.is_primary), indicators[0] if indicators else None)

            primary_data = None
            status = {"status": "neutral", "color": "yellow", "emoji": "🟡"}

            if primary and primary.id in latest_data:
                dp = latest_data[primary.id]
                data_points = await repo.get_data_points(primary.id, limit=365)

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
                    change_30d = stats.get("changes", {}).get("30d", {}).get("change_pct")
                    status = LiquidityProcessor.determine_status(change_30d, primary.direction or "up_is_loose")

                    primary_data = {
                        "indicator": {
                            "id": primary.id,
                            "name": primary.name,
                            "name_en": primary.name_en,
                            "unit": primary.unit
                        },
                        "current_value": stats.get("current_value"),
                        "current_date": stats.get("current_date"),
                        "changes": stats.get("changes", {}),
                        "status": status
                    }

            markets.append({
                "market_id": market_id,
                "market_name": market["name"],
                "emoji": market["emoji"],
                "status": status,
                "primary_indicator": primary_data,
                "indicators_count": len(indicators)
            })

        return {
            "markets": markets,
            "last_updated": datetime.utcnow().isoformat()
        }
    finally:
        await session.close()


@app.get("/api/sources")
async def get_data_sources():
    """Get list of available data sources."""
    from backend.core import CollectorRegistry
    # Import collectors to register them
    import backend.collectors  # noqa

    sources = CollectorRegistry.list_sources()
    return {
        "sources": sources,
        "count": len(sources)
    }
