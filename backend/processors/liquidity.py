"""Data processing and liquidity calculations."""
from datetime import datetime
from typing import Optional
import pandas as pd

from backend.core import DataPoint


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

        df = df_fed
        if not df_rrp.empty:
            df = df.merge(df_rrp, on="date", how="left")
        else:
            df["rrp"] = 0

        if not df_tga.empty:
            df = df.merge(df_tga, on="date", how="left")
        else:
            df["tga"] = 0

        df = df.sort_values("date")
        df = df.fillna(method="ffill").fillna(0)
        df["net_liquidity"] = df["fed"] - df["rrp"] - df["tga"]

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

        if direction == "up_is_loose":
            is_positive = change_pct_30d > 0
        else:
            is_positive = change_pct_30d < 0

        threshold = 2.0

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
