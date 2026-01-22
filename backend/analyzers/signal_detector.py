"""Signal detector - identifies important market signals."""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from backend.core import AnalyzerRegistry


class Signal(BaseModel):
    """Detected signal."""
    indicator_id: str
    indicator_name: str
    signal_type: str  # threshold_breach, trend_change, divergence
    severity: str  # info, warning, critical
    description: str
    current_value: float
    threshold_value: Optional[float] = None
    change_pct: Optional[float] = None
    detected_at: datetime


@AnalyzerRegistry.register("signal_detector")
class SignalDetector:
    """Detects important signals from indicator data."""

    # Thresholds for signal detection
    CHANGE_THRESHOLDS = {
        "critical": 10.0,  # 10% change
        "warning": 5.0,    # 5% change
        "info": 2.0        # 2% change
    }

    def detect_signals(self, indicators_data: list[dict]) -> list[Signal]:
        """Detect signals from indicator data."""
        signals = []

        for item in indicators_data:
            indicator = item.get("indicator", {})
            changes = item.get("changes", {})
            current_value = item.get("current_value")

            if current_value is None:
                continue

            # Check 7-day change
            if "7d" in changes:
                change_pct = changes["7d"].get("change_pct", 0)
                signal = self._check_change_signal(indicator, change_pct, current_value, "7d")
                if signal:
                    signals.append(signal)

            # Check 30-day change
            if "30d" in changes:
                change_pct = changes["30d"].get("change_pct", 0)
                signal = self._check_change_signal(indicator, change_pct, current_value, "30d")
                if signal:
                    signals.append(signal)

        return signals

    def _check_change_signal(
        self,
        indicator: dict,
        change_pct: float,
        current_value: float,
        period: str
    ) -> Optional[Signal]:
        """Check if change warrants a signal."""
        abs_change = abs(change_pct)

        if abs_change >= self.CHANGE_THRESHOLDS["critical"]:
            severity = "critical"
        elif abs_change >= self.CHANGE_THRESHOLDS["warning"]:
            severity = "warning"
        elif abs_change >= self.CHANGE_THRESHOLDS["info"]:
            severity = "info"
        else:
            return None

        direction = indicator.get("direction", "up_is_loose")
        is_positive_for_liquidity = (
            (direction == "up_is_loose" and change_pct > 0) or
            (direction == "down_is_loose" and change_pct < 0)
        )

        trend = "扩张" if is_positive_for_liquidity else "收缩"
        description = f"{indicator.get('name', 'Unknown')} {period}变化 {change_pct:+.2f}%，流动性{trend}"

        return Signal(
            indicator_id=indicator.get("id", "unknown"),
            indicator_name=indicator.get("name", "Unknown"),
            signal_type="trend_change",
            severity=severity,
            description=description,
            current_value=current_value,
            change_pct=change_pct,
            detected_at=datetime.utcnow()
        )

    def detect_divergence(
        self,
        indicator1_data: dict,
        indicator2_data: dict
    ) -> Optional[Signal]:
        """Detect divergence between two indicators."""
        changes1 = indicator1_data.get("changes", {}).get("30d", {})
        changes2 = indicator2_data.get("changes", {}).get("30d", {})

        pct1 = changes1.get("change_pct", 0)
        pct2 = changes2.get("change_pct", 0)

        # Check for significant divergence (opposite directions)
        if pct1 * pct2 < 0 and abs(pct1) > 3 and abs(pct2) > 3:
            ind1 = indicator1_data.get("indicator", {})
            ind2 = indicator2_data.get("indicator", {})

            return Signal(
                indicator_id=f"{ind1.get('id', '')}_{ind2.get('id', '')}",
                indicator_name=f"{ind1.get('name', '')} vs {ind2.get('name', '')}",
                signal_type="divergence",
                severity="warning",
                description=f"指标背离: {ind1.get('name', '')} ({pct1:+.1f}%) 与 {ind2.get('name', '')} ({pct2:+.1f}%) 走势相反",
                current_value=0,
                detected_at=datetime.utcnow()
            )

        return None
