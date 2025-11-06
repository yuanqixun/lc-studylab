"""
向量存储模块

提供统一的向量数据库接口，支持多种向量存储后端：
- FAISS: 本地向量库，支持持久化（推荐）
- InMemoryVectorStore: 内存向量库，用于开发测试
- Chroma: 可选的向量库

参考：
- https://reference.langchain.com/python/langchain_core/vectorstores/
- https://reference.langchain.com/python/langchain_community/vectorstores/
"""

import os
from pathlib import Path
from typing import List, Optional, Literal
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore, InMemoryVectorStore

try:
    from langchain_community.vectorstores import FAISS
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from config import settings, get_logger

logger = get_logger(__name__)


# 向量库类型
VectorStoreType = Literal["faiss", "inmemory"]


def create_vector_store(
    documents: List[Document],
    embeddings: Embeddings,
    store_type: Optional[VectorStoreType] = None,
    **kwargs,
) -> VectorStore:
    """
    从文档创建向量存储
    
    Args:
        documents: 文档列表
        embeddings: Embedding 模型
        store_type: 向量库类型，默认使用配置中的类型
        **kwargs: 其他传递给向量库的参数
        
    Returns:
        VectorStore 实例
        
    Raises:
        ValueError: 如果文档列表为空或向量库类型不支持
        
    Example:
        >>> from rag import load_document, split_documents, get_embeddings
        >>> 
        >>> # 加载和分块文档
        >>> documents = load_document("document.pdf")
        >>> chunks = split_documents(documents)
        >>> 
        >>> # 创建 embeddings
        >>> embeddings = get_embeddings()
        >>> 
        >>> # 创建向量库
        >>> vector_store = create_vector_store(chunks, embeddings)
    """
    if not documents:
        raise ValueError("文档列表不能为空")
    
    store_type = store_type or settings.vector_store_type
    
    logger.info(f"🗄️  创建向量存储: type={store_type}, documents={len(documents)}")
    
    try:
        if store_type == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError(
                    "FAISS 未安装。请运行: pip install faiss-cpu"
                )
            
            vector_store = FAISS.from_documents(
                documents=documents,
                embedding=embeddings,
                **kwargs,
            )
            logger.info("✅ FAISS 向量库创建成功")
            
        elif store_type == "inmemory":
            vector_store = InMemoryVectorStore.from_documents(
                documents=documents,
                embedding=embeddings,
                **kwargs,
            )
            logger.info("✅ 内存向量库创建成功")
            
        else:
            raise ValueError(
                f"不支持的向量库类型: {store_type}。"
                f"支持的类型: faiss, inmemory"
            )
        
        return vector_store
        
    except Exception as e:
        logger.error(f"❌ 创建向量库失败: {e}")
        raise


def save_vector_store(
    vector_store: VectorStore,
    save_path: str,
    embeddings: Optional[Embeddings] = None,
) -> None:
    """
    保存向量存储到磁盘
    
    Args:
        vector_store: 向量存储实例
        save_path: 保存路径
        embeddings: Embedding 模型（某些向量库需要）
        
    Raises:
        ValueError: 如果向量库类型不支持持久化
        
    Example:
        >>> # 保存 FAISS 向量库
        >>> save_vector_store(vector_store, "data/indexes/my_index")
    """
    save_path = Path(save_path)
    
    # 确保目录存在
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"💾 保存向量库: {save_path}")
    
    try:
        if isinstance(vector_store, FAISS):
            # FAISS 支持本地保存
            vector_store.save_local(str(save_path))
            logger.info("✅ FAISS 向量库保存成功")
            
        elif isinstance(vector_store, InMemoryVectorStore):
            # InMemoryVectorStore 不支持持久化
            logger.warning("⚠️  InMemoryVectorStore 不支持持久化")
            raise ValueError("InMemoryVectorStore 不支持持久化")
            
        else:
            logger.warning(f"⚠️  未知的向量库类型: {type(vector_store)}")
            raise ValueError(f"不支持的向量库类型: {type(vector_store)}")
            
    except Exception as e:
        logger.error(f"❌ 保存向量库失败: {e}")
        raise


