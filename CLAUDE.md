# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack macroeconomic liquidity monitoring system with AI analysis capabilities.
- Backend: Python FastAPI with async SQLAlchemy
- Frontend: React TypeScript with TailwindCSS
- AI: Anthropic Claude / OpenAI for market analysis

## Build & Run Commands

### Quick Start
```bash
chmod +x start.sh && ./start.sh
```

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=".." python scripts/generate_demo_data.py  # Demo data
PYTHONPATH=".." python scripts/init_data.py          # Real data (needs API keys)
PYTHONPATH=".." uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Dev server :5173
npm run build    # Production build
```

## Architecture

```
liquid/
├── backend/
│   ├── core/                    # Interfaces & plugin registry
│   │   ├── interfaces.py       # DataPoint, AnalysisResult, protocols
│   │   └── registry.py         # CollectorRegistry, AnalyzerRegistry
│   ├── collectors/              # Data source plugins
│   │   ├── fred.py             # US Federal Reserve data
│   │   ├── eastmoney.py        # China financial data
│   │   └── coingecko.py        # Crypto market data
│   ├── analyzers/               # AI analysis engine
│   │   ├── llm_client.py       # Anthropic/OpenAI wrapper
│   │   ├── market_summary.py   # Market analysis generator
│   │   └── signal_detector.py  # Signal detection
│   ├── processors/liquidity.py  # Net liquidity calculation
│   ├── storage/
│   │   ├── models.py           # Indicator, DataPoint, AnalysisReport, SignalEvent
│   │   └── repository.py       # Data access layer
│   └── api/
│       ├── main.py             # FastAPI app
│       └── routes/             # markets, indicators, analysis
├── frontend/src/
│   ├── components/
│   │   ├── AIInsights.tsx      # AI analysis card
│   │   ├── SignalAlert.tsx     # Real-time signals
│   │   └── IndicatorChart.tsx  # ECharts visualization
│   └── pages/
│       ├── Overview.tsx        # Market overview
│       ├── MarketDetail.tsx    # Market + AI insights
│       ├── IndicatorDetail.tsx # Single indicator
│       └── Analysis.tsx        # AI Q&A center
└── config/
    ├── indicators.yaml         # All indicator definitions
    └── prompts/market_summary.md
```

## Key Patterns

### Adding a New Data Source
```python
from backend.core import BaseCollector, DataPoint, CollectorRegistry

@CollectorRegistry.register("NewSource")
class NewSourceCollector(BaseCollector):
    source_name = "NewSource"
    supported_markets = ["us"]

    async def fetch(self, indicator_id, series_id, ...) -> list[DataPoint]:
        # Implement data fetching
        pass
```

### Data Flow
1. Collector.fetch() → list[DataPoint]
2. Repository.save_data_points() (upsert)
3. LiquidityProcessor.calculate_change_stats()
4. MarketSummaryAnalyzer.generate_summary() → AI analysis

### Status Logic
- `LiquidityProcessor.determine_status()`: 30d change % + direction (up_is_loose/down_is_loose)
- Net Liquidity = Fed Balance Sheet - RRP - TGA

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET /api/overview | Market overview with status |
| GET /api/markets/{id}/indicators | Market indicators |
| GET /api/indicators/{id} | Indicator data + stats |
| GET /api/analysis/markets/{id}/summary | AI market summary |
| GET /api/analysis/signals | Active signals |
| POST /api/analysis/ask | AI Q&A |

## Environment Variables

```bash
FRED_API_KEY=xxx           # US data
COINGECKO_API_KEY=xxx      # Crypto data
ANTHROPIC_API_KEY=xxx      # AI analysis
LLM_PROVIDER=anthropic     # or openai
```
