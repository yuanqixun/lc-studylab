"""
安全节点包装器 - 为 LangGraph 节点添加 Guardrails

这个模块提供了包装器函数，可以为任何 LangGraph 节点添加安全检查。
"""

from typing import Callable, Optional, Any, Dict
from functools import wraps

from config.logging import get_logger
from core.guardrails import (
    InputValidator,
    OutputValidator,
    ContentFilter,
)
from .state import StudyFlowState

logger = get_logger(__name__)


def with_input_guardrails(
    node_func: Callable,
    validator: Optional[InputValidator] = None,
    input_field: str = "question",
    strict_mode: bool = False,
):
    """
    为节点添加输入 Guardrails
    
    Args:
        node_func: 原始节点函数
        validator: 输入验证器
        input_field: 要验证的状态字段名
        strict_mode: 严格模式
        
    Returns:
        包装后的节点函数
        
    Example:
        >>> @with_input_guardrails
        >>> def my_node(state: StudyFlowState) -> StudyFlowState:
        >>>     # 节点逻辑
        >>>     return state
    """
    if validator is None:
        validator = InputValidator(
            content_filter=ContentFilter(),
            strict_mode=strict_mode,
        )
    
    @wraps(node_func)
    def wrapped_node(state: StudyFlowState) -> StudyFlowState:
        """包装后的节点"""
        logger.info(f"[Guardrails] 对节点 '{node_func.__name__}' 执行输入验证")
        
        # 获取输入内容
        input_content = state.get(input_field, "")
        
        if input_content:
            # 验证输入
            result = validator.validate(str(input_content))
            
            if not result.is_valid:
                error_msg = f"输入验证失败: {', '.join(result.errors)}"
                logger.error(f"[Guardrails] ❌ {error_msg}")
                
                # 更新状态，记录错误
                state["error"] = error_msg
                state["validation_failed"] = True
                return state
            
            if result.warnings:
                logger.warning(f"[Guardrails] ⚠️ 输入警告: {result.warnings}")
                state["warnings"] = state.get("warnings", []) + result.warnings
            
            # 使用过滤后的输入
            state[input_field] = result.filtered_input
            logger.info(f"[Guardrails] ✅ 输入验证通过")
        
        # 执行原始节点
        return node_func(state)
    
    return wrapped_node


def with_output_guardrails(
    node_func: Callable,
    validator: Optional[OutputValidator] = None,
    output_field: str = "plan",
    require_sources: bool = False,
    strict_mode: bool = False,
):
    """
    为节点添加输出 Guardrails
    
    Args:
        node_func: 原始节点函数
        validator: 输出验证器
        output_field: 要验证的输出字段名
        require_sources: 是否要求来源
        strict_mode: 严格模式
        
    Returns:
        包装后的节点函数
        
    Example:
        >>> @with_output_guardrails(output_field="plan")
        >>> def planner_node(state: StudyFlowState) -> StudyFlowState:
        >>>     # 生成学习计划
        >>>     return state
    """
    if validator is None:
        validator = OutputValidator(
            content_filter=ContentFilter(),
            require_sources=require_sources,
            strict_mode=strict_mode,
        )
    
    @wraps(node_func)
    def wrapped_node(state: StudyFlowState) -> StudyFlowState:
        """包装后的节点"""
        # 先执行原始节点
        result_state = node_func(state)
        
        logger.info(f"[Guardrails] 对节点 '{node_func.__name__}' 执行输出验证")
        
        # 获取输出内容
        output_content = result_state.get(output_field, "")
        
        if output_content:
            # 获取来源（如果需要）
            sources = None
            if require_sources:
                sources = result_state.get("sources", []) or result_state.get("retrieved_docs", [])
                if sources and hasattr(sources[0], "metadata"):
                    # 如果是文档对象，提取来源
                    sources = [
                        doc.metadata.get("source", "unknown")
                        for doc in sources
                        if hasattr(doc, "metadata")
                    ]
            
            # 验证输出
            validation_result = validator.validate(
                str(output_content),
                sources=sources,
            )
            
            if not validation_result.is_valid:
                error_msg = f"输出验证失败: {', '.join(validation_result.errors)}"
                logger.error(f"[Guardrails] ❌ {error_msg}")
                
                # 更新状态，记录错误
                result_state["error"] = error_msg
                result_state["validation_failed"] = True
                return result_state
            
            if validation_result.warnings:
                logger.warning(f"[Guardrails] ⚠️ 输出警告: {validation_result.warnings}")
                result_state["warnings"] = result_state.get("warnings", []) + validation_result.warnings
            
            # 使用过滤后的输出
            result_state[output_field] = validation_result.filtered_output
            logger.info(f"[Guardrails] ✅ 输出验证通过")
        
        return result_state
    
    return wrapped_node


