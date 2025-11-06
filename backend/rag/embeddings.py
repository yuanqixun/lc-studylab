"""
Embeddings 模块

提供统一的 Embedding 模型接口，用于将文本转换为向量。

支持的 Embedding 模型：
- OpenAI Embeddings (text-embedding-3-small, text-embedding-3-large)
- 可扩展支持其他 embedding 模型

参考：
- https://reference.langchain.com/python/langchain_core/embeddings/
- https://reference.langchain.com/python/langchain_openai/embeddings/
"""

from typing import Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

from config import settings, get_logger

logger = get_logger(__name__)


def get_embeddings(
    model: Optional[str] = None,
    batch_size: Optional[int] = None,
    **kwargs,
) -> Embeddings:
    """
    获取 Embedding 模型实例
    
    Args:
        model: 模型名称，默认使用配置中的 embedding_model
            - "text-embedding-3-small": 小型模型，速度快，成本低
            - "text-embedding-3-large": 大型模型，效果好，成本高
            - "text-embedding-ada-002": 旧版模型（不推荐）
        batch_size: 批处理大小，默认使用配置值
        **kwargs: 其他传递给模型的参数
        
    Returns:
        Embeddings 实例
        
    Example:
        >>> # 使用默认配置
        >>> embeddings = get_embeddings()
        >>> 
        >>> # 使用大型模型
        >>> embeddings = get_embeddings(model="text-embedding-3-large")
        >>> 
        >>> # 嵌入单个文本
        >>> vector = embeddings.embed_query("你好，世界")
        >>> print(f"向量维度: {len(vector)}")
        >>> 
        >>> # 批量嵌入
        >>> texts = ["文本1", "文本2", "文本3"]
        >>> vectors = embeddings.embed_documents(texts)
        >>> print(f"生成了 {len(vectors)} 个向量")
    """
    # 使用配置中的默认值
    model = model or settings.embedding_model
    batch_size = batch_size or settings.embedding_batch_size
    
    logger.info(f"🔢 创建 Embedding 模型: {model}")
    logger.debug(f"   batch_size: {batch_size}")
    
    try:
        # 创建 OpenAI Embeddings 实例
        embeddings = OpenAIEmbeddings(
            model=model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            # chunk_size 参数控制批处理大小
            chunk_size=batch_size,
            **kwargs,
        )
        
        logger.debug(f"✅ Embedding 模型创建成功")
        return embeddings
        
    except Exception as e:
        logger.error(f"❌ 创建 Embedding 模型失败: {e}")
        raise


def get_embedding_dimension(model: Optional[str] = None) -> int:
    """
    获取 Embedding 模型的向量维度
    
    Args:
        model: 模型名称
        
    Returns:
        向量维度
        
    Example:
        >>> dim = get_embedding_dimension("text-embedding-3-small")
        >>> print(f"向量维度: {dim}")  # 1536
    """
    model = model or settings.embedding_model
    
    # OpenAI Embedding 模型的维度
    dimensions = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    if model not in dimensions:
        logger.warning(f"未知的模型维度: {model}，返回默认值 1536")
        return 1536
    
    return dimensions[model]


def estimate_embedding_cost(
    num_tokens: int,
    model: Optional[str] = None,
) -> float:
    """
    估算 Embedding 成本（美元）
    
    Args:
        num_tokens: Token 数量
        model: 模型名称
        
    Returns:
        估算成本（美元）
        
    Example:
        >>> # 假设有 100,000 tokens
        >>> cost = estimate_embedding_cost(100000, "text-embedding-3-small")
        >>> print(f"估算成本: ${cost:.4f}")
    """
    model = model or settings.embedding_model
    
    # OpenAI Embedding 定价（每百万 tokens 的美元价格）
    # 参考: https://openai.com/pricing
    pricing = {
        "text-embedding-3-small": 0.02,   # $0.02 / 1M tokens
        "text-embedding-3-large": 0.13,   # $0.13 / 1M tokens
        "text-embedding-ada-002": 0.10,   # $0.10 / 1M tokens
    }
    
    if model not in pricing:
        logger.warning(f"未知的模型定价: {model}，使用默认值")
        price_per_million = 0.02
    else:
        price_per_million = pricing[model]
    
    # 计算成本
    cost = (num_tokens / 1_000_000) * price_per_million
    
    logger.info(
        f"💰 Embedding 成本估算: "
        f"{num_tokens:,} tokens × ${price_per_million}/M = ${cost:.4f}"
    )
    
    return cost


def test_embeddings(
    model: Optional[str] = None,
    test_text: str = "这是一个测试文本",
) -> bool:
    """
    测试 Embedding 模型是否正常工作
    
    Args:
        model: 模型名称
        test_text: 测试文本
        
    Returns:
        是否测试成功
        
    Example:
        >>> if test_embeddings():
        ...     print("Embedding 模型工作正常")
    """
    try:
        logger.info("🧪 测试 Embedding 模型...")
        
        embeddings = get_embeddings(model=model)
        
        # 测试单个文本嵌入
        vector = embeddings.embed_query(test_text)
        logger.info(f"   单文本嵌入: 维度={len(vector)}")
        
        # 测试批量嵌入
        texts = [test_text, test_text + " 2", test_text + " 3"]
        vectors = embeddings.embed_documents(texts)
        logger.info(f"   批量嵌入: {len(vectors)} 个向量")
        
        logger.info("✅ Embedding 模型测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ Embedding 模型测试失败: {e}")
        return False


# 预定义的 Embedding 配置
EMBEDDING_CONFIGS = {
    "fast": {
        "model": "text-embedding-3-small",
        "description": "快速模型，适合开发和测试",
    },
    "quality": {
        "model": "text-embedding-3-large",
        "description": "高质量模型，适合生产环境",
    },
    "legacy": {
        "model": "text-embedding-ada-002",
        "description": "旧版模型（不推荐）",
    },
}


def get_embeddings_by_preset(
    preset: str = "fast",
    **kwargs,
) -> Embeddings:
    """
    根据预设配置获取 Embedding 模型
    
    Args:
        preset: 预设名称
            - "fast": 快速模型（text-embedding-3-small）
            - "quality": 高质量模型（text-embedding-3-large）
            - "legacy": 旧版模型（text-embedding-ada-002）
        **kwargs: 覆盖预设的参数
        
    Returns:
        Embeddings 实例
        
    Raises:
        ValueError: 如果预设名称不存在
        
    Example:
        >>> # 使用快速模型
        >>> embeddings = get_embeddings_by_preset("fast")
        >>> 
        >>> # 使用高质量模型
        >>> embeddings = get_embeddings_by_preset("quality")
    """
    if preset not in EMBEDDING_CONFIGS:
        available = ", ".join(EMBEDDING_CONFIGS.keys())
        raise ValueError(
            f"未知的预设: {preset}. 可用预设: {available}"
        )
    
    config = EMBEDDING_CONFIGS[preset].copy()
    model = config.pop("model")
    config.pop("description", None)
    config.update(kwargs)
    
    logger.info(f"📋 使用预设 Embedding 配置: {preset}")
    return get_embeddings(model=model, **config)

