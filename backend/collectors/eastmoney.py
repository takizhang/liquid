"""东方财富 (EastMoney) data collector for China market."""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import httpx

from backend.core import BaseCollector, DataPoint, CollectorRegistry


@CollectorRegistry.register("EastMoney")
class EastMoneyCollector(BaseCollector):
    """Collector for 东方财富 (EastMoney) - China financial data."""

    source_name = "EastMoney"
    supported_markets = ["china"]

    # API endpoints
    SHIBOR_URL = "https://datacenter.eastmoney.com/api/data/v1/get"
    MACRO_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://data.eastmoney.com/"
        }

    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        market: str = "china",
        unit_divisor: float = 1.0
    ) -> list[DataPoint]:
        """Fetch data based on indicator type."""
        if series_id.startswith("SHIBOR"):
            return await self._fetch_shibor(indicator_id, series_id, start_date, end_date, unit_divisor)
        elif series_id.startswith("MACRO_"):
            return await self._fetch_macro(indicator_id, series_id, start_date, end_date, unit_divisor)
        elif series_id.startswith("LPR_"):
            return await self._fetch_lpr(indicator_id, series_id, start_date, end_date, unit_divisor)
        elif series_id == "BOND_10Y":
            return await self._fetch_bond_yield(indicator_id, start_date, end_date, unit_divisor)
        elif series_id == "PBOC_OMO":
            return await self._fetch_omo(indicator_id, start_date, end_date, unit_divisor)
        else:
            raise ValueError(f"Unknown series type: {series_id}")

    async def _fetch_shibor(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch SHIBOR interest rate data."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # Map series_id to column name
        column_map = {
            "SHIBOR_ON": "ON",      # Overnight
            "SHIBOR_1W": "1W",      # 1 Week
            "SHIBOR_1M": "1M",      # 1 Month
            "SHIBOR_3M": "3M",      # 3 Months
        }
        column = column_map.get(series_id, "ON")

        params = {
            "reportName": "RPT_IMP_INTRESTRATEN",
            "columns": f"REPORT_DATE,{column}",
            "filter": f"(MARKET=\"上海银行同业拆借市场\")(REPORT_DATE>='{start_date}')(REPORT_DATE<='{end_date}')",
            "pageNumber": "1",
            "pageSize": "500",
            "sortColumns": "REPORT_DATE",
            "sortTypes": "1",
            "source": "WEB",
            "client": "WEB"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.SHIBOR_URL, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("result", {}).get("data"):
            return []

        data_points = []
        for item in data["result"]["data"]:
            try:
                timestamp = datetime.strptime(item["REPORT_DATE"][:10], "%Y-%m-%d")
                value = float(item[column])
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(value, unit_divisor),
                    source=self.source_name,
                    market="china"
                ))
            except (ValueError, KeyError, TypeError):
                continue

        return data_points

    async def _fetch_macro(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch macro economic data (M2, GDP, etc.)."""
        # Map series to report names
        report_map = {
            "MACRO_M2": ("RPT_ECONOMY_CURRENCY", "BASIC_CURRENCY", "REPORT_DATE"),
            "MACRO_M1": ("RPT_ECONOMY_CURRENCY", "CURRENCY", "REPORT_DATE"),
            "MACRO_FOREX": ("RPT_ECONOMY_FOREX", "GOLD_RESERVES", "REPORT_DATE"),
        }

        if series_id not in report_map:
            return []

        report_name, value_col, date_col = report_map[series_id]

        params = {
            "reportName": report_name,
            "columns": f"{date_col},{value_col}",
            "pageNumber": "1",
            "pageSize": "100",
            "sortColumns": date_col,
            "sortTypes": "-1",
            "source": "WEB",
            "client": "WEB"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.MACRO_URL, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("result", {}).get("data"):
            return []

        data_points = []
        for item in data["result"]["data"]:
            try:
                date_str = item[date_col]
                if isinstance(date_str, str):
                    timestamp = datetime.strptime(date_str[:10], "%Y-%m-%d")
                else:
                    continue
                value = float(item[value_col])
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(value, unit_divisor),
                    source=self.source_name,
                    market="china"
                ))
            except (ValueError, KeyError, TypeError):
                continue

        return sorted(data_points, key=lambda x: x.timestamp)

    async def _fetch_lpr(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch LPR (Loan Prime Rate) data."""
        column = "LPR1Y" if series_id == "LPR_1Y" else "LPR5Y"

        params = {
            "reportName": "RPT_ECONOMY_LPR",
            "columns": f"TRADE_DATE,{column}",
            "pageNumber": "1",
            "pageSize": "100",
            "sortColumns": "TRADE_DATE",
            "sortTypes": "-1",
            "source": "WEB",
            "client": "WEB"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.MACRO_URL, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("result", {}).get("data"):
            return []

        data_points = []
        for item in data["result"]["data"]:
            try:
                date_str = item["TRADE_DATE"]
                if isinstance(date_str, str):
                    timestamp = datetime.strptime(date_str[:10], "%Y-%m-%d")
                else:
                    continue
                value = float(item[column])
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(value, unit_divisor),
                    source=self.source_name,
                    market="china"
                ))
            except (ValueError, KeyError, TypeError):
                continue

        return sorted(data_points, key=lambda x: x.timestamp)

    async def _fetch_bond_yield(
        self,
        indicator_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch China 10Y bond yield."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        params = {
            "reportName": "RPT_BOND_CHINABONDYIELD",
            "columns": "SOLAR_DATE,EMM00166466",
            "filter": f"(SOLAR_DATE>='{start_date}')(SOLAR_DATE<='{end_date}')",
            "pageNumber": "1",
            "pageSize": "500",
            "sortColumns": "SOLAR_DATE",
            "sortTypes": "1",
            "source": "WEB",
            "client": "WEB"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.MACRO_URL, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("result", {}).get("data"):
            return []

        data_points = []
        for item in data["result"]["data"]:
            try:
                date_str = item["SOLAR_DATE"]
                if isinstance(date_str, str):
                    timestamp = datetime.strptime(date_str[:10], "%Y-%m-%d")
                else:
                    continue
                value = float(item["EMM00166466"])
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(value, unit_divisor),
                    source=self.source_name,
                    market="china"
                ))
            except (ValueError, KeyError, TypeError):
                continue

        return sorted(data_points, key=lambda x: x.timestamp)

    async def _fetch_omo(
        self,
        indicator_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        unit_divisor: float
    ) -> list[DataPoint]:
        """Fetch PBOC Open Market Operations data."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        params = {
            "reportName": "RPT_DMSK_OPENMARKET",
            "columns": "TRADE_DATE,NET_AMOUNT",
            "filter": f"(TRADE_DATE>='{start_date}')(TRADE_DATE<='{end_date}')",
            "pageNumber": "1",
            "pageSize": "500",
            "sortColumns": "TRADE_DATE",
            "sortTypes": "1",
            "source": "WEB",
            "client": "WEB"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.MACRO_URL, params=params, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        if not data.get("success") or not data.get("result", {}).get("data"):
            return []

        data_points = []
        for item in data["result"]["data"]:
            try:
                date_str = item["TRADE_DATE"]
                if isinstance(date_str, str):
                    timestamp = datetime.strptime(date_str[:10], "%Y-%m-%d")
                else:
                    continue
                value = float(item.get("NET_AMOUNT", 0) or 0)
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    indicator_id=indicator_id,
                    value=self.normalize_value(value, unit_divisor),
                    source=self.source_name,
                    market="china"
                ))
            except (ValueError, KeyError, TypeError):
                continue

        return sorted(data_points, key=lambda x: x.timestamp)

    async def health_check(self) -> bool:
        """Check EastMoney API availability."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.SHIBOR_URL,
                    params={"reportName": "RPT_IMP_INTRESTRATEN", "pageSize": "1"},
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_update_schedule(self, indicator_id: str) -> str:
        """China data updates daily."""
        return "0 9 * * *"
