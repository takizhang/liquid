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

实时监控全球宏观流动性指标，支持美国、中国、加密货币市场，集成 AI 分析功能。

## 🌐 在线访问

**前端界面**：https://liquid-pi.vercel.app
**后端 API**：https://richzhang666-liquid-monitor.hf.space
**API 文档**：https://richzhang666-liquid-monitor.hf.space/docs

## ✨ 主要功能

- 📊 **市场总览** - 实时查看美国、中国、加密货币市场流动性状态
- 📈 **指标图表** - 交互式图表展示历史数据和趋势
- 🤖 **AI 分析** - 基于 Anthropic Claude 的智能市场分析
- 🔔 **信号提醒** - 自动检测流动性变化信号
- 📱 **响应式设计** - 支持桌面和移动设备

## 📊 监控指标

### 美国市场 🇺🇸
- Fed 资产负债表 (WALCL)
- 逆回购 RRP (RRPONTSYD)
- 财政部 TGA (WTREGEN)
- M2 货币供应 (M2SL)
- 联邦基金利率 (FEDFUNDS)
- 10年期国债收益率 (DGS10)

### 中国市场 🇨🇳
- M2 货币供应
- 社会融资规模
- 央行资产负债表

### 加密货币市场 🪙
- BTC/ETH 价格
- 稳定币总市值
- BTC 市值占比

## 🚀 本地开发

### 快速启动

```bash
chmod +x start.sh && ./start.sh
```

启动后访问：
- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 环境配置

复制 `.env.example` 为 `.env` 并填写：

```bash
# 必需 - FRED API (免费)
FRED_API_KEY=your_key_here

# 可选 - AI 分析功能
ANTHROPIC_API_KEY=your_key_here
LLM_PROVIDER=anthropic
```

获取 API 密钥：
- FRED API: https://fred.stlouisfed.org/docs/api/api_key.html
- Anthropic API: https://console.anthropic.com

## 🏗️ 技术栈

**后端**
- Python 3.11+
- FastAPI - 异步 Web 框架
- SQLAlchemy + aiosqlite - 异步数据库
- Anthropic Claude - AI 分析

**前端**
- React 19 + TypeScript
- TailwindCSS - 样式框架
- ECharts - 数据可视化
- Vite - 构建工具

**部署**
- 后端：Hugging Face Spaces (Docker)
- 前端：Vercel
- 数据库：SQLite

## 📁 项目结构

```
liquid/
├── backend/              # Python FastAPI 后端
│   ├── api/             # REST API 路由
│   ├── collectors/      # 数据收集器（FRED, CoinGecko 等）
│   ├── analyzers/       # AI 分析引擎
│   ├── processors/      # 流动性计算处理器
│   ├── storage/         # 数据库模型和仓储
│   └── scripts/         # 数据初始化脚本
├── frontend/             # React TypeScript 前端
│   ├── src/
│   │   ├── components/  # UI 组件
│   │   ├── pages/       # 页面组件
│   │   └── api/         # API 客户端
│   └── public/
├── config/               # 配置文件
│   ├── indicators.yaml  # 指标定义
│   └── prompts/         # AI 提示词模板
├── Dockerfile            # Docker 部署配置
└── DEPLOYMENT_HF.md      # 部署指南
```

## 🔧 API 端点

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/overview` | 市场总览 |
| `GET /api/markets/{id}/indicators` | 市场指标列表 |
| `GET /api/indicators/{id}` | 指标详情和历史数据 |
| `GET /api/analysis/markets/{id}/summary` | AI 市场分析 |
| `GET /api/analysis/signals` | 活跃信号列表 |
| `POST /api/analysis/ask` | AI 问答 |

## 📖 部署指南

查看 [DEPLOYMENT_HF.md](./DEPLOYMENT_HF.md) 获取完整的部署教程。

### 快速部署

**后端（Hugging Face Spaces）**
1. Fork 本仓库
2. 在 HF 创建 Space，选择 Docker SDK
3. 推送代码到 Space
4. 配置环境变量

**前端（Vercel）**
1. 导入 GitHub 仓库
2. Root Directory: `frontend`
3. 添加环境变量：`VITE_API_URL`
4. 部署

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- GitHub: https://github.com/takizhang/liquid
- 在线演示: https://liquid-pi.vercel.app
- API 文档: https://richzhang666-liquid-monitor.hf.space/docs

