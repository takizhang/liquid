"""Scheduler for periodic data collection."""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.core import CollectorRegistry
from backend.storage import get_session, IndicatorRepository
import backend.collectors  # noqa - register collectors

logger = logging.getLogger(__name__)

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

            except Exception as e:
                logger.error(f"Error collecting data for {indicator.name}: {e}")
                continue

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
