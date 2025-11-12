"""
数据提取器
从 LangChain 的 Agent 输出中提取结构化数据
用于前端 AI Elements 组件的渲染
"""

from typing import Optional, Dict, List, Any
import re
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from config import get_logger

logger = get_logger(__name__)


def extract_reasoning(message: BaseMessage) -> Optional[Dict[str, Any]]:
    """
    提取推理过程
    
    某些模型（如 OpenAI o1）支持输出推理过程
    
    Args:
        message: LangChain 消息对象
        
    Returns:
        推理信息字典，包含 content 和 duration
    """
    if not isinstance(message, AIMessage):
        return None
    
    # 检查是否有推理相关的响应元数据
    response_metadata = getattr(message, "response_metadata", {})
    
    # OpenAI o1 模型的推理
    if "reasoning" in response_metadata:
        reasoning_data = response_metadata["reasoning"]
        return {
            "content": reasoning_data.get("content", ""),
            "duration": reasoning_data.get("duration_ms", 0) / 1000,  # 转换为秒
        }
    
    # 检查消息内容中是否包含 <thinking> 标签
    content = message.content
    if isinstance(content, str):
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
        if thinking_match:
            return {
                "content": thinking_match.group(1).strip(),
                "duration": 0,
            }
    
    return None


def extract_tool_calls(message: BaseMessage) -> List[Dict[str, Any]]:
    """
    提取工具调用信息
    
    Args:
        message: LangChain 消息对象
        
    Returns:
        工具调用列表
    """
    if not isinstance(message, AIMessage):
        return []
    
    # AIMessage 的 tool_calls 属性
    tool_calls = getattr(message, "tool_calls", [])
    
    if not tool_calls:
        return []
    
    result = []
    for tool_call in tool_calls:
        tool_info = {
            "id": tool_call.get("id", ""),
            "name": tool_call.get("name", ""),
            "type": f"tool-call-{tool_call.get('name', 'unknown')}",
            "state": "input-available",  # 初始状态
            "parameters": tool_call.get("args", {}),
            "result": None,
            "error": None,
        }
        result.append(tool_info)
    
    logger.debug(f"🔧 提取到 {len(result)} 个工具调用")
    return result


def extract_tool_result(message: ToolMessage) -> Optional[Dict[str, Any]]:
    """
    提取工具执行结果
    
    Args:
        message: ToolMessage 对象
        
    Returns:
        工具结果信息
    """
    if not isinstance(message, ToolMessage):
        return None
    
    tool_call_id = getattr(message, "tool_call_id", "")
    content = message.content
    
    # 检查是否有错误
    is_error = getattr(message, "status", None) == "error"
    
    return {
        "id": tool_call_id,
        "state": "output-error" if is_error else "output-available",
        "result": None if is_error else content,
        "error": content if is_error else None,
    }


def extract_sources(message: BaseMessage, context: Optional[Dict] = None) -> List[Dict[str, str]]:
    """
    提取来源引用
    
    通常来自 RAG 检索的文档
    
    Args:
        message: LangChain 消息对象
        context: 额外上下文信息（如 RAG 检索结果）
        
    Returns:
        来源列表
    """
    sources = []
    
    # 从上下文中获取 RAG 来源
    if context and "retrieved_docs" in context:
        docs = context["retrieved_docs"]
        for doc in docs:
            source = {
                "href": doc.get("metadata", {}).get("source", "#"),
                "title": doc.get("metadata", {}).get("title", "Unknown Source"),
            }
            sources.append(source)
    
    # 从消息元数据中获取
    if isinstance(message, AIMessage):
        response_metadata = getattr(message, "response_metadata", {})
        if "sources" in response_metadata:
            sources.extend(response_metadata["sources"])
    
    logger.debug(f"📚 提取到 {len(sources)} 个来源")
    return sources


def extract_citations(content: str) -> List[Dict[str, Any]]:
    """
    从内容中提取引用标记
    
    解析 [1], [2] 等引用标记
    
    Args:
        content: 消息内容
        
    Returns:
        引用列表
    """
    citations = []
    
    # 查找所有 [数字] 格式的引用
    pattern = r'\[(\d+)\]'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        citation_num = int(match.group(1))
        citations.append({
            "index": citation_num,
            "position": match.start(),
            "text": match.group(0),
        })
    
    return citations


