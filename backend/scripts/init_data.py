"""Initialize database with indicator configurations and fetch initial data."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import yaml
from backend.storage import init_db, get_session, IndicatorRepository
from backend.collectors import CollectorRegistry, FREDCollector, EastMoneyCollector, CoinGeckoCollector
from backend.core import DataPoint


async def load_indicators_config():
    """Load indicators from YAML config."""
    config_path = Path(__file__).parent.parent.parent / "config" / "indicators.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def init_indicators(session, config):
    """Initialize indicator metadata in database."""
    repo = IndicatorRepository(session)
    indicators = config.get("indicators", [])

    print(f"Initializing {len(indicators)} indicators...")

    for ind in indicators:
        await repo.upsert_indicator(ind)
        print(f"  ✓ {ind['id']}")

    print("Indicators initialized.")


async def fetch_data(session, config):
    """Fetch data from all sources."""
    repo = IndicatorRepository(session)
    indicators = config.get("indicators", [])

    # Group indicators by source
    by_source = {}
    for ind in indicators:
        source = ind["source"]
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(ind)

    print("\nFetching data from sources...")

    for source_name, source_indicators in by_source.items():
        print(f"\n[{source_name}] Fetching {len(source_indicators)} indicators...")

        try:
            collector = CollectorRegistry.get(source_name)

            for ind in source_indicators:
                try:
                    print(f"  Fetching {ind['id']}...", end=" ")

                    data_points = await collector.fetch(
                        indicator_id=ind["id"],
                        series_id=ind["series_id"],
                        market=ind["market"],
                        unit_divisor=ind.get("unit_divisor", 1.0)
                    )

                    if data_points:
                        count = await repo.save_data_points(data_points)
                        print(f"✓ {count} points")
                    else:
                        print("⚠ No data")

                except Exception as e:
                    print(f"✗ Error: {e}")

        except Exception as e:
            print(f"  ✗ Source error: {e}")

    print("\nData fetch complete.")


async def main():
    """Main initialization function."""
    print("=" * 50)
    print("Liquidity Monitor - Data Initialization")
    print("=" * 50)

    # Initialize database
    print("\nInitializing database...")
    await init_db()
    print("Database initialized.")

    # Load config
    config = await load_indicators_config()

    # Get session
    session = await get_session()

    try:
        # Initialize indicators
        await init_indicators(session, config)

        # Fetch data
        await fetch_data(session, config)

    finally:
        await session.close()

    print("\n" + "=" * 50)
    print("Initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
