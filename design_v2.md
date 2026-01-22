# Liquidity Monitor v2 - 增强架构设计

## 核心改进

1. **多数据源插件架构** - 轻松添加新数据源
2. **AI 分析引擎** - 自动生成市场洞察
3. **事件驱动更新** - 智能调度数据刷新
4. **指标关联分析** - 发现跨市场信号

---

## 目录结构

```
liquid/
├── backend/
│   ├── core/                         # 核心抽象
│   │   ├── __init__.py
│   │   ├── interfaces.py             # 协议定义
│   │   └── registry.py               # 插件注册中心
│   │
│   ├── collectors/                   # 数据收集器插件
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseCollector
│   │   ├── fred.py                   # 美国 FRED
│   │   ├── pboc.py                   # 中国央行
│   │   ├── ecb.py                    # 欧洲央行
│   │   ├── coingecko.py              # 加密货币
│   │   ├── glassnode.py              # 链上数据
│   │   └── eastmoney.py              # 东方财富
│   │
│   ├── analyzers/                    # AI 分析引擎
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseAnalyzer
│   │   ├── llm_client.py             # LLM 客户端封装
│   │   ├── market_summary.py         # 市场总结生成
│   │   ├── signal_detector.py        # 信号检测
│   │   └── correlation.py            # 相关性分析
│   │
│   ├── processors/                   # 数据处理
│   │   ├── __init__.py
│   │   ├── liquidity.py              # 流动性计算
│   │   ├── normalizer.py             # 数据标准化
│   │   └── aggregator.py             # 多源聚合
│   │
│   ├── storage/                      # 存储层
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py                 # 增强模型
│   │   ├── repository.py
│   │   └── cache.py                  # Redis 缓存
│   │
│   ├── scheduler/                    # 调度系统
│   │   ├── __init__.py
│   │   ├── manager.py                # 调度管理器
│   │   └── strategies.py             # 更新策略
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/                   # 路由拆分
│   │   │   ├── markets.py
│   │   │   ├── indicators.py
│   │   │   ├── analysis.py           # AI 分析端点
│   │   │   └── admin.py
│   │   └── websocket.py              # 实时推送
│   │
│   └── config/
│       ├── settings.py
│       └── sources.yaml              # 数据源配置
│
├── config/
│   ├── indicators.yaml
│   └── prompts/                      # AI 提示词模板
│       ├── market_summary.md
│       ├── signal_analysis.md
│       └── correlation_report.md
│
└── frontend/                         # 增强前端
    └── src/
        ├── components/
        │   ├── AIInsights.tsx        # AI 洞察卡片
        │   ├── CorrelationMatrix.tsx # 相关性矩阵
        │   └── SignalAlert.tsx       # 信号提醒
        └── pages/
            └── Analysis.tsx          # AI 分析页面
```

---

## 核心接口设计

### 1. 数据收集器协议

```python
# backend/core/interfaces.py
from abc import ABC, abstractmethod
from typing import Protocol, AsyncIterator
from datetime import date
from pydantic import BaseModel

class DataPoint(BaseModel):
    timestamp: datetime
    indicator_id: str
    value: float
    source: str
    market: str
    metadata: dict = {}

class CollectorProtocol(Protocol):
    """数据收集器协议 - 所有收集器必须实现"""

    source_name: str
    supported_markets: list[str]

    async def fetch(
        self,
        indicator_id: str,
        series_id: str,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> list[DataPoint]:
        """获取指标数据"""
        ...

    async def health_check(self) -> bool:
        """检查数据源可用性"""
        ...

    def get_update_schedule(self, indicator_id: str) -> str:
        """返回 cron 表达式，指示更新频率"""
        ...


class AnalyzerProtocol(Protocol):
    """AI 分析器协议"""

    async def analyze(
        self,
        context: dict,
        prompt_template: str | None = None
    ) -> AnalysisResult:
        ...
```

### 2. 插件注册中心

