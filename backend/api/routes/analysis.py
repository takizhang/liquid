"""AI Analysis API routes."""
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.storage import get_db, IndicatorRepository
from backend.processors import LiquidityProcessor
from backend.core import DataPoint, AnalysisResult

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AskRequest(BaseModel):
    question: str
    context_market: Optional[str] = None


def is_ai_configured() -> bool:
    """Check if any AI provider is configured."""
    return bool(
        os.getenv("ANTHROPIC_API_KEY") or
        os.getenv("OPENAI_API_KEY") or
        os.getenv("DEEPSEEK_API_KEY")
    )


def get_placeholder_analysis(market_id: str) -> dict:
    """Return placeholder when AI is not configured."""
    market_names = {"us": "美国", "china": "中国", "crypto": "加密货币"}
    return {
        "summary": f"AI 分析功能尚未配置。请在 .env 文件中设置 DEEPSEEK_API_KEY 或 ANTHROPIC_API_KEY 以启用智能分析。",
        "signals": [],
        "risk_level": "unknown",
        "recommendations": [
            "配置 DeepSeek API (推荐，便宜): DEEPSEEK_API_KEY=xxx",
            "或配置 Anthropic API: ANTHROPIC_API_KEY=xxx",
            "配置后重启后端服务"
        ],
        "confidence": 0,
        "reasoning": "AI 服务未配置",
        "generated_at": datetime.utcnow().isoformat(),
        "ai_not_configured": True
    }


def is_fresh(created_at: datetime, hours: int = 24) -> bool:
    """Check if a report is still fresh (default 24 hours)."""
    return datetime.utcnow() - created_at < timedelta(hours=hours)


