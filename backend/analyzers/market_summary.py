"""Market summary analyzer - generates AI insights for markets."""
import os
from pathlib import Path
from typing import Optional

from backend.core import BaseAnalyzer, AnalysisResult, AnalyzerRegistry
from .llm_client import LLMClient


@AnalyzerRegistry.register("market_summary")
class MarketSummaryAnalyzer(BaseAnalyzer):
    """Generates market liquidity summaries using AI."""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.use_ai = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))
        self.llm = llm or (LLMClient() if self.use_ai else None)
        self.prompt_template = self._load_prompt("market_summary.md")

    def _load_prompt(self, name: str) -> str:
        """Load prompt template from file."""
        path = Path(__file__).parent.parent.parent / "config" / "prompts" / name
        if path.exists():
            return path.read_text(encoding="utf-8")
        return self._default_prompt()

    def _default_prompt(self) -> str:
        """Default prompt if file not found."""
        return """# 角色
你是一位专业的宏观经济分析师，专注于全球流动性分析。

# 任务
基于提供的流动性指标数据，生成简洁、专业的市场分析报告。

# 输出要求
请以 JSON 格式输出，包含以下字段：
- summary: 核心结论 (1-2句话)
- signals: 关键信号数组 [{name, direction, significance}]
- risk_level: "low" | "medium" | "high"
- recommendations: 操作建议数组
- confidence: 置信度 (0-1)
- reasoning: 推理过程

# 分析框架
- 流动性扩张 → 利好风险资产
- 流动性收缩 → 利好避险资产
- 关注指标间的背离和确认信号"""

    async def analyze(
        self,
        context: dict,
        prompt_template: Optional[str] = None
    ) -> AnalysisResult:
        """Generate market summary analysis."""
        market_id = context.get("market_id", "unknown")
        indicators_data = context.get("indicators_data", [])

        user_content = self._build_context(market_id, indicators_data)

        return await self.llm.analyze(
            system_prompt=prompt_template or self.prompt_template,
            user_content=user_content
        )

    async def generate_summary(
        self,
        market_id: str,
        indicators_data: list[dict],
        historical_summaries: Optional[list[str]] = None
    ) -> AnalysisResult:
        """Generate market summary with optional historical context."""
        context = {
            "market_id": market_id,
            "indicators_data": indicators_data
        }

        user_content = self._build_context(market_id, indicators_data)

        if historical_summaries:
            user_content += f"\n\n## 历史分析参考\n" + "\n".join(historical_summaries[-3:])

        return await self.llm.analyze(
            system_prompt=self.prompt_template,
            user_content=user_content
        )

    def _build_context(self, market_id: str, data: list[dict]) -> str:
        """Build analysis context from indicator data."""
        market_names = {
            "us": "美国",
            "china": "中国",
            "crypto": "加密货币"
        }

        lines = [f"# {market_names.get(market_id, market_id)} 市场流动性数据\n"]
        lines.append(f"分析时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        for item in data:
            indicator = item.get("indicator", {})
            lines.append(f"## {indicator.get('name', 'Unknown')} ({indicator.get('name_en', '')})")
            lines.append(f"- 当前值: {item.get('current_value', 'N/A')} {indicator.get('unit', '')}")

            changes = item.get("changes", {})
            if "7d" in changes:
                lines.append(f"- 7日变化: {changes['7d'].get('change_pct', 'N/A')}%")
            if "30d" in changes:
                lines.append(f"- 30日变化: {changes['30d'].get('change_pct', 'N/A')}%")

            direction = indicator.get("direction", "up_is_loose")
            lines.append(f"- 方向含义: {'上涨=宽松' if direction == 'up_is_loose' else '下跌=宽松'}")

            if indicator.get("impact_up"):
                lines.append(f"- 上涨影响: {indicator['impact_up']}")
            if indicator.get("impact_down"):
                lines.append(f"- 下跌影响: {indicator['impact_down']}")

            lines.append("")

        return "\n".join(lines)
