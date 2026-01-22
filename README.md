---
title: Liquid Monitor
emoji: 💧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Liquidity Monitor - 宏观流动性监控系统

实时监控全球宏观流动性指标，支持美国、中国、加密货币市场。

## 🚀 API 端点

部署后可访问以下端点：

- `GET /api/health` - 健康检查
- `GET /api/overview` - 市场总览
- `GET /api/markets/{id}/indicators` - 市场指标列表
- `GET /api/indicators/{id}` - 指标详情
- `GET /api/analysis/markets/{id}/summary` - AI 市场分析

## 📊 主要指标

### 美国市场
- Fed 资产负债表 (WALCL)
- 逆回购 RRP (RRPONTSYD)
- 财政部 TGA (WTREGEN)
- M2 货币供应 (M2SL)

### 加密货币市场
- BTC/ETH 价格
- 稳定币总市值

## 🔧 技术栈

- **后端**: Python FastAPI + SQLAlchemy
- **AI**: Anthropic Claude
- **部署**: Docker on Hugging Face Spaces

## 📖 完整文档

查看 GitHub 仓库获取完整文档和源代码：
https://github.com/takizhang/liquid
