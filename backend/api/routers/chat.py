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
import time

from agents import create_base_agent
from core.tools import BASIC_TOOLS, WEB_SEARCH_TOOLS, WEATHER_TOOLS
from deep_research import create_deep_research_agent
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

DEEP_RESEARCH_KEYWORDS = [
    "深度", "研究", "趋势", "对比", "分析", "报告", "总结",
    "未来", "影响", "市场", "发展", "机制", "原理", "workflow",
    "architecture", "best practice", "最佳实践", "详解", "详述",
    "react", "hooks", "langchain", "ai", "大模型", "机器学习",
    "编译器", "架构", "模式", "best practice", "最佳 实践",
    "使用方法", "介绍", "explain", "how to", "原理", "深入",
]


def should_use_deep_research(message: str) -> bool:
    """
    简单判断问题是否需要深度研究
    """
    if not message:
        return False
    lower = message.lower()
    if any(keyword in message for keyword in DEEP_RESEARCH_KEYWORDS):
        return True
    if len(message.strip()) >= 80:
        return True
    if lower.count("?") + message.count("？") >= 2:
        return True
    return False


async def run_deep_research_task(query: str) -> Dict[str, Any]:
    """
    在线程池中运行深度研究任务，避免阻塞事件循环
    """
    loop = asyncio.get_running_loop()
    thread_id = f"deep_{int(time.time() * 1000)}"

    def _task():
        agent = create_deep_research_agent(
            thread_id=thread_id,
            enable_web_search=True,
            enable_doc_analysis=False,
        )
        return agent.research(query)

    return await loop.run_in_executor(None, _task)


