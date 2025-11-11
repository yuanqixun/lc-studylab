# Chat UI 升级说明

## 📝 更新内容

已将 Chat UI 页面升级为使用 **AI Elements 官方示例代码**，展示了更完整和专业的 AI 聊天界面实现。

**参考文档：** https://v6.ai-sdk.dev/elements/examples/chatbot

---

## ✨ 新增功能

### 1. **消息分支（Message Branches）**
- ✅ 支持同一消息的多个版本
- ✅ 用户可以切换查看不同版本的回复
- ✅ 前进/后退按钮浏览消息历史

**示例：**
```tsx
<MessageBranch defaultBranch={0}>
  <MessageBranchContent>
    {/* 多个版本的消息 */}
  </MessageBranchContent>
  <MessageBranchSelector>
    <MessageBranchPrevious />
    <MessageBranchPage />
    <MessageBranchNext />
  </MessageBranchSelector>
</MessageBranch>
```

### 2. **来源展示（Sources）**
- ✅ 显示 RAG 检索到的文档来源
- ✅ 可折叠的来源列表
- ✅ 点击查看完整来源信息

**示例数据：**
```typescript
sources: [
  {
    href: "https://react.dev/reference/react",
    title: "React Documentation",
  },
  {
    href: "https://react.dev/reference/react-dom",
    title: "React DOM Documentation",
  },
]
```

### 3. **推理过程（Reasoning）**
- ✅ 显示 AI 的思考过程
- ✅ 显示推理耗时
- ✅ 可展开/折叠查看详细内容

**示例数据：**
```typescript
reasoning: {
  content: "The user is asking for...",
  duration: 10, // 秒
}
```

### 4. **工具调用（Tools）**
- ✅ 显示工具调用信息
- ✅ 显示工具参数和结果
- ✅ 支持多种工具状态

**示例数据：**
```typescript
tools: [
  {
    name: "mcp",
    description: "Searching React documentation",
    status: "input-available",
    parameters: { query: "React hooks" },
    result: "...",
    error: undefined,
  },
]
```

### 5. **模型选择器（Model Selector）**
- ✅ 支持多个 AI 模型选择
- ✅ 按提供商分组（OpenAI / Anthropic / Google）
- ✅ 显示模型 Logo 和名称
- ✅ 搜索过滤功能

**支持的模型：**
- OpenAI: GPT-4o, GPT-4o Mini
- Anthropic: Claude 4 Opus, Claude 4 Sonnet
- Google: Gemini 2.0 Flash

### 6. **附件上传（Attachments）**
- ✅ 支持拖拽上传文件
- ✅ 支持多文件上传
- ✅ 显示附件预览
- ✅ Toast 通知上传状态

### 7. **建议提示词（Suggestions）**
- ✅ 8 个预设建议提示
- ✅ 点击快速输入
- ✅ 响应式网格布局

**建议列表：**
- What are the latest trends in AI?
- How does machine learning work?
- Explain quantum computing
- Best practices for React development
- Tell me about TypeScript benefits
- How to optimize database queries?
- What is the difference between SQL and NoSQL?
- Explain cloud computing basics

### 8. **输入工具栏（Input Tools）**
- ✅ 附件上传按钮
- ✅ 麦克风按钮（语音输入）
- ✅ 网络搜索开关
- ✅ 模型选择器

---

## 🎨 UI 特性

### 消息展示
- ✅ Markdown 渲染支持
- ✅ 代码高亮
- ✅ 流式输出动画
- ✅ 用户/助手消息区分

### 交互体验
- ✅ 自动滚动到底部
- ✅ 滚动按钮快速返回底部
- ✅ 流式输出状态指示
- ✅ 禁用状态管理

### 响应式设计
- ✅ 适配各种屏幕尺寸
- ✅ 移动端友好
- ✅ 触摸手势支持

---

## 📊 数据结构

### MessageType

```typescript
type MessageType = {
  key: string;                    // 消息唯一标识
  from: "user" | "assistant";     // 消息来源
  sources?: {                     // RAG 来源
    href: string;
    title: string;
  }[];
  versions: {                     // 消息版本
    id: string;
    content: string;
  }[];
  reasoning?: {                   // 推理过程
    content: string;
    duration: number;
  };
  tools?: {                       // 工具调用
    name: string;
    description: string;
    status: ToolUIPart["state"];
    parameters: Record<string, unknown>;
    result: string | undefined;
    error: string | undefined;
  }[];
};
```

---

## 🔄 状态管理

### 状态类型

```typescript
type Status = "submitted" | "streaming" | "ready" | "error";
```

### 主要状态

1. **model** - 当前选择的模型
2. **text** - 输入框文本
3. **useWebSearch** - 是否启用网络搜索
4. **useMicrophone** - 是否启用麦克风
5. **status** - 当前状态
6. **messages** - 消息列表
7. **streamingMessageId** - 正在流式输出的消息 ID

---

## 🎯 核心功能实现

### 1. 流式输出

