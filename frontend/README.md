# LC-StudyLab 前端

基于 **Next.js 16 + AI SDK v6 + AI Elements** 构建的智能学习助手前端。

## ✨ 特性

- 🎨 **现代化 UI** - 使用 shadcn/ui + Tailwind CSS
- 🤖 **AI 对话** - 集成 AI SDK v6 和 AI Elements 组件
- 🔄 **流式输出** - 实时显示 AI 回复
- 📱 **响应式设计** - 适配各种屏幕尺寸
- 🌓 **主题切换** - 支持浅色/深色模式
- 💾 **会话管理** - 本地持久化对话历史
- 🔀 **消息分支** - 支持多版本消息切换
- 📚 **来源展示** - 显示 RAG 文档来源
- 🧠 **推理过程** - 展示 AI 思考过程
- 🛠️ **工具调用** - 可视化工具执行

## 🚀 快速开始

### 方式 1：使用启动脚本（推荐）

```bash
./start_dev.sh
```

### 方式 2：手动启动

```bash
# 1. 安装依赖
pnpm install

# 2. 配置环境变量
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 3. 启动开发服务器
pnpm dev
```

访问：http://localhost:3000

## 📦 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.0.1 | React 框架 |
| React | 19.2.0 | UI 库 |
| AI SDK | 6.0.0-beta.95 | AI 集成 |
| AI Elements | latest | AI UI 组件 |
| shadcn/ui | latest | UI 组件库 |
| Tailwind CSS | 4.x | CSS 框架 |
| TypeScript | 5.x | 类型系统 |

## 📁 项目结构

```
frontend/
├── app/                      # Next.js App Router
│   ├── api/chat/            # Chat API 路由
│   ├── chat/                # ✅ Chat 页面（已完成）
│   ├── rag/                 # RAG 页面（骨架）
│   ├── workflows/           # 工作流页面（骨架）
│   ├── deep-research/       # 深度研究页面（骨架）
│   └── settings/            # 设置页面（骨架）
├── components/
│   ├── ai-elements/         # AI Elements 组件（30+）
│   ├── chat/                # Chat 相关组件
│   │   ├── chat-panel.tsx          # 主对话面板
│   │   ├── chat-header.tsx         # 头部（模式切换）
│   │   ├── chat-right-panel.tsx    # 右侧详情面板
│   │   └── chat-mode-selector.tsx  # 模式选择器
│   ├── layout/              # 布局组件
│   │   ├── app-layout.tsx          # 全局布局
│   │   ├── app-header.tsx          # 顶部导航
│   │   └── app-sidebar.tsx         # 左侧边栏
│   └── ui/                  # shadcn/ui 组件（19+）
├── lib/
│   ├── types.ts             # 类型定义
│   ├── session.ts           # 会话管理
│   ├── api-client.ts        # API 客户端
│   └── utils.ts             # 工具函数
├── providers/
│   ├── theme-provider.tsx   # 主题 Provider
│   └── session-provider.tsx # 会话 Provider
└── docs/
    └── sprint_01/           # Sprint 1 文档
        ├── SPRINT1_COMPLETION.md
        └── QUICKSTART.md
```

## 🎯 功能清单

### ✅ Sprint 1 已完成

- [x] 项目基础设施（types, session, api-client, providers）
- [x] 全局布局（header, sidebar, layout）
- [x] Chat API 路由处理器
- [x] Chat 页面核心组件
- [x] AI Elements 组件集成（15+ 组件）
- [x] 流式输出和会话管理
- [x] 官方示例 Chat UI（消息分支、来源、推理、工具调用）
- [x] 模型选择器（OpenAI / Anthropic / Google）
- [x] 附件上传支持
- [x] 建议提示词

### 🚧 Sprint 2 计划

- [ ] Chat 增强（编辑、删除、搜索、导出）
- [ ] 会话管理增强（分组、标签、搜索）
- [ ] RAG 页面实现
- [ ] Workflows 页面实现
- [ ] Deep Research 页面实现
- [ ] Settings 页面实现

