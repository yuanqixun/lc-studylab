# Chatbot 完整特性实现计划

## 📋 任务概述

本文档详细规划如何在 `/chat-ui` 页面中实现 AI Elements 提供的所有 Chatbot 特性，确保前后端协同工作，实现一个功能完整、体验流畅的智能对话系统。

---

## 🎯 目标

实现以下 AI Elements Chatbot 组件的完整集成:

1. **Chain of Thought** - 思维链展示
2. **Checkpoint** - 对话检查点/书签
3. **Confirmation** - 工具调用确认
4. **Context** - 上下文使用情况展示
5. **Conversation** - 对话容器（已基本实现）
6. **Inline Citation** - 内联引用
7. **Message** - 消息组件（已基本实现）
8. **Model Selector** - 模型选择器（已基本实现）
9. **Plan** - AI 规划展示
10. **Prompt Input** - 输入框（已基本实现）
11. **Queue** - 任务队列展示
12. **Reasoning** - 推理过程展示（已基本实现）
13. **Shimmer** - 加载动画（已有）
14. **Sources** - 来源引用（已基本实现）
15. **Suggestion** - 建议提示（已基本实现）
16. **Task** - 任务展示
17. **Tool** - 工具调用展示

---

## 📊 当前状态分析

### ✅ 已实现的特性

从 `chat-example.tsx` 分析:
- ✅ 基础消息展示 (Message, MessageContent, MessageResponse)
- ✅ 消息分支 (MessageBranch)
- ✅ 模型选择器 (ModelSelector)
- ✅ 输入框 (PromptInput)
- ✅ 来源展示 (Sources)
- ✅ 推理展示 (Reasoning)
- ✅ 建议提示 (Suggestions)

### ❌ 未实现的特性

需要新增实现:
1. Chain of Thought - 思维链
2. Checkpoint - 检查点
3. Confirmation - 确认对话
4. Context - 上下文使用
5. Inline Citation - 内联引用
6. Plan - 规划展示
7. Queue - 队列展示
8. Task - 任务展示
9. Tool - 工具调用详情

### 🔧 后端支持情况

从 `backend/api/routers/chat.py` 和 `backend/agents/base_agent.py` 分析:

**已有能力:**
- ✅ 流式输出 (`/chat/stream`)
- ✅ 工具调用 (tools 参数)
- ✅ 对话历史管理
- ✅ 多种 Agent 模式

**需要增强:**
- ❌ 工具调用详情返回 (parameters, status, result)
- ❌ 思维链数据返回
- ❌ 推理过程详细数据
- ❌ Token 使用统计
- ❌ 来源文档元数据
- ❌ 计划/任务结构化数据

---

## 🏗️ 实现架构

### 1. 数据流设计

```
用户输入 → Frontend (chat-ui/page.tsx)
           ↓
  API Route (/api/chat/route.ts)
           ↓
  Backend (/chat/stream)
           ↓
  BaseAgent (LangChain V1)
           ↓
  SSE 流式返回 (增强数据结构)
           ↓
  Frontend 解析并渲染各个 AI Elements 组件
```

### 2. 消息数据结构设计

```typescript
interface EnhancedMessage {
  // 基础字段
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  
  // 分支管理
  versions?: MessageVersion[];
  
  // 思维链
  chainOfThought?: ChainOfThought;
  
  // 推理过程
  reasoning?: Reasoning;
  
  // 工具调用
  tools?: ToolCall[];
  
  // 来源引用
  sources?: Source[];
  
  // 内联引用
  citations?: Citation[];
  
  // 计划
  plan?: Plan;
  
  // 任务列表
  tasks?: Task[];
  
  // 队列
  queue?: QueueItem[];
  
  // 上下文使用
  contextUsage?: ContextUsage;
  
  // 检查点
  checkpoints?: Checkpoint[];
}
```

---

## 🔨 实现步骤

### Phase 1: 后端增强 (Backend Enhancement)

#### 1.1 增强消息输出结构

**文件**: `backend/api/routers/chat.py`

