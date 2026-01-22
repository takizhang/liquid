"""Core interfaces and protocols for the liquidity monitoring system."""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, Protocol, runtime_checkable
from pydantic import BaseModel


class DataPoint(BaseModel):
    """Standardized data point format."""
    timestamp: datetime
    indicator_id: str
    value: float
    source: str
    market: str
    metadata: dict = {}


class AnalysisResult(BaseModel):
    """AI analysis result structure."""
    summary: str
    signals: list[dict]
    risk_level: str  # low/medium/high
    recommendations: list[str]
    confidence: float  # 0-1
    reasoning: str


@runtime_checkable
class CollectorProtocol(Protocol):
    """Protocol for all data collectors."""

    source_name: str
    supported_markets: list[str]

    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[DataPoint]:
        """Fetch indicator data."""
        ...

    async def health_check(self) -> bool:
        """Check if data source is available."""
        ...

    def get_update_schedule(self, indicator_id: str) -> str:
        """Return cron expression for update frequency."""
        ...


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """Protocol for AI analyzers."""

    async def analyze(
        self,
        context: dict,
        prompt_template: Optional[str] = None
    ) -> AnalysisResult:
        """Perform analysis and return structured result."""
        ...


class BaseCollector(ABC):
    """Base class for all data collectors."""

    source_name: str = "base"
    supported_markets: list[str] = []

    def __init__(self):
        self._client = None

    @abstractmethod
    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[DataPoint]:
        """Fetch data from source."""
        pass

    async def health_check(self) -> bool:
        """Default health check."""
        return True

    def get_update_schedule(self, indicator_id: str) -> str:
        """Default: daily at 6 AM."""
        return "0 6 * * *"

    def normalize_value(self, value: float, unit_divisor: float = 1.0) -> float:
        """Normalize value with unit divisor."""
        return value / unit_divisor if unit_divisor else value


class BaseAnalyzer(ABC):
    """Base class for AI analyzers."""

    @abstractmethod
    async def analyze(
        self,
        context: dict,
        prompt_template: Optional[str] = None
    ) -> AnalysisResult:
        """Perform analysis."""
        pass
