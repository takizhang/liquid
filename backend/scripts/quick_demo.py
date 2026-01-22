"""Quick demo data generator - minimal version."""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.storage import init_db, get_session, IndicatorRepository
from backend.core import Indicator, DataPoint


async def generate_demo_data():
    """Generate minimal demo data."""
    await init_db()
    session = await get_session()
    repo = IndicatorRepository(session)

    # Create a few indicators
    indicators = [
        Indicator(
            id="us_fed_balance",
            name="Fed 资产负债表",
            name_en="Fed Balance Sheet",
            market="us",
            source="FRED",
            series_id="WALCL",
            unit="百万美元",
            is_primary=True,
            direction="up_is_loose"
        ),
        Indicator(
            id="us_rrp",
            name="逆回购 RRP",
            name_en="Reverse Repo",
            market="us",
            source="FRED",
            series_id="RRPONTSYD",
            unit="百万美元",
            is_primary=False,
            direction="down_is_loose"
        ),
        Indicator(
            id="crypto_btc",
            name="BTC 价格",
            name_en="Bitcoin Price",
            market="crypto",
            source="CoinGecko",
            series_id="bitcoin",
            unit="USD",
            is_primary=True,
            direction="up_is_loose"
        )
    ]

    # Save indicators
    for indicator in indicators:
        await repo.save_indicator(indicator)
        print(f"Created indicator: {indicator.name}")

        # Generate demo data points (last 90 days)
        data_points = []
        base_value = random.randint(5000000, 8000000)  # Random base value

        for i in range(90):
            date = datetime.now() - timedelta(days=90-i)
            value = base_value + random.randint(-500000, 500000)

            data_points.append(DataPoint(
                timestamp=date,
                indicator_id=indicator.id,
                value=float(value),
                source=indicator.source,
                market=indicator.market
            ))

        # Save data points
        await repo.save_data_points(data_points)
        print(f"  Generated {len(data_points)} data points")

    await session.close()
    print("\n✅ Demo data generated successfully!")


if __name__ == "__main__":
    asyncio.run(generate_demo_data())