```typescript
const streamResponse = useCallback(
  async (messageId: string, content: string) => {
    setStatus("streaming");
    setStreamingMessageId(messageId);

    const words = content.split(" ");
    let currentContent = "";

    for (let i = 0; i < words.length; i++) {
      currentContent += (i > 0 ? " " : "") + words[i];
      
      // 更新消息内容
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.versions.some((v) => v.id === messageId)) {
            return {
              ...msg,
              versions: msg.versions.map((v) =>
                v.id === messageId ? { ...v, content: currentContent } : v
              ),
            };
          }
          return msg;
        })
      );

      // 模拟延迟
      await new Promise((resolve) =>
        setTimeout(resolve, Math.random() * 100 + 50)
      );
    }

    setStatus("ready");
    setStreamingMessageId(null);
  },
  []
);
```

### 2. 添加用户消息

```typescript
const addUserMessage = useCallback(
  (content: string) => {
    const userMessage: MessageType = {
      key: `user-${Date.now()}`,
      from: "user",
      versions: [
        {
          id: `user-${Date.now()}`,
          content,
        },
      ],
    };

    setMessages((prev) => [...prev, userMessage]);

    // 延迟后添加助手回复
    setTimeout(() => {
      const assistantMessageId = `assistant-${Date.now()}`;
      const randomResponse =
        mockResponses[Math.floor(Math.random() * mockResponses.length)];

      const assistantMessage: MessageType = {
        key: `assistant-${Date.now()}`,
        from: "assistant",
        versions: [
          {
            id: assistantMessageId,
            content: "",
          },
        ],
      };

      setMessages((prev) => [...prev, assistantMessage]);
      streamResponse(assistantMessageId, randomResponse);
    }, 500);
  },
  [streamResponse]
);
```

### 3. 处理提交

```typescript
const handleSubmit = (message: PromptInputMessage) => {
  const hasText = Boolean(message.text);
  const hasAttachments = Boolean(message.files?.length);

  if (!(hasText || hasAttachments)) {
    return;
  }

  setStatus("submitted");

  if (message.files?.length) {
    toast.success("Files attached", {
      description: `${message.files.length} file(s) attached to message`,
    });
  }

  addUserMessage(message.text || "Sent with attachments");
  setText("");
};
```

---

## 🔌 后端集成

### 当前状态
- ✅ 使用 Mock 数据和模拟流式输出
- ✅ 完整的 UI 交互体验
- ⏳ 待对接真实后端 API

### 下一步集成

1. **替换 Mock 数据**
   - 使用 AI SDK 的 `useChat` hook
   - 对接 `/api/chat` 路由
   - 处理真实的流式响应

2. **添加后端数据映射**
   - 将后端响应映射到 `MessageType` 结构
   - 处理 sources、reasoning、tools 数据
   - 实现消息版本管理

3. **集成会话管理**
   - 使用 `useSession` hook
   - 保存和恢复对话历史
   - 同步 thread_id

---

## 📝 使用示例

### 基础对话

```typescript
// 用户输入
"Can you explain how to use React hooks effectively?"

// 助手回复（带来源和工具调用）
{
  from: "assistant",
  sources: [...],
  tools: [...],
  content: "# React Hooks Best Practices..."
}
```

### 消息分支

```typescript
// 同一个问题的多个版本
{
  from: "user",
  versions: [
    { id: "v1", content: "Explain useCallback" },
    { id: "v2", content: "Performance implications of useCallback" },
    { id: "v3", content: "Use cases for useCallback" },
  ]
}
```

### 推理过程

```typescript
{
  from: "assistant",
  reasoning: {
    content: "The user is asking for...",
    duration: 10,
  },
  content: "## useCallback vs useMemo..."
}
```

---

## 🎉 优势

### 相比之前的实现

1. **更完整的功能**
   - ✅ 消息分支
   - ✅ 来源展示
   - ✅ 推理过程
   - ✅ 工具调用
   - ✅ 附件上传

2. **更好的用户体验**
   - ✅ 流畅的动画
   - ✅ 清晰的状态指示
   - ✅ 丰富的交互反馈

3. **更专业的设计**
   - ✅ 遵循 AI Elements 最佳实践
   - ✅ 完整的组件使用示例
   - ✅ 易于扩展和定制

---

## 🚀 下一步

### Sprint 2 计划

1. **对接真实后端**
   - [ ] 替换 Mock 数据
   - [ ] 使用 AI SDK `useChat`
   - [ ] 处理真实流式响应

2. **增强功能**
   - [ ] 实现真实的工具调用
   - [ ] 添加文件上传处理
   - [ ] 实现语音输入
   - [ ] 添加网络搜索功能

3. **优化体验**
   - [ ] 添加加载骨架屏
   - [ ] 优化流式输出性能
   - [ ] 添加错误重试机制
   - [ ] 实现消息编辑和删除

---

## 📚 参考资源

- **官方示例：** https://v6.ai-sdk.dev/elements/examples/chatbot
- **AI Elements 文档：** https://v6.ai-sdk.dev/elements
- **AI SDK 文档：** https://v6.ai-sdk.dev/docs

---

**更新时间：** 2025-11-11  
**版本：** Sprint 1 (v0.1.1)  
**状态：** ✅ 完成

