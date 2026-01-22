"""Generate demo data for testing without API keys."""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
import math

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from backend.storage import init_db, get_session, IndicatorRepository
from backend.core import DataPoint


async def load_indicators_config():
    """Load indicators from YAML config."""
    config_path = Path(__file__).parent.parent.parent / "config" / "indicators.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_time_series(
    base_value: float,
    days: int = 365,
    volatility: float = 0.02,
    trend: float = 0.0001
) -> list[tuple[datetime, float]]:
    """Generate realistic time series data."""
    data = []
    value = base_value
    end_date = datetime.now()

    for i in range(days, 0, -1):
        date = end_date - timedelta(days=i)

        # Add trend
        value *= (1 + trend)

        # Add random walk
        change = random.gauss(0, volatility)
        value *= (1 + change)

        # Add some seasonality
        seasonal = math.sin(i / 30 * math.pi) * volatility * 0.5
        value *= (1 + seasonal)

        data.append((date, value))

    return data


# Base values for different indicators
INDICATOR_CONFIGS = {
    # US Market
    "fed_balance_sheet": {"base": 6.8, "volatility": 0.005, "trend": -0.0001},
    "rrp": {"base": 0.3, "volatility": 0.03, "trend": -0.002},
    "tga": {"base": 0.75, "volatility": 0.05, "trend": 0.0},
    "m2_us": {"base": 21.0, "volatility": 0.003, "trend": 0.0001},
    "fed_funds_rate": {"base": 4.5, "volatility": 0.01, "trend": -0.0001},
    "us_10y": {"base": 4.2, "volatility": 0.02, "trend": 0.0},
    "us_2y": {"base": 4.0, "volatility": 0.025, "trend": 0.0},
    "yield_curve": {"base": 0.2, "volatility": 0.1, "trend": 0.001},
    "dxy": {"base": 104, "volatility": 0.008, "trend": 0.0},
    "vix": {"base": 16, "volatility": 0.08, "trend": 0.0},
    "net_liquidity": {"base": 5.8, "volatility": 0.01, "trend": 0.0001},
    # China Market
    "shibor_on": {"base": 1.7, "volatility": 0.05, "trend": 0.0},
    "shibor_1w": {"base": 1.9, "volatility": 0.04, "trend": 0.0},
    "m2_china": {"base": 310, "volatility": 0.005, "trend": 0.0003},
    "m1_china": {"base": 68, "volatility": 0.008, "trend": 0.0001},
    "lpr_1y": {"base": 3.1, "volatility": 0.005, "trend": -0.0001},
    "lpr_5y": {"base": 3.6, "volatility": 0.003, "trend": -0.0001},
    "china_10y": {"base": 2.3, "volatility": 0.02, "trend": -0.0001},
    "pboc_omo": {"base": 200, "volatility": 0.5, "trend": 0.0},
    "forex_reserve": {"base": 3.2, "volatility": 0.005, "trend": 0.0},
    # Crypto Market
    "btc_price": {"base": 95000, "volatility": 0.025, "trend": 0.001},
    "eth_price": {"base": 3200, "volatility": 0.03, "trend": 0.001},
    "stablecoin_mcap": {"base": 200, "volatility": 0.01, "trend": 0.0003},
    "btc_mcap": {"base": 1.9, "volatility": 0.025, "trend": 0.001},
    "total_crypto_mcap": {"base": 3.5, "volatility": 0.03, "trend": 0.001},
    "btc_dominance": {"base": 55, "volatility": 0.01, "trend": 0.0},
    "defi_tvl": {"base": 85, "volatility": 0.04, "trend": 0.001},
    "usdt_mcap": {"base": 140, "volatility": 0.008, "trend": 0.0002},
    "usdc_mcap": {"base": 45, "volatility": 0.01, "trend": 0.0001},
}


async def main():
    """Generate demo data."""
    print("=" * 50)
    print("Liquidity Monitor - Demo Data Generator")
    print("=" * 50)

    # Initialize database
    print("\nInitializing database...")
    await init_db()

    # Load config
    config = await load_indicators_config()
    indicators = config.get("indicators", [])

    # Get session
    session = await get_session()
    repo = IndicatorRepository(session)

    try:
        # Initialize indicators
        print(f"\nInitializing {len(indicators)} indicators...")
        for ind in indicators:
            await repo.upsert_indicator(ind)
            print(f"  ✓ {ind['id']}")

        # Generate data for each indicator
        print("\nGenerating demo data...")
        for ind in indicators:
            ind_id = ind["id"]
            ind_config = INDICATOR_CONFIGS.get(ind_id, {"base": 100, "volatility": 0.02, "trend": 0.0})

            print(f"  Generating {ind_id}...", end=" ")

            time_series = generate_time_series(
                base_value=ind_config["base"],
                days=365,
                volatility=ind_config["volatility"],
                trend=ind_config["trend"]
            )

            data_points = [
                DataPoint(
                    timestamp=ts,
                    indicator_id=ind_id,
                    value=value,
                    source=ind["source"],
                    market=ind["market"]
                )
                for ts, value in time_series
            ]

            count = await repo.save_data_points(data_points)
            print(f"✓ {count} points")

    finally:
        await session.close()

    print("\n" + "=" * 50)
    print("Demo data generation complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