**修改点**:
```python
# 当前 SSE 输出格式
{
  "type": "chunk",
  "content": "文本内容"
}

# 增强后的 SSE 输出格式
{
  "type": "chunk | tool | reasoning | plan | task | source | context",
  "content": "...",
  "metadata": {
    "toolCall": {...},
    "reasoning": {...},
    "sources": [...],
    "tokens": {...},
    # ... 其他元数据
  }
}
```

#### 1.2 工具调用数据追踪

**文件**: `backend/agents/base_agent.py`

在 `astream` 方法中:
```python
async def astream(...):
    # 追踪工具调用
    tool_calls = []
    
    async for chunk in self.graph.astream(...):
        # 检测工具调用
        if is_tool_call(chunk):
            tool_info = extract_tool_info(chunk)
            tool_calls.append(tool_info)
            yield {
                "type": "tool",
                "data": tool_info
            }
        
        # 正常内容
        if content := extract_content(chunk):
            yield {
                "type": "chunk",
                "content": content
            }
```

#### 1.3 增加 Token 使用统计

**新增工具**: `backend/core/usage_tracker.py`

```python
class UsageTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.reasoning_tokens = 0
    
    def track_chunk(self, chunk):
        # 从 LangChain chunk 中提取 token 信息
        pass
    
    def get_usage(self):
        return {
            "inputTokens": self.input_tokens,
            "outputTokens": self.output_tokens,
            "reasoningTokens": self.reasoning_tokens,
        }
```

#### 1.4 结构化数据提取

**新增**: `backend/core/extractors.py`

```python
def extract_reasoning(chunk) -> Optional[dict]:
    """提取推理过程"""
    pass

def extract_plan(chunk) -> Optional[dict]:
    """提取计划"""
    pass

def extract_sources(chunk) -> Optional[list]:
    """提取来源"""
    pass

def extract_citations(content: str) -> list:
    """从内容中提取引用"""
    # 解析 [1], [2] 等引用标记
    pass
```

### Phase 2: 前端数据层 (Frontend Data Layer)

#### 2.1 增强 API 客户端

**文件**: `frontend/lib/api-client.ts`

```typescript
export async function* chatStreamEnhanced(
  request: ChatRequest
): AsyncGenerator<StreamChunk, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        yield data;
      }
    }
  }
}
```

#### 2.2 消息状态管理

**新增**: `frontend/lib/message-manager.ts`

```typescript
class MessageManager {
  private messages: Map<string, EnhancedMessage>;
  
  constructor() {
    this.messages = new Map();
  }
  
  addMessage(msg: EnhancedMessage) {
    this.messages.set(msg.id, msg);
  }
  
  updateMessage(id: string, updates: Partial<EnhancedMessage>) {
    const msg = this.messages.get(id);
    if (msg) {
      Object.assign(msg, updates);
    }
  }
  
  appendContent(id: string, content: string) {
    const msg = this.messages.get(id);
    if (msg) {
      msg.content += content;
    }
  }
  
  addToolCall(id: string, tool: ToolCall) {
    const msg = this.messages.get(id);
    if (msg) {
      msg.tools = msg.tools || [];
      msg.tools.push(tool);
    }
  }
  
  // ... 其他方法
}
```

#### 2.3 流处理 Hook

**新增**: `frontend/hooks/use-enhanced-chat.ts`

```typescript
export function useEnhancedChat() {
  const [messages, setMessages] = useState<EnhancedMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const messageManager = useRef(new MessageManager());
  
  const sendMessage = async (text: string) => {
    // 添加用户消息
    const userMsg: EnhancedMessage = {
      id: nanoid(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    
    // 创建 AI 消息占位
    const aiMsg: EnhancedMessage = {
      id: nanoid(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, aiMsg]);
    messageManager.current.addMessage(aiMsg);
    
    try {
      // 流式接收
      for await (const chunk of chatStreamEnhanced({
        message: text,
        chat_history: messages.map(m => ({
          role: m.role,
          content: m.content,
        })),
      })) {
        handleStreamChunk(aiMsg.id, chunk);
      }
    } finally {
      setIsStreaming(false);
    }
  };
  
  const handleStreamChunk = (msgId: string, chunk: StreamChunk) => {
    switch (chunk.type) {
      case 'chunk':
        messageManager.current.appendContent(msgId, chunk.content);
        break;
      case 'tool':
        messageManager.current.addToolCall(msgId, chunk.data);
        break;
      case 'reasoning':
        messageManager.current.updateMessage(msgId, {
          reasoning: chunk.data,
        });
        break;
      // ... 处理其他类型
    }
    
    // 触发重新渲染
    setMessages(prev => [...prev]);
  };
  
  return {
    messages,
    isStreaming,
    sendMessage,
  };
}
```

