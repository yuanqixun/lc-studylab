/**
 * 增强的聊天 Hook
 * 处理流式聊天、消息管理和状态更新
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { nanoid } from 'nanoid';
import type { EnhancedMessage, StreamChunk, ChatRequest } from '@/lib/types';
import { MessageManager, createMessageManager } from '@/lib/message-manager';
import { chatStreamEnhanced } from '@/lib/api-client-enhanced';

export interface UseEnhancedChatOptions {
  /**
   * 初始消息列表
   */
  initialMessages?: EnhancedMessage[];
  
  /**
   * Agent 模式
   */
  mode?: string;
  
  /**
   * 是否启用工具
   */
  useTools?: boolean;
  
  /**
   * 错误回调
   */
  onError?: (error: Error) => void;
  
  /**
   * 流开始回调
   */
  onStreamStart?: () => void;
  
  /**
   * 流结束回调
   */
  onStreamEnd?: () => void;
}

export interface UseEnhancedChatReturn {
  /**
   * 所有消息
   */
  messages: EnhancedMessage[];
  
  /**
   * 是否正在流式输出
   */
  isStreaming: boolean;
  
  /**
   * 发送消息
   */
  sendMessage: (text: string) => Promise<void>;
  
  /**
   * 停止流式输出
   */
  stopStreaming: () => void;
  
  /**
   * 清空消息
   */
  clearMessages: () => void;
  
  /**
   * 重新生成最后一条回复
   */
  regenerateLastResponse: () => Promise<void>;
  
  /**
   * 错误信息
   */
  error: Error | null;
}

