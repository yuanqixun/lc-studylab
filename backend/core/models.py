"""
模型封装模块
提供统一的 LLM 模型接口，支持 OpenAI 等多种提供商

使用 LangChain 1.0.3 的标准接口封装模型

在 LangChain V1.0.0 中，create_agent 接受字符串格式的模型标识符，
如 "openai:gpt-4o"，这样可以自动初始化模型并使用环境变量中的 API Key。

参考：
- https://docs.langchain.com/oss/python/langchain/models
- https://reference.langchain.com/python/langchain/models/
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from config import settings, get_logger

logger = get_logger(__name__)


def get_chat_model(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    streaming: Optional[bool] = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    获取配置好的聊天模型实例
    
    这是一个工厂函数，根据配置创建 LangChain 的 ChatModel 实例。
    默认使用 OpenAI 的模型，支持流式输出和自定义参数。
    
    Args:
        model_name: 模型名称，默认使用配置中的 openai_model
        temperature: 温度参数 (0.0-2.0)，控制输出随机性，默认使用配置值
        max_tokens: 最大生成 token 数，默认使用配置值
        streaming: 是否启用流式输出，默认使用配置值
        **kwargs: 其他传递给模型的参数
        
    Returns:
        配置好的 ChatModel 实例
        
    Example:
        >>> # 使用默认配置
        >>> model = get_chat_model()
        >>> 
        >>> # 自定义参数
        >>> model = get_chat_model(
        ...     model_name="gpt-4o-mini",
        ...     temperature=0.5,
        ...     streaming=True
        ... )
    """
    # 使用配置中的默认值
    model_name = model_name or settings.openai_model
    temperature = temperature if temperature is not None else settings.openai_temperature
    streaming = streaming if streaming is not None else settings.openai_streaming
    
    # 构建模型配置
    model_config: Dict[str, Any] = {
        "model": model_name,
        "temperature": temperature,
        "streaming": streaming,
        "api_key": settings.openai_api_key,
        "base_url": settings.openai_api_base,
    }
    
    # 添加可选的 max_tokens
    if max_tokens is not None:
        model_config["max_tokens"] = max_tokens
    elif settings.openai_max_tokens is not None:
        model_config["max_tokens"] = settings.openai_max_tokens
    
    # 合并额外的参数
    model_config.update(kwargs)
    
    logger.info(
        f"🤖 创建聊天模型: {model_name} "
        f"(temperature={temperature}, streaming={streaming})"
    )
    
    # 创建 OpenAI ChatModel 实例
    # 这里使用 LangChain 1.0.3 的标准接口
    try:
        model = ChatOpenAI(**model_config)
        logger.debug(f"✅ 模型创建成功: {model_name}")
        return model
    except Exception as e:
        logger.error(f"❌ 模型创建失败: {e}")
        raise


def get_streaming_model(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    获取启用流式输出的聊天模型
    
    这是 get_chat_model 的便捷包装，强制启用流式输出。
    
    Args:
        model_name: 模型名称
        temperature: 温度参数
        **kwargs: 其他参数
        
    Returns:
        启用流式输出的 ChatModel 实例
        
    Example:
        >>> model = get_streaming_model()
        >>> for chunk in model.stream("你好"):
        ...     print(chunk.content, end="", flush=True)
    """
    return get_chat_model(
        model_name=model_name,
        temperature=temperature,
        streaming=True,
        **kwargs,
    )


def get_structured_output_model(
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs: Any,
) -> BaseChatModel:
    """
    获取用于结构化输出的聊天模型
    
    结构化输出通常需要更低的温度以确保输出格式的一致性。
    
    Args:
        model_name: 模型名称
        temperature: 温度参数，默认为 0.0（更确定性的输出）
        **kwargs: 其他参数
        
    Returns:
        配置为结构化输出的 ChatModel 实例
        
    Example:
        >>> from pydantic import BaseModel
        >>> 
        >>> class Answer(BaseModel):
        ...     answer: str
        ...     confidence: float
        >>> 
        >>> model = get_structured_output_model()
        >>> structured_model = model.with_structured_output(Answer)
        >>> result = structured_model.invoke("What is 2+2?")
    """
    return get_chat_model(
        model_name=model_name,
        temperature=temperature,
        streaming=False,  # 结构化输出通常不使用流式
        **kwargs,
    )


# 预定义的模型配置
MODEL_CONFIGS = {
    "default": {
        "model_name": "gpt-4o",
        "temperature": 0.7,
        "description": "默认模型，平衡性能和成本",
    },
    "fast": {
        "model_name": "gpt-4o-mini",
        "temperature": 0.7,
        "description": "快速模型，适合简单任务",
    },
    "precise": {
        "model_name": "gpt-4o",
        "temperature": 0.3,
        "description": "精确模型，适合需要准确性的任务",
    },
    "creative": {
        "model_name": "gpt-4o",
        "temperature": 1.0,
        "description": "创意模型，适合需要创造性的任务",
    },
}


def get_model_by_preset(preset: str = "default", **kwargs: Any) -> BaseChatModel:
    """
    根据预设配置获取模型
    
    Args:
        preset: 预设名称，可选值: default, fast, precise, creative
        **kwargs: 覆盖预设的参数
        
    Returns:
        配置好的 ChatModel 实例
        
    Raises:
        ValueError: 如果预设名称不存在
        
    Example:
        >>> # 使用快速模型
        >>> model = get_model_by_preset("fast")
        >>> 
        >>> # 使用精确模型，但覆盖温度
        >>> model = get_model_by_preset("precise", temperature=0.1)
    """
    if preset not in MODEL_CONFIGS:
        available = ", ".join(MODEL_CONFIGS.keys())
        raise ValueError(f"未知的预设: {preset}. 可用预设: {available}")
    
    config = MODEL_CONFIGS[preset].copy()
    config.pop("description", None)  # 移除描述字段
    config.update(kwargs)  # 用户参数覆盖预设
    
    logger.info(f"📋 使用预设模型配置: {preset}")
    return get_chat_model(**config)


def get_model_string(
    model_name: Optional[str] = None,
    provider: str = "openai",
) -> str:
    """
    获取模型标识符字符串
    
    在 LangChain V1.0.0 中，create_agent 接受字符串格式的模型标识符，
    如 "openai:gpt-4o"、"anthropic:claude-3-5-sonnet-20241022" 等。
    
    这个函数根据配置生成正确的模型标识符字符串。
    
    Args:
        model_name: 模型名称，如果为 None 则使用配置中的默认模型
        provider: 提供商名称，默认为 "openai"
        
    Returns:
        模型标识符字符串，格式为 "provider:model_name"
        
    Example:
        >>> # 获取默认模型字符串
        >>> model_str = get_model_string()
        >>> print(model_str)  # "openai:gpt-4o"
        >>> 
        >>> # 指定模型
        >>> model_str = get_model_string("gpt-4o-mini")
        >>> print(model_str)  # "openai:gpt-4o-mini"
        >>> 
        >>> # 使用其他提供商
        >>> model_str = get_model_string("claude-3-5-sonnet-20241022", "anthropic")
        >>> print(model_str)  # "anthropic:claude-3-5-sonnet-20241022"
    
    参考：
        https://reference.langchain.com/python/langchain/models/
    """
    model_name = model_name or settings.openai_model
    model_string = f"{provider}:{model_name}"
    
    logger.debug(f"🔤 生成模型标识符: {model_string}")
    return model_string

