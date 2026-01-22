"""CoinGecko collector for cryptocurrency data."""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import httpx

from backend.core import BaseCollector, DataPoint, CollectorRegistry


@CollectorRegistry.register("CoinGecko")
class CoinGeckoCollector(BaseCollector):
    """Collector for CoinGecko - Cryptocurrency market data."""

    source_name = "CoinGecko"
    supported_markets = ["crypto"]
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        import os
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY", "")
        self.headers = {"accept": "application/json"}
        if self.api_key:
            self.headers["x-cg-pro-api-key"] = self.api_key

    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        market: str = "crypto",
        unit_divisor: float = 1.0
    ) -> list[DataPoint]:
        """Fetch crypto data based on series type."""
        if series_id.startswith("PRICE_"):
            coin_id = series_id.replace("PRICE_", "").lower()
            return await self._fetch_price_history(indicator_id, coin_id, start_date, end_date, unit_divisor)
        elif series_id == "STABLECOIN_MCAP":
            return await self._fetch_stablecoin_mcap(indicator_id, unit_divisor)
        elif series_id.startswith("MCAP_"):
            coin_id = series_id.replace("MCAP_", "").lower()
            return await self._fetch_market_cap(indicator_id, coin_id, start_date, end_date, unit_divisor)
        elif series_id == "TOTAL_MCAP":
            return await self._fetch_total_mcap(indicator_id, start_date, end_date, unit_divisor)
        elif series_id == "BTC_DOMINANCE":
            return await self._fetch_btc_dominance(indicator_id, start_date, end_date, unit_divisor)
        elif series_id == "DEFI_TVL":
            return await self._fetch_defi_tvl(indicator_id, unit_divisor)
        elif series_id.startswith("VOLUME_"):
            coin_id = series_id.replace("VOLUME_", "").lower()
            return await self._fetch_volume(indicator_id, coin_id, start_date, end_date, unit_divisor)
        elif series_id == "FEAR_GREED":
            return await self._fetch_fear_greed(indicator_id, unit_divisor)
        else:
            return await self._fetch_price_history(indicator_id, series_id.lower(), start_date, end_date, unit_divisor)

    async def _fetch_price_history(
        self,
        indicator_id: str,
        coin_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch historical price data for a coin."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        days = (end_date - start_date).days

        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(days),
            "interval": "daily"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        prices = data.get("prices", [])
        if not prices:
            return []

        data_points = []
        for timestamp_ms, price in prices:
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            data_points.append(DataPoint(
                timestamp=timestamp,
                indicator_id=indicator_id,
                value=self.normalize_value(price, unit_divisor),
                source=self.source_name,
                market="crypto"
            ))

        return data_points

    async def _fetch_stablecoin_mcap(
        self,
        indicator_id: str,
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch total stablecoin market cap."""
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "category": "stablecoins",
            "order": "market_cap_desc",
            "per_page": "50",
            "page": "1"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        if not data:
            return []

        total_mcap = sum(coin.get("market_cap", 0) or 0 for coin in data)

        return [DataPoint(
            timestamp=datetime.utcnow(),
            indicator_id=indicator_id,
            value=self.normalize_value(total_mcap, unit_divisor),
            source=self.source_name,
            market="crypto",
            metadata={"top_stablecoins": [c["id"] for c in data[:5]]}
        )]

    async def _fetch_market_cap(
        self,
        indicator_id: str,
        coin_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch historical market cap for a coin."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        days = (end_date - start_date).days

        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(days),
            "interval": "daily"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        market_caps = data.get("market_caps", [])
        if not market_caps:
            return []

        data_points = []
        for timestamp_ms, mcap in market_caps:
            if mcap:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(mcap, unit_divisor),
                    source=self.source_name,
                    market="crypto"
                ))

        return data_points

    async def _fetch_total_mcap(
        self,
        indicator_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch total crypto market cap from /global endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/global", headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        total_mcap = data.get("data", {}).get("total_market_cap", {}).get("usd", 0)
        return [DataPoint(
            timestamp=datetime.utcnow(),
            indicator_id=indicator_id,
            value=self.normalize_value(total_mcap, unit_divisor),
            source=self.source_name,
            market="crypto"
        )]

    async def _fetch_btc_dominance(
        self,
        indicator_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch BTC dominance percentage."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/global", headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        btc_dominance = data.get("data", {}).get("market_cap_percentage", {}).get("btc", 0)
        return [DataPoint(
            timestamp=datetime.utcnow(),
            indicator_id=indicator_id,
            value=self.normalize_value(btc_dominance, unit_divisor),
            source=self.source_name,
            market="crypto"
        )]

    async def _fetch_defi_tvl(
        self,
        indicator_id: str,
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch DeFi TVL from CoinGecko."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/global/decentralized_finance_defi", headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        defi_mcap = float(data.get("data", {}).get("defi_market_cap", "0").replace(",", ""))
        return [DataPoint(
            timestamp=datetime.utcnow(),
            indicator_id=indicator_id,
            value=self.normalize_value(defi_mcap, unit_divisor),
            source=self.source_name,
            market="crypto"
        )]

    async def _fetch_volume(
        self,
        indicator_id: str,
        coin_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch 24h trading volume for a coin."""
        days = 365 if start_date is None else (date.today() - start_date).days
        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": str(days), "interval": "daily"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        volumes = data.get("total_volumes", [])
        if not volumes:
            return []

        data_points = []
        for timestamp_ms, vol in volumes:
            if vol:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(vol, unit_divisor),
                    source=self.source_name,
                    market="crypto"
                ))
        return data_points

    async def _fetch_fear_greed(self, indicator_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch Fear & Greed Index from Alternative.me."""
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.alternative.me/fng/?limit=90", timeout=30.0)
            response.raise_for_status()
            data = response.json()

        fng_data = data.get("data", [])
        if not fng_data:
            return []

        data_points = []
        for item in fng_data:
            timestamp = datetime.fromtimestamp(int(item["timestamp"]))
            value = float(item["value"])
            data_points.append(DataPoint(
                timestamp=timestamp,
                indicator_id=indicator_id,
                value=self.normalize_value(value, unit_divisor),
                source="Alternative.me",
                market="crypto",
                metadata={"classification": item.get("value_classification")}
            ))
        return sorted(data_points, key=lambda x: x.timestamp)

    async def health_check(self) -> bool:
        """Check CoinGecko API availability."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/ping",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_update_schedule(self, indicator_id: str) -> str:
        """Crypto data updates every hour."""
        return "0 * * * *"
