"""
安全学习工作流 - 集成 Guardrails 的学习工作流

这是增强版的学习工作流，在关键节点添加了安全检查。
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import StudyFlowState
from .nodes import (
    planner_node,
    retrieval_node,
    quiz_generator_node,
    grading_node,
    feedback_node
)
from .safe_nodes import (
    with_guardrails,
    create_safe_node,
    create_human_review_node,
)
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


def should_continue(state: StudyFlowState) -> Literal["retry", "end"]:
    """条件路由函数"""
    should_retry = state.get("should_retry", False)
    retry_count = state.get("retry_count", 0)
    
    # 检查是否有验证错误
    if state.get("validation_failed", False):
        logger.error("[Safe Flow] 检测到验证失败，终止流程")
        return "end"
    
    if should_retry and retry_count < 3:
        return "retry"
    else:
        return "end"


def create_safe_study_flow_graph(
    checkpointer_path: str = None,
    enable_human_review: bool = True,
    strict_mode: bool = False,
) -> StateGraph:
    """
    创建安全的学习工作流图
    
    相比普通工作流，增加了：
    1. 输入验证（用户问题）
    2. 输出验证（学习计划、测验题等）
    3. 人工审核节点（可选）
    4. 安全日志记录
    
    Args:
        checkpointer_path: 检查点路径
        enable_human_review: 是否启用人工审核
        strict_mode: 严格模式（任何警告都视为错误）
        
    Returns:
        编译后的安全工作流图
        
    Example:
        >>> from workflows.safe_study_flow import create_safe_study_flow_graph
        >>> 
        >>> # 创建安全工作流
        >>> graph = create_safe_study_flow_graph(
        >>>     enable_human_review=True,
        >>>     strict_mode=True,
        >>> )
        >>> 
        >>> # 运行工作流
        >>> config = {"configurable": {"thread_id": "user_123"}}
        >>> result = graph.invoke({
        >>>     "question": "如何学习 LangChain？",
        >>>     "messages": []
        >>> }, config)
    """
    logger.info("[Safe Study Flow] 开始创建安全学习工作流图")
    logger.info(f"   人工审核: {enable_human_review}")
    logger.info(f"   严格模式: {strict_mode}")
    
    # 创建状态图
    workflow = StateGraph(StudyFlowState)
    
    # ==================== 创建安全节点 ====================
    
    # 1. 规划节点（验证输入和输出）
    safe_planner = create_safe_node(
        planner_node,
        validate_input=True,
        validate_output=True,
        input_field="question",
        output_field="plan",
        strict_mode=strict_mode,
    )
    
    # 2. 检索节点（验证输出，要求来源）
    safe_retrieval = create_safe_node(
        retrieval_node,
        validate_input=False,
        validate_output=True,
        output_field="retrieved_docs",
        require_sources=False,  # 检索节点本身就是获取来源
        strict_mode=strict_mode,
    )
    
    # 3. 测验生成节点（验证输出）
    safe_quiz_generator = create_safe_node(
        quiz_generator_node,
        validate_input=False,
        validate_output=True,
        output_field="quiz",
        strict_mode=strict_mode,
    )
    
    # 4. 评分节点（验证输入和输出）
    safe_grading = create_safe_node(
        grading_node,
        validate_input=True,
        validate_output=True,
        input_field="answers",
        output_field="score",
        strict_mode=strict_mode,
    )
    
    # 5. 反馈节点（验证输出）
    safe_feedback = create_safe_node(
        feedback_node,
        validate_input=False,
        validate_output=True,
        output_field="feedback",
        strict_mode=strict_mode,
    )
    
    # ==================== 添加节点到工作流 ====================
    
    logger.info("[Safe Study Flow] 添加安全节点...")
    
    workflow.add_node("planner", safe_planner)
    workflow.add_node("retrieval", safe_retrieval)
    workflow.add_node("quiz_generator", safe_quiz_generator)
    workflow.add_node("grading", safe_grading)
    workflow.add_node("feedback", safe_feedback)
    
    # 添加人工审核节点（可选）
    if enable_human_review:
        human_review = create_human_review_node(
            review_field="plan",
            approval_required=True,
        )
        workflow.add_node("human_review", human_review)
        logger.info("[Safe Study Flow] 已添加人工审核节点")
    
    # ==================== 定义边 ====================
    
    logger.info("[Safe Study Flow] 定义工作流边...")
    
    # 设置入口点
    workflow.set_entry_point("planner")
    
    # 定义流程
    if enable_human_review:
        # 带人工审核的流程
        workflow.add_edge("planner", "human_review")
        workflow.add_edge("human_review", "retrieval")
    else:
        # 不带人工审核的流程
        workflow.add_edge("planner", "retrieval")
    
    workflow.add_edge("retrieval", "quiz_generator")
    workflow.add_edge("quiz_generator", "grading")
    workflow.add_edge("grading", "feedback")
    
    # 条件边：决定是否重试
    workflow.add_conditional_edges(
        "feedback",
        should_continue,
        {
            "retry": "quiz_generator",
            "end": END,
        }
    )
    
    # ==================== 编译工作流 ====================
    
    logger.info("[Safe Study Flow] 编译工作流...")
    
    # 设置检查点
    if checkpointer_path:
        from langgraph.checkpoint.sqlite import SqliteSaver
        checkpointer = SqliteSaver.from_conn_string(checkpointer_path)
        logger.info(f"[Safe Study Flow] 使用 SQLite 检查点: {checkpointer_path}")
    else:
        checkpointer = MemorySaver()
        logger.info("[Safe Study Flow] 使用内存检查点")
    
    # 编译
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    logger.info("[Safe Study Flow] ✅ 安全学习工作流图创建完成")
    
    return compiled_graph


# 便捷函数：创建默认的安全工作流
def create_default_safe_flow():
    """创建默认配置的安全工作流"""
    import os
    
    # 使用默认检查点路径
    checkpoint_dir = os.path.join(settings.DATA_DIR, "checkpoints", "safe_study_flow")
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, "safe_study_flow.db")
    
    return create_safe_study_flow_graph(
        checkpointer_path=checkpoint_path,
        enable_human_review=True,
        strict_mode=False,
    )


# 便捷函数：运行安全工作流
def run_safe_study_flow(
    question: str,
    thread_id: str = "default",
    enable_human_review: bool = True,
    strict_mode: bool = False,
):
    """
    运行安全学习工作流的便捷函数
    
    Args:
        question: 学习问题
        thread_id: 线程 ID（用于检查点）
        enable_human_review: 是否启用人工审核
        strict_mode: 严格模式
        
    Returns:
        工作流执行结果
        
    Example:
        >>> result = run_safe_study_flow(
        >>>     question="如何学习 LangChain？",
        >>>     thread_id="user_123",
        >>>     enable_human_review=True,
        >>> )
        >>> print(result["plan"])
    """
    logger.info(f"[Safe Study Flow] 运行安全工作流: {question}")
    
    # 创建工作流
    graph = create_safe_study_flow_graph(
        enable_human_review=enable_human_review,
        strict_mode=strict_mode,
    )
    
    # 配置
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    # 初始状态
    initial_state = {
        "question": question,
        "messages": [],
        "plan": "",
        "retrieved_docs": [],
        "quiz": "",
        "answers": "",
        "score": 0,
        "feedback": "",
        "should_retry": False,
        "retry_count": 0,
        "validation_failed": False,
        "warnings": [],
    }
    
    # 执行
    try:
        result = graph.invoke(initial_state, config)
        logger.info("[Safe Study Flow] ✅ 工作流执行完成")
        return result
    except Exception as e:
        logger.error(f"[Safe Study Flow] ❌ 工作流执行失败: {e}")
        raise


# 流式执行安全工作流
async def stream_safe_study_flow(
    question: str,
    thread_id: str = "default",
    enable_human_review: bool = True,
    strict_mode: bool = False,
):
    """
    流式执行安全学习工作流
    
    Args:
        question: 学习问题
        thread_id: 线程 ID
        enable_human_review: 是否启用人工审核
        strict_mode: 严格模式
        
    Yields:
        工作流的每个步骤结果
        
    Example:
        >>> async for chunk in stream_safe_study_flow("如何学习 LangChain？"):
        >>>     print(chunk)
    """
    logger.info(f"[Safe Study Flow] 流式运行安全工作流: {question}")
    
    # 创建工作流
    graph = create_safe_study_flow_graph(
        enable_human_review=enable_human_review,
        strict_mode=strict_mode,
    )
    
    # 配置
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    # 初始状态
    initial_state = {
        "question": question,
        "messages": [],
        "plan": "",
        "retrieved_docs": [],
        "quiz": "",
        "answers": "",
        "score": 0,
        "feedback": "",
        "should_retry": False,
        "retry_count": 0,
        "validation_failed": False,
        "warnings": [],
    }
    
    # 流式执行
    try:
        async for chunk in graph.astream(initial_state, config):
            yield chunk
        
        logger.info("[Safe Study Flow] ✅ 流式执行完成")
    except Exception as e:
        logger.error(f"[Safe Study Flow] ❌ 流式执行失败: {e}")
        raise

