# AI Elements 组件使用说明

本文档说明如何在项目中使用 AI Elements 的各个组件。

## 📦 已安装的组件

所有 AI Elements 组件已安装在 `components/ai-elements/` 目录下：

```
components/ai-elements/
├── artifact.tsx              # 工件展示
├── canvas.tsx                # 画布（Workflow）
├── chain-of-thought.tsx      # ✅ 思维链
├── checkpoint.tsx            # ✅ 检查点
├── code-block.tsx            # 代码块
├── confirmation.tsx          # 确认对话
├── connection.tsx            # 连接（Workflow）
├── context.tsx               # 上下文信息
├── controls.tsx              # 控制器（Workflow）
├── conversation.tsx          # ✅ 对话容器
├── edge.tsx                  # 边（Workflow）
├── image.tsx                 # 图片
├── inline-citation.tsx       # 行内引用
├── loader.tsx                # 加载器
├── message.tsx               # ✅ 消息
├── model-selector.tsx        # ✅ 模型选择器
├── node.tsx                  # 节点（Workflow）
├── open-in-chat.tsx          # 在聊天中打开
├── panel.tsx                 # 面板（Workflow）
├── plan.tsx                  # ✅ 计划
├── prompt-input.tsx          # ✅ 输入框
├── queue.tsx                 # 队列
├── reasoning.tsx             # ✅ 推理
├── shimmer.tsx               # 闪烁动画
├── sources.tsx               # ✅ 来源
├── suggestion.tsx            # ✅ 建议
├── task.tsx                  # ✅ 任务
├── tool.tsx                  # ✅ 工具
├── toolbar.tsx               # 工具栏（Workflow）
└── web-preview.tsx           # Web 预览
```

✅ = 已在 Chat 页面中使用

---

## 🎯 Chatbot 组件

### 1. Conversation - 对话容器

**用途：** 包裹所有消息的容器

**使用示例：**
```tsx
import { Conversation } from "@/components/ai-elements/conversation"

<Conversation>
  {messages.map((message) => (
    <Message key={message.id} {...message} />
  ))}
</Conversation>
```

**位置：** `components/chat/chat-panel.tsx`

---

### 2. Message - 消息展示

**用途：** 显示单条消息（用户/助手）

**使用示例：**
```tsx
import { Message } from "@/components/ai-elements/message"

<Message
  role="assistant"
  content="Hello, how can I help you?"
  onClick={() => handleMessageClick()}
/>
```

**Props：**
- `role`: 'user' | 'assistant' | 'system'
- `content`: string
- `onClick?`: () => void

**位置：** `components/chat/chat-panel.tsx`

---

### 3. PromptInput - 输入框

**用途：** 用户输入消息的输入框

**使用示例：**
```tsx
import { PromptInput } from "@/components/ai-elements/prompt-input"

<PromptInput
  value={input}
  onChange={handleInputChange}
  onSubmit={handleSubmit}
  disabled={isLoading}
  placeholder="输入消息..."
  onStop={stop}
  isLoading={isLoading}
/>
```

**Props：**
- `value`: string
- `onChange`: (e: ChangeEvent) => void
- `onSubmit`: (e: FormEvent) => void
- `disabled?`: boolean
- `placeholder?`: string
- `onStop?`: () => void
- `isLoading?`: boolean

**位置：** `components/chat/chat-panel.tsx`

---

### 4. Suggestion - 建议提示词

**用途：** 显示建议的提示词，用户点击快速输入

**使用示例：**
```tsx
import { Suggestion } from "@/components/ai-elements/suggestion"

<Suggestion
  text="介绍一下 LangChain"
  icon="💡"
  onClick={() => handleSuggestionClick("介绍一下 LangChain")}
/>
```

**Props：**
- `text`: string
- `icon?`: string | ReactNode
- `onClick`: () => void

**位置：** `components/chat/chat-panel.tsx`

---

### 5. Sources - RAG 来源

**用途：** 显示 RAG 检索到的文档来源

**使用示例：**
```tsx
import { Sources } from "@/components/ai-elements/sources"

<Sources
  sources={[
    {
      id: "1",
      title: "LangChain 文档",
      url: "https://docs.langchain.com",
      content: "LangChain is a framework...",
      similarity: 0.95,
    },
  ]}
/>
```

**Props：**
- `sources`: Source[]

**Source 类型：**
```typescript
interface Source {
  id: string
  title: string
  url?: string
  content: string
  similarity?: number
  metadata?: Record<string, any>
}
```

**位置：** `components/chat/chat-right-panel.tsx`

---

### 6. Reasoning - 推理过程

**用途：** 显示 AI 的推理过程

**使用示例：**
```tsx
import { Reasoning } from "@/components/ai-elements/reasoning"

<Reasoning
  reasoning="First, I need to understand the question..."
/>
```

**Props：**
- `reasoning`: string

**位置：** `components/chat/chat-right-panel.tsx`

---

### 7. Tool - 工具调用

**用途：** 显示工具调用的详细信息

**使用示例：**
```tsx
import { Tool } from "@/components/ai-elements/tool"

<Tool
  id="tool-1"
  name="web_search"
  args={{ query: "LangChain" }}
  result={{ results: [...] }}
  status="success"
/>
```

**Props：**
```typescript
interface ToolProps {
  id: string
  name: string
  args: Record<string, any>
  result?: any
  status: 'pending' | 'running' | 'success' | 'error'
  error?: string
}
```

**位置：** `components/chat/chat-right-panel.tsx`

---

### 8. Plan - 计划步骤

