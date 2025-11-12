"""
高德天气查询工具
基于高德地图 Web 服务 API 实现天气查询功能

API 文档：https://lbs.amap.com/api/webservice/guide/api/weatherinfo
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, Literal
from langchain_core.tools import tool

from config import settings, get_logger

logger = get_logger(__name__)


def _get_weather_impl(
    city: str,
    extensions: Literal["base", "all"] = "base"
) -> str:
    """
    天气查询的底层实现函数
    
    Args:
        city: 城市名称或城市编码
        extensions: 气象类型（"base" 或 "all"）
    
    Returns:
        格式化的天气信息字符串
    """
    # 检查 API Key
    amap_key = getattr(settings, 'amap_key', None)
    if not amap_key:
        error_msg = "高德地图 API Key 未设置！请在 .env 文件中设置 AMAP_KEY。\n获取 API Key: https://console.amap.com/"
        logger.error(error_msg)
        return f"错误：{error_msg}"
    
    # API 端点
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    # 构建请求参数
    params = {
        "key": amap_key,
        "city": city,
        "extensions": extensions,
        "output": "JSON"
    }
    
    logger.info(f"🌤️ 查询天气: city={city}, extensions={extensions}")
    
    try:
        # 发送 HTTP 请求
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # 检查返回状态
        if data.get("status") != "1":
            error_msg = f"天气查询失败: {data.get('info', '未知错误')}"
            logger.error(error_msg)
            return f"错误：{error_msg}"
        
        # 解析并格式化天气信息
        if extensions == "base":
            # 实况天气
            return _format_live_weather(data)
        else:
            # 预报天气
            return _format_forecast_weather(data)
            
    except httpx.TimeoutException:
        error_msg = "天气查询超时，请稍后重试"
        logger.error(error_msg)
        return f"错误：{error_msg}"
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP 请求失败: {e.response.status_code}"
        logger.error(error_msg)
        return f"错误：{error_msg}"
    except Exception as e:
        error_msg = f"天气查询出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"错误：{error_msg}"


@tool
def get_weather(
    city: str,
    extensions: Literal["base", "all"] = "base"
) -> str:
    """
    查询指定城市的天气信息
    
    支持查询实况天气和预报天气：
    - base: 返回实况天气（当前天气状况）
    - all: 返回预报天气（未来3天预报）
    
    Args:
        city: 城市名称或城市编码（adcode）
              例如："北京"、"110101"
              城市编码表可参考：https://lbs.amap.com/api/webservice/download
        extensions: 气象类型
                   "base" - 返回实况天气（默认）
                   "all" - 返回预报天气
    
    Returns:
        格式化的天气信息字符串
        
    Example:
        >>> # 查询北京实况天气
        >>> result = get_weather.invoke({"city": "北京"})
        >>> print(result)
        
        >>> # 查询上海未来天气预报
        >>> result = get_weather.invoke({"city": "上海", "extensions": "all"})
        >>> print(result)
    
    注意：
        - 实况天气每小时更新多次
        - 预报天气每天更新3次（8点、11点、18点左右）
        - 需要在 .env 文件中设置 AMAP_KEY
    """
    return _get_weather_impl(city, extensions)


def _format_live_weather(data: dict) -> str:
    """
    格式化实况天气数据
    
    Args:
        data: API 返回的 JSON 数据
        
    Returns:
        格式化的天气信息字符串
    """
    lives = data.get("lives", [])
    if not lives:
        return "未查询到天气数据"
    
    live = lives[0]
    
    # 提取字段
    province = live.get("province", "")
    city = live.get("city", "")
    weather = live.get("weather", "")
    temperature = live.get("temperature", "")
    winddirection = live.get("winddirection", "")
    windpower = live.get("windpower", "")
    humidity = live.get("humidity", "")
    reporttime = live.get("reporttime", "")
    
    # 格式化输出
    result = f"""
