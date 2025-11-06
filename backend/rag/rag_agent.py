"""
RAG Agent 模块

基于 LangChain 1.0.3 的 create_tool_calling_agent 实现 RAG Agent。

RAG Agent 的核心特性：
- 自动检索相关文档
- 基于检索到的上下文生成回答
- 引用来源文档
- 支持流式输出
- 支持对话历史

参考：
- https://docs.langchain.com/oss/python/langchain/agents
- https://docs.langchain.com/oss/python/langchain/retrieval
"""

from typing import List, Optional, Dict, Any
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models.chat_models import BaseChatModel

from config import settings, get_logger
from core.models import get_chat_model, get_model_string
from rag.retrievers import create_retriever_tool

logger = get_logger(__name__)


# RAG 系统提示词
DEFAULT_RAG_SYSTEM_PROMPT = """你是一个智能问答助手，专门回答基于知识库的问题。

你的任务：
1. 使用 knowledge_base 工具搜索相关信息
2. 基于检索到的文档内容回答用户问题
3. 如果文档中没有相关信息，诚实地告诉用户
4. 在回答中引用来源文档（如果有 source 信息）

回答要求：
- 准确：严格基于文档内容，不要编造信息
- 完整：尽可能提供详细的回答
- 清晰：使用简洁明了的语言
- 引用：在回答末尾列出参考的文档来源

示例回答格式：
[回答内容]

参考来源：
- 文档1: [来源信息]
- 文档2: [来源信息]
"""


def create_rag_agent(
    retriever: BaseRetriever,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tool_name: str = "knowledge_base",
    tool_description: Optional[str] = None,
    streaming: bool = True,
    **kwargs,
):
    """
    创建 RAG Agent
    
    使用 LangChain 1.0.3 的 create_agent API。
    
    Args:
        retriever: 检索器实例
        model: 模型字符串（如 "openai:gpt-4o"），默认使用配置中的模型
        system_prompt: 系统提示词，默认使用 RAG 专用提示词
        tool_name: 检索工具名称
        tool_description: 检索工具描述
        streaming: 是否启用流式输出
        **kwargs: 其他传递给 create_agent 的参数
        
    Returns:
        Agent 实例
        
    Example:
        >>> from rag import (
        ...     load_vector_store,
        ...     get_embeddings,
        ...     create_retriever,
        ...     create_rag_agent
        ... )
        >>> 
        >>> # 加载向量库和创建检索器
        >>> embeddings = get_embeddings()
        >>> vector_store = load_vector_store("data/indexes/my_docs", embeddings)
        >>> retriever = create_retriever(vector_store)
        >>> 
        >>> # 创建 RAG Agent
        >>> agent = create_rag_agent(retriever)
        >>> 
        >>> # 查询
        >>> result = agent.invoke("什么是机器学习？")
        >>> print(result)
        >>> 
        >>> # 流式查询
        >>> for chunk in agent.stream("解释深度学习"):
        ...     print(chunk, end="", flush=True)
    """
    logger.info("🤖 创建 RAG Agent")
    
    # 使用默认模型
    if model is None:
        model = get_model_string()
    
    # 使用默认系统提示词
    if system_prompt is None:
        system_prompt = DEFAULT_RAG_SYSTEM_PROMPT
    
    # 创建检索器工具
    if tool_description is None:
        tool_description = (
            "搜索知识库中的相关信息。"
            "当需要回答关于文档内容的问题时使用此工具。"
            "输入应该是一个搜索查询。"
        )
    
    retriever_tool = create_retriever_tool(
        retriever=retriever,
        name=tool_name,
        description=tool_description,
    )
    
    tools = [retriever_tool]
    
    logger.debug("   创建 Agent...")
    
    # 使用 LangChain 1.0.3 的 create_agent API
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        **kwargs,
    )
    
    logger.info(f"✅ RAG Agent 创建成功")
    logger.info(f"   模型: {model}")
    logger.info(f"   流式输出: {streaming}")
    
    return agent


def format_rag_response(
    output: str,
    intermediate_steps: Optional[List] = None,
) -> Dict[str, Any]:
    """
    格式化 RAG 响应，提取来源文档
    
    Args:
        output: Agent 输出
        intermediate_steps: 中间步骤（包含检索的文档）
        
    Returns:
        格式化后的响应字典
        
    Example:
        >>> result = agent.invoke({"input": "什么是机器学习？"})
        >>> formatted = format_rag_response(
        ...     result["output"],
        ...     result.get("intermediate_steps")
        ... )
        >>> print(formatted["answer"])
        >>> for source in formatted["sources"]:
        ...     print(f"- {source}")
    """
    response = {
        "answer": output,
        "sources": [],
        "retrieved_documents": [],
    }
    
    if not intermediate_steps:
        return response
    
    # 提取检索到的文档
    for step in intermediate_steps:
        if len(step) >= 2:
            action, observation = step[0], step[1]
            
            # 如果是检索工具的结果
            if hasattr(action, "tool") and "knowledge" in action.tool.lower():
                # observation 可能是文档列表或字符串
                if isinstance(observation, list):
                    for doc in observation:
                        response["retrieved_documents"].append(doc)
                        
                        # 提取来源信息
                        if hasattr(doc, "metadata") and doc.metadata:
                            source = doc.metadata.get("source") or doc.metadata.get("filename")
                            if source and source not in response["sources"]:
                                response["sources"].append(source)
    
    return response