### Phase 3: UI 组件集成 (UI Components Integration)

#### 3.1 重构 ChatExample 组件

**文件**: `frontend/components/chat/chat-enhanced.tsx`

```tsx
export const ChatEnhanced = () => {
  const { messages, isStreaming, sendMessage } = useEnhancedChat();
  
  return (
    <div className="chat-container">
      {/* 消息列表 */}
      <Conversation>
        <ConversationContent>
          {messages.map(message => (
            <EnhancedMessageRenderer 
              key={message.id} 
              message={message}
              isStreaming={isStreaming && message.role === 'assistant'}
            />
          ))}
        </ConversationContent>
      </Conversation>
      
      {/* 输入区域 */}
      <PromptInput onSubmit={(msg) => sendMessage(msg.text)}>
        {/* ... */}
      </PromptInput>
    </div>
  );
};
```

#### 3.2 增强的消息渲染器

**文件**: `frontend/components/chat/enhanced-message-renderer.tsx`

```tsx
export const EnhancedMessageRenderer = ({
  message,
  isStreaming,
}: {
  message: EnhancedMessage;
  isStreaming?: boolean;
}) => {
  return (
    <Message from={message.role}>
      {/* 1. Chain of Thought */}
      {message.chainOfThought && (
        <ChainOfThought>
          <ChainOfThoughtHeader />
          <ChainOfThoughtContent>
            {message.chainOfThought.steps.map(step => (
              <ChainOfThoughtStep
                key={step.id}
                label={step.label}
                description={step.description}
                status={step.status}
              />
            ))}
          </ChainOfThoughtContent>
        </ChainOfThought>
      )}
      
      {/* 2. Plan */}
      {message.plan && (
        <Plan isStreaming={isStreaming}>
          <PlanHeader>
            <PlanTitle>{message.plan.title}</PlanTitle>
            <PlanDescription>{message.plan.description}</PlanDescription>
            <PlanAction>
              <PlanTrigger />
            </PlanAction>
          </PlanHeader>
          <PlanContent>
            {/* 计划步骤列表 */}
          </PlanContent>
        </Plan>
      )}
      
      {/* 3. Queue */}
      {message.queue && message.queue.length > 0 && (
        <Queue>
          <QueueSection>
            <QueueSectionTrigger>
              <QueueSectionLabel 
                count={message.queue.length}
                label="任务"
              />
            </QueueSectionTrigger>
            <QueueSectionContent>
              <QueueList>
                {message.queue.map(item => (
                  <QueueItem key={item.id}>
                    <QueueItemIndicator completed={item.completed} />
                    <QueueItemContent>{item.title}</QueueItemContent>
                  </QueueItem>
                ))}
              </QueueList>
            </QueueSectionContent>
          </QueueSection>
        </Queue>
      )}
      
      {/* 4. Tools */}
      {message.tools && message.tools.map(tool => (
        <Tool key={tool.id}>
          <ToolHeader 
            title={tool.name}
            type={tool.type}
            state={tool.state}
          />
          <ToolContent>
            <ToolInput input={tool.parameters} />
            {tool.result && (
              <ToolOutput 
                output={tool.result}
                errorText={tool.error}
              />
            )}
          </ToolContent>
        </Tool>
      ))}
      
      {/* 5. Confirmation (for tool approval) */}
      {message.tools?.some(t => t.requiresApproval) && (
        <Confirmation 
          approval={getToolApproval(message)}
          state={getToolState(message)}
        >
          <ConfirmationTitle>
            工具需要批准
          </ConfirmationTitle>
          <ConfirmationRequest>
            <ConfirmationActions>
              <ConfirmationAction onClick={handleApprove}>
                批准
              </ConfirmationAction>
              <ConfirmationAction onClick={handleReject} variant="outline">
                拒绝
              </ConfirmationAction>
            </ConfirmationActions>
          </ConfirmationRequest>
        </Confirmation>
      )}
      
      {/* 6. Sources */}
      {message.sources && message.sources.length > 0 && (
        <Sources>
          <SourcesTrigger count={message.sources.length} />
          <SourcesContent>
            {message.sources.map(source => (
              <Source
                key={source.href}
                href={source.href}
                title={source.title}
              />
            ))}
          </SourcesContent>
        </Sources>
      )}
      
      {/* 7. Reasoning */}
      {message.reasoning && (
        <Reasoning duration={message.reasoning.duration}>
          <ReasoningTrigger />
          <ReasoningContent>
            {message.reasoning.content}
          </ReasoningContent>
        </Reasoning>
      )}
      
      {/* 8. Main Content with Citations */}
      <MessageContent>
        <MessageResponse>
          {renderContentWithCitations(message.content, message.citations)}
        </MessageResponse>
      </MessageContent>
      
      {/* 9. Checkpoints */}
      {message.checkpoints && (
        <Checkpoint>
          {message.checkpoints.map(cp => (
            <CheckpointTrigger
              key={cp.id}
              tooltip={cp.tooltip}
              onClick={() => handleCheckpoint(cp.id)}
            >
              <CheckpointIcon />
              {cp.label}
            </CheckpointTrigger>
          ))}
        </Checkpoint>
      )}
      
      {/* 10. Context Usage */}
      {message.contextUsage && (
        <Context
          usedTokens={message.contextUsage.usedTokens}
          maxTokens={message.contextUsage.maxTokens}
          usage={message.contextUsage.usage}
          modelId={message.contextUsage.modelId}
        >
          <ContextTrigger />
          <ContextContent>
            <ContextContentHeader />
            <ContextContentBody>
              <ContextInputUsage />
              <ContextOutputUsage />
              <ContextReasoningUsage />
            </ContextContentBody>
            <ContextContentFooter />
          </ContextContent>
        </Context>
      )}
    </Message>
  );
};
```