**用途：** 显示多步骤计划

**使用示例：**
```tsx
import { Plan } from "@/components/ai-elements/plan"

<Plan
  steps={[
    {
      id: "1",
      title: "理解问题",
      description: "分析用户的需求",
      status: "completed",
      order: 1,
    },
    {
      id: "2",
      title: "搜索资料",
      description: "查找相关文档",
      status: "in_progress",
      order: 2,
    },
  ]}
/>
```

**Props：**
```typescript
interface PlanStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  order: number
}
```

**位置：** `components/chat/chat-panel.tsx`

---

### 9. Task - 任务信息

**用途：** 显示单个任务的详细信息

**使用示例：**
```tsx
import { Task } from "@/components/ai-elements/task"

<Task
  id="task-1"
  title="学习 LangChain 基础"
  description="完成 LangChain 入门教程"
  status="in_progress"
  progress={60}
/>
```

**Props：**
```typescript
interface TaskInfo {
  id: string
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  progress?: number
}
```

**位置：** `components/chat/chat-panel.tsx`

---

### 10. Checkpoint - 检查点

**用途：** 显示 LangGraph 检查点信息

**使用示例：**
```tsx
import { Checkpoint } from "@/components/ai-elements/checkpoint"

<Checkpoint
  id="checkpoint-1"
  threadId="thread-123"
  timestamp={Date.now()}
  state={{ step: 2, data: {...} }}
/>
```

**Props：**
```typescript
interface CheckpointInfo {
  id: string
  threadId: string
  timestamp: number
  state: Record<string, any>
}
```

**位置：** `components/chat/chat-panel.tsx`

---

### 11. ChainOfThought - 思维链

**用途：** 显示 AI 的思维链过程

**使用示例：**
```tsx
import { ChainOfThought } from "@/components/ai-elements/chain-of-thought"

<ChainOfThought
  content="Step 1: Analyze the question\nStep 2: Search for information\nStep 3: Synthesize the answer"
/>
```

**Props：**
- `content`: string

**位置：** `components/chat/chat-panel.tsx`

---

### 12. ModelSelector - 模型选择器

**用途：** 选择 AI 模型

**使用示例：**
```tsx
import { ModelSelector } from "@/components/ai-elements/model-selector"

<ModelSelector />
```

**位置：** `components/chat/chat-header.tsx`

---

## 🔧 Workflow 组件

以下组件用于 Workflow 页面（未来实现）：

- `Canvas` - 工作流画布
- `Node` - 工作流节点
- `Edge` - 节点连接
- `Connection` - 连接管理
- `Controls` - 画布控制
- `Panel` - 侧边面板
- `Toolbar` - 工具栏

---

## 🎨 Utility 组件

### CodeBlock - 代码块

**用途：** 显示代码

```tsx
import { CodeBlock } from "@/components/ai-elements/code-block"

<CodeBlock
  code="const hello = 'world'"
  language="typescript"
/>
```

### Image - 图片

**用途：** 显示图片

```tsx
import { Image } from "@/components/ai-elements/image"

<Image
  src="/path/to/image.png"
  alt="Description"
/>
```

### Loader - 加载器

**用途：** 显示加载动画

```tsx
import { Loader } from "@/components/ai-elements/loader"

<Loader />
```

---

## 📝 最佳实践

### 1. 消息元数据结构

在 `lib/types.ts` 中定义了统一的元数据结构：

```typescript
interface MessageMetadata {
  sources?: Source[]
  tools?: ToolCall[]
  reasoning?: string
  plan?: PlanStep[]
  task?: TaskInfo
  checkpoint?: CheckpointInfo
  chainOfThought?: string
}
```

### 2. 后端响应格式

后端应该在消息的 `annotations` 字段中返回元数据：

```json
{
  "id": "msg-1",
  "role": "assistant",
  "content": "Here is the answer...",
  "annotations": [
    {
      "sources": [...],
      "tools": [...],
      "reasoning": "..."
    }
  ]
}
```

### 3. 条件渲染

只在有数据时才渲染组件：

```tsx
{metadata?.plan && metadata.plan.length > 0 && (
  <Plan steps={metadata.plan} />
)}

{metadata?.task && (
  <Task {...metadata.task} />
)}
```

### 4. 组件组合

可以组合多个组件：

```tsx
<div className="space-y-4">
  <Message {...message} />
  {metadata?.plan && <Plan steps={metadata.plan} />}
  {metadata?.task && <Task {...metadata.task} />}
  {metadata?.reasoning && <Reasoning reasoning={metadata.reasoning} />}
</div>
```

---

## 🔗 参考资源

- **AI Elements 官方文档：** https://v6.ai-sdk.dev/elements
- **Chatbot 示例：** https://v6.ai-sdk.dev/elements/examples/chatbot
- **组件 API：** https://v6.ai-sdk.dev/elements/components

---

## 💡 下一步

### Sprint 2 计划使用的组件

- [ ] `Context` - 显示上下文信息
- [ ] `Confirmation` - 人类在环确认
- [ ] `Queue` - 任务队列管理
- [ ] `Shimmer` - 加载骨架屏
- [ ] `InlineCitation` - 行内引用
- [ ] `Artifact` - 工件展示
- [ ] `WebPreview` - Web 预览

### Workflow 页面组件

- [ ] `Canvas` - 工作流画布
- [ ] `Node` - 工作流节点
- [ ] `Edge` - 节点连接
- [ ] `Controls` - 画布控制
- [ ] `Panel` - 侧边面板
- [ ] `Toolbar` - 工具栏

