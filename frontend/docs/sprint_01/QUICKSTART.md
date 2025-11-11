# Sprint 1 快速开始指南

## 🚀 5 分钟快速启动

### 1. 安装依赖

```bash
cd frontend
pnpm install
```

### 2. 配置环境变量

创建 `.env.local` 文件（或复制示例文件）：

```bash
# 后端 API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
pnpm dev
```

浏览器访问：http://localhost:3000

### 4. 启动后端服务

在另一个终端窗口：

```bash
cd ../backend
./start_server.sh
```

---

## 📖 使用指南

### Chat 页面

1. **选择模式**
   - 点击顶部的模式选择器
   - 选择 5 种模式之一：
     - 基础对话 (basic-agent)
     - RAG 问答 (rag)
     - 学习工作流 (workflow)
     - 深度研究 (deep-research)
     - 安全模式 (guarded)

2. **开始对话**
   - 在底部输入框输入消息
   - 按 Enter 或点击发送按钮
   - 支持流式输出，实时看到回复

3. **使用建议提示**
   - 首次进入时会显示 4 个建议提示词
   - 点击任意一个快速填充到输入框

4. **查看详细信息**
   - 点击任意消息，右侧面板会显示详细信息
   - 切换 Tab 查看：来源 / 工具 / 推理 / JSON

5. **会话管理**
   - 左侧边栏显示最近 10 条会话
   - 点击会话快速切换
   - 点击"新建对话"创建新会话

---

## 🎨 功能演示

### 1. 基础对话模式

```
你：介绍一下 LangChain 的核心概念
AI：[流式输出回复...]
```

### 2. RAG 问答模式

```
你：根据文档回答：什么是 LangGraph？
AI：[基于文档的回答 + 右侧显示来源]
```

### 3. 工作流模式

```
你：帮我创建一个学习 Python 的计划
AI：[显示计划步骤 + 任务列表]
```

### 4. 深度研究模式

```
你：研究一下最新的 AI Agent 技术
AI：[显示研究进度 + 子任务 + 最终报告]
```

### 5. 安全模式

```
你：[任意输入]
AI：[带安全过滤的回复]
```

---

## 🔧 开发调试

### 开启调试模式

1. 点击右上角的 Bug 图标
2. 右侧面板会显示原始 JSON 数据
3. 可以查看：
   - 消息列表
   - 当前模式
   - 会话信息

### 查看网络请求

打开浏览器开发者工具：
- Network 标签
- 查看 `/api/chat` 请求
- 查看 SSE 流式响应

### 查看控制台日志

```bash
# 前端日志
浏览器控制台

# 后端日志
cd backend
tail -f logs/app.log
```

---

## 📦 项目结构

```
frontend/
├── app/                      # Next.js 页面
│   ├── api/chat/            # Chat API 路由
│   ├── chat/                # Chat 页面
│   ├── rag/                 # RAG 页面
│   ├── workflows/           # 工作流页面
│   ├── deep-research/       # 深度研究页面
│   └── settings/            # 设置页面
├── components/
│   ├── ai-elements/         # AI Elements 组件
│   ├── chat/                # Chat 相关组件
│   ├── layout/              # 布局组件
│   └── ui/                  # shadcn/ui 组件
├── lib/
│   ├── types.ts             # 类型定义
│   ├── session.ts           # 会话管理
│   ├── api-client.ts        # API 客户端
│   └── utils.ts             # 工具函数
└── providers/
    ├── theme-provider.tsx   # 主题 Provider
    └── session-provider.tsx # 会话 Provider
```

---

## 🎯 常见问题

### 1. 后端连接失败

**问题：** 前端显示"Backend request failed"

**解决：**
- 检查后端是否启动：`curl http://localhost:8000/health`
- 检查环境变量：`.env.local` 中的 `NEXT_PUBLIC_API_URL`
- 检查防火墙设置

### 2. 流式输出不工作

**问题：** 消息一次性显示，没有流式效果

**解决：**
- 检查后端是否支持 SSE
- 检查 `/api/chat` 路由是否使用 Edge Runtime
- 检查浏览器是否支持 EventSource

### 3. 会话不保存

**问题：** 刷新页面后会话丢失

**解决：**
- 检查浏览器是否禁用 localStorage
- 检查浏览器隐私模式
- 清除浏览器缓存后重试

### 4. AI Elements 组件不显示

**问题：** 某些组件不渲染

**解决：**
- 检查 `components/ai-elements/` 目录是否存在
- 重新运行 `npx ai-elements@latest`
- 检查组件导入路径

---

## 🔗 相关链接

- **AI SDK 文档：** https://v6.ai-sdk.dev/docs
- **AI Elements 文档：** https://v6.ai-sdk.dev/elements
- **Next.js 文档：** https://nextjs.org/docs
- **shadcn/ui 文档：** https://ui.shadcn.com

---

## 💡 提示

1. **快捷键**
   - `Ctrl/Cmd + Enter` - 发送消息
   - `Esc` - 停止生成

2. **最佳实践**
   - 每个模式对应不同的后端能力
   - 使用右侧面板查看详细信息
   - 定期清理旧会话

3. **性能优化**
   - 避免同时打开过多会话
   - 定期清理 localStorage
   - 使用生产构建：`pnpm build && pnpm start`

---

## 🎉 开始使用

现在你已经准备好了！打开浏览器，访问 http://localhost:3000，开始体验 LC-StudyLab 智能学习助手吧！