#### 3.3 内联引用渲染

**文件**: `frontend/components/chat/citation-renderer.tsx`

```tsx
function renderContentWithCitations(
  content: string,
  citations?: Citation[]
): ReactNode {
  if (!citations || citations.length === 0) {
    return <Markdown>{content}</Markdown>;
  }
  
  // 解析内容中的 [1], [2] 等引用标记
  const parts = content.split(/(\[\d+\])/g);
  
  return (
    <>
      {parts.map((part, idx) => {
        const match = part.match(/\[(\d+)\]/);
        if (match) {
          const citationIndex = parseInt(match[1]) - 1;
          const citation = citations[citationIndex];
          
          return (
            <InlineCitation
              key={idx}
              href={citation?.href}
              title={citation?.title}
            >
              {part}
            </InlineCitation>
          );
        }
        
        return <Markdown key={idx}>{part}</Markdown>;
      })}
    </>
  );
}
```

### Phase 4: 特性细节实现

#### 4.1 Chain of Thought (思维链)

**后端**:
```python
# backend/core/extractors.py
def extract_chain_of_thought(agent_output):
    """
    从 Agent 输出中提取思维链
    LangChain V1 的某些模型支持思维链输出
    """
    if hasattr(agent_output, 'reasoning_steps'):
        return {
            "steps": [
                {
                    "id": step.id,
                    "label": step.label,
                    "description": step.description,
                    "status": step.status,
                }
                for step in agent_output.reasoning_steps
            ]
        }
    return None
```

**前端**: 已在 3.2 中展示

#### 4.2 Checkpoint (检查点)

**实现思路**:
- 用户可以为重要的消息添加"书签"
- 存储在 localStorage 或后端
- 快速跳转到标记的位置