@router.get("/markets/{market_id}/summary")
async def get_market_summary(
    market_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get AI analysis summary for a market (cached 24 hours)."""
    # Check if AI is configured
    if not is_ai_configured():
        return get_placeholder_analysis(market_id)

    repo = IndicatorRepository(db)

    # Check for cached analysis (24 hours)
    report = await repo.get_latest_analysis(market_id, "daily_summary")
    if report and is_fresh(report.created_at):
        return {
            "summary": report.summary,
            "signals": report.signals,
            "risk_level": report.risk_level,
            "recommendations": report.recommendations,
            "confidence": report.confidence,
            "reasoning": report.reasoning,
            "generated_at": report.created_at.isoformat(),
            "cached": True
        }

    # Get indicator data for analysis
    indicators = await repo.get_indicators_by_market(market_id)
    latest_data = await repo.get_latest_for_all_indicators(market_id)

    indicators_data = []
    for ind in indicators:
        item = {
            "indicator": {
                "id": ind.id,
                "name": ind.name,
                "name_en": ind.name_en,
                "unit": ind.unit,
                "direction": ind.direction,
                "impact_up": ind.impact_up,
                "impact_down": ind.impact_down
            },
            "current_value": None,
            "changes": {}
        }

        if ind.id in latest_data:
            dp = latest_data[ind.id]
            item["current_value"] = dp.value

            data_points = await repo.get_data_points(ind.id, limit=90)
            if data_points:
                points = [
                    DataPoint(
                        timestamp=p.timestamp,
                        indicator_id=p.indicator_id,
                        value=p.value,
                        source=p.source,
                        market=p.market
                    )
                    for p in data_points
                ]
                stats = LiquidityProcessor.calculate_change_stats(points, [7, 30])
                item["changes"] = stats.get("changes", {})

        indicators_data.append(item)

    # Generate AI analysis
    try:
        from backend.analyzers import MarketSummaryAnalyzer
        analyzer = MarketSummaryAnalyzer()
        result = await analyzer.generate_summary(market_id, indicators_data)

        # Save report
        await repo.save_analysis_report(
            market_id=market_id,
            report_type="daily_summary",
            result=result,
            data_snapshot={"indicators_count": len(indicators_data)},
            model_used=analyzer.llm.model
        )

        return {
            "summary": result.summary,
            "signals": result.signals,
            "risk_level": result.risk_level,
            "recommendations": result.recommendations,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "generated_at": datetime.utcnow().isoformat(),
            "cached": False
        }

    except Exception as e:
        # Return error but don't crash
        return {
            "summary": f"分析生成失败: {str(e)}",
            "signals": [],
            "risk_level": "unknown",
            "recommendations": ["请稍后重试或检查 API 配置"],
            "confidence": 0,
            "reasoning": str(e),
            "generated_at": datetime.utcnow().isoformat(),
            "error": True
        }


@router.get("/signals")
async def get_active_signals(
    market_id: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get active signal events."""
    repo = IndicatorRepository(db)

    # Get indicators and detect signals
    if market_id:
        indicators = await repo.get_indicators_by_market(market_id)
    else:
        indicators = await repo.get_all_indicators()

    latest_data = await repo.get_latest_for_all_indicators(market_id)

    indicators_data = []
    for ind in indicators:
        if ind.id not in latest_data:
            continue

        dp = latest_data[ind.id]
        data_points = await repo.get_data_points(ind.id, limit=90)

        if data_points:
            points = [
                DataPoint(
                    timestamp=p.timestamp,
                    indicator_id=p.indicator_id,
                    value=p.value,
                    source=p.source,
                    market=p.market
                )
                for p in data_points
            ]
            stats = LiquidityProcessor.calculate_change_stats(points, [7, 30])

            indicators_data.append({
                "indicator": {
                    "id": ind.id,
                    "name": ind.name,
                    "direction": ind.direction
                },
                "current_value": dp.value,
                "changes": stats.get("changes", {})
            })

    # Detect signals
    detector = SignalDetector()
    signals = detector.detect_signals(indicators_data)

    # Filter by severity if specified
    if severity:
        signals = [s for s in signals if s.severity == severity]

    return [
        {
            "indicator_id": s.indicator_id,
            "indicator_name": s.indicator_name,
            "signal_type": s.signal_type,
            "severity": s.severity,
            "description": s.description,
            "current_value": s.current_value,
            "change_pct": s.change_pct,
            "detected_at": s.detected_at.isoformat()
        }
        for s in signals
    ]


@router.post("/signals/{signal_id}/acknowledge")
async def acknowledge_signal(
    signal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark a signal as acknowledged."""
    repo = IndicatorRepository(db)
    success = await repo.acknowledge_signal(signal_id)

    if not success:
        raise HTTPException(status_code=404, detail="Signal not found")

    return {"success": True}


@router.get("/history/{market_id}")
async def get_analysis_history(
    market_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get historical analysis reports for a market."""
    repo = IndicatorRepository(db)
    reports = await repo.get_analysis_history(market_id, "daily_summary", limit)

    return [
        {
            "id": r.id,
            "summary": r.summary,
            "risk_level": r.risk_level,
            "confidence": r.confidence,
            "created_at": r.created_at.isoformat()
        }
        for r in reports
    ]


@router.post("/ask")
async def ask_question(
    request: AskRequest,
    db: AsyncSession = Depends(get_db)
):
    """Free-form Q&A based on current data."""
    if not is_ai_configured():
        return {
            "question": request.question,
            "answer": "AI 服务未配置。请在 .env 文件中设置 API key 后重启服务。",
            "error": True
        }

    repo = IndicatorRepository(db)

    # Build context from all markets or specific market
    context_parts = []

    if request.context_market:
        markets = [request.context_market]
    else:
        markets = ["us", "china", "crypto"]

    for market_id in markets:
        indicators = await repo.get_indicators_by_market(market_id)
        latest_data = await repo.get_latest_for_all_indicators(market_id)

        market_names = {"us": "美国", "china": "中国", "crypto": "加密货币"}
        context_parts.append(f"\n## {market_names.get(market_id, market_id)} 市场")

        for ind in indicators[:10]:  # Limit to top 10 per market
            if ind.id in latest_data:
                dp = latest_data[ind.id]
                context_parts.append(f"- {ind.name}: {dp.value} {ind.unit or ''}")

    context = "\n".join(context_parts)

    # Ask LLM
    try:
        from backend.analyzers import LLMClient
        llm = LLMClient()
        system_prompt = """你是一位专业的宏观经济分析师。基于提供的市场数据回答用户问题。
回答要简洁、专业，并给出具体的分析依据。"""

        response = await llm.chat(
            messages=[{"role": "user", "content": f"当前市场数据:\n{context}\n\n问题: {request.question}"}],
            system=system_prompt
        )

        return {
            "question": request.question,
            "answer": response,
            "context_market": request.context_market
        }

    except Exception as e:
        return {
            "question": request.question,
            "answer": f"抱歉，无法生成回答: {str(e)}",
            "error": True
        }
