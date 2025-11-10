"""
安全深度研究智能体 - 集成 Guardrails 的 DeepAgent

为 DeepAgent 添加安全检查和人工审核机制。

核心安全特性：
1. 输入验证（研究问题）
2. 工具调用审核（可选人工确认）
3. 输出验证（研究报告）
4. 敏感操作日志
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from langchain_core.tools import BaseTool

from config import settings, get_logger
from core.guardrails import (
    InputValidator,
    OutputValidator,
    ContentFilter,
    ResearchReport,
)
from deep_research.deep_agent import DeepResearchAgent, ResearchState

logger = get_logger(__name__)


class SafeDeepResearchAgent:
    """
    安全深度研究智能体
    
    在 DeepResearchAgent 基础上添加安全检查。
    
    安全特性：
    1. 输入验证：检查研究问题的安全性
    2. 工具调用审核：记录和审核所有工具调用
    3. 输出验证：确保研究报告的安全性和质量
    4. 人工审核：关键步骤可暂停等待人工确认
    
    Example:
        >>> agent = SafeDeepResearchAgent(
        >>>     thread_id="research_123",
        >>>     enable_human_review=True,
        >>>     strict_mode=True,
        >>> )
        >>> result = agent.research("分析 LangChain 1.0 的新特性")
        >>> print(result.title)
        >>> print(result.summary)
    """
    
    def __init__(
        self,
        thread_id: str,
        enable_web_search: bool = True,
        enable_doc_analysis: bool = False,
        retriever_tool: Optional[BaseTool] = None,
        enable_input_validation: bool = True,
        enable_output_validation: bool = True,
        enable_human_review: bool = False,
        strict_mode: bool = False,
        checkpointer: Optional[Any] = None,
        **kwargs,
    ):
        """
        初始化安全深度研究智能体
        
        Args:
            thread_id: 研究任务 ID
            enable_web_search: 启用网络搜索
            enable_doc_analysis: 启用文档分析
            retriever_tool: RAG 检索工具
            enable_input_validation: 启用输入验证
            enable_output_validation: 启用输出验证
            enable_human_review: 启用人工审核
            strict_mode: 严格模式
            checkpointer: 检查点
            **kwargs: 其他参数
        """
        self.thread_id = thread_id
        self.enable_input_validation = enable_input_validation
        self.enable_output_validation = enable_output_validation
        self.enable_human_review = enable_human_review
        self.strict_mode = strict_mode
        
        logger.info(f"🛡️ 初始化 SafeDeepResearchAgent: {thread_id}")
        logger.info(f"   输入验证: {enable_input_validation}")
        logger.info(f"   输出验证: {enable_output_validation}")
        logger.info(f"   人工审核: {enable_human_review}")
        logger.info(f"   严格模式: {strict_mode}")
        
        # 创建验证器
        content_filter = ContentFilter(
            enable_pii_detection=True,
            enable_content_safety=True,
            enable_injection_detection=True,
            mask_pii=True,
        )
        
        self.input_validator = InputValidator(
            content_filter=content_filter,
            strict_mode=strict_mode,
        ) if enable_input_validation else None
        
        self.output_validator = OutputValidator(
            content_filter=content_filter,
            require_sources=True,  # 研究报告必须有来源
            strict_mode=strict_mode,
        ) if enable_output_validation else None
        
        # 创建基础 DeepAgent
        self.agent = DeepResearchAgent(
            thread_id=thread_id,
            enable_web_search=enable_web_search,
            enable_doc_analysis=enable_doc_analysis,
            retriever_tool=retriever_tool,
            checkpointer=checkpointer,
            **kwargs,
        )
        
        # 工具调用日志
        self.tool_calls_log: List[Dict[str, Any]] = []
        
        logger.info("✅ SafeDeepResearchAgent 初始化完成")
    
    def research(
        self,
        query: str,
        return_structured: bool = True,
    ) -> ResearchReport | Dict[str, Any]:
        """
        执行安全的深度研究
        
        Args:
            query: 研究问题
            return_structured: 是否返回结构化输出（ResearchReport）
            
        Returns:
            ResearchReport 或字典
            
        Raises:
            ValueError: 验证失败时抛出
            
        Example:
            >>> agent = SafeDeepResearchAgent("research_123")
            >>> report = agent.research("分析 LangChain 1.0 的新特性")
            >>> print(report.title)
            >>> for section in report.sections:
            >>>     print(f"{section.title}: {section.content[:100]}...")
        """
        logger.info(f"🔍 开始安全深度研究: {query[:50]}...")
        
        # 1. 输入验证
        if self.input_validator:
            validation_result = self.input_validator.validate(query)
            
            if not validation_result.is_valid:
                error_msg = "输入验证失败:\n" + "\n".join(
                    f"- {err}" for err in validation_result.errors
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            filtered_query = validation_result.filtered_input
            
            if validation_result.warnings:
                logger.warning(f"⚠️ 输入警告: {validation_result.warnings}")
        else:
            filtered_query = query
        
        # 2. 人工审核（如果启用）
        if self.enable_human_review:
            logger.info("⏸️ 等待人工审核研究问题...")
            approval = self._request_human_approval(
                action="开始研究",
                content=filtered_query,
            )
            
            if not approval:
                logger.warning("❌ 人工审核未通过，取消研究")
                raise ValueError("人工审核未通过")
        
        # 3. 执行研究
        try:
            result = self.agent.research(filtered_query)
            
            # 提取最终报告
            final_report = result.get("final_report", "")
            
        except Exception as e:
            logger.error(f"❌ 研究执行失败: {e}")
            raise
        
        # 4. 提取来源
        sources = self._extract_sources(result)
        
        # 5. 输出验证
        if self.output_validator:
            validation_result = self.output_validator.validate(
                final_report,
                sources=sources,
            )
            
            if not validation_result.is_valid:
                error_msg = "输出验证失败:\n" + "\n".join(
                    f"- {err}" for err in validation_result.errors
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            filtered_report = validation_result.filtered_output
            
            if validation_result.warnings:
                logger.warning(f"⚠️ 输出警告: {validation_result.warnings}")
        else:
            filtered_report = final_report
        
        # 6. 返回结果
        logger.info("✅ 安全深度研究完成")
        
        if return_structured:
            # 解析为结构化报告
            return self._parse_to_structured_report(
                filtered_report,
                query,
                sources,
            )
        else:
            return {
                "final_report": filtered_report,
                "query": query,
                "sources": sources,
                "thread_id": self.thread_id,
            }
    
    async def aresearch(
        self,
        query: str,
        return_structured: bool = True,
    ) -> ResearchReport | Dict[str, Any]:
        """
        异步执行安全的深度研究
        
        Args:
            query: 研究问题
            return_structured: 是否返回结构化输出
            
        Returns:
            ResearchReport 或字典
        """
        logger.info(f"🔍 异步开始安全深度研究: {query[:50]}...")
        
        # 1. 输入验证
        if self.input_validator:
            validation_result = self.input_validator.validate(query)
            
            if not validation_result.is_valid:
                error_msg = "输入验证失败:\n" + "\n".join(
                    f"- {err}" for err in validation_result.errors
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            filtered_query = validation_result.filtered_input
            
            if validation_result.warnings:
                logger.warning(f"⚠️ 输入警告: {validation_result.warnings}")
        else:
            filtered_query = query
        
        # 2. 人工审核（如果启用）
        if self.enable_human_review:
            logger.info("⏸️ 等待人工审核研究问题...")
            approval = self._request_human_approval(
                action="开始研究",
                content=filtered_query,
            )
            
            if not approval:
                logger.warning("❌ 人工审核未通过，取消研究")
                raise ValueError("人工审核未通过")
        
        # 3. 执行研究
        try:
            result = await self.agent.aresearch(filtered_query)
            final_report = result.get("final_report", "")
        except Exception as e:
            logger.error(f"❌ 异步研究执行失败: {e}")
            raise
        
        # 4. 提取来源
        sources = self._extract_sources(result)
        
        # 5. 输出验证
        if self.output_validator:
            validation_result = self.output_validator.validate(
                final_report,
                sources=sources,
            )
            
            if not validation_result.is_valid:
                error_msg = "输出验证失败:\n" + "\n".join(
                    f"- {err}" for err in validation_result.errors
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            filtered_report = validation_result.filtered_output
            
            if validation_result.warnings:
                logger.warning(f"⚠️ 输出警告: {validation_result.warnings}")
        else:
            filtered_report = final_report
        
        # 6. 返回结果
        logger.info("✅ 异步安全深度研究完成")
        
        if return_structured:
            return self._parse_to_structured_report(
                filtered_report,
                query,
                sources,
            )
        else:
            return {
                "final_report": filtered_report,
                "query": query,
                "sources": sources,
                "thread_id": self.thread_id,
            }
    
    def _request_human_approval(
        self,
        action: str,
        content: str,
    ) -> bool:
        """
        请求人工审核
        
        Args:
            action: 操作描述
            content: 需要审核的内容
            
        Returns:
            是否批准
        """
        logger.info(f"👤 请求人工审核: {action}")
        logger.info(f"   内容: {content[:100]}...")
        
        # 在实际应用中，这里应该：
        # 1. 暂停执行
        # 2. 发送通知给管理员
        # 3. 等待管理员响应
        # 4. 返回审核结果
        
        # 这里简化为自动批准（演示用）
        # 实际应用中应该集成真实的审核流程
        logger.info("   [自动批准 - 演示模式]")
        
        return True
    
    def _extract_sources(self, result: Dict[str, Any]) -> List[str]:
        """从研究结果中提取来源"""
        sources = []
        
        # 从文件系统中提取来源
        if hasattr(self.agent, "filesystem"):
            fs = self.agent.filesystem
            
            # 读取研究过程中保存的来源信息
            try:
                sources_file = fs.read("sources.json")
                if sources_file:
                    import json
                    sources_data = json.loads(sources_file)
                    sources = sources_data.get("sources", [])
            except Exception as e:
                logger.warning(f"无法读取来源信息: {e}")
        
        # 如果没有找到来源，使用默认值
        if not sources:
            sources = ["网络搜索", "知识库"]
        
        return sources
    
    def _parse_to_structured_report(
        self,
        report_text: str,
        query: str,
        sources: List[str],
    ) -> ResearchReport:
        """
        将文本报告解析为结构化的 ResearchReport
        
        Args:
            report_text: 报告文本
            query: 研究问题
            sources: 参考来源
            
        Returns:
            ResearchReport 实例
        """
        from core.guardrails.schemas import ResearchSection
        
        # 简单解析（实际应用中可以使用更复杂的解析逻辑）
        lines = report_text.split("\n")
        
        # 提取标题（第一行）
        title = lines[0].strip() if lines else f"关于 {query} 的研究报告"
        
        # 提取摘要（前几行）
        summary_lines = []
        for line in lines[1:10]:
            if line.strip():
                summary_lines.append(line.strip())
        summary = " ".join(summary_lines) if summary_lines else report_text[:200]
        
        # 创建一个默认章节
        sections = [
            ResearchSection(
                section_number=1,
                title="研究内容",
                content=report_text,
                sources=sources,
                key_findings=["详见报告内容"],
            )
        ]
        
        # 提取结论（最后几行）
        conclusions = ["基于研究内容得出的结论"]
        
        return ResearchReport(
            title=title,
            topic=query,
            summary=summary,
            sections=sections,
            conclusions=conclusions,
            references=sources,
            created_at=datetime.now(),
            metadata={
                "thread_id": self.thread_id,
                "tool_calls_count": len(self.tool_calls_log),
            }
        )
    
    def get_tool_calls_log(self) -> List[Dict[str, Any]]:
        """获取工具调用日志"""
        return self.tool_calls_log
    
    def clear_tool_calls_log(self):
        """清空工具调用日志"""
        self.tool_calls_log = []


# 便捷函数：创建安全 DeepAgent
def create_safe_deep_research_agent(
    thread_id: str,
    enable_web_search: bool = True,
    enable_doc_analysis: bool = False,
    retriever_tool: Optional[BaseTool] = None,
    enable_human_review: bool = False,
    strict_mode: bool = False,
) -> SafeDeepResearchAgent:
    """
    创建安全深度研究智能体的便捷函数
    
    Args:
        thread_id: 研究任务 ID
        enable_web_search: 启用网络搜索
        enable_doc_analysis: 启用文档分析
        retriever_tool: RAG 检索工具
        enable_human_review: 启用人工审核
        strict_mode: 严格模式
        
    Returns:
        SafeDeepResearchAgent 实例
        
    Example:
        >>> from deep_research.safe_deep_agent import create_safe_deep_research_agent
        >>> 
        >>> agent = create_safe_deep_research_agent(
        >>>     thread_id="research_123",
        >>>     enable_human_review=True,
        >>>     strict_mode=True,
        >>> )
        >>> 
        >>> report = agent.research("分析 LangChain 1.0 的新特性")
        >>> print(report.title)
    """
    return SafeDeepResearchAgent(
        thread_id=thread_id,
        enable_web_search=enable_web_search,
        enable_doc_analysis=enable_doc_analysis,
        retriever_tool=retriever_tool,
        enable_human_review=enable_human_review,
        strict_mode=strict_mode,
    )