**前端**:
```tsx
const [checkpoints, setCheckpoints] = useState<string[]>([]);

const handleCheckpoint = (messageId: string) => {
  setCheckpoints(prev => 
    prev.includes(messageId)
      ? prev.filter(id => id !== messageId)
      : [...prev, messageId]
  );
};

// 在消息列表顶部显示检查点导航
<Checkpoint>
  {checkpoints.map(cpId => (
    <CheckpointTrigger
      key={cpId}
      onClick={() => scrollToMessage(cpId)}
      tooltip="跳转到此消息"
    >
      <CheckpointIcon />
    </CheckpointTrigger>
  ))}
</Checkpoint>
```

#### 4.3 Confirmation (工具确认)

**后端增强**:
```python
# backend/agents/base_agent.py
# 支持 human-in-the-loop

async def astream_with_approval(...):
    async for chunk in self.graph.astream(...):
        # 检测需要人工确认的工具调用
        if is_approval_required(chunk):
            yield {
                "type": "tool_approval_required",
                "data": {
                    "toolId": ...,
                    "toolName": ...,
                    "parameters": ...,
                }
            }
            
            # 等待前端确认
            approval = await wait_for_approval()
            
            if not approval:
                continue
        
        # 正常流程
        yield chunk
```

**前端**: 已在 3.2 中展示

#### 4.4 Context (上下文使用)

**后端**:
```python
# backend/core/usage_tracker.py
class UsageTracker:
    def get_context_info(self, model_id: str):
        # 获取模型的最大 token 数
        max_tokens = MODEL_LIMITS.get(model_id, 4096)
        
        return {
            "usedTokens": self.input_tokens + self.output_tokens,
            "maxTokens": max_tokens,
            "usage": {
                "inputTokens": self.input_tokens,
                "outputTokens": self.output_tokens,
                "reasoningTokens": self.reasoning_tokens,
            },
            "modelId": model_id,
        }

# 在流式输出结束时发送
yield {
    "type": "context",
    "data": tracker.get_context_info(model_id)
}
```

**前端**: 已在 3.2 中展示

#### 4.5 Queue & Task

**使用场景**:
- 显示 Agent 的任务队列
- 显示正在执行的任务列表
- 适用于复杂的多步骤工作流

**后端**:
```python
# 在 workflow 或 deep_research 模式下
# 返回任务队列信息

yield {
    "type": "queue",
    "data": {
        "items": [
            {
                "id": "task-1",
                "title": "搜索相关文档",
                "status": "completed",
            },
            {
                "id": "task-2",
                "title": "分析搜索结果",
                "status": "active",
            },
            {
                "id": "task-3",
                "title": "生成总结",
                "status": "pending",
            },
        ]
    }
}
```

**前端**: 已在 3.2 中展示

#### 4.6 Plan

**使用场景**:
- DeepAgents 的研究计划
- LangGraph workflow 的执行计划

**后端**:
```python
# 在 planning 阶段返回计划
yield {
    "type": "plan",
    "data": {
        "title": "研究计划",
        "description": "关于 XXX 的深度研究",
        "steps": [
            {"id": "1", "title": "文献搜索", "status": "pending"},
            {"id": "2", "title": "资料整理", "status": "pending"},
            {"id": "3", "title": "撰写报告", "status": "pending"},
        ]
    }
}
```

**前端**: 已在 3.2 中展示

---

## 🧪 测试计划

### 1. 单元测试

- [ ] `message-manager.ts` 的消息管理逻辑
- [ ] `use-enhanced-chat.ts` 的 Hook 状态管理
- [ ] 各个提取函数 (extractors.py)
- [ ] UsageTracker 的 token 统计

### 2. 集成测试

- [ ] 前后端流式数据传输
- [ ] SSE 事件解析
- [ ] 消息状态同步
- [ ] 工具调用流程

### 3. UI 测试

- [ ] 各个 AI Elements 组件的渲染
- [ ] 交互功能 (展开/折叠, 点击, hover)
- [ ] 流式更新时的 UI 响应
- [ ] 多消息并发处理

### 4. 端到端测试

