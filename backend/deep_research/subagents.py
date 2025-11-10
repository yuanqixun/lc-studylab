"""
SubAgents 子智能体模块

定义专门的子智能体，每个负责特定的研究任务：
1. WebResearcher: 网络搜索和信息整理
2. DocAnalyst: 文档分析和知识提取
3. ReportWriter: 报告撰写和内容组织

这些子智能体由 DeepAgent 协调，共同完成复杂的研究任务。

技术要点：
- 基于 LangChain 1.0.3 的 create_agent API
- 每个子智能体有专门的系统提示词
- 配备特定的工具集
- 支持流式输出

参考：
- https://docs.langchain.com/oss/python/deepagents/subagents
- https://docs.langchain.com/oss/python/langchain/agents
"""

from typing import Optional, List, Sequence
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel

from config import settings, get_logger
from core.models import get_model_string
from core.tools.web_search import create_tavily_search_tool
from core.tools.filesystem import FILESYSTEM_TOOLS

logger = get_logger(__name__)


# ==================== 系统提示词 ====================

WEB_RESEARCHER_PROMPT = """你是一个专业的网络研究员，擅长从互联网搜索和整理信息。

你的任务：
1. 使用搜索工具查找相关信息
2. 评估搜索结果的可信度和相关性
3. 提取关键信息和数据
4. 整理成结构化的研究笔记
5. 使用文件系统工具保存研究结果

工作流程：
1. 分析研究问题，确定搜索关键词
2. 执行多次搜索，覆盖不同角度
3. 筛选高质量的信息源
4. 提取和整理关键信息
5. 将结果保存到文件系统（使用 write_research_file）

注意事项：
- 优先选择权威来源（官方文档、学术论文、知名媒体）
- 记录所有来源链接和发布时间
- 识别信息的时效性和可靠性
- 对比多个来源，确保信息准确性
- 将研究笔记保存为 Markdown 格式

输出格式：
# 研究笔记：[主题]

## 搜索策略
- 关键词：...
- 搜索次数：...

## 主要发现
1. [发现1]
   - 来源：[URL]
   - 时间：[日期]
   - 可信度：⭐⭐⭐⭐⭐

2. [发现2]
   ...

## 关键数据
- ...

## 参考来源
1. [标题] - [URL]
2. ...
"""


DOC_ANALYST_PROMPT = """你是一个专业的文档分析师，擅长从知识库中提取相关信息。

你的任务：
1. 使用知识库检索工具查找相关文档
2. 分析文档内容的相关性和重要性
3. 提炼关键段落和数据
4. 整理成结构化的分析报告
5. 使用文件系统工具保存分析结果

工作流程：
1. 分析研究问题，确定检索查询
2. 执行多次检索，覆盖不同方面
3. 评估检索到的文档相关性
4. 提取关键段落和信息
5. 将分析结果保存到文件系统（使用 write_research_file）

注意事项：
- 确保信息准确性，直接引用原文
- 记录文档来源和位置
- 识别文档之间的关联和矛盾
- 提炼核心观点和数据
- 将分析报告保存为 Markdown 格式

输出格式：
# 文档分析：[主题]

## 检索策略
- 查询：...
- 检索次数：...
- 文档数量：...

## 关键文档
1. [文档名称]
   - 来源：[路径]
   - 相关性：⭐⭐⭐⭐⭐
   - 关键内容：
     > [引用原文]

2. [文档名称]
   ...

## 核心观点
1. ...
2. ...

## 数据摘要
- ...

## 参考文档
1. [文档名] - [路径]
2. ...
"""


REPORT_WRITER_PROMPT = """你是一个专业的研究报告撰写者，擅长组织和呈现研究发现。

你的任务：
1. 阅读所有研究材料（使用 read_research_file 和 list_research_files）
2. 整合网络搜索和文档分析的结果
3. 组织逻辑清晰的报告结构
4. 撰写详细的研究报告
5. 使用文件系统工具保存最终报告

工作流程：
1. 列出并阅读所有研究笔记和分析报告
2. 识别关键发现和主要观点
3. 组织报告结构（大纲）
4. 撰写各个章节
5. 添加引用和来源
6. 将最终报告保存到 reports 目录

注意事项：
- 确保逻辑清晰，结构合理
- 整合多个来源的信息
- 解决矛盾的信息
- 提供深入的分析和洞察
- 添加完整的引用和来源
- 使用专业的学术写作风格

报告结构：
# [研究主题]

## 执行摘要
[简明扼要的总结，200-300字]

## 1. 研究背景
### 1.1 研究问题
### 1.2 研究方法
### 1.3 信息来源

## 2. 主要发现
### 2.1 [发现1]
### 2.2 [发现2]
### 2.3 [发现3]

## 3. 详细分析
### 3.1 [分析1]
### 3.2 [分析2]

## 4. 数据和证据
[图表、数据、引用]

## 5. 结论和建议
### 5.1 主要结论
### 5.2 实践建议
### 5.3 未来方向

## 6. 参考来源
### 6.1 网络来源
1. ...

### 6.2 文档来源
1. ...

---
*报告生成时间：[时间]*
*研究任务 ID：[thread_id]*
"""


# ==================== SubAgent 创建函数 ====================