```python
# backend/core/registry.py
from typing import Type

class CollectorRegistry:
    """收集器注册中心 - 自动发现和管理数据源"""

    _collectors: dict[str, Type[CollectorProtocol]] = {}

    @classmethod
    def register(cls, source_name: str):
        """装饰器：注册收集器"""
        def decorator(collector_cls: Type[CollectorProtocol]):
            cls._collectors[source_name] = collector_cls
            return collector_cls
        return decorator

    @classmethod
    def get(cls, source_name: str) -> CollectorProtocol:
        if source_name not in cls._collectors:
            raise ValueError(f"Unknown source: {source_name}")
        return cls._collectors[source_name]()

    @classmethod
    def list_sources(cls) -> list[str]:
        return list(cls._collectors.keys())


# 使用示例
@CollectorRegistry.register("FRED")
class FREDCollector:
    source_name = "FRED"
    supported_markets = ["us"]
    # ...

@CollectorRegistry.register("PBOC")
class PBOCCollector:
    source_name = "PBOC"
    supported_markets = ["china"]
    # ...
```

---

## AI 分析引擎

### 1. LLM 客户端封装

```python
# backend/analyzers/llm_client.py
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str                    # 核心结论
    signals: list[dict]             # 检测到的信号
    risk_level: str                 # low/medium/high
    recommendations: list[str]      # 建议
    confidence: float               # 置信度 0-1
    reasoning: str                  # 推理过程

class LLMClient:
    """统一的 LLM 客户端，支持多个提供商"""

    def __init__(self, provider: str = "anthropic"):
        self.provider = provider
        if provider == "anthropic":
            self.client = AsyncAnthropic()
        elif provider == "openai":
            self.client = AsyncOpenAI()

    async def analyze(
        self,
        system_prompt: str,
        user_content: str,
        response_model: type[BaseModel] = AnalysisResult
    ) -> AnalysisResult:
        """结构化输出的分析"""

        if self.provider == "anthropic":
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            # 解析为结构化输出
            return self._parse_response(response.content[0].text, response_model)

        # OpenAI 实现...
```

### 2. 市场总结生成器

```python
# backend/analyzers/market_summary.py
from pathlib import Path

class MarketSummaryAnalyzer:
    """生成市场流动性总结"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.prompt_template = self._load_prompt("market_summary.md")

    def _load_prompt(self, name: str) -> str:
        path = Path(__file__).parent.parent.parent / "config" / "prompts" / name
        return path.read_text()

    async def generate_summary(
        self,
        market_id: str,
        indicators_data: list[dict],
        historical_summaries: list[str] | None = None
    ) -> AnalysisResult:
        """生成市场总结"""

        # 构建上下文
        context = self._build_context(market_id, indicators_data)

        # 添加历史总结以保持连贯性
        if historical_summaries:
            context += f"\n\n## 历史分析参考\n{historical_summaries[-3:]}"

        return await self.llm.analyze(
            system_prompt=self.prompt_template,
            user_content=context
        )

    def _build_context(self, market_id: str, data: list[dict]) -> str:
        """构建分析上下文"""
        lines = [f"# {market_id.upper()} 市场流动性数据\n"]

        for item in data:
            indicator = item["indicator"]
            lines.append(f"## {indicator['name']} ({indicator['name_en']})")
            lines.append(f"- 当前值: {item['current_value']} {indicator.get('unit', '')}")
            lines.append(f"- 7日变化: {item['changes'].get('7d', {}).get('change_pct', 'N/A')}%")
            lines.append(f"- 30日变化: {item['changes'].get('30d', {}).get('change_pct', 'N/A')}%")
            lines.append(f"- 方向含义: {indicator.get('direction', 'up_is_loose')}")
            lines.append(f"- 上涨影响: {indicator.get('impact_up', '')}")
            lines.append(f"- 下跌影响: {indicator.get('impact_down', '')}")
            lines.append("")

        return "\n".join(lines)
```

### 3. AI 提示词模板

```markdown
<!-- config/prompts/market_summary.md -->
# 角色
你是一位专业的宏观经济分析师，专注于全球流动性分析。

# 任务
基于提供的流动性指标数据，生成简洁、专业的市场分析报告。

# 输出要求
1. **核心结论** (1-2句话): 当前流动性状态和趋势
2. **关键信号** (3-5个): 最重要的变化和异常
3. **风险评估**: low/medium/high
4. **操作建议** (2-3条): 针对投资者的具体建议
5. **推理过程**: 简述得出结论的逻辑

# 分析框架
- 流动性扩张 → 利好风险资产（股票、加密货币）
- 流动性收缩 → 利好避险资产（美元、国债）
- 关注指标间的背离和确认信号

# 输出格式
使用 JSON 格式，包含以下字段：
- summary: string
- signals: [{name, direction, significance}]
- risk_level: "low" | "medium" | "high"
- recommendations: string[]
- confidence: number (0-1)
- reasoning: string
```