#### Test Case 1: 基础对话 + 工具调用
```
用户: 现在几点？明天天气怎么样？
预期:
- ✅ 显示两个 Tool 组件
- ✅ 显示工具调用参数和结果
- ✅ 显示最终回答
- ✅ 显示 Context 使用情况
```

#### Test Case 2: RAG 模式 + Sources
```
用户: 在 RAG 模式下问关于文档的问题
预期:
- ✅ 显示 Sources 组件
- ✅ 显示内联 Citation
- ✅ 点击引用跳转到来源
```

#### Test Case 3: Workflow 模式 + Plan + Queue
```
用户: 启动 workflow
预期:
- ✅ 显示 Plan 组件
- ✅ 显示 Queue 组件
- ✅ 实时更新任务状态
- ✅ 显示每个步骤的输出
```

#### Test Case 4: Deep Research + Chain of Thought
```
用户: 启动深度研究
预期:
- ✅ 显示 Chain of Thought
- ✅ 显示研究步骤
- ✅ 显示 SubAgents 工具调用
- ✅ 显示最终报告
```

---

## 📝 实施清单

### Week 1: 后端增强

- [ ] Day 1-2: 增强 SSE 输出结构
  - [ ] 修改 `chat.py` 的流式输出
  - [ ] 实现 `UsageTracker`
  - [ ] 实现各种 extractors

- [ ] Day 3-4: 工具调用追踪
  - [ ] 修改 `base_agent.py` 的 `astream` 方法
  - [ ] 实现工具调用信息提取
  - [ ] 实现 approval 机制

- [ ] Day 5: 测试后端改动
  - [ ] 单元测试
  - [ ] CLI 测试验证

### Week 2: 前端数据层

- [ ] Day 1-2: API 客户端和 Hook
  - [ ] 实现 `chatStreamEnhanced`
  - [ ] 实现 `MessageManager`
  - [ ] 实现 `useEnhancedChat`

- [ ] Day 3-4: 消息渲染器
  - [ ] 实现 `EnhancedMessageRenderer`
  - [ ] 实现各种辅助组件

- [ ] Day 5: 数据层测试

### Week 3: UI 集成与测试

- [ ] Day 1-2: 组件集成
  - [ ] 集成所有 AI Elements 组件
  - [ ] 样式调整

- [ ] Day 3-4: 交互完善
  - [ ] Checkpoint 功能
  - [ ] Confirmation 交互
  - [ ] Context 悬浮显示

- [ ] Day 5: 端到端测试

---

## 🎨 UI/UX 考虑

### 1. 性能优化

- 使用 `React.memo` 优化组件渲染
- 虚拟滚动处理大量消息
- 防抖/节流处理频繁更新

### 2. 交互体验

- 流畅的展开/折叠动画
- 清晰的加载状态指示
- 友好的错误提示
- 响应式布局

### 3. 可访问性

- 键盘导航支持
- ARIA 标签
- 屏幕阅读器支持

---

## 🚀 扩展计划

### 阶段 2: 高级特性

1. **消息编辑与重新生成**
2. **对话分支管理**
3. **消息搜索与过滤**
4. **导出对话记录**

### 阶段 3: 多模态支持

1. **图片上传与识别**
2. **语音输入与输出**
3. **文件上传与分析**

---

## 📚 参考文档

1. [AI Elements Components](https://v6.ai-sdk.dev/elements/components)
2. [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
3. [LangChain Streaming](https://docs.langchain.com/oss/python/langchain/streaming)
4. [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## ✅ 验收标准

当以下所有条件满足时，认为本计划已完成:

1. ✅ 所有 17 个 AI Elements Chatbot 组件都能正常工作
2. ✅ 后端流式输出包含完整的元数据
3. ✅ 前端能正确解析并渲染所有数据
4. ✅ 所有测试用例通过
5. ✅ UI 流畅无卡顿
6. ✅ 代码有完整的文档和注释
7. ✅ 用户手册和开发文档完善

---

**计划制定日期**: 2025-11-11
**预计完成日期**: 2025-12-02 (3周)
**负责人**: AI 开发团队