def load_vector_store(
    load_path: str,
    embeddings: Embeddings,
    store_type: Optional[VectorStoreType] = None,
    **kwargs,
) -> VectorStore:
    """
    从磁盘加载向量存储
    
    Args:
        load_path: 加载路径
        embeddings: Embedding 模型
        store_type: 向量库类型，默认使用配置中的类型
        **kwargs: 其他传递给向量库的参数
        
    Returns:
        VectorStore 实例
        
    Raises:
        FileNotFoundError: 如果路径不存在
        ValueError: 如果向量库类型不支持
        
    Example:
        >>> from rag import get_embeddings, load_vector_store
        >>> 
        >>> embeddings = get_embeddings()
        >>> vector_store = load_vector_store(
        ...     "data/indexes/my_index",
        ...     embeddings
        ... )
    """
    load_path = Path(load_path)
    
    if not load_path.exists():
        raise FileNotFoundError(f"向量库路径不存在: {load_path}")
    
    store_type = store_type or settings.vector_store_type
    
    logger.info(f"📂 加载向量库: {load_path}")
    
    try:
        if store_type == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError(
                    "FAISS 未安装。请运行: pip install faiss-cpu"
                )
            
            vector_store = FAISS.load_local(
                folder_path=str(load_path),
                embeddings=embeddings,
                allow_dangerous_deserialization=True,  # 允许反序列化
                **kwargs,
            )
            logger.info("✅ FAISS 向量库加载成功")
            
        elif store_type == "inmemory":
            raise ValueError("InMemoryVectorStore 不支持从磁盘加载")
            
        else:
            raise ValueError(
                f"不支持的向量库类型: {store_type}。"
                f"支持的类型: faiss"
            )
        
        return vector_store
        
    except Exception as e:
        logger.error(f"❌ 加载向量库失败: {e}")
        raise


def add_documents_to_vector_store(
    vector_store: VectorStore,
    documents: List[Document],
) -> None:
    """
    向现有向量库添加文档
    
    Args:
        vector_store: 向量存储实例
        documents: 要添加的文档列表
        
    Example:
        >>> # 加载现有向量库
        >>> vector_store = load_vector_store("data/indexes/my_index", embeddings)
        >>> 
        >>> # 添加新文档
        >>> new_docs = load_document("new_document.pdf")
        >>> chunks = split_documents(new_docs)
        >>> add_documents_to_vector_store(vector_store, chunks)
        >>> 
        >>> # 保存更新后的向量库
        >>> save_vector_store(vector_store, "data/indexes/my_index")
    """
    if not documents:
        logger.warning("文档列表为空，无需添加")
        return
    
    logger.info(f"➕ 向向量库添加文档: {len(documents)} 个")
    
    try:
        vector_store.add_documents(documents)
        logger.info("✅ 文档添加成功")
        
    except Exception as e:
        logger.error(f"❌ 添加文档失败: {e}")
        raise


def search_vector_store(
    vector_store: VectorStore,
    query: str,
    k: int = 4,
    score_threshold: Optional[float] = None,
) -> List[tuple[Document, float]]:
    """
    在向量库中搜索相似文档
    
    Args:
        vector_store: 向量存储实例
        query: 查询文本
        k: 返回的文档数量
        score_threshold: 相似度阈值（可选）
        
    Returns:
        (Document, score) 元组列表，按相似度降序排列
        
    Example:
        >>> results = search_vector_store(
        ...     vector_store,
        ...     "什么是机器学习？",
        ...     k=3
        ... )
        >>> 
        >>> for doc, score in results:
        ...     print(f"相似度: {score:.4f}")
        ...     print(f"内容: {doc.page_content[:100]}")
    """
    logger.info(f"🔍 搜索向量库: query='{query[:50]}...', k={k}")
    
    try:
        # 使用 similarity_search_with_score 获取相似度分数
        results = vector_store.similarity_search_with_score(
            query=query,
            k=k,
        )
        
        # 如果设置了阈值，过滤结果
        if score_threshold is not None:
            results = [
                (doc, score) for doc, score in results
                if score >= score_threshold
            ]
        
        logger.info(f"✅ 找到 {len(results)} 个相关文档")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        raise


def get_vector_store_stats(vector_store: VectorStore) -> dict:
    """
    获取向量库的统计信息
    
    Args:
        vector_store: 向量存储实例
        
    Returns:
        包含统计信息的字典
        
    Example:
        >>> stats = get_vector_store_stats(vector_store)
        >>> print(f"文档数量: {stats.get('num_documents', 'N/A')}")
    """
    stats = {
        "type": type(vector_store).__name__,
    }
    
    try:
        # FAISS 特有的统计信息
        if isinstance(vector_store, FAISS):
            stats["num_documents"] = vector_store.index.ntotal
            stats["dimension"] = vector_store.index.d
            
        # InMemoryVectorStore 特有的统计信息
        elif isinstance(vector_store, InMemoryVectorStore):
            # InMemoryVectorStore 没有直接的统计方法
            # 可以通过其他方式获取
            stats["num_documents"] = "N/A"
            
    except Exception as e:
        logger.warning(f"获取统计信息失败: {e}")
    
    logger.info("📊 向量库统计:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    return stats


def delete_vector_store(path: str) -> None:
    """
    删除向量库文件
    
    Args:
        path: 向量库路径
        
    Example:
        >>> delete_vector_store("data/indexes/old_index")
    """
    path = Path(path)
    
    if not path.exists():
        logger.warning(f"向量库不存在: {path}")
        return
    
    logger.info(f"🗑️  删除向量库: {path}")
    
    try:
        # 删除目录及其内容
        if path.is_dir():
            import shutil
            shutil.rmtree(path)
        else:
            path.unlink()
        
        logger.info("✅ 向量库删除成功")
        
    except Exception as e:
        logger.error(f"❌ 删除向量库失败: {e}")
        raise

