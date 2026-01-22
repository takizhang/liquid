"""Initialize indicators from config file."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.storage import get_session, IndicatorRepository, init_db
from backend.core import Indicator
import yaml


async def init_indicators():
    """Initialize indicators from config file."""
    # Load config
    config_path = Path(__file__).parent.parent.parent / "config" / "indicators.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Initialize database
    await init_db()

    session = await get_session()
    repo = IndicatorRepository(session)

    # Process each market
    for market in config.get("markets", []):
        market_id = market["id"]
        print(f"\nProcessing market: {market['name']} ({market_id})")

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
            print(f"  ✓ {indicator.name}")

    await session.close()
    print("\n✅ Indicators initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_indicators())
