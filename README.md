# Liquidity Monitor - 宏观流动性监控系统

实时监控全球宏观流动性指标，支持美国、中国、加密货币市场。

## 快速启动

```bash
./start.sh
```

启动后访问：
- 前端界面: http://localhost:5173
- API 文档: http://localhost:8000/docs

## 手动启动

### 1. 后端

```bash
cd backend

# 首次运行：创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据（需要先配置 .env）
PYTHONPATH=".." python scripts/init_data.py

# 启动服务
PYTHONPATH=".." uvicorn api.main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend

# 首次运行：安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 环境配置

复制 `.env.example` 为 `.env` 并填写：

```bash
# 必需 - FRED API (免费)
# 获取: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY=your_key_here

# 可选 - AI 分析功能
DEEPSEEK_API_KEY=your_key_here
LLM_PROVIDER=deepseek
```

## 数据源

| 市场 | 数据源 | 状态 |
|------|--------|------|
| 🇺🇸 美国 | FRED | ✅ 可用 |
| 🇨🇳 中国 | 东方财富 | ⚠️ 开发中 |
| 🪙 加密货币 | CoinGecko | ✅ 可用 |

## 主要指标

### 美国市场
- Fed 资产负债表 (WALCL)
- 逆回购 RRP (RRPONTSYD)
- 财政部 TGA (WTREGEN)
- M2 货币供应 (M2SL)
- 联邦基金利率 (FEDFUNDS)
- 10年期国债收益率 (DGS10)

### 加密货币市场
- BTC/ETH 价格
- 稳定币总市值
- BTC 市值

## 项目结构

```
liquid/
├── backend/           # Python FastAPI 后端
│   ├── api/          # REST API
│   ├── collectors/   # 数据收集器
│   ├── analyzers/    # AI 分析引擎
│   ├── storage/      # 数据库
│   └── scripts/      # 初始化脚本
├── frontend/          # React TypeScript 前端
├── config/            # 配置文件
│   └── indicators.yaml
├── .env               # 环境变量（需创建）
└── start.sh           # 一键启动脚本
```

## 常用命令

```bash
# 重新获取数据
cd backend && source venv/bin/activate
PYTHONPATH=".." python scripts/init_data.py

# 生成演示数据（无需 API key）
PYTHONPATH=".." python scripts/generate_demo_data.py

# 前端构建
cd frontend && npm run build
```

## API 端点

| 端点 | 说明 |
|------|------|
| GET /api/overview | 市场总览 |
| GET /api/markets/{id}/indicators | 市场指标列表 |
| GET /api/indicators/{id} | 指标详情 |
| GET /api/analysis/markets/{id}/summary | AI 分析（需配置） |

## 技术栈

- **后端**: Python 3.12+, FastAPI, SQLAlchemy, aiosqlite
- **前端**: React 19, TypeScript, TailwindCSS, ECharts
- **AI**: Anthropic Claude / DeepSeek（可选）
