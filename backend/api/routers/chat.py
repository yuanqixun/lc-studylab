"""
聊天 API 路由
提供 /chat 接口，支持流式和非流式对话

这是第 1 阶段的 API 接口，实现：
1. POST /chat - 非流式对话
2. POST /chat/stream - 流式对话（SSE）
3. 支持对话历史管理
4. 支持不同的 Agent 模式
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio

from agents import create_base_agent
from core.tools import ALL_TOOLS, BASIC_TOOLS
from config import settings, get_logger

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/chat", tags=["chat"])


# ==================== 请求/响应模型 ====================

class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息", min_length=1)
    chat_history: Optional[List[Message]] = Field(
        default=None,
        description="对话历史"
    )
    mode: str = Field(
        default="default",
        description="Agent 模式：default/coding/research/concise/detailed"
    )
    use_tools: bool = Field(
        default=True,
        description="是否启用工具"
    )
    use_advanced_tools: bool = Field(
        default=False,
        description="是否启用高级工具（需要 API Key）"
    )
    streaming: bool = Field(
        default=False,
        description="是否使用流式输出（此字段在非流式接口中无效）"
    )


class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str = Field(..., description="AI 回复")
    mode: str = Field(..., description="使用的 Agent 模式")
    tools_used: List[str] = Field(default_factory=list, description="使用的工具列表")
    success: bool = Field(default=True, description="是否成功")
    error: Optional[str] = Field(default=None, description="错误信息")


# ==================== 辅助函数 ====================

def get_tools_for_request(use_tools: bool, use_advanced_tools: bool) -> List:
    """
    根据请求参数获取工具列表
    
    Args:
        use_tools: 是否使用工具
        use_advanced_tools: 是否使用高级工具
        
    Returns:
        工具列表
    """
    if not use_tools:
        return []
    
    if use_advanced_tools:
        # 检查是否配置了必要的 API Key
        if not settings.tavily_api_key:
            logger.warning("⚠️ 请求使用高级工具，但未配置 Tavily API Key")
            return BASIC_TOOLS
        return ALL_TOOLS
    
    return BASIC_TOOLS


def convert_chat_history(messages: Optional[List[Message]]) -> List:
    """
    将 API 的消息格式转换为 LangChain 的消息格式
    
    Args:
        messages: API 消息列表
        
    Returns:
        LangChain 消息列表
    """
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    if not messages:
        return []
    
    langchain_messages = []
    for msg in messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            langchain_messages.append(SystemMessage(content=msg.content))
    
    return langchain_messages


# ==================== API 端点 ====================

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    非流式聊天接口
    
    接收用户消息，返回 AI 的完整回复。
    适合需要一次性获取完整响应的场景。
    
    Args:
        request: 聊天请求
        
    Returns:
        聊天响应
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/chat" \\
          -H "Content-Type: application/json" \\
          -d '{
            "message": "你好，请介绍一下自己",
            "mode": "default",
            "use_tools": true
          }'
        ```
    """
    logger.info(f"📨 收到聊天请求: {request.message[:50]}...")
    logger.debug(f"   模式: {request.mode}, 工具: {request.use_tools}")
    
    try:
        # 获取工具列表
        tools = get_tools_for_request(request.use_tools, request.use_advanced_tools)
        
        # 创建 Agent
        agent = create_base_agent(
            tools=tools,
            prompt_mode=request.mode,
            # streaming=False,  # 非流式接口
        )
        
        # 转换对话历史
        chat_history = convert_chat_history(request.chat_history)
        
        # 调用 Agent
        response = await agent.ainvoke(
            input_text=request.message,
            chat_history=chat_history,
        )
        
        # 构建响应
        tool_names = [tool.name for tool in tools]
        
        logger.info(f"✅ 聊天请求处理完成，响应长度: {len(response)} 字符")
        
        return ChatResponse(
            message=response,
            mode=request.mode,
            tools_used=tool_names,
            success=True,
        )
        
    except Exception as e:
        error_msg = f"处理聊天请求时出错: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        return ChatResponse(
            message="抱歉，处理您的请求时出现错误。",
            mode=request.mode,
            tools_used=[],
            success=False,
            error=str(e),
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口（SSE - Server-Sent Events）
    
    接收用户消息，以流式方式返回 AI 的回复。
    适合需要实时显示生成过程的场景。
    
    Args:
        request: 聊天请求
        
    Returns:
        SSE 流式响应
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/chat/stream" \\
          -H "Content-Type: application/json" \\
          -d '{
            "message": "讲一个关于编程的笑话",
            "mode": "default"
          }'
        ```
        
    响应格式（SSE）:
        ```
        data: {"type": "start", "message": "开始生成..."}
        
        data: {"type": "chunk", "content": "从前"}
        
        data: {"type": "chunk", "content": "有个"}
        
        data: {"type": "chunk", "content": "程序员"}
        
        data: {"type": "end", "message": "生成完成"}
        ```
    """
    logger.info(f"🌊 收到流式聊天请求: {request.message[:50]}...")
    
    async def generate():
        """SSE 生成器函数"""
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成...'}, ensure_ascii=False)}\n\n"
            
            # 获取工具列表
            tools = get_tools_for_request(request.use_tools, request.use_advanced_tools)
            
            # 创建 Agent（启用流式）
            agent = create_base_agent(
                tools=tools,
                prompt_mode=request.mode,
                # streaming=True,
            )
            
            # 转换对话历史
            chat_history = convert_chat_history(request.chat_history)
            
            # 流式调用 Agent
            async for chunk in agent.astream(
                input_text=request.message,
                chat_history=chat_history,
            ):
                # 发送内容块
                chunk_data = {
                    "type": "chunk",
                    "content": chunk,
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                # 小延迟，让前端有时间处理
                await asyncio.sleep(0.01)
            
            # 发送结束事件
            yield f"data: {json.dumps({'type': 'end', 'message': '生成完成'}, ensure_ascii=False)}\n\n"
            
            logger.info("✅ 流式聊天请求处理完成")
            
        except Exception as e:
            error_msg = f"流式处理出错: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 发送错误事件
            error_data = {
                "type": "error",
                "message": "抱歉，处理您的请求时出现错误",
                "error": str(e),
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    # 返回 SSE 响应
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


@router.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": "chat",
        "version": settings.app_version,
    }


@router.get("/modes")
async def get_available_modes():
    """
    获取可用的 Agent 模式列表
    
    Returns:
        模式列表及其描述
    """
    from core.prompts import SYSTEM_PROMPTS
    
    modes = {}
    for mode_name in SYSTEM_PROMPTS.keys():
        # 提取每个模式的简短描述
        prompt = SYSTEM_PROMPTS[mode_name]
        first_line = prompt.split('\n')[0]
        modes[mode_name] = first_line
    
    return {
        "modes": modes,
        "default": "default",
    }

