"""
网络搜索工具
使用 Tavily API 提供网络搜索功能，获取最新信息

Tavily 是一个专为 AI Agent 设计的搜索 API，提供高质量的搜索结果

注意：在 LangChain V1.0.0 中，推荐使用 langchain-tavily 包
参考：https://python.langchain.com/docs/integrations/tools/tavily_search/
"""

from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from config import settings, get_logger

logger = get_logger(__name__)


# 尝试导入新的 Tavily 包，如果失败则使用旧的
try:
    from langchain_tavily import TavilySearchResults as TavilySearch
    USING_NEW_TAVILY = True
    logger.info("✅ 使用新的 langchain-tavily 包")
except ImportError:
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults as TavilySearch
        USING_NEW_TAVILY = False
        logger.warning("⚠️ 使用旧的 langchain-community Tavily（已弃用），建议安装: pip install langchain-tavily")
    except ImportError:
        TavilySearch = None
        USING_NEW_TAVILY = False
        logger.error("❌ 未安装 Tavily 搜索工具，请安装: pip install langchain-tavily")


def create_tavily_search_tool(
    max_results: Optional[int] = None,
    search_depth: str = "advanced",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
):
    """
    创建 Tavily 搜索工具实例
    
    在 LangChain V1.0.0 中，推荐使用 langchain-tavily 包。
    
    Args:
        max_results: 返回的最大结果数，默认使用配置值
        search_depth: 搜索深度，"basic" 或 "advanced"
        include_domains: 限制搜索的域名列表
        exclude_domains: 排除的域名列表
        
    Returns:
        配置好的 Tavily 搜索工具实例
        
    Raises:
        ValueError: 如果 Tavily API Key 未设置或未安装 Tavily 包
        
    Example:
        >>> tool = create_tavily_search_tool(max_results=3)
        >>> results = tool.invoke("LangChain 1.0.3 新特性")
    
    参考：
        https://python.langchain.com/docs/integrations/tools/tavily_search/
    """
    if TavilySearch is None:
        raise ValueError(
            "Tavily 搜索工具未安装！请安装: pip install langchain-tavily"
        )
    
    if not settings.tavily_api_key:
        raise ValueError(
            "Tavily API Key 未设置！请在环境变量或 .env 文件中设置 TAVILY_API_KEY"
        )
    
    max_results = max_results or settings.tavily_max_results
    
    logger.info(
        f"🔍 创建 Tavily 搜索工具 (max_results={max_results}, depth={search_depth})"
    )
    
    # 根据使用的包版本构建参数
    tool_kwargs = {
        "max_results": max_results,
        "api_key": settings.tavily_api_key,
    }
    
    # 新版本的 langchain-tavily 参数不同
    if USING_NEW_TAVILY:
        # 新版本使用不同的参数名
        tool_kwargs["search_depth"] = search_depth
        # 新版本的 include_domains 和 exclude_domains 处理方式不同
        # 只在非 None 时添加
        if include_domains is not None:
            tool_kwargs["include_domains"] = include_domains
        if exclude_domains is not None:
            tool_kwargs["exclude_domains"] = exclude_domains
    else:
        # 旧版本参数
        tool_kwargs["search_depth"] = search_depth
        # 旧版本需要传递空列表而不是 None
        tool_kwargs["include_domains"] = include_domains if include_domains is not None else []
        tool_kwargs["exclude_domains"] = exclude_domains if exclude_domains is not None else []
    
    try:
        tool = TavilySearch(**tool_kwargs)
        return tool
    except Exception as e:
        logger.error(f"❌ 创建 Tavily 工具失败: {e}")
        raise


@tool
def web_search(query: str) -> str:
    """
    在互联网上搜索信息
    
    使用 Tavily 搜索引擎查找最新、最相关的信息。
    适用于需要实时数据、最新新闻、技术文档等场景。
    
    Args:
        query: 搜索查询字符串，用自然语言描述你想找的信息
        
    Returns:
        搜索结果的摘要，包含标题、内容片段和来源链接
        
    Example:
        >>> web_search("Python 3.12 新特性")
        '找到 5 条搜索结果：
        
        1. Python 3.12 发布说明
           内容: Python 3.12 带来了多项性能改进...
           来源: https://docs.python.org/3.12/whatsnew/
        
        2. ...'
    """
    logger.info(f"🔍 执行网络搜索: {query}")
    
    try:
        # 检查 API Key
        if not settings.tavily_api_key:
            logger.warning("⚠️ Tavily API Key 未设置，无法执行搜索")
            return (
                "抱歉，网络搜索功能暂时不可用（未配置 Tavily API Key）。"
                "请在 .env 文件中设置 TAVILY_API_KEY。"
            )
        
        # 创建搜索工具
        search_tool = create_tavily_search_tool()
        
        # 执行搜索
        results = search_tool.invoke({"query": query})
        
        # 格式化结果
        if not results:
            logger.info("📭 未找到搜索结果")
            return f"未找到关于 '{query}' 的相关信息。"
        
        # 构建格式化的搜索结果
        formatted_results = [f"找到 {len(results)} 条搜索结果：\n"]
        
        for i, result in enumerate(results, 1):
            # Tavily 返回的结果格式
            title = result.get("title", "无标题")
            content = result.get("content", "")
            url = result.get("url", "")
            
            # 截断过长的内容
            if len(content) > 200:
                content = content[:200] + "..."
            
            formatted_results.append(f"\n{i}. {title}")
            if content:
                formatted_results.append(f"   内容: {content}")
            if url:
                formatted_results.append(f"   来源: {url}")
        
        result_text = "\n".join(formatted_results)
        logger.info(f"✅ 搜索完成，找到 {len(results)} 条结果")
        
        return result_text
        
    except Exception as e:
        error_msg = f"搜索时发生错误: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return f"抱歉，{error_msg}"


@tool
def web_search_simple(query: str) -> str:
    """
    简单的网络搜索（快速模式）
    
    使用基础搜索深度，返回更快但可能不够深入的结果。
    适合快速查询和简单问题。
    
    Args:
        query: 搜索查询字符串
        
    Returns:
        搜索结果摘要
    """
    logger.info(f"🔍 执行快速搜索: {query}")
    
    try:
        if not settings.tavily_api_key:
            return "网络搜索功能暂时不可用（未配置 API Key）"
        
        # 使用基础搜索深度，返回更少结果
        search_tool = create_tavily_search_tool(
            max_results=3,
            search_depth="basic"
        )
        
        results = search_tool.invoke({"query": query})
        
        if not results:
            return f"未找到关于 '{query}' 的相关信息。"
        
        # 简化的结果格式
        formatted_results = [f"快速搜索结果（{len(results)} 条）：\n"]
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            formatted_results.append(f"{i}. {title} - {url}")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"❌ 快速搜索失败: {e}")
        return f"搜索失败: {str(e)}"

