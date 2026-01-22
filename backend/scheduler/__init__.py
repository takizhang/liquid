"""Scheduler for periodic data collection."""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.core import CollectorRegistry
from backend.storage import get_session, IndicatorRepository
from backend.processors.liquidity import LiquidityProcessor
import backend.collectors  # noqa - register collectors

logger = logging.getLogger(__name__)


async def calculate_computed_indicators(repo: IndicatorRepository):
    """Calculate computed indicators like net_liquidity."""
    logger.info("Calculating computed indicators...")

    try:
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=400)

        # Get data for net_liquidity calculation
        fed_data = await repo.get_data_points("fed_balance_sheet", start_date=start_date)
        rrp_data = await repo.get_data_points("rrp", start_date=start_date)
        tga_data = await repo.get_data_points("tga", start_date=start_date)

        if fed_data:
            # Convert DataPointModel to DataPoint for processor
            from backend.core import DataPoint as CoreDataPoint

            def to_core_dp(models):
                return [CoreDataPoint(
                    timestamp=m.timestamp,
                    indicator_id=m.indicator_id,
                    value=m.value,
                    source=m.source,
                    market=m.market
                ) for m in models]

            net_liquidity_points = LiquidityProcessor.calculate_net_liquidity(
                fed_balance=to_core_dp(fed_data),
                rrp=to_core_dp(rrp_data),
                tga=to_core_dp(tga_data)
            )

            if net_liquidity_points:
                await repo.save_data_points(net_liquidity_points)
                logger.info(f"Calculated {len(net_liquidity_points)} net_liquidity data points")
        else:
            logger.warning("No Fed balance sheet data for net_liquidity calculation")

    except Exception as e:
        logger.error(f"Error calculating computed indicators: {e}")

scheduler = AsyncIOScheduler()


async def collect_all_data():
    """Collect data for all registered indicators."""
    logger.info("Starting scheduled data collection...")

    try:
        session = await get_session()
        repo = IndicatorRepository(session)

        # Get all indicators
        indicators = await repo.get_all_indicators()
        logger.info(f"Found {len(indicators)} indicators to update")

        for indicator in indicators:
            # Skip computed indicators - they'll be calculated after
            if indicator.is_computed:
                logger.info(f"Skipping computed indicator: {indicator.name}")
                continue

            try:
                # Get collector for this indicator
                try:
                    collector = CollectorRegistry.get(indicator.source)
                except ValueError:
                    logger.warning(f"No collector found for source: {indicator.source}")
                    continue

                # Fetch data
                data_points = await collector.fetch(
                    indicator_id=indicator.id,
                    series_id=indicator.series_id,
                    market=indicator.market
                )

                if data_points:
                    # Save to database
                    await repo.save_data_points(data_points)
                    logger.info(f"Updated {len(data_points)} data points for {indicator.name}")
                else:
                    logger.warning(f"No data returned for {indicator.name}")

                # Add delay to avoid API rate limits
                # CoinGecko free tier: 10-30 calls/min, use 3s delay
                delay = 3 if indicator.source == "CoinGecko" else 1
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Error collecting data for {indicator.name}: {e}")
                continue

        # Calculate computed indicators (net_liquidity)
        await calculate_computed_indicators(repo)

        await session.close()
        logger.info("Scheduled data collection completed")

    except Exception as e:
        logger.error(f"Error in scheduled data collection: {e}")


def start_scheduler():
    """Start the scheduler with configured jobs."""
    # Run data collection every 6 hours
    scheduler.add_job(
        collect_all_data,
        CronTrigger(hour="*/6"),  # Every 6 hours
        id="collect_data",
        name="Collect market data",
        replace_existing=True
    )

    # Run initial collection on startup (after 1 minute)
    scheduler.add_job(
        collect_all_data,
        "date",
        run_date=datetime.now(),
        id="initial_collection",
        name="Initial data collection"
    )

    scheduler.start()
    logger.info("Scheduler started - data will be collected every 6 hours")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