def get_tools_for_request(use_tools: bool, use_advanced_tools: bool) -> List:
    """
    根据请求参数获取工具列表
    
    规则：
    1. 如果用户关闭 use_tools，则不加载任何工具
    2. 天气工具只要配置了 AMAP_KEY，就默认提供（常见问答场景）
    """
    if not use_tools:
        return []
    
    tools: List = list(BASIC_TOOLS)
    
    # 自动注入天气工具（前提：配置了高德 API Key）
    if settings.amap_key:
        for tool in WEATHER_TOOLS:
            if tool not in tools:
                tools.append(tool)
    else:
        logger.debug("🌤️ 未配置 AMAP_KEY，天气工具不可用")
    
    # 默认启用 Tavily 搜索（只要配置了 API Key）
    if settings.tavily_api_key:
        for tool in WEB_SEARCH_TOOLS:
            if tool not in tools:
                tools.append(tool)
    else:
        logger.debug("🌐 未配置 Tavily API Key，网络搜索工具不可用")
    
    return tools


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
        
        # 配置 - 增加递归限制以支持复杂的工具调用链
        config = {
            "recursion_limit": 50,  # 增加递归限制（默认 25）
        }
        
        # 调用 Agent
        response = await agent.ainvoke(
            input_text=request.message,
            chat_history=chat_history,
            config=config,
        )
        def _needs_completion(text: str) -> bool:
            if not text:
                return True
            t = text.strip()
            if len(t) < 30:
                return True
            if not any(t.endswith(p) for p in ["。", "！", "？", ".", "!", "?"]):
                return True
            return False
        if _needs_completion(response):
            from core.models import get_chat_model
            model = get_chat_model()
            prompt = (
                f"用户问题：{request.message}\n\n"
                f"当前回复（不完整）：{response}\n\n"
                "请继续并完整回答上述问题，补充必要的解释或例子，最后给出一句简明结论。"
            )
            completion = await model.ainvoke([{ "role": "user", "content": prompt }])
            if getattr(completion, "content", None):
                response = completion.content
        
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
    流式聊天接口（SSE - Server-Sent Events）- 增强版
    
    接收用户消息，以流式方式返回 AI 的回复。
    适合需要实时显示生成过程的场景。
    
    增强功能:
    - 支持工具调用详情输出
    - 支持推理过程输出
    - 支持 token 使用统计
    - 支持来源引用输出
    - 支持计划和任务输出
    
    Args:
        request: 聊天请求
        
    Returns:
        SSE 流式响应
        
    响应格式（SSE）:
        ```
        data: {"type": "start", "message": "开始生成..."}
        data: {"type": "chunk", "content": "文本内容"}
        data: {"type": "tool", "data": {...}}
        data: {"type": "reasoning", "data": {...}}
        data: {"type": "source", "data": {...}}
        data: {"type": "context", "data": {...}}
        data: {"type": "end", "message": "生成完成"}
        ```
    """
    logger.info(f"🌊 收到流式聊天请求: {request.message[:50]}...")
    
    async def generate():
        """SSE 生成器函数 - 增强版"""
        from core.usage_tracker import create_usage_tracker
        from core.extractors import MessageExtractor
        from langchain_core.messages import AIMessage, ToolMessage
        
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成...'}, ensure_ascii=False)}\n\n"
            
            # 创建 usage tracker
            usage_tracker = create_usage_tracker()
            
            # 创建消息提取器
            extractor = MessageExtractor()

            # 如果问题需要深度研究，优先走 DeepResearch 流程
            if should_use_deep_research(request.message):
                logger.info("🧠 触发深度研究流程，交给 DeepResearchAgent 处理")
                
                reasoning_event = {
                    "type": "reasoning",
                    "data": {
                        "content": "问题较为复杂，正在调度深度研究工作流并执行网络搜索...",
                        "duration": 0,
                    },
                }
                yield f"data: {json.dumps(reasoning_event, ensure_ascii=False)}\n\n"
                
                deep_result = await run_deep_research_task(request.message)
                final_report = deep_result.get("final_report") or deep_result.get("error")
                if not final_report:
                    final_report = (
                        "深度研究已完成，但未生成可用报告。"
                        " 请稍后重试或调整问题表述。"
                    )
                
                chunk_data = {
                    "type": "chunk",
                    "content": final_report,
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                # 发送上下文信息（深度研究模式下 token 统计可能为零）
                context_info = usage_tracker.get_usage_info()
                yield f"data: {json.dumps({'type': 'context', 'data': context_info}, ensure_ascii=False)}\n\n"
                
                # 结束事件
                yield f"data: {json.dumps({'type': 'end', 'message': '生成完成'}, ensure_ascii=False)}\n\n"
                
                usage_tracker.log_summary()
                logger.info("✅ 深度研究流程完成")
                return
            
            # 获取工具列表
            tools = get_tools_for_request(request.use_tools, request.use_advanced_tools)
            tool_names = [tool.name for tool in tools]
            weather_tool_names = {tool.name for tool in WEATHER_TOOLS}
            
            # 创建 Agent（启用流式）
            agent = create_base_agent(
                tools=tools,
                prompt_mode=request.mode,
            )
            
            # 转换对话历史
            chat_history = convert_chat_history(request.chat_history)
            
            # 准备输入
            messages = []
            if chat_history:
                messages.extend(chat_history)
            
            from langchain_core.messages import HumanMessage
            messages.append(HumanMessage(content=request.message))
            
            graph_input = {"messages": messages}
            
            # 追踪工具调用
            tool_calls_map = {}
            current_message_content = ""
            last_ai_message = None  # 保存最后一条 AI 消息
            all_messages = []  # 保存所有消息，用于最终提取
            tool_call_count = {}
            prefer_tool_result = False
            
            # 配置 - 增加递归限制以支持复杂的工具调用链
            config = {
                "recursion_limit": 50,  # 增加递归限制（默认 25）
            }
            
            # 使用 graph.astream 获取更详细的输出
            async for chunk in agent.graph.astream(graph_input, config=config, stream_mode="messages"):
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    message, metadata = chunk
                else:
                    message = chunk
                    metadata = {}
                
                # 更新 token 使用
                if metadata:
                    usage_tracker.update_from_metadata(metadata)
                
                # 保存所有消息
                all_messages.append(message)
                
                # 处理 AI 消息
                if isinstance(message, AIMessage):
                    # 保存最后一条 AI 消息
                    last_ai_message = message
                    
                    # 提取并发送工具调用
                    tool_calls = getattr(message, "tool_calls", [])
                    if tool_calls:
                        for tool_call in tool_calls:
                            tool_id = tool_call.get("id", "")
                            tool_name = tool_call.get("name", "")
                            
                            # 追踪工具调用次数
                            if tool_name not in tool_call_count:
                                tool_call_count[tool_name] = 0
                            tool_call_count[tool_name] += 1
                            
                            # 如果同一个工具被调用超过 3 次，记录警告
                            if tool_call_count[tool_name] > 3:
                                logger.warning(f"⚠️ 工具 {tool_name} 被调用了 {tool_call_count[tool_name]} 次，可能存在循环调用")
                            
                            tool_info = {
                                "id": tool_id,
                                "name": tool_name,
                                "type": f"tool-call-{tool_name}",
                                "state": "input-available",
                                "parameters": tool_call.get("args", {}),
                                "result": None,
                                "error": None,
                            }
                            tool_calls_map[tool_id] = tool_info
                            
                            # 发送工具调用事件
                            yield f"data: {json.dumps({'type': 'tool', 'data': tool_info}, ensure_ascii=False)}\n\n"
                    
                    if message.content and not tool_calls and not prefer_tool_result:
                        def _lcp_len(a: str, b: str) -> int:
                            i = 0
                            for ca, cb in zip(a, b):
                                if ca != cb:
                                    break
                                i += 1
                            return i
                        lcp = _lcp_len(current_message_content, message.content)
                        if lcp < len(message.content):
                            new_content = message.content[lcp:]
                            current_message_content = message.content
                            chunk_data = {
                                "type": "chunk",
                                "content": new_content,
                            }
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    
                    # 提取推理过程
                    from core.extractors import extract_reasoning
                    reasoning = extract_reasoning(message)
                    if reasoning:
                        yield f"data: {json.dumps({'type': 'reasoning', 'data': reasoning}, ensure_ascii=False)}\n\n"
                
                # 处理工具结果
                elif isinstance(message, ToolMessage):
                    tool_call_id = getattr(message, "tool_call_id", "")
                    is_error = getattr(message, "status", None) == "error"
                    
                    if tool_call_id in tool_calls_map:
                        tool_info = tool_calls_map[tool_call_id]
                        tool_info["state"] = "output-error" if is_error else "output-available"
                        tool_info["result"] = None if is_error else message.content
                        tool_info["error"] = message.content if is_error else None
                        
                        # 发送工具结果更新
                        yield f"data: {json.dumps({'type': 'tool_result', 'data': tool_info}, ensure_ascii=False)}\n\n"
                        
                        # 针对天气类工具，直接将结果作为助手回复推送，避免等待模型再次总结
                        if (not is_error 
                                and tool_info.get("name") in weather_tool_names
                                and tool_info.get("result")
                                and not tool_info.get("delivered")):
                            weather_result = tool_info["result"]
                            chunk_data = {
                                "type": "chunk",
                                "content": weather_result,
                            }
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                            current_message_content += weather_result
                            
                            # 将该结果作为 AIMessage 保存，确保历史记录完整
                            ai_message = AIMessage(content=weather_result)
                            all_messages.append(ai_message)
                            last_ai_message = ai_message
                            
                            # 防止重复发送
                            tool_info["delivered"] = True
                            prefer_tool_result = True
                
                # 小延迟
                await asyncio.sleep(0.01)
            
            # 从所有消息中提取最终回复
            # 优先查找最后一条有内容的 AI 消息
            final_ai_message = None
            for msg in reversed(all_messages):
                if isinstance(msg, AIMessage) and msg.content and msg.content.strip():
                    final_ai_message = msg
                    break
            
            # 如果找到了最终 AI 消息，发送其内容
            if final_ai_message and final_ai_message.content:
                final_content = final_ai_message.content
                # 如果还有未发送的内容，发送它
                if len(final_content) > len(current_message_content):
                    remaining_content = final_content[len(current_message_content):]
                    if remaining_content:
                        chunk_data = {
                            "type": "chunk",
                            "content": remaining_content,
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        current_message_content = final_content
            
            # 如果最终消息为空或内容很少，但有工具调用结果，使用工具结果作为回复
            if (not final_ai_message or not final_ai_message.content or len(final_ai_message.content.strip()) < 10) and tool_calls_map:
                # 查找天气工具的结果（优先）
                weather_tools = ["get_daily_weather", "get_weather_forecast", "get_weather"]
                for tool_name in weather_tools:
                    for tool_info in tool_calls_map.values():
                        if (tool_info.get("name") == tool_name and 
                            tool_info.get("state") == "output-available" and 
                            tool_info.get("result")):
                            result_content = tool_info.get("result", "")
                            if result_content and result_content not in current_message_content:
                                # 发送工具结果作为最终回复
                                chunk_data = {
                                    "type": "chunk",
                                    "content": result_content,
                                }
                                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                                logger.info(f"✅ 使用工具 {tool_name} 的结果作为最终回复")
                                break
                    else:
                        continue
                    break
                else:
                    # 如果没有天气工具结果，使用第一个成功的工具结果
                    for tool_info in tool_calls_map.values():
                        if (tool_info.get("state") == "output-available" and 
                            tool_info.get("result") and
                            tool_info.get("result") not in current_message_content):
                            result_content = tool_info.get("result", "")
                            if result_content:
                                chunk_data = {
                                    "type": "chunk",
                                    "content": result_content,
                                }
                                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        logger.info(f"✅ 使用工具 {tool_info.get('name')} 的结果作为最终回复")
                        break

            def _needs_completion(text: str) -> bool:
                if not text:
                    return True
                t = text.strip()
                if len(t) < 30:
                    return True
                if not any(t.endswith(p) for p in ["。", "！", "？", ".", "!", "?"]):
                    return True
                return False

            if not prefer_tool_result and _needs_completion(current_message_content):
                from core.models import get_chat_model
                model = get_chat_model()
                prompt = (
                    f"用户问题：{request.message}\n\n"
                    f"当前回复（不完整）：{current_message_content}\n\n"
                    "请继续并完整回答上述问题，补充必要的解释或例子，最后给出一句简明结论。"
                )
                try:
                    completion = await model.ainvoke([{ "role": "user", "content": prompt }])
                    extra = getattr(completion, "content", "")
                    if extra:
                        chunk_data = {
                            "type": "chunk",
                            "content": extra,
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        current_message_content += extra
                except Exception:
                    pass
            
            # 生成动态建议（基于用户问题与最终助手回复）
            try:
                from core.models import get_chat_model
                model = get_chat_model()
                suggestions_prompt = (
                    "你是一个辅助对话的助手。请根据以下用户问题和最终回复，生成4条简洁、相关、可点击的后续问题建议。\n"
                    "用JSON数组返回，每个元素是不超过30字的中文字符串，不要包含编号或多余文本。\n\n"
                    f"用户问题：{request.message}\n\n"
                    f"最终回复：{current_message_content}"
                )
                completion = await model.ainvoke([{ "role": "user", "content": suggestions_prompt }])
                raw = getattr(completion, "content", "")
                suggestions: list[str] = []
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        suggestions = [str(x) for x in parsed if isinstance(x, (str, int, float))]
                        suggestions = [s for s in suggestions if s.strip()][:4]
                except Exception:
                    # 尝试提取JSON片段
                    import re
                    m = re.search(r"\[.*\]", raw, re.DOTALL)
                    if m:
                        try:
                            parsed2 = json.loads(m.group(0))
                            if isinstance(parsed2, list):
                                suggestions = [str(x) for x in parsed2 if isinstance(x, (str, int, float))]
                                suggestions = [s for s in suggestions if s.strip()][:4]
                        except Exception:
                            suggestions = []
                if suggestions:
                    yield f"data: {json.dumps({'type': 'suggestions', 'data': suggestions}, ensure_ascii=False)}\n\n"
            except Exception:
                pass

            # 发送最终的 context 信息
            context_info = usage_tracker.get_usage_info()
            yield f"data: {json.dumps({'type': 'context', 'data': context_info}, ensure_ascii=False)}\n\n"

            # 发送结束事件
            yield f"data: {json.dumps({'type': 'end', 'message': '生成完成'}, ensure_ascii=False)}\n\n"
            
            # 打印统计
            usage_tracker.log_summary()
            logger.info("✅ 流式聊天请求处理完成")
            
        except Exception as e:
            error_msg = f"流式处理出错: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.exception(e)
            
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