export function useEnhancedChat(
  options: UseEnhancedChatOptions = {}
): UseEnhancedChatReturn {
  const {
    initialMessages = [],
    mode = 'default',
    useTools = true,
    onError,
    onStreamStart,
    onStreamEnd,
  } = options;

  // 状态
  const [messages, setMessages] = useState<EnhancedMessage[]>(initialMessages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Refs
  const messageManagerRef = useRef<MessageManager>(createMessageManager());
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentStreamingMessageIdRef = useRef<string | null>(null);

  // 初始化消息管理器
  useEffect(() => {
    const manager = messageManagerRef.current;
    
    // 添加初始消息
    if (initialMessages.length > 0) {
      manager.addMessages(initialMessages);
    }

    // 订阅消息变化
    const unsubscribe = manager.subscribe(() => {
      setMessages(manager.getAllMessages());
    });

    return unsubscribe;
  }, [initialMessages]);

  /**
   * 处理流式数据块
   */
  const handleStreamChunk = useCallback((
    messageId: string,
    chunk: StreamChunk
  ) => {
    const manager = messageManagerRef.current;

    switch (chunk.type) {
      case 'start':
        // 流开始
        if (onStreamStart) {
          onStreamStart();
        }
        break;

      case 'chunk':
        // 追加内容，避免与工具结果重复
        {
          const existingMessage = manager.getMessage(messageId);
          const pendingToolResult = existingMessage?.metadata?.lastToolResult;
          if (pendingToolResult && pendingToolResult === chunk.content) {
            manager.setContent(messageId, chunk.content);
            manager.setMetadata(messageId, { lastToolResult: undefined });
          } else {
            manager.appendContent(messageId, chunk.content);
          }
        }
        break;

      case 'tool':
        // 添加工具调用
        manager.addToolCall(messageId, chunk.data);
        break;

      case 'tool_result':
        // 更新工具结果
        manager.updateToolResult(messageId, chunk.data.id, chunk.data);
        // 如果当前消息还没有正文，而工具已经产出结果，则直接使用工具结果填充，
        // 这样像天气查询这类只依赖工具输出的场景也能及时显示
        if (chunk.data.result) {
          const targetMessage = manager.getMessage(messageId);
          if (targetMessage) {
            if (!targetMessage.content?.trim()) {
              manager.setContent(messageId, chunk.data.result);
            } else {
              manager.appendContent(messageId, chunk.data.result);
            }
            manager.setMetadata(messageId, { lastToolResult: chunk.data.result });
          }
        }
        break;

      case 'reasoning':
        // 设置推理信息
        manager.setReasoning(messageId, chunk.data);
        break;

      case 'source':
        // 添加单个来源
        manager.addSource(messageId, chunk.data);
        break;

      case 'sources':
        // 批量添加来源
        manager.addSources(messageId, chunk.data);
        break;

      case 'plan':
        // 设置计划
        manager.setPlan(messageId, chunk.data);
        break;

      case 'task':
        // 添加任务
        manager.addTask(messageId, chunk.data);
        break;

      case 'queue':
        // 设置队列
        manager.setQueue(messageId, chunk.data);
        break;

      case 'context':
        // 设置上下文使用信息
        manager.setContextUsage(messageId, chunk.data);
        break;

      case 'citation':
        // 添加引用
        manager.addCitation(messageId, chunk.data);
        break;

      case 'chainOfThought':
        // 设置思维链
        manager.setChainOfThought(messageId, chunk.data);
        break;

      case 'suggestions':
        // 写入模型生成的建议到当前助手消息的 metadata
        manager.setMetadata(messageId, { suggestions: Array.isArray(chunk.data) ? chunk.data : [] });
        break;

      case 'end':
        // 流结束
        if (onStreamEnd) {
          onStreamEnd();
        }
        break;

      case 'error':
        // 错误
        const errorObj = new Error(chunk.message);
        setError(errorObj);
        if (onError) {
          onError(errorObj);
        }
        break;
    }
  }, [onError, onStreamStart, onStreamEnd]);

  /**
   * 发送消息
   */
  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) {
      return;
    }

    const manager = messageManagerRef.current;

    try {
      setError(null);
      setIsStreaming(true);

      // 创建用户消息
      const userMessage: EnhancedMessage = {
        id: nanoid(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date(),
      };

      manager.addMessage(userMessage);

      // 创建 AI 消息占位
      const assistantMessageId = nanoid();
      const assistantMessage: EnhancedMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      manager.addMessage(assistantMessage);
      currentStreamingMessageIdRef.current = assistantMessageId;

      // 准备请求
      const chatHistory = manager.getAllMessages()
        .filter(msg => msg.id !== assistantMessageId) // 排除当前 AI 消息
        .map(msg => ({
          role: msg.role,
          content: msg.content,
        }));

      const request: ChatRequest = {
        message: text.trim(),
        chat_history: chatHistory,
        mode,
        use_tools: useTools,
      };

      // 创建 AbortController
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // 流式接收
      for await (const chunk of chatStreamEnhanced(request)) {
        // 检查是否被中止
        if (abortController.signal.aborted) {
          break;
        }

        handleStreamChunk(assistantMessageId, chunk);
      }

    } catch (err) {
      const error = err as Error;
      console.error('Failed to send message:', error);
      setError(error);
      
      if (onError) {
        onError(error);
      }

      // 更新消息显示错误
      if (currentStreamingMessageIdRef.current) {
        const manager = messageManagerRef.current;
        manager.updateMessage(currentStreamingMessageIdRef.current, {
          content: '抱歉，处理您的请求时出现错误。',
          metadata: { error: error.message },
        });
      }
    } finally {
      setIsStreaming(false);
      currentStreamingMessageIdRef.current = null;
      abortControllerRef.current = null;
    }
  }, [isStreaming, mode, useTools, handleStreamChunk, onError]);

  /**
   * 停止流式输出
   */
  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    currentStreamingMessageIdRef.current = null;
  }, []);

  /**
   * 清空消息
   */
  const clearMessages = useCallback(() => {
    messageManagerRef.current.clear();
    setError(null);
  }, []);

  /**
   * 重新生成最后一条回复
   */
  const regenerateLastResponse = useCallback(async () => {
    const manager = messageManagerRef.current;
    const lastAssistantMsg = manager.getLastAssistantMessage();
    
    if (!lastAssistantMsg) {
      return;
    }

    // 找到上一条用户消息
    const allMessages = manager.getAllMessages();
    const assistantIndex = allMessages.findIndex(m => m.id === lastAssistantMsg.id);
    
    if (assistantIndex <= 0) {
      return;
    }

    let userMessage: EnhancedMessage | undefined;
    for (let i = assistantIndex - 1; i >= 0; i--) {
      if (allMessages[i].role === 'user') {
        userMessage = allMessages[i];
        break;
      }
    }

    if (!userMessage) {
      return;
    }

    // 删除最后一条 AI 消息
    manager.deleteMessage(lastAssistantMsg.id);

    // 重新发送
    await sendMessage(userMessage.content);
  }, [sendMessage]);

  return {
    messages,
    isStreaming,
    sendMessage,
    stopStreaming,
    clearMessages,
    regenerateLastResponse,
    error,
  };
}