---

## 增强的数据模型

```python
# backend/storage/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

class Indicator(Base):
    __tablename__ = "indicators"
    # ... 原有字段 ...

    # 新增字段
    data_source = Column(String)          # 数据源名称
    api_endpoint = Column(String)         # API 端点
    transform_formula = Column(String)    # 转换公式 (如 "value / 1000000")
    dependencies = Column(JSON)           # 依赖的其他指标 ID
    tags = Column(JSON)                   # 标签 ["fed", "balance_sheet", "qe"]


class AnalysisReport(Base):
    """AI 分析报告存储"""
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True)
    market_id = Column(String, nullable=False, index=True)
    report_type = Column(String)          # daily_summary, signal_alert, correlation

    summary = Column(Text)
    signals = Column(JSON)
    risk_level = Column(String)
    recommendations = Column(JSON)
    confidence = Column(Float)
    reasoning = Column(Text)

    # 生成此报告使用的数据快照
    data_snapshot = Column(JSON)
    prompt_version = Column(String)       # 提示词版本追踪
    model_used = Column(String)           # claude-sonnet-4-20250514

    created_at = Column(DateTime, default=datetime.utcnow)

    # 用户反馈
    user_rating = Column(Integer)         # 1-5
    user_feedback = Column(Text)


class SignalEvent(Base):
    """信号事件记录"""
    __tablename__ = "signal_events"

    id = Column(Integer, primary_key=True)
    indicator_id = Column(String, ForeignKey("indicators.id"))
    event_type = Column(String)           # threshold_breach, trend_change, divergence
    severity = Column(String)             # info, warning, critical

    description = Column(Text)
    current_value = Column(Float)
    threshold_value = Column(Float)

    acknowledged = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 新增 API 端点

```python
# backend/api/routes/analysis.py
from fastapi import APIRouter, Depends, BackgroundTasks

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.get("/markets/{market_id}/summary")
async def get_market_summary(
    market_id: str,
    refresh: bool = False,
    repo: IndicatorRepository = Depends(get_repository),
    analyzer: MarketSummaryAnalyzer = Depends(get_analyzer)
):
    """
    获取市场 AI 分析总结
    - 默认返回缓存的最新分析
    - refresh=true 触发新分析
    """
    if not refresh:
        # 返回最近的分析报告
        report = await repo.get_latest_analysis(market_id, "daily_summary")
        if report and is_fresh(report.created_at, hours=4):
            return report

    # 生成新分析
    indicators_data = await repo.get_market_indicators_with_data(market_id)
    result = await analyzer.generate_summary(market_id, indicators_data)

    # 保存报告
    await repo.save_analysis_report(market_id, "daily_summary", result)

    return result


@router.get("/signals")
async def get_active_signals(
    market_id: str | None = None,
    severity: str | None = None,
    repo: IndicatorRepository = Depends(get_repository)
):
    """获取活跃的信号事件"""
    return await repo.get_signals(market_id, severity, acknowledged=False)


@router.post("/signals/{signal_id}/acknowledge")
async def acknowledge_signal(signal_id: int):
    """确认信号已读"""
    ...


@router.get("/correlation")
async def get_correlation_analysis(
    indicators: list[str],
    days: int = 90
):
    """获取指标间相关性分析"""
    ...


@router.post("/ask")
async def ask_question(
    question: str,
    context_market: str | None = None
):
    """
    自由问答 - 基于当前数据回答用户问题
    例如: "美联储缩表对 BTC 有什么影响？"
    """
    ...
