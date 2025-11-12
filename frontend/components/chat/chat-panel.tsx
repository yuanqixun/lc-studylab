"use client"

import { useState, useEffect } from "react"
import { useChat } from "@ai-sdk/react"
import { AgentMode, MessageMetadata } from "@/lib/types"
import { useSession } from "@/providers/session-provider"
import { ChatHeader } from "./chat-header"
import { ChatRightPanel } from "./chat-right-panel"
import { Conversation } from "@/components/ai-elements/conversation"
import { Message } from "@/components/ai-elements/message"
import { PromptInput } from "@/components/ai-elements/prompt-input"
import { Suggestion } from "@/components/ai-elements/suggestion"
import { Plan } from "@/components/ai-elements/plan"
import { Task } from "@/components/ai-elements/task"
import { Checkpoint } from "@/components/ai-elements/checkpoint"
import { ChainOfThought } from "@/components/ai-elements/chain-of-thought"
import { ScrollArea } from "@/components/ui/scroll-area"
import { toast } from "sonner"

interface ChatPanelProps {
  initialMode?: AgentMode
}

export function ChatPanel({ initialMode = 'basic-agent' }: ChatPanelProps) {
  const [mode, setMode] = useState<AgentMode>(initialMode)
  const [showDebug, setShowDebug] = useState(false)
  const [showRightPanel, setShowRightPanel] = useState(true)
  const [selectedMessageMetadata, setSelectedMessageMetadata] = useState<MessageMetadata>()
  
  const { currentSession, updateCurrentSession } = useSession()

  // 使用 AI SDK 的 useChat hook
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    reload,
    stop,
  } = useChat({
    api: '/api/chat',
    body: {
      mode,
      threadId: currentSession?.threadId,
      sessionId: currentSession?.id,
    },
    onFinish: (message) => {
      // 更新会话消息计数
      if (currentSession) {
        updateCurrentSession({
          messageCount: messages.length + 1,
          title: messages[0]?.content.slice(0, 50) || currentSession.title,
        })
      }
    },
    onError: (error) => {
      toast.error('发送消息失败', {
        description: error.message,
      })
    },
  })

  // 模式切换时的处理
  const handleModeChange = (newMode: AgentMode) => {
    setMode(newMode)
    if (currentSession) {
      updateCurrentSession({ mode: newMode })
    }
  }

  // 建议提示词
  const suggestions = [
    { text: "介绍一下 LangChain 的核心概念", icon: "💡" },
    { text: "帮我创建一个学习计划", icon: "📚" },
    { text: "搜索并总结最新的 AI 技术", icon: "🔍" },
    { text: "解释一下 RAG 的工作原理", icon: "🤖" },
  ]

  return (
    <div className="flex flex-col h-full">
      <ChatHeader
        mode={mode}
        onModeChange={handleModeChange}
        onDebugToggle={() => setShowDebug(!showDebug)}
        showDebug={showDebug}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* 主对话区 */}
        <div className="flex-1 flex flex-col">
          {/* 消息列表 */}
          <ScrollArea className="flex-1">
            <div className="container max-w-4xl mx-auto py-6 px-4 min-h-full">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center min-h-full py-12">
                  <h2 className="text-2xl font-bold text-center">您今天在想什么？</h2>
                </div>
              ) : (
                <Conversation>
                  {messages.map((message, index) => {
                    // 解析消息元数据
                    const metadata = message.annotations?.[0] as MessageMetadata | undefined

                    return (
                      <div key={message.id} className="space-y-4">
                        <Message
                          role={message.role}
                          content={message.content}
                          onClick={() => {
                            setSelectedMessageMetadata(metadata)
                            setShowRightPanel(true)
                          }}
                        />

                        {/* 显示计划 */}
                        {metadata?.plan && metadata.plan.length > 0 && (
                          <Plan steps={metadata.plan} />
                        )}

                        {/* 显示任务 */}
                        {metadata?.task && (
                          <Task {...metadata.task} />
                        )}

                        {/* 显示检查点 */}
                        {metadata?.checkpoint && (
                          <Checkpoint {...metadata.checkpoint} />
                        )}

                        {/* 显示思维链 */}
                        {metadata?.chainOfThought && (
                          <ChainOfThought content={metadata.chainOfThought} />
                        )}
                      </div>
                    )
                  })}

                  {/* 加载状态 */}
                  {isLoading && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                      <span>思考中...</span>
                    </div>
                  )}
                </Conversation>
              )}
            </div>
          </ScrollArea>

          {/* 输入区 */}
          <div className="border-t bg-background p-4">
            <div className="container max-w-4xl mx-auto">
              <PromptInput
                value={input}
                onChange={handleInputChange}
                onSubmit={handleSubmit}
                disabled={isLoading}
                placeholder={`在 ${mode} 模式下输入消息...`}
                onStop={stop}
                isLoading={isLoading}
              />
            </div>
          </div>
        </div>

        {/* 右侧面板 */}
        {showRightPanel && (
          <ChatRightPanel
            metadata={selectedMessageMetadata}
            rawJson={showDebug ? { messages, mode, currentSession } : undefined}
          />
        )}
      </div>
    </div>
  )
}
