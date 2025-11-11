/**
 * 前端类型定义
 */

// 后端模式类型
export type AgentMode = 'basic-agent' | 'rag' | 'workflow' | 'deep-research' | 'guarded';

// 会话类型
export interface Session {
  id: string;
  title: string;
  mode: AgentMode;
  threadId?: string; // 后端 LangGraph/DeepAgents thread_id
  createdAt: number;
  updatedAt: number;
  messageCount: number;
}

// 消息附加元数据
export interface MessageMetadata {
  sources?: Source[];
  tools?: ToolCall[];
  reasoning?: string;
  plan?: PlanStep[];
  task?: TaskInfo;
  checkpoint?: CheckpointInfo;
  chainOfThought?: string;
}

// RAG 来源
export interface Source {
  id: string;
  title: string;
  url?: string;
  content: string;
  similarity?: number;
  metadata?: Record<string, any>;
}

// 工具调用
export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, any>;
  result?: any;
  status: 'pending' | 'running' | 'success' | 'error';
  error?: string;
}

// 计划步骤
export interface PlanStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  order: number;
}

// 任务信息
export interface TaskInfo {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
}

// 检查点信息
export interface CheckpointInfo {
  id: string;
  threadId: string;
  timestamp: number;
  state: Record<string, any>;
}

// API 请求
export interface ChatRequest {
  messages: any[]; // AI SDK Message 类型
  mode: AgentMode;
  threadId?: string;
  sessionId?: string;
  config?: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
  };
}

// API 响应
export interface ChatResponse {
  message: string;
  metadata?: MessageMetadata;
  threadId?: string;
  error?: string;
}

// 模型配置
export interface ModelConfig {
  provider: 'openai' | 'anthropic' | 'google' | 'deepseek';
  model: string;
  displayName: string;
  maxTokens: number;
}

// 应用配置
export interface AppConfig {
  backendUrl: string;
  defaultModel: ModelConfig;
  enableGuardrails: boolean;
  streamingEnabled: boolean;
}