📍 地区：{province} {city}
🌤️ 天气：{weather}
🌡️ 温度：{temperature}°C
💨 风向：{winddirection}风
💨 风力：{windpower}级
💧 湿度：{humidity}%
⏰ 更新时间：{reporttime}
""".strip()
    
    logger.info(f"✅ 实况天气查询成功: {city}")
    return result


def _format_forecast_weather(data: dict, day_offset: Optional[int] = None) -> str:
    """
    格式化预报天气数据
    
    Args:
        data: API 返回的 JSON 数据
        day_offset: 指定查询第几天的天气（0=今天，1=明天，2=后天，None=所有天）
        
    Returns:
        格式化的天气信息字符串
    """
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return "未查询到天气预报数据"
    
    forecast = forecasts[0]
    
    # 提取基本信息
    province = forecast.get("province", "")
    city = forecast.get("city", "")
    reporttime = forecast.get("reporttime", "")
    casts = forecast.get("casts", [])
    
    if not casts:
        return "未查询到具体预报数据"
    
    # 如果指定了 day_offset，只返回那一天的数据
    if day_offset is not None:
        if day_offset < 0 or day_offset >= len(casts):
            return f"错误：无法查询第 {day_offset} 天的天气（可用范围: 0-{len(casts)-1}）"
        
        cast = casts[day_offset]
        date = cast.get("date", "")
        week = cast.get("week", "")
        dayweather = cast.get("dayweather", "")
        nightweather = cast.get("nightweather", "")
        daytemp = cast.get("daytemp", "")
        nighttemp = cast.get("nighttemp", "")
        daywind = cast.get("daywind", "")
        nightwind = cast.get("nightwind", "")
        daypower = cast.get("daypower", "")
        nightpower = cast.get("nightpower", "")
        
        # 生成时间描述
        day_names = ["今天", "明天", "后天"]
        day_name = day_names[day_offset] if day_offset < len(day_names) else f"{day_offset}天后"
        
        result = f"""📍 地区：{province} {city}
⏰ 预报发布时间：{reporttime}

📅 {day_name}（{date} 星期{week}）
  🌞 白天：{dayweather}  {daytemp}°C  {daywind}风{daypower}级
  🌙 夜间：{nightweather}  {nighttemp}°C  {nightwind}风{nightpower}级"""
        
        logger.info(f"✅ 预报天气查询成功: {city} {day_name}")
        return result
    
    # 返回所有天的预报
    result = [f"📍 地区：{province} {city}"]
    result.append(f"⏰ 预报发布时间：{reporttime}")
    result.append("")
    
    # 遍历每天的预报
    for idx, cast in enumerate(casts):
        date = cast.get("date", "")
        week = cast.get("week", "")
        dayweather = cast.get("dayweather", "")
        nightweather = cast.get("nightweather", "")
        daytemp = cast.get("daytemp", "")
        nighttemp = cast.get("nighttemp", "")
        daywind = cast.get("daywind", "")
        nightwind = cast.get("nightwind", "")
        daypower = cast.get("daypower", "")
        nightpower = cast.get("nightpower", "")
        
        # 生成时间描述
        day_names = ["今天", "明天", "后天"]
        day_name = day_names[idx] if idx < len(day_names) else f"{idx}天后"
        
        day_info = f"""
📅 {day_name}（{date} 星期{week}）
  🌞 白天：{dayweather}  {daytemp}°C  {daywind}风{daypower}级
  🌙 夜间：{nightweather}  {nighttemp}°C  {nightwind}风{nightpower}级