def extract_plan(message: BaseMessage) -> Optional[Dict[str, Any]]:
    """
    提取 AI 生成的计划
    
    适用于 DeepAgents 或 Workflow 模式
    
    Args:
        message: LangChain 消息对象
        
    Returns:
        计划信息
    """
    if not isinstance(message, AIMessage):
        return None
    
    content = message.content
    
    # 尝试解析计划格式
    # 常见格式: "## Plan\n1. xxx\n2. yyy\n3. zzz"
    if not isinstance(content, str):
        return None
    
    plan_match = re.search(
        r'##?\s*(?:Plan|计划|步骤)\s*\n((?:\d+\.\s*.+\n?)+)',
        content,
        re.IGNORECASE | re.MULTILINE
    )
    
    if not plan_match:
        return None
    
    plan_text = plan_match.group(1)
    steps = []
    
    # 解析步骤
    for line in plan_text.split('\n'):
        step_match = re.match(r'(\d+)\.\s*(.+)', line.strip())
        if step_match:
            steps.append({
                "id": f"step-{step_match.group(1)}",
                "title": step_match.group(2).strip(),
                "status": "pending",
            })
    
    if not steps:
        return None
    
    return {
        "title": "执行计划",
        "description": f"共 {len(steps)} 个步骤",
        "steps": steps,
    }


def extract_tasks(message: BaseMessage) -> List[Dict[str, Any]]:
    """
    提取任务列表
    
    从消息中解析任务相关内容
    
    Args:
        message: LangChain 消息对象
        
    Returns:
        任务列表
    """
    if not isinstance(message, AIMessage):
        return []
    
    content = message.content
    if not isinstance(content, str):
        return []
    
    tasks = []
    
    # 解析任务列表格式
    # 格式: "- [ ] xxx" 或 "- [x] xxx"
    task_pattern = r'-\s*\[([ x])\]\s*(.+)'
    
    for match in re.finditer(task_pattern, content, re.MULTILINE):
        is_completed = match.group(1).lower() == 'x'
        task_title = match.group(2).strip()
        
        tasks.append({
            "id": f"task-{len(tasks) + 1}",
            "title": task_title,
            "completed": is_completed,
        })
    
    return tasks


def extract_chain_of_thought(message: BaseMessage) -> Optional[Dict[str, Any]]:
    """
    提取思维链
    
    某些模型会输出逐步推理过程
    
    Args:
        message: LangChain 消息对象
        
    Returns:
        思维链信息
    """
    if not isinstance(message, AIMessage):
        return None
    
    # 检查响应元数据
    response_metadata = getattr(message, "response_metadata", {})
    
    if "chain_of_thought" in response_metadata:
        cot_data = response_metadata["chain_of_thought"]
        return {
            "steps": cot_data.get("steps", [])
        }
    
    # 尝试从内容中解析
    content = message.content
    if not isinstance(content, str):
        return None
    
    # 查找 <step> 标签或数字序号
    steps = []
    
    # 格式 1: <step>xxx</step>
    step_matches = re.finditer(
        r'<step(?:\s+id="([^"]+)")?>(.+?)</step>',
        content,
        re.DOTALL
    )
    
    for idx, match in enumerate(step_matches):
        step_id = match.group(1) or f"step-{idx + 1}"
        step_content = match.group(2).strip()
        
        steps.append({
            "id": step_id,
            "label": f"Step {idx + 1}",
            "description": step_content,
            "status": "complete",
        })
    
    if steps:
        return {"steps": steps}
    
    return None


def extract_queue_items(context: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    提取队列项目
    
    通常从 workflow 或 agent 的执行上下文中获取
    
    Args:
        context: 执行上下文
        
    Returns:
        队列项目列表
    """
    if not context:
        return []
    
    # 从上下文中提取队列信息
    if "queue" in context:
        return context["queue"]
    
    if "pending_tasks" in context:
        tasks = context["pending_tasks"]
        return [
            {
                "id": task.get("id", f"task-{idx}"),
                "title": task.get("title", "Unknown Task"),
                "status": task.get("status", "pending"),
            }
            for idx, task in enumerate(tasks)
        ]
    
    return []


class MessageExtractor:
    """
    消息提取器
    
    统一管理所有提取逻辑
    """
    
    def __init__(self):
        self.context: Dict[str, Any] = {}
    
    def set_context(self, context: Dict[str, Any]):
        """设置额外上下文"""
        self.context = context
    
    def extract_all(self, message: BaseMessage) -> Dict[str, Any]:
        """
        提取消息的所有结构化信息
        
        Args:
            message: LangChain 消息对象
            
        Returns:
            包含所有提取信息的字典
        """
        extracted = {
            "reasoning": extract_reasoning(message),
            "tools": extract_tool_calls(message),
            "sources": extract_sources(message, self.context),
            "plan": extract_plan(message),
            "tasks": extract_tasks(message),
            "chainOfThought": extract_chain_of_thought(message),
            "queue": extract_queue_items(self.context),
        }
        
        # 提取内容中的引用
        if isinstance(message, AIMessage) and message.content:
            extracted["citations"] = extract_citations(message.content)
        
        # 移除空值
        return {k: v for k, v in extracted.items() if v}