```

---

## 数据源配置

```yaml
# config/sources.yaml
sources:
  FRED:
    name: "Federal Reserve Economic Data"
    base_url: "https://api.stlouisfed.org/fred"
    auth_type: "api_key"
    env_key: "FRED_API_KEY"
    rate_limit: 120  # requests per minute
    markets: ["us"]

  PBOC:
    name: "中国人民银行"
    base_url: "http://www.pbc.gov.cn/diaochatongjisi"
    auth_type: "none"
    parser: "html"  # 需要 HTML 解析
    markets: ["china"]

  EastMoney:
    name: "东方财富"
    base_url: "https://datacenter.eastmoney.com/api"
    auth_type: "none"
    markets: ["china"]

  CoinGecko:
    name: "CoinGecko"
    base_url: "https://api.coingecko.com/api/v3"
    auth_type: "api_key"  # Pro 版本
    env_key: "COINGECKO_API_KEY"
    rate_limit: 30
    markets: ["crypto"]

  Glassnode:
    name: "Glassnode"
    base_url: "https://api.glassnode.com/v1"
    auth_type: "api_key"
    env_key: "GLASSNODE_API_KEY"
    markets: ["crypto"]

# 指标到数据源的映射
indicator_sources:
  # 美国
  fed_balance_sheet:
    source: FRED
    series_id: WALCL

  # 中国
  m2_china:
    source: PBOC
    path: "/tongjishuju/M2"

  shibor_overnight:
    source: EastMoney
    endpoint: "/shibor"

  # 加密货币
  btc_exchange_reserve:
    source: Glassnode
    metric: "distribution/balance_exchanges"

  stablecoin_supply:
    source: CoinGecko
    endpoint: "/coins/markets"
    params:
      category: "stablecoins"
```

---

## 前端增强

### AI 洞察组件

```typescript
// frontend/src/components/AIInsights.tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface AIInsightsProps {
  marketId: string;
}

export const AIInsights = ({ marketId }: AIInsightsProps) => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['analysis', marketId],
    queryFn: () => api.getMarketSummary(marketId),
    staleTime: 4 * 60 * 60 * 1000, // 4 hours
  });

  if (isLoading) return <div>AI 正在分析...</div>;

  return (
    <div className="card bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-lg flex items-center gap-2">
          <span>🤖</span> AI 市场洞察
        </h3>
        <button onClick={() => refetch()} className="btn btn-secondary text-sm">
          刷新分析
        </button>
      </div>

      {/* 核心结论 */}
      <div className="mb-4 p-4 bg-white rounded-lg">
        <p className="text-gray-800 font-medium">{data?.summary}</p>
      </div>

      {/* 风险等级 */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-600">风险等级:</span>
        <RiskBadge level={data?.risk_level} />
        <span className="text-xs text-gray-400">
          置信度: {(data?.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* 关键信号 */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">关键信号</h4>
        <div className="space-y-2">
          {data?.signals.map((signal, i) => (
            <SignalItem key={i} signal={signal} />
          ))}
        </div>
      </div>

      {/* 建议 */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">操作建议</h4>
        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
          {data?.recommendations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      </div>

      {/* 推理过程（可折叠） */}
      <details className="mt-4">
        <summary className="text-sm text-gray-500 cursor-pointer">
          查看分析推理过程
        </summary>
        <p className="mt-2 text-sm text-gray-600 bg-gray-50 p-3 rounded">
          {data?.reasoning}
        </p>
      </details>
    </div>
  );
};
```

---

## 环境变量

```bash
# .env
# 数据源 API Keys
FRED_API_KEY=your_fred_key
COINGECKO_API_KEY=your_coingecko_key
GLASSNODE_API_KEY=your_glassnode_key

# AI 分析
ANTHROPIC_API_KEY=your_anthropic_key
# 或
OPENAI_API_KEY=your_openai_key
LLM_PROVIDER=anthropic  # anthropic | openai

# 缓存
REDIS_URL=redis://localhost:6379

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/liquidity.db
```

---

## 迁移路径

1. **Phase 1**: 添加 AI 分析模块，使用现有 FRED 数据
2. **Phase 2**: 实现插件注册中心，重构 FRED 收集器
3. **Phase 3**: 添加中国数据源 (PBOC, EastMoney)
4. **Phase 4**: 添加加密货币数据源 (CoinGecko, Glassnode)
5. **Phase 5**: 实现实时推送和信号告警
