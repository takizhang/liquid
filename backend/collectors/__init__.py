from backend.core import BaseCollector, DataPoint, CollectorRegistry

# Import collectors to trigger registration
from .fred import FREDCollector
from .eastmoney import EastMoneyCollector
from .coingecko import CoinGeckoCollector
from .akshare_collector import AkShareCollector

__all__ = [
    "BaseCollector",
    "DataPoint",
    "CollectorRegistry",
    "FREDCollector",
    "EastMoneyCollector",
    "CoinGeckoCollector",
    "AkShareCollector"
]
