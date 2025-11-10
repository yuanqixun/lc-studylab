"""
Deep Research API 路由

提供深度研究相关的 HTTP 接口。

端点：
- POST /deep-research/start: 启动深度研究任务
- GET /deep-research/status/{thread_id}: 查询研究状态
- GET /deep-research/result/{thread_id}: 获取研究结果
- GET /deep-research/files/{thread_id}: 列出研究文件

技术要点：
- 使用 FastAPI 异步接口
- 支持后台任务执行
- 提供详细的错误处理
- 返回结构化的 JSON 响应

参考：
- FastAPI 文档: https://fastapi.tiangolo.com/
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from config import settings, get_logger
from deep_research import create_deep_research_agent
from core.tools.filesystem import get_filesystem

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/deep-research",
    tags=["deep-research"],
    responses={404: {"description": "Not found"}},
)


# ==================== 请求/响应模型 ====================

class StartResearchRequest(BaseModel):
    """启动研究请求"""
    query: str = Field(..., description="研究问题", min_length=1, max_length=1000)
    research_depth: str = Field(
        default="standard",
        description="研究深度：basic, standard, comprehensive"
    )
    enable_web_search: bool = Field(default=True, description="是否启用网络搜索")
    enable_doc_analysis: bool = Field(default=False, description="是否启用文档分析")
    index_name: Optional[str] = Field(default=None, description="文档索引名称（如果启用文档分析）")
    thread_id: Optional[str] = Field(default=None, description="自定义线程 ID（可选）")


class StartResearchResponse(BaseModel):
    """启动研究响应"""
    status: str = Field(..., description="状态：success, error")
    thread_id: str = Field(..., description="研究任务 ID")
    message: str = Field(..., description="提示消息")
    estimated_time: str = Field(..., description="预计完成时间")


class ResearchStatusResponse(BaseModel):
    """研究状态响应"""
    status: str = Field(..., description="状态：pending, running, completed, failed")
    thread_id: str = Field(..., description="研究任务 ID")
    current_step: Optional[str] = Field(None, description="当前步骤")
    progress: int = Field(..., description="进度百分比（0-100）")
    message: str = Field(..., description="状态消息")


class ResearchResultResponse(BaseModel):
    """研究结果响应"""
    status: str = Field(..., description="状态")
    thread_id: str = Field(..., description="研究任务 ID")
    query: str = Field(..., description="研究问题")
    final_report: Optional[str] = Field(None, description="最终报告")
    plan: Optional[Dict[str, Any]] = Field(None, description="研究计划")
    steps_completed: Optional[Dict[str, bool]] = Field(None, description="完成的步骤")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class FileListResponse(BaseModel):
    """文件列表响应"""
    thread_id: str = Field(..., description="研究任务 ID")
    files: List[str] = Field(..., description="文件列表")
    total: int = Field(..., description="文件总数")


# ==================== 全局状态管理 ====================

# 存储研究任务状态
_research_tasks: Dict[str, Dict[str, Any]] = {}


def get_task_status(thread_id: str) -> Optional[Dict[str, Any]]:
    """获取任务状态"""
    return _research_tasks.get(thread_id)


def update_task_status(thread_id: str, status: Dict[str, Any]) -> None:
    """更新任务状态"""
    if thread_id not in _research_tasks:
        _research_tasks[thread_id] = {}
    _research_tasks[thread_id].update(status)


# ==================== 后台任务函数 ====================

async def run_research_task(
    thread_id: str,
    query: str,
    enable_web_search: bool,
    enable_doc_analysis: bool,
    index_name: Optional[str] = None,
) -> None:
    """
    在后台运行研究任务
    
    Args:
        thread_id: 研究任务 ID
        query: 研究问题
        enable_web_search: 是否启用网络搜索
        enable_doc_analysis: 是否启用文档分析
        index_name: 文档索引名称
    """
    logger.info(f"🚀 后台任务启动: {thread_id}")
    
    # 更新状态为运行中
    update_task_status(thread_id, {
        "status": "running",
        "current_step": "initializing",
        "start_time": datetime.now().isoformat(),
    })
    
    try:
        # 创建 retriever_tool（如果需要）
        retriever_tool = None
        if enable_doc_analysis and index_name:
            try:
                from rag import get_embeddings, load_vector_store, create_retriever_tool
                
                logger.info(f"   加载文档索引: {index_name}")
                embeddings = get_embeddings()
                vector_store = load_vector_store(
                    f"{settings.vector_store_path}/{index_name}",
                    embeddings
                )
                retriever = vector_store.as_retriever()
                retriever_tool = create_retriever_tool(retriever)
                logger.info("   ✓ 文档索引已加载")
                
            except Exception as e:
                logger.warning(f"⚠️ 加载文档索引失败: {e}")
                # 继续执行，但禁用文档分析
                enable_doc_analysis = False
        
        # 创建 DeepAgent
        update_task_status(thread_id, {"current_step": "creating_agent"})
        
        agent = create_deep_research_agent(
            thread_id=thread_id,
            enable_web_search=enable_web_search,
            enable_doc_analysis=enable_doc_analysis,
            retriever_tool=retriever_tool,
        )
        
        # 执行研究
        update_task_status(thread_id, {"current_step": "researching"})
        
        # 在同步上下文中执行（因为 agent.research 是同步的）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.research, query)
        
        # 更新状态为完成
        update_task_status(thread_id, {
            "status": "completed",
            "current_step": "completed",
            "end_time": datetime.now().isoformat(),
            "result": result,
        })
        
        logger.info(f"✅ 后台任务完成: {thread_id}")
        
    except Exception as e:
        logger.error(f"❌ 后台任务失败: {thread_id}, 错误: {e}")
        
        # 更新状态为失败
        update_task_status(thread_id, {
            "status": "failed",
            "current_step": "failed",
            "end_time": datetime.now().isoformat(),
            "error": str(e),
        })


# ==================== API 端点 ====================

@router.post("/start", response_model=StartResearchResponse)
async def start_research(
    request: StartResearchRequest,
    background_tasks: BackgroundTasks,
) -> StartResearchResponse:
    """
    启动深度研究任务
    
    创建一个新的研究任务，在后台执行。
    
    Args:
        request: 研究请求
        background_tasks: FastAPI 后台任务
        
    Returns:
        启动响应，包含 thread_id
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/deep-research/start" \\
          -H "Content-Type: application/json" \\
          -d '{
            "query": "分析 LangChain 1.0 的新特性",
            "enable_web_search": true,
            "enable_doc_analysis": false
          }'
        ```
    """
    logger.info(f"📥 收到研究请求: {request.query}")
    
    try:
        # 生成或使用提供的 thread_id
        thread_id = request.thread_id or f"research_{uuid.uuid4().hex[:12]}"
        
        # 检查是否已存在
        if thread_id in _research_tasks:
            raise HTTPException(
                status_code=400,
                detail=f"研究任务 {thread_id} 已存在"
            )
        
        # 初始化任务状态
        update_task_status(thread_id, {
            "status": "pending",
            "query": request.query,
            "current_step": "pending",
            "created_at": datetime.now().isoformat(),
        })
        
        # 添加后台任务
        background_tasks.add_task(
            run_research_task,
            thread_id=thread_id,
            query=request.query,
            enable_web_search=request.enable_web_search,
            enable_doc_analysis=request.enable_doc_analysis,
            index_name=request.index_name,
        )
        
        # 估算完成时间
        if request.research_depth == "basic":
            estimated_time = "3-5分钟"
        elif request.research_depth == "comprehensive":
            estimated_time = "10-15分钟"
        else:
            estimated_time = "5-10分钟"
        
        logger.info(f"✅ 研究任务已启动: {thread_id}")
        
        return StartResearchResponse(
            status="success",
            thread_id=thread_id,
            message="研究任务已启动，正在后台执行",
            estimated_time=estimated_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 启动研究任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.get("/status/{thread_id}", response_model=ResearchStatusResponse)
async def get_research_status(thread_id: str) -> ResearchStatusResponse:
    """
    查询研究状态
    
    Args:
        thread_id: 研究任务 ID
        
    Returns:
        研究状态
        
    Example:
        ```bash
        curl "http://localhost:8000/deep-research/status/research_abc123"
        ```
    """
    logger.info(f"📊 查询研究状态: {thread_id}")
    
    task_status = get_task_status(thread_id)
    
    if task_status is None:
        raise HTTPException(
            status_code=404,
            detail=f"研究任务 {thread_id} 不存在"
        )
    
    # 计算进度
    status = task_status.get("status", "pending")
    current_step = task_status.get("current_step", "pending")
    
    progress_map = {
        "pending": 0,
        "initializing": 10,
        "creating_agent": 20,
        "researching": 50,
        "completed": 100,
        "failed": 0,
    }
    
    progress = progress_map.get(current_step, 0)
    
    # 状态消息
    message_map = {
        "pending": "任务等待中",
        "initializing": "正在初始化...",
        "creating_agent": "正在创建研究智能体...",
        "researching": "正在执行研究任务...",
        "completed": "研究任务已完成",
        "failed": "研究任务失败",
    }
    
    message = message_map.get(current_step, "处理中...")
    
    if status == "failed":
        error = task_status.get("error", "未知错误")
        message = f"任务失败: {error}"
    
    return ResearchStatusResponse(
        status=status,
        thread_id=thread_id,
        current_step=current_step,
        progress=progress,
        message=message,
    )


@router.get("/result/{thread_id}", response_model=ResearchResultResponse)
async def get_research_result(thread_id: str) -> ResearchResultResponse:
    """
    获取研究结果
    
    Args:
        thread_id: 研究任务 ID
        
    Returns:
        研究结果，包含最终报告
        
    Example:
        ```bash
        curl "http://localhost:8000/deep-research/result/research_abc123"
        ```
    """
    logger.info(f"📄 获取研究结果: {thread_id}")
    
    task_status = get_task_status(thread_id)
    
    if task_status is None:
        raise HTTPException(
            status_code=404,
            detail=f"研究任务 {thread_id} 不存在"
        )
    
    status = task_status.get("status", "pending")
    
    if status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"研究任务尚未完成，当前状态: {status}"
        )
    
    # 提取结果
    result = task_status.get("result", {})
    
    # 构建元数据
    metadata = {
        "start_time": task_status.get("start_time"),
        "end_time": task_status.get("end_time"),
        "created_at": task_status.get("created_at"),
    }
    
    return ResearchResultResponse(
        status=status,
        thread_id=thread_id,
        query=task_status.get("query", ""),
        final_report=result.get("final_report"),
        plan=result.get("plan"),
        steps_completed=result.get("steps_completed"),
        error=result.get("error") or task_status.get("error"),
        metadata=metadata,
    )


@router.get("/files/{thread_id}", response_model=FileListResponse)
async def list_research_files(
    thread_id: str,
    subdirectory: Optional[str] = Query(None, description="子目录过滤")
) -> FileListResponse:
    """
    列出研究文件
    
    Args:
        thread_id: 研究任务 ID
        subdirectory: 子目录过滤（可选）
        
    Returns:
        文件列表
        
    Example:
        ```bash
        curl "http://localhost:8000/deep-research/files/research_abc123"
        curl "http://localhost:8000/deep-research/files/research_abc123?subdirectory=reports"
        ```
    """
    logger.info(f"📁 列出研究文件: {thread_id}")
    
    try:
        fs = get_filesystem(thread_id)
        files = fs.list_files(subdirectory=subdirectory)
        
        return FileListResponse(
            thread_id=thread_id,
            files=files,
            total=len(files),
        )
        
    except Exception as e:
        logger.error(f"❌ 列出文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")


@router.get("/file/{thread_id}/{filename:path}")
async def get_research_file(
    thread_id: str,
    filename: str,
) -> Dict[str, Any]:
    """
    获取研究文件内容
    
    Args:
        thread_id: 研究任务 ID
        filename: 文件名（可以包含子目录，如 "reports/final_report.md"）
        
    Returns:
        文件内容
        
    Example:
        ```bash
        curl "http://localhost:8000/deep-research/file/research_abc123/reports/final_report.md"
        ```
    """
    logger.info(f"📖 读取研究文件: {thread_id}/{filename}")
    
    try:
        fs = get_filesystem(thread_id)
        
        # 解析文件路径
        if "/" in filename:
            parts = filename.split("/")
            subdirectory = "/".join(parts[:-1])
            file_name = parts[-1]
        else:
            subdirectory = None
            file_name = filename
        
        # 读取文件
        content = fs.read_file(file_name, subdirectory=subdirectory)
        
        # 获取文件信息
        file_info = fs.get_file_info(file_name, subdirectory=subdirectory)
        
        return {
            "filename": filename,
            "content": content,
            "info": file_info,
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"文件不存在: {filename}"
        )
    except Exception as e:
        logger.error(f"❌ 读取文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.delete("/task/{thread_id}")
async def delete_research_task(thread_id: str) -> Dict[str, str]:
    """
    删除研究任务
    
    删除任务状态和相关文件。
    
    Args:
        thread_id: 研究任务 ID
        
    Returns:
        删除结果
        
    Example:
        ```bash
        curl -X DELETE "http://localhost:8000/deep-research/task/research_abc123"
        ```
    """
    logger.info(f"🗑️ 删除研究任务: {thread_id}")
    
    # 删除任务状态
    if thread_id in _research_tasks:
        del _research_tasks[thread_id]
    
    # 注意：文件系统中的文件不会被删除，需要手动清理
    
    return {
        "status": "success",
        "message": f"研究任务 {thread_id} 已删除（文件保留）"
    }


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点
    
    Returns:
        服务状态
    """
    return {
        "status": "healthy",
        "service": "deep-research",
        "active_tasks": len(_research_tasks),
        "tasks": {
            thread_id: task.get("status")
            for thread_id, task in _research_tasks.items()
        }
    }


logger.info("✅ Deep Research API 路由已加载")

