# 🚀 免费部署指南

完全免费的部署方案：**Vercel (前端) + Render (后端)**

## 📋 部署前准备

### 1. 注册账号
- [Vercel](https://vercel.com) - 使用 GitHub 账号登录
- [Render](https://render.com) - 使用 GitHub 账号登录

### 2. 推送代码到 GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/liquid.git
git push -u origin main
```

---

## 🔧 后端部署 (Render)

### 方式一：使用配置文件（推荐）

1. **连接 GitHub 仓库**
   - 登录 Render Dashboard
   - 点击 "New +" → "Blueprint"
   - 连接你的 GitHub 仓库
   - Render 会自动读取 `render.yaml` 配置

2. **设置环境变量**
   在 Render Dashboard 中添加：
   ```
   FRED_API_KEY=你的密钥
   COINGECKO_API_KEY=你的密钥
   ANTHROPIC_API_KEY=你的密钥
   LLM_PROVIDER=anthropic
   ```

3. **部署**
   - 点击 "Apply" 开始部署
   - 等待 5-10 分钟完成构建
   - 获取后端 URL：`https://liquid-backend.onrender.com`

### 方式二：手动创建

1. **New Web Service**
   - Runtime: Python 3
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn api.main:app --host 0.0.0.0 --port $PORT`

2. **设置环境变量**（同上）

### ⚠️ Render 免费版限制
- **15 分钟无活动后休眠**
- 首次访问需要 30-60 秒冷启动
- 每月 750 小时免费运行时间

---

## 🎨 前端部署 (Vercel)

### 方式一：使用 Vercel CLI

```bash
# 安装 CLI
npm i -g vercel

# 部署
cd frontend
vercel login
vercel --prod
```

### 方式二：通过 Dashboard

1. **导入项目**
   - 登录 Vercel Dashboard
   - 点击 "Add New..." → "Project"
   - 导入你的 GitHub 仓库

2. **配置项目**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **设置环境变量**
   在 Vercel 项目设置中添加：
   ```
   VITE_API_URL=https://liquid-backend.onrender.com
   ```
   （替换为你的 Render 后端地址）

4. **部署**
   - 点击 "Deploy"
   - 获取前端 URL：`https://your-app.vercel.app`

---

## 🔗 连接前后端

### 1. 更新后端 CORS

编辑 `backend/api/main.py`，将 Vercel 域名添加到允许列表：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",  # 你的 Vercel 域名
        "http://localhost:5173"         # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 更新前端 API 地址

在 Vercel 环境变量中设置：
```
VITE_API_URL=https://liquid-backend.onrender.com
```

---

## 📊 数据库方案

### 选项 1：SQLite + Render 持久化存储（推荐）

Render 免费版提供持久化存储，SQLite 数据库会保存在 `/opt/render/project/src/data` 目录。

在 `render.yaml` 中已配置，无需额外操作。

### 选项 2：Supabase PostgreSQL（可选）

如果需要更强大的数据库：

1. 注册 [Supabase](https://supabase.com)（免费 500MB）
2. 创建项目，获取数据库连接字符串
3. 修改 `backend/storage/database.py` 使用 PostgreSQL
4. 在 Render 环境变量中添加 `DATABASE_URL`

---

## ✅ 验证部署

### 1. 测试后端
```bash
curl https://liquid-backend.onrender.com/api/health
```

应返回：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T..."
}
```

### 2. 测试前端
访问 `https://your-app.vercel.app`，检查：
- 页面正常加载
- API 数据正常显示
- 无 CORS 错误

---

## 🔄 自动部署

### GitHub 集成
- **Render**：推送到 `main` 分支自动部署后端
- **Vercel**：推送到任何分支自动部署前端（预览环境）

### 手动触发
- Render Dashboard → "Manual Deploy"
- Vercel Dashboard → "Redeploy"

---

## 💡 优化建议

### 1. 防止后端休眠
使用免费的 Cron 服务定时访问后端：

- [Cron-job.org](https://cron-job.org)（免费）
- 设置每 10 分钟访问一次 `/api/health`

### 2. 加速首次加载
在前端添加加载提示：
```tsx
// 检测后端是否休眠
if (response.status === 503) {
  showMessage("后端正在唤醒，请稍候 30 秒...")
}
```

### 3. 数据初始化
首次部署后，运行数据初始化脚本：

```bash
# 在 Render Shell 中执行
cd backend
python scripts/generate_demo_data.py
```

---

## 🆘 常见问题

### Q: Render 后端一直显示 "Building"
A: 首次构建需要 5-10 分钟，耐心等待。检查 Logs 查看进度。

### Q: Vercel 部署失败
A: 检查 `frontend/vercel.json` 配置是否正确，确保 `dist` 目录存在。

### Q: CORS 错误
A: 确保后端 `allow_origins` 包含你的 Vercel 域名。

### Q: API 请求失败
A: 检查 Vercel 环境变量 `VITE_API_URL` 是否正确设置。

---

## 📈 成本总结

| 服务 | 免费额度 | 限制 |
|------|---------|------|
| Vercel | 无限部署 | 100GB 带宽/月 |
| Render | 750 小时/月 | 15 分钟无活动休眠 |
| **总计** | **完全免费** | 适合个人项目 |

---

## 🎯 下一步

部署完成后，你可以：
1. 绑定自定义域名（Vercel 和 Render 都支持）
2. 设置 HTTPS（自动提供）
3. 配置 CI/CD 自动化测试
4. 添加监控和日志分析

需要帮助？查看：
- [Render 文档](https://render.com/docs)
- [Vercel 文档](https://vercel.com/docs)
