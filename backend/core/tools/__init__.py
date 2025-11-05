"""
工具模块
提供各种工具供 Agent 使用，包括时间、计算、网络搜索、天气查询等

在 LangChain 1.0.3 中，使用 @tool 装饰器定义工具
所有工具都遵循 LangChain 的工具接口规范
"""

from .time_tools import get_current_time, get_current_date
from .calculator import calculator
from .web_search import web_search, web_search_simple, create_tavily_search_tool
from .weather import get_weather, get_weather_forecast

# ==================== 工具集合 ====================

# 基础工具集（不需要 API Key）
BASIC_TOOLS = [
    get_current_time,
    get_current_date,
    calculator,
]

# 需要 API Key 的工具
ADVANCED_TOOLS = [
    web_search,
    web_search_simple,
    get_weather,
    get_weather_forecast,
]

# 所有工具的完整列表
ALL_TOOLS = BASIC_TOOLS + ADVANCED_TOOLS

__all__ = [
    # 单个工具
    "get_current_time",
    "get_current_date",
    "calculator",
    "web_search",
    "web_search_simple",
    "create_tavily_search_tool",
    "get_weather",
    "get_weather_forecast",
    # 工具集合
    "BASIC_TOOLS",
    "ADVANCED_TOOLS",
    "ALL_TOOLS",
]