def create_web_researcher(
    model: Optional[str] = None,
    tools: Optional[Sequence[BaseTool]] = None,
    **kwargs,
):
    """
    创建网络研究员子智能体
    
    专门负责网络搜索和信息整理。
    
    Args:
        model: 模型字符串（如 "openai:gpt-4o"）
        tools: 工具列表，默认包含搜索和文件系统工具
        **kwargs: 其他传递给 create_agent 的参数
        
    Returns:
        WebResearcher Agent
        
    Example:
        >>> researcher = create_web_researcher()
        >>> result = researcher.invoke({
        ...     "messages": [{"role": "user", "content": "搜索 LangChain 1.0 的新特性"}]
        ... })
    """
    logger.info("🔍 创建 WebResearcher 子智能体")
    
    # 使用默认模型
    if model is None:
        model = get_model_string()
    
    # 配置工具：搜索 + 文件系统
    if tools is None:
        agent_tools = []
        
        # 添加搜索工具
        try:
            if settings.tavily_api_key:
                search_tool = create_tavily_search_tool()
                agent_tools.append(search_tool)
                logger.debug("   添加 Tavily 搜索工具")
        except Exception as e:
            logger.warning(f"⚠️ 无法添加搜索工具: {e}")
        
        # 添加文件系统工具
        agent_tools.extend(FILESYSTEM_TOOLS)
        logger.debug(f"   添加文件系统工具: {len(FILESYSTEM_TOOLS)} 个")
        
        tools = agent_tools
    
    # 创建 Agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=WEB_RESEARCHER_PROMPT,
        **kwargs,
    )
    
    logger.info("✅ WebResearcher 创建成功")
    return agent


def create_doc_analyst(
    model: Optional[str] = None,
    tools: Optional[Sequence[BaseTool]] = None,
    retriever_tool: Optional[BaseTool] = None,
    **kwargs,
):
    """
    创建文档分析师子智能体
    
    专门负责文档分析和知识提取。
    
    Args:
        model: 模型字符串
        tools: 工具列表，默认包含 RAG 检索和文件系统工具
        retriever_tool: RAG 检索工具（可选）
        **kwargs: 其他参数
        
    Returns:
        DocAnalyst Agent
        
    Example:
        >>> from rag import create_retriever_tool, get_embeddings, load_vector_store
        >>> 
        >>> # 创建检索工具
        >>> embeddings = get_embeddings()
        >>> vector_store = load_vector_store("data/indexes/test_index", embeddings)
        >>> retriever = vector_store.as_retriever()
        >>> retriever_tool = create_retriever_tool(retriever)
        >>> 
        >>> # 创建文档分析师
        >>> analyst = create_doc_analyst(retriever_tool=retriever_tool)
    """
    logger.info("📚 创建 DocAnalyst 子智能体")
    
    # 使用默认模型
    if model is None:
        model = get_model_string()
    
    # 配置工具：RAG 检索 + 文件系统
    if tools is None:
        agent_tools = []
        
        # 添加 RAG 检索工具
        if retriever_tool is not None:
            agent_tools.append(retriever_tool)
            logger.debug("   添加 RAG 检索工具")
        else:
            logger.warning("⚠️ 未提供 retriever_tool，DocAnalyst 将无法检索文档")
        
        # 添加文件系统工具
        agent_tools.extend(FILESYSTEM_TOOLS)
        logger.debug(f"   添加文件系统工具: {len(FILESYSTEM_TOOLS)} 个")
        
        tools = agent_tools
    
    # 创建 Agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=DOC_ANALYST_PROMPT,
        **kwargs,
    )
    
    logger.info("✅ DocAnalyst 创建成功")
    return agent


def create_report_writer(
    model: Optional[str] = None,
    tools: Optional[Sequence[BaseTool]] = None,
    **kwargs,
):
    """
    创建报告撰写者子智能体
    
    专门负责报告撰写和内容组织。
    
    Args:
        model: 模型字符串
        tools: 工具列表，默认只包含文件系统工具
        **kwargs: 其他参数
        
    Returns:
        ReportWriter Agent
        
    Example:
        >>> writer = create_report_writer()
        >>> result = writer.invoke({
        ...     "messages": [{
        ...         "role": "user",
        ...         "content": "根据研究笔记撰写最终报告，thread_id: research_123"
        ...     }]
        ... })
    """
    logger.info("✍️ 创建 ReportWriter 子智能体")
    
    # 使用默认模型（可以使用更强大的模型）
    if model is None:
        # ReportWriter 使用主模型，确保报告质量
        model = f"openai:{settings.openai_model}"
    
    # 配置工具：只需要文件系统工具
    if tools is None:
        tools = FILESYSTEM_TOOLS
        logger.debug(f"   添加文件系统工具: {len(FILESYSTEM_TOOLS)} 个")
    
    # 创建 Agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=REPORT_WRITER_PROMPT,
        **kwargs,
    )
    
    logger.info("✅ ReportWriter 创建成功")
    return agent


# ==================== SubAgent 辅助函数 ====================

def get_subagent_info() -> dict:
    """
    获取所有子智能体的信息
    
    Returns:
        包含子智能体信息的字典
    """
    return {
        "web_researcher": {
            "name": "WebResearcher",
            "description": "网络搜索和信息整理专家",
            "capabilities": [
                "网络搜索",
                "信息筛选",
                "来源评估",
                "笔记整理"
            ],
            "tools": ["tavily_search", "write_research_file", "read_research_file"]
        },
        "doc_analyst": {
            "name": "DocAnalyst",
            "description": "文档分析和知识提取专家",
            "capabilities": [
                "文档检索",
                "内容分析",
                "信息提炼",
                "关联识别"
            ],
            "tools": ["knowledge_base", "write_research_file", "read_research_file"]
        },
        "report_writer": {
            "name": "ReportWriter",
            "description": "研究报告撰写专家",
            "capabilities": [
                "内容组织",
                "报告撰写",
                "引用管理",
                "质量把控"
            ],
            "tools": ["write_research_file", "read_research_file", "list_research_files"]
        }
    }


logger.info("✅ SubAgents 模块已加载")

