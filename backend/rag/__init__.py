"""
RAG（Retrieval-Augmented Generation）模块

这个模块提供完整的 RAG 功能，包括：
- 文档加载（Document Loaders）
- 文本分块（Text Splitters）
- 向量化（Embeddings）
- 向量存储（Vector Stores）
- 检索器（Retrievers）
- RAG Agent

使用 LangChain 1.0.3 的标准 API 实现。

参考：
- https://docs.langchain.com/oss/python/langchain/retrieval
"""

from rag.loaders import load_document, load_directory, get_supported_extensions
from rag.splitters import get_text_splitter, split_documents
from rag.embeddings import get_embeddings
from rag.vector_stores import create_vector_store, load_vector_store, save_vector_store
from rag.retrievers import create_retriever, create_retriever_tool
from rag.rag_agent import create_rag_agent, query_rag_agent
from rag.index_manager import IndexManager

__all__ = [
    # 文档加载
    "load_document",
    "load_directory",
    "get_supported_extensions",
    
    # 文本分块
    "get_text_splitter",
    "split_documents",
    
    # Embeddings
    "get_embeddings",
    
    # 向量存储
    "create_vector_store",
    "load_vector_store",
    "save_vector_store",
    
    # 检索器
    "create_retriever",
    "create_retriever_tool",
    
    # RAG Agent
    "create_rag_agent",
    "query_rag_agent",
    
    # 索引管理
    "IndexManager",
]

