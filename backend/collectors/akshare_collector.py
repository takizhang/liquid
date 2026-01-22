"""AkShare collector for China market data."""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
import akshare as ak

from backend.core import BaseCollector, DataPoint, CollectorRegistry


@CollectorRegistry.register("AkShare")
class AkShareCollector(BaseCollector):
    """Collector for AkShare - Free China financial data."""

    source_name = "AkShare"
    supported_markets = ["china"]

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
        loop = asyncio.get_event_loop()

        if series_id.startswith("SHIBOR"):
            return await loop.run_in_executor(None, self._fetch_shibor, indicator_id, series_id, unit_divisor)
        elif series_id.startswith("LPR"):
            return await loop.run_in_executor(None, self._fetch_lpr, indicator_id, series_id, unit_divisor)
        elif series_id == "BOND_10Y":
            return await loop.run_in_executor(None, self._fetch_bond_yield, indicator_id, unit_divisor)
        elif series_id == "MACRO_M2":
            return await loop.run_in_executor(None, self._fetch_m2, indicator_id, unit_divisor)
        elif series_id == "MACRO_M1":
            return await loop.run_in_executor(None, self._fetch_m1, indicator_id, unit_divisor)
        elif series_id == "MACRO_FOREX":
            return await loop.run_in_executor(None, self._fetch_forex, indicator_id, unit_divisor)
        else:
            return []

    def _fetch_shibor(self, indicator_id: str, series_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch SHIBOR data."""
        try:
            df = ak.rate_interbank(market="上海银行间同业拆放利率(Shibor)", symbol="Shibor人民币", indicator="隔夜" if "ON" in series_id else "1周")
            if df is None or df.empty:
                return []

            data_points = []
            for _, row in df.tail(365).iterrows():
                try:
                    timestamp = datetime.strptime(str(row.iloc[0])[:10], "%Y-%m-%d")
                    value = float(row.iloc[1])
                    data_points.append(DataPoint(
                        timestamp=timestamp,
                        indicator_id=indicator_id,
                        value=self.normalize_value(value, unit_divisor),
                        source=self.source_name,
                        market="china"
                    ))
                except:
                    continue
            return data_points
        except Exception as e:
            print(f"SHIBOR fetch error: {e}")
            return []

    def _fetch_lpr(self, indicator_id: str, series_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch LPR data."""
        try:
            df = ak.macro_china_lpr()
            if df is None or df.empty:
                return []

            col = "LPR1Y" if "1Y" in series_id else "LPR5Y"
            data_points = []
            for _, row in df.tail(100).iterrows():
                try:
                    timestamp = datetime.strptime(str(row["TRADE_DATE"])[:10], "%Y-%m-%d")
                    value = row[col]
                    if value is None or (isinstance(value, float) and (value != value)):  # Check for NaN
                        continue
                    value = float(value)
                    data_points.append(DataPoint(
                        timestamp=timestamp,
                        indicator_id=indicator_id,
                        value=self.normalize_value(value, unit_divisor),
                        source=self.source_name,
                        market="china"
                    ))
                except:
                    continue
            return sorted(data_points, key=lambda x: x.timestamp)
        except Exception as e:
            print(f"LPR fetch error: {e}")
            return []

    def _fetch_bond_yield(self, indicator_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch China 10Y bond yield."""
        try:
            df = ak.bond_china_yield(start_date=(date.today() - timedelta(days=365)).strftime("%Y%m%d"), end_date=date.today().strftime("%Y%m%d"))
            if df is None or df.empty:
                return []

            data_points = []
            for _, row in df.iterrows():
                try:
                    timestamp = datetime.strptime(str(row["日期"])[:10], "%Y-%m-%d")
                    value = float(row["中国国债收益率10年"])
                    data_points.append(DataPoint(
                        timestamp=timestamp,
                        indicator_id=indicator_id,
                        value=self.normalize_value(value, unit_divisor),
                        source=self.source_name,
                        market="china"
                    ))
                except:
                    continue
            return sorted(data_points, key=lambda x: x.timestamp)
        except Exception as e:
            print(f"Bond yield fetch error: {e}")
            return []

    def _fetch_m2(self, indicator_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch M2 money supply."""
        try:
            df = ak.macro_china_money_supply()
            if df is None or df.empty:
                return []

            data_points = []
            for _, row in df.iterrows():
                try:
                    month_str = str(row["月份"]).replace("年", "-").replace("月份", "")
                    timestamp = datetime.strptime(month_str + "-01", "%Y-%m-%d")
                    value = float(row["货币和准货币(M2)-数量(亿元)"])
                    data_points.append(DataPoint(
                        timestamp=timestamp,
                        indicator_id=indicator_id,
                        value=self.normalize_value(value, unit_divisor),
                        source=self.source_name,
                        market="china"
                    ))
                except:
                    continue
            return sorted(data_points, key=lambda x: x.timestamp)[-60:]
        except Exception as e:
            print(f"M2 fetch error: {e}")
            return []

    def _fetch_m1(self, indicator_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch M1 money supply."""
        try:
            df = ak.macro_china_money_supply()
            if df is None or df.empty:
                return []

            data_points = []
            for _, row in df.iterrows():
                try:
                    month_str = str(row["月份"]).replace("年", "-").replace("月份", "")
                    timestamp = datetime.strptime(month_str + "-01", "%Y-%m-%d")
                    value = float(row["货币(M1)-数量(亿元)"])
                    data_points.append(DataPoint(
                        timestamp=timestamp,
                        indicator_id=indicator_id,
                        value=self.normalize_value(value, unit_divisor),
                        source=self.source_name,
                        market="china"
                    ))
                except:
                    continue
            return sorted(data_points, key=lambda x: x.timestamp)[-60:]
        except Exception as e:
            print(f"M1 fetch error: {e}")
            return []

    def _fetch_forex(self, indicator_id: str, unit_divisor: float) -> list[DataPoint]:
        """Fetch forex reserves."""
        try:
            df = ak.macro_china_fx_reserves_yearly()
            if df is None or df.empty:
                return []

            data_points = []
            for _, row in df.tail(20).iterrows():
                try:
                    timestamp = datetime(int(row["日期"]), 12, 31)
                    value = float(row["国家外汇储备"])
                    data_points.append(DataPoint(
                        timestamp=timestamp,
                        indicator_id=indicator_id,
                        value=self.normalize_value(value, unit_divisor),
                        source=self.source_name,
                        market="china"
                    ))
                except:
                    continue
            return sorted(data_points, key=lambda x: x.timestamp)
        except Exception as e:
            print(f"Forex fetch error: {e}")
            return []

    async def health_check(self) -> bool:
        """Check AkShare availability."""
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, ak.macro_china_lpr)
            return df is not None and not df.empty
        except:
            return False

    def get_update_schedule(self, indicator_id: str) -> str:
        return "0 10 * * *"
