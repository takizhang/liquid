"""FRED (Federal Reserve Economic Data) collector."""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import httpx
import pandas as pd

from backend.core import BaseCollector, DataPoint, CollectorRegistry


@CollectorRegistry.register("FRED")
class FREDCollector(BaseCollector):
    """Collector for Federal Reserve Economic Data (FRED)."""

    source_name = "FRED"
    supported_markets = ["us"]
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        import os
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")

    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        market: str = "us",
        unit_divisor: float = 1.0
    ) -> list[DataPoint]:
        """Fetch data from FRED API."""
        if not self.api_key:
            raise ValueError("FRED API key not configured. Set FRED_API_KEY environment variable.")

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
            return []

        data_points = []
        for obs in observations:
            try:
                value = float(obs["value"])
                timestamp = datetime.strptime(obs["date"], "%Y-%m-%d")
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(value, unit_divisor),
                    source=self.source_name,
                    market=market
                ))
            except (ValueError, KeyError):
                continue

        return data_points

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
                data_points = await self.fetch(
                    indicator_id, series_id, start_date, end_date, market, unit_divisor
                )
                return indicator_id, data_points
            except Exception as e:
                print(f"Error fetching {indicator_id}: {e}")
                return indicator_id, []

        tasks = [fetch_one(ind) for ind in indicators]
        completed = await asyncio.gather(*tasks)

        for indicator_id, data_points in completed:
            results[indicator_id] = data_points

        return results

    async def health_check(self) -> bool:
        """Check FRED API availability."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.stlouisfed.org/fred/series",
                    params={"series_id": "GNPCA", "api_key": self.api_key, "file_type": "json"},
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_update_schedule(self, indicator_id: str) -> str:
        """FRED data updates weekly on Thursday."""
        return "0 6 * * 4"