""".strip()
        
        result.append(day_info)
    
    logger.info(f"✅ 预报天气查询成功: {city} ({len(casts)}天)")
    return "\n".join(result)


@tool
def get_weather_forecast(city: str) -> str:
    """
    查询指定城市未来3天的天气预报
    
    这是 get_weather 的便捷版本，直接返回预报天气。
    
    Args:
        city: 城市名称或城市编码（adcode）
              例如："北京"、"上海"、"广州"
    
    Returns:
        格式化的天气预报信息字符串
        
    Example:
        >>> result = get_weather_forecast.invoke({"city": "深圳"})
        >>> print(result)
    """
    return _get_weather_impl(city=city, extensions="all")


@tool
def get_daily_weather(
    city: str,
    day: Literal["today", "tomorrow", "day_after_tomorrow"] = "tomorrow"
) -> str:
    """
    查询指定城市某一天的天气预报（推荐使用）
    
    **重要：这个工具内部已经知道当前日期，不需要先调用 get_current_date 或 get_current_time！**
    
    当用户问"今天天气"、"明天天气"、"后天天气"时，直接使用这个工具。
    
    Args:
        city: 城市名称或城市编码（adcode）
              例如："北京"、"上海"、"深圳"、"广州"
        day: 查询哪一天的天气（相对于当前日期）
             - "today": 今天（相对于当前日期）
             - "tomorrow": 明天（相对于当前日期，默认）
             - "day_after_tomorrow": 后天（相对于当前日期）
    
    Returns:
        格式化的天气预报信息字符串（只包含指定那一天）
        
    Example:
        >>> # 查询深圳今天的天气
        >>> result = get_daily_weather.invoke({"city": "深圳", "day": "today"})
        >>> 
        >>> # 查询北京明天的天气
        >>> result = get_daily_weather.invoke({"city": "北京", "day": "tomorrow"})
        >>> 
        >>> # 查询上海后天的天气
        >>> result = get_daily_weather.invoke({"city": "上海", "day": "day_after_tomorrow"})
    
    重要提示：
        - **不要先调用 get_current_date 或 get_current_time**，这个工具内部已经知道当前日期
        - 如果用户问"今天天气"，直接调用 get_daily_weather(city="城市名", day="today")
        - 如果用户问"明天天气"，直接调用 get_daily_weather(city="城市名", day="tomorrow")
        - 如果用户问"后天天气"，直接调用 get_daily_weather(city="城市名", day="day_after_tomorrow")
        - 这个工具会自动调用预报天气API，但只返回指定那一天的信息
        - 更节省 token，适合用户只问某一天天气的场景
    """
    # 映射 day 参数到 day_offset
    day_offset_map = {
        "today": 0,
        "tomorrow": 1,
        "day_after_tomorrow": 2,
    }
    
    day_offset = day_offset_map.get(day, 1)
    
    # 调用底层实现获取预报数据
    # 检查 API Key
    amap_key = getattr(settings, 'amap_key', None)
    if not amap_key:
        error_msg = "高德地图 API Key 未设置！请在 .env 文件中设置 AMAP_KEY。\n获取 API Key: https://console.amap.com/"
        logger.error(error_msg)
        return f"错误：{error_msg}"
    
    # API 端点
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    # 构建请求参数（使用 all 获取预报）
    params = {
        "key": amap_key,
        "city": city,
        "extensions": "all",
        "output": "JSON"
    }
    
    logger.info(f"🌤️ 查询天气: city={city}, day={day} (offset={day_offset})")
    
    try:
        # 发送 HTTP 请求
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # 检查返回状态
        if data.get("status") != "1":
            error_msg = f"天气查询失败: {data.get('info', '未知错误')}"
            logger.error(error_msg)
            return f"错误：{error_msg}"
        
        # 格式化输出（只返回指定那一天）
        return _format_forecast_weather(data, day_offset=day_offset)
            
    except httpx.TimeoutException:
        error_msg = "天气查询超时，请稍后重试"
        logger.error(error_msg)
        return f"错误：{error_msg}"
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP 请求失败: {e.response.status_code}"
        logger.error(error_msg)
        return f"错误：{error_msg}"
    except Exception as e:
        error_msg = f"天气查询出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"错误：{error_msg}"


# 导出工具
__all__ = [
    "get_weather",
    "get_weather_forecast",
    "get_daily_weather",
]