## 🎨 AI Elements 组件使用

已集成的 AI Elements 组件：

**Chatbot 组件（已使用）：**
- ✅ `Conversation` - 对话容器
- ✅ `Message` - 消息展示
- ✅ `MessageBranch` - 消息分支
- ✅ `MessageResponse` - 消息响应渲染
- ✅ `PromptInput` - 输入框（完整功能）
- ✅ `Suggestion` - 建议提示词
- ✅ `Sources` - RAG 来源展示
- ✅ `Reasoning` - 推理过程展示
- ✅ `ModelSelector` - 模型选择器
- ✅ `ConversationScrollButton` - 滚动按钮

**其他可用组件：**
- `Tool` - 工具调用
- `Plan` - 计划步骤
- `Task` - 任务信息
- `Checkpoint` - 检查点
- `ChainOfThought` - 思维链
- `Context` - 上下文信息
- `Confirmation` - 确认对话
- `Queue` - 队列管理
- `Shimmer` - 加载动画
- `InlineCitation` - 行内引用

## 🔧 开发指南

### 添加新页面

```bash
# 1. 创建页面文件
mkdir -p app/new-page
touch app/new-page/page.tsx

# 2. 使用 AppLayout 包裹
# app/new-page/page.tsx
import { AppLayout } from "@/components/layout/app-layout"

export default function NewPage() {
  return (
    <AppLayout>
      <div>Your content here</div>
    </AppLayout>
  )
}

# 3. 在侧边栏添加导航
# components/layout/app-sidebar.tsx
```

### 添加新模式

```typescript
// 1. 在 lib/types.ts 添加类型
export type AgentMode = 'basic-agent' | 'rag' | 'workflow' | 'deep-research' | 'guarded' | 'new-mode';

// 2. 在 lib/session.ts 添加标签和描述
const labels: Record<AgentMode, string> = {
  // ...
  'new-mode': '新模式',
};

// 3. 在 chat-mode-selector.tsx 添加图标
const modeIcons: Record<AgentMode, React.ComponentType> = {
  // ...
  'new-mode': YourIcon,
};
```

### 使用 AI Elements 组件

```tsx
import { Message } from "@/components/ai-elements/message"
import { Sources } from "@/components/ai-elements/sources"

function YourComponent() {
  return (
    <>
      <Message role="assistant" content="Hello!" />
      <Sources sources={[...]} />
    </>
  )
}
```

## 📚 文档

- [Sprint 1 完成总结](./docs/sprint_01/SPRINT1_COMPLETION.md)
- [快速开始指南](./docs/sprint_01/QUICKSTART.md)
- [AI Elements 使用说明](./docs/sprint_01/AI_ELEMENTS_USAGE.md)
- [Chat UI 升级说明](./docs/sprint_01/CHAT_EXAMPLE_UPGRADE.md) ⭐ 新增
- [故障排除指南](./TROUBLESHOOTING.md)
- [AI SDK 文档](https://v6.ai-sdk.dev/docs)
- [AI Elements 文档](https://v6.ai-sdk.dev/elements)
- [AI Elements Chatbot 示例](https://v6.ai-sdk.dev/elements/examples/chatbot)

## 🐛 故障排除

### 后端连接失败

```bash
# 检查后端是否启动
curl http://localhost:8000/health

# 检查环境变量
cat .env.local
```

### 依赖安装失败

```bash
# 清除缓存
rm -rf node_modules .next
pnpm install
```

### 端口被占用

```bash
# 使用其他端口
pnpm dev -- -p 3001
```

## 📝 环境变量

创建 `.env.local` 文件：

```bash
# 后端 API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# OpenAI API Key（可选，如果前端直接调用）
# OPENAI_API_KEY=sk-...

# Anthropic API Key（可选）
# ANTHROPIC_API_KEY=sk-ant-...
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**开发者：** LC-StudyLab Team  
**版本：** Sprint 1 (v0.1.0)  
**更新时间：** 2025-11-10
