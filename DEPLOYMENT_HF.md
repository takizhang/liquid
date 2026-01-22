# 🤗 Hugging Face Spaces 部署指南

完全免费，无需信用卡，不会休眠！

## 📋 部署步骤

### 1. 注册 Hugging Face 账号
访问：https://huggingface.co/join
- 使用邮箱注册（免费）
- 验证邮箱

### 2. 创建新 Space
访问：https://huggingface.co/new-space

填写信息：
- **Owner**: 你的用户名
- **Space name**: `liquid-monitor`（或任意名字）
- **License**: MIT
- **Select the Space SDK**: **Docker**（重要！）
- **Space hardware**: CPU basic（免费）
- **Visibility**: Public

点击 **"Create Space"**

### 3. 连接 GitHub 仓库

#### 方式一：直接推送（推荐）

在你的本地项目目录运行：

```bash
# 添加 Hugging Face 远程仓库
git remote add hf https://huggingface.co/spaces/你的用户名/liquid-monitor

# 推送代码
git push hf main
```

#### 方式二：通过 Web 界面

1. 在 Space 页面点击 "Files and versions"
2. 点击 "Add file" → "Upload files"
3. 上传以下文件：
   - `Dockerfile`
   - `README_HF.md`（重命名为 `README.md`）
   - `backend/` 整个目录
   - `config/` 整个目录
   - `.env.example`

### 4. 配置环境变量

在 Space 页面：
1. 点击 **"Settings"** 标签
2. 滚动到 **"Repository secrets"**
3. 添加以下密钥：

| Name | Value |
|------|-------|
| `FRED_API_KEY` | 你的 FRED API 密钥 |
| `ANTHROPIC_API_KEY` | 你的 Anthropic API 密钥 |
| `LLM_PROVIDER` | `anthropic` |
| `COINGECKO_API_KEY` | 你的 CoinGecko API 密钥（可选）|

### 5. 等待构建

- Space 会自动开始构建（5-10 分钟）
- 在 "Logs" 标签查看构建进度
- 构建成功后，Space 会自动运行

### 6. 获取后端 URL

部署成功后，你的后端地址为：
```
https://你的用户名-liquid-monitor.hf.space
```

测试后端：
```bash
curl https://你的用户名-liquid-monitor.hf.space/api/health
```

---

## 🎨 部署前端到 Vercel

后端部署完成后，部署前端：

### 1. 访问 Vercel
https://vercel.com/new

### 2. 导入 GitHub 仓库
- 选择 `takizhang/liquid` 仓库
- Root Directory: `frontend`
- Framework Preset: Vite
- 点击 "Deploy"

### 3. 设置环境变量
在 Vercel 项目设置中添加：
```
VITE_API_URL=https://你的用户名-liquid-monitor.hf.space
```

### 4. 重新部署
添加环境变量后，点击 "Redeploy"

---

## 🔗 更新后端 CORS

部署完成后，需要更新后端 CORS 配置以允许 Vercel 前端访问。

编辑 `backend/api/main.py`，将 Vercel 域名添加到允许列表：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://你的前端.vercel.app",  # 你的 Vercel 域名
        "http://localhost:5173"         # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

提交并推送更新：
```bash
git add backend/api/main.py
git commit -m "Update CORS for Vercel frontend"
git push origin main
git push hf main  # 推送到 Hugging Face
```

---

## ✅ 验证部署

### 测试后端
```bash
curl https://你的用户名-liquid-monitor.hf.space/api/health
```

应返回：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T..."
}
```

### 测试前端
访问你的 Vercel 地址，检查：
- 页面正常加载
- API 数据正常显示
- 无 CORS 错误

---

## 💡 优势

✅ **完全免费**：无需信用卡
✅ **不会休眠**：24/7 运行
✅ **自动部署**：推送代码自动更新
✅ **强大资源**：2 vCPU + 16GB RAM
✅ **适合 AI 项目**：Hugging Face 专为 AI 应用设计

---

## 🆘 常见问题

### Q: 构建失败怎么办？
A: 查看 "Logs" 标签，检查错误信息。常见问题：
- 缺少依赖：检查 `requirements.txt`
- 端口错误：确保使用端口 7860

### Q: API 请求失败
A: 检查：
1. Space 是否正在运行（状态显示 "Running"）
2. 环境变量是否正确设置
3. CORS 配置是否包含 Vercel 域名

### Q: 如何查看日志？
A: 在 Space 页面点击 "Logs" 标签

---

## 🎯 下一步

部署完成后：
1. 测试所有 API 端点
2. 运行数据初始化脚本
3. 配置定时任务（如果需要）
4. 绑定自定义域名（可选）

需要帮助？随时问我！