def with_guardrails(
    input_field: Optional[str] = None,
    output_field: Optional[str] = None,
    require_sources: bool = False,
    strict_mode: bool = False,
):
    """
    装饰器：同时添加输入和输出 Guardrails
    
    Args:
        input_field: 要验证的输入字段名
        output_field: 要验证的输出字段名
        require_sources: 是否要求来源
        strict_mode: 严格模式
        
    Returns:
        装饰器函数
        
    Example:
        >>> @with_guardrails(input_field="question", output_field="answer", require_sources=True)
        >>> def rag_node(state: StudyFlowState) -> StudyFlowState:
        >>>     # RAG 节点逻辑
        >>>     return state
    """
    def decorator(node_func: Callable) -> Callable:
        """装饰器"""
        wrapped = node_func
        
        # 先包装输出（内层）
        if output_field:
            wrapped = with_output_guardrails(
                wrapped,
                output_field=output_field,
                require_sources=require_sources,
                strict_mode=strict_mode,
            )
        
        # 再包装输入（外层）
        if input_field:
            wrapped = with_input_guardrails(
                wrapped,
                input_field=input_field,
                strict_mode=strict_mode,
            )
        
        return wrapped
    
    return decorator


def create_safe_node(
    node_func: Callable,
    validate_input: bool = True,
    validate_output: bool = True,
    input_field: str = "question",
    output_field: str = "result",
    require_sources: bool = False,
    strict_mode: bool = False,
) -> Callable:
    """
    创建安全节点（函数式 API）
    
    Args:
        node_func: 原始节点函数
        validate_input: 是否验证输入
        validate_output: 是否验证输出
        input_field: 输入字段名
        output_field: 输出字段名
        require_sources: 是否要求来源
        strict_mode: 严格模式
        
    Returns:
        包装后的安全节点
        
    Example:
        >>> from workflows.nodes import planner_node
        >>> safe_planner = create_safe_node(
        >>>     planner_node,
        >>>     input_field="question",
        >>>     output_field="plan",
        >>> )
    """
    wrapped = node_func
    
    if validate_output:
        wrapped = with_output_guardrails(
            wrapped,
            output_field=output_field,
            require_sources=require_sources,
            strict_mode=strict_mode,
        )
    
    if validate_input:
        wrapped = with_input_guardrails(
            wrapped,
            input_field=input_field,
            strict_mode=strict_mode,
        )
    
    return wrapped


# 便捷函数：为现有节点批量添加 Guardrails
def add_guardrails_to_nodes(
    nodes_dict: Dict[str, Callable],
    config: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Callable]:
    """
    为多个节点批量添加 Guardrails
    
    Args:
        nodes_dict: 节点字典 {节点名: 节点函数}
        config: 配置字典 {节点名: {参数}}
        
    Returns:
        包装后的节点字典
        
    Example:
        >>> from workflows.nodes import planner_node, retrieval_node
        >>> 
        >>> safe_nodes = add_guardrails_to_nodes(
        >>>     {
        >>>         "planner": planner_node,
        >>>         "retrieval": retrieval_node,
        >>>     },
        >>>     config={
        >>>         "planner": {"input_field": "question", "output_field": "plan"},
        >>>         "retrieval": {"output_field": "retrieved_docs", "require_sources": True},
        >>>     }
        >>> )
    """
    config = config or {}
    safe_nodes = {}
    
    for node_name, node_func in nodes_dict.items():
        node_config = config.get(node_name, {})
        
        safe_nodes[node_name] = create_safe_node(
            node_func,
            **node_config,
        )
        
        logger.info(f"[Guardrails] 为节点 '{node_name}' 添加了安全检查")
    
    return safe_nodes


# 人工审核节点（Human-in-the-Loop + Guardrails）
def create_human_review_node(
    review_field: str = "plan",
    approval_required: bool = True,
):
    """
    创建人工审核节点
    
    这个节点会暂停工作流，等待人工审核和批准。
    
    Args:
        review_field: 需要审核的字段
        approval_required: 是否必须批准才能继续
        
    Returns:
        人工审核节点函数
        
    Example:
        >>> human_review = create_human_review_node(
        >>>     review_field="plan",
        >>>     approval_required=True,
        >>> )
        >>> workflow.add_node("human_review", human_review)
    """
    def human_review_node(state: StudyFlowState) -> StudyFlowState:
        """人工审核节点"""
        logger.info(f"[Human Review] 等待人工审核字段: {review_field}")
        
        # 获取需要审核的内容
        content = state.get(review_field, "")
        
        logger.info(f"[Human Review] 审核内容: {content[:100]}...")
        
        # 标记为等待审核状态
        state["awaiting_review"] = True
        state["review_field"] = review_field
        state["approval_required"] = approval_required
        
        # 在实际应用中，这里会暂停并等待外部输入
        # LangGraph 的 interrupt 机制会在这里生效
        
        return state
    
    return human_review_node

