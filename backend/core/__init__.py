"""
核心模块
提供模型封装、提示词模板、工具和安全防护
"""

from .models import get_chat_model
from .prompts import SYSTEM_PROMPTS, get_system_prompt

__all__ = [
    "get_chat_model",
    "SYSTEM_PROMPTS",
    "get_system_prompt",
]

