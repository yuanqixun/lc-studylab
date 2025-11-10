"""
DeepAgents 深度研究模块

Stage 4: 实现深度研究模式，支持复杂的多步骤研究任务。

核心组件：
- DeepAgent: 深度研究智能体
- SubAgents: 专门的子智能体（WebResearcher, DocAnalyst, ReportWriter）
- Planner: 研究规划器
- Middleware: 子智能体中间件

功能特性：
- 自动规划研究任务
- 多智能体协作
- 文件系统管理
- Human-in-the-loop 支持

参考：
- https://docs.langchain.com/oss/python/deepagents/quickstart
- https://docs.langchain.com/oss/python/deepagents/subagents
"""

from deep_research.deep_agent import (
    DeepResearchAgent,
    create_deep_research_agent,
)

from deep_research.subagents import (
    create_web_researcher,
    create_doc_analyst,
    create_report_writer,
)

__all__ = [
    "DeepResearchAgent",
    "create_deep_research_agent",
    "create_web_researcher",
    "create_doc_analyst",
    "create_report_writer",
]