def create_conversational_rag_agent(
    retriever: BaseRetriever,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    **kwargs,
):
    """
    创建支持对话历史的 RAG Agent
    
    这是 create_rag_agent 的便捷包装，配置为更好地支持多轮对话。
    
    Args:
        retriever: 检索器实例
        model: 聊天模型
        system_prompt: 系统提示词
        **kwargs: 其他参数
        
    Returns:
        AgentExecutor 实例
        
    Example:
        >>> agent = create_conversational_rag_agent(retriever)
        >>> 
        >>> # 多轮对话
        >>> chat_history = []
        >>> 
        >>> result1 = agent.invoke({
        ...     "input": "什么是机器学习？",
        ...     "chat_history": chat_history
        ... })
        >>> chat_history.extend([
        ...     HumanMessage(content="什么是机器学习？"),
        ...     AIMessage(content=result1["output"])
        ... ])
        >>> 
        >>> result2 = agent.invoke({
        ...     "input": "它有哪些应用？",
        ...     "chat_history": chat_history
        ... })
    """
    # 对话式 RAG 的系统提示词
    if system_prompt is None:
        system_prompt = """你是一个智能问答助手，专门回答基于知识库的问题。

你的任务：
1. 理解用户的问题，考虑对话历史的上下文
2. 使用 knowledge_base 工具搜索相关信息
3. 基于检索到的文档内容和对话历史回答问题
4. 保持对话的连贯性和上下文感知

回答要求：
- 上下文感知：理解用户问题与之前对话的关系
- 准确：严格基于文档内容
- 自然：像人类一样进行对话
- 引用：适当引用来源文档
"""
    
    logger.info("💬 创建对话式 RAG Agent")
    
    return create_rag_agent(
        retriever=retriever,
        model=model,
        system_prompt=system_prompt,
        **kwargs,
    )


def query_rag_agent(
    agent,
    query: str,
    return_sources: bool = True,
) -> Dict[str, Any]:
    """
    查询 RAG Agent 的便捷函数
    
    Args:
        agent: RAG Agent 实例
        query: 查询问题
        return_sources: 是否返回来源文档
        
    Returns:
        包含回答的字典
        
    Example:
        >>> agent = create_rag_agent(retriever)
        >>> result = query_rag_agent(agent, "什么是机器学习？")
        >>> print(result["answer"])
    """
    logger.info(f"🔍 查询 RAG Agent: {query[:50]}...")
    
    try:
        # 执行查询 - LangChain 1.0.3 的 agent 需要字典输入
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        
        # 提取回答
        if isinstance(result, dict) and "messages" in result:
            # 获取最后一条消息
            messages = result["messages"]
            if messages:
                answer = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            else:
                answer = str(result)
        else:
            answer = str(result)
        
        # 格式化响应
        formatted = {"answer": answer}
        
        logger.info("✅ 查询完成")
        return formatted
        
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")
        raise


async def aquery_rag_agent(
    agent,
    query: str,
    return_sources: bool = True,
) -> Dict[str, Any]:
    """
    异步查询 RAG Agent
    
    Args:
        agent: RAG Agent 实例
        query: 查询问题
        return_sources: 是否返回来源文档
        
    Returns:
        包含回答的字典
        
    Example:
        >>> agent = create_rag_agent(retriever)
        >>> result = await aquery_rag_agent(agent, "什么是机器学习？")
    """
    logger.info(f"🔍 异步查询 RAG Agent: {query[:50]}...")
    
    try:
        # 异步执行查询 - LangChain 1.0.3 的 agent 需要字典输入
        result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        
        # 提取回答
        if isinstance(result, dict) and "messages" in result:
            # 获取最后一条消息
            messages = result["messages"]
            if messages:
                answer = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            else:
                answer = str(result)
        else:
            answer = str(result)
        
        # 格式化响应
        formatted = {"answer": answer}
        
        logger.info("✅ 异步查询完成")
        return formatted
        
    except Exception as e:
        logger.error(f"❌ 异步查询失败: {e}")
        raise

