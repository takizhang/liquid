# 🚀 Liquidity Monitor 部署指南

完全免费的部署方案：**Hugging Face Spaces (后端) + Vercel (前端)**

## 🌐 在线演示

- **前端界面**: https://liquid-pi.vercel.app
- **后端 API**: https://richzhang666-liquid-monitor.hf.space
- **API 文档**: https://richzhang666-liquid-monitor.hf.space/docs

---

## 📋 前置准备

### 1. 注册账号（免费）
- [GitHub](https://github.com/join) - 代码托管
- [Hugging Face](https://huggingface.co/join) - 后端部署
- [Vercel](https://vercel.com/signup) - 前端部署

### 2. 获取 API 密钥（可选）
- [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html) - 美国市场数据（免费）
- [Anthropic API](https://console.anthropic.com) - AI 分析功能（需付费）

---

## 🔧 第一步：准备代码

### 1. Fork 仓库
访问 https://github.com/takizhang/liquid 点击 "Fork"

### 2. 克隆到本地（可选）
```bash
git clone https://github.com/你的用户名/liquid.git
cd liquid
```

---

## 🐳 第二步：部署后端到 Hugging Face Spaces

### 1. 创建 Space
访问：https://huggingface.co/new-space

填写信息：
- **Space name**: `liquid-monitor`（或任意名字）
- **License**: MIT
- **Select the Space SDK**: **Docker**（重要！）
- **Space hardware**: CPU basic（免费）
- **Visibility**: Public

点击 **"Create Space"**

### 2. 推送代码到 Space

#### 方式一：通过 Git（推荐）

```bash
# 获取 Hugging Face Access Token
# 访问 https://huggingface.co/settings/tokens
# 创建 Write 权限的 token

# 添加远程仓库
git remote add hf https://huggingface.co/spaces/你的用户名/liquid-monitor

# 推送代码
git push hf main
# 输入用户名和 token
```

#### 方式二：通过 Web 界面

1. 在 Space 页面点击 "Files and versions"
2. 上传以下文件：
   - `Dockerfile`
   - `README.md`
   - `backend/` 目录
   - `config/` 目录

### 3. 配置环境变量

在 Space 页面：
1. 点击 **"Settings"** 标签
2. 滚动到 **"Repository secrets"**
3. 添加以下密钥：

| Name | Value | 说明 |
|------|-------|------|
| `FRED_API_KEY` | 你的密钥 | 美国市场数据（可选）|
| `ANTHROPIC_API_KEY` | 你的密钥 | AI 分析功能（可选）|
| `LLM_PROVIDER` | `anthropic` | AI 提供商 |

### 4. 等待构建

- Space 会自动开始构建（5-10 分钟）
- 在 "Logs" 标签查看构建进度
- 构建成功后，Space 状态显示 "Running"

### 5. 测试后端

```bash
curl https://你的用户名-liquid-monitor.hf.space/api/health
```

应返回：
```json
{
  "status": "healthy",
  "timestamp": "..."
}
```

---

## 🎨 第三步：部署前端到 Vercel

### 1. 导入项目

访问：https://vercel.com/new

- 选择 "Import Git Repository"
- 选择你 Fork 的 `liquid` 仓库
- 点击 "Import"

### 2. 配置项目

**Framework Preset**: Vite（自动检测）

**Root Directory**: `frontend`（重要！）

**Build Command**: `npm run build`（自动填充）

**Output Directory**: `dist`（自动填充）

### 3. 添加环境变量

在配置页面点击 "Environment Variables"，添加：

| Name | Value |
|------|-------|
| `VITE_API_URL` | `https://你的用户名-liquid-monitor.hf.space` |

**注意**：替换为你的 Hugging Face Space 地址

### 4. 部署

点击 **"Deploy"** 按钮

等待 2-3 分钟，部署完成后会显示：
```
https://你的项目名.vercel.app
```

### 5. 测试前端

访问你的 Vercel 地址，检查：
- ✅ 页面正常加载
- ✅ 市场数据正常显示
- ✅ 图表正常渲染
- ✅ 无 CORS 错误

---

## 🔗 第四步：连接前后端

### 1. 更新后端 CORS

如果前端无法访问后端，需要更新 CORS 配置：

编辑 `backend/api/main.py`：

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

### 2. 验证连接

访问前端，打开浏览器控制台（F12），检查：
- Network 标签：API 请求返回 200
- Console 标签：无 CORS 错误

---

## 💡 第五步：初始化数据（可选）

### 方式一：通过 API 文档

1. 访问 `https://你的后端.hf.space/docs`
2. 测试各个端点
3. 数据会自动保存到数据库

### 方式二：运行初始化脚本（本地）

```bash
cd backend
source venv/bin/activate
PYTHONPATH=".." python scripts/init_data.py
```

---

## ✅ 部署完成检查清单

- [ ] 后端 Space 状态显示 "Running"
- [ ] 后端健康检查返回 200
- [ ] 前端页面正常加载
- [ ] 前端可以获取后端数据
- [ ] 无 CORS 错误
- [ ] API 文档可访问

---

## 🔄 自动部署

### GitHub 集成

- **Hugging Face**: 推送到 `main` 分支自动部署后端
- **Vercel**: 推送到任何分支自动部署前端

### 手动触发

- Hugging Face: Space 页面 → "Factory reboot"
- Vercel: Dashboard → "Redeploy"

---

## 💰 成本总结

| 服务 | 免费额度 | 限制 |
|------|---------|------|
| Hugging Face Spaces | 无限制 | CPU 基础版 |
| Vercel | 100GB 带宽/月 | 个人项目 |
| **总计** | **完全免费** | 适合个人使用 |

---

## 🆘 常见问题

### Q: Hugging Face Space 构建失败
A: 查看 Logs 标签，常见问题：
- 缺少依赖：检查 `requirements.txt`
- 端口错误：确保使用端口 7860
- 数据库错误：检查 `backend/data` 目录权限

### Q: Vercel 部署失败
A: 检查：
- Root Directory 是否设置为 `frontend`
- 环境变量 `VITE_API_URL` 是否正确
- Build Command 是否为 `npm run build`

### Q: CORS 错误
A: 确保后端 `allow_origins` 包含你的 Vercel 域名

### Q: API 请求失败
A: 检查：
1. 后端 Space 是否正在运行
2. Vercel 环境变量是否正确设置
3. 浏览器控制台是否有错误信息

### Q: 数据为空
A: 需要配置 API 密钥并运行数据初始化脚本

---

## 🎯 下一步

部署完成后，你可以：

1. **绑定自定义域名**
   - Vercel: Settings → Domains
   - Hugging Face: 暂不支持

2. **配置 CI/CD**
   - GitHub Actions 自动测试
   - 自动部署到生产环境

3. **添加监控**
   - Vercel Analytics
   - Sentry 错误追踪

4. **优化性能**
   - 启用 CDN
   - 配置缓存策略

---

## 📚 相关资源

- [Hugging Face Spaces 文档](https://huggingface.co/docs/hub/spaces)
- [Vercel 文档](https://vercel.com/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [React 文档](https://react.dev)

---

需要帮助？提交 Issue：https://github.com/takizhang/liquid/issues
