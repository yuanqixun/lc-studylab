#!/usr/bin/env python3
"""
天气查询工具测试脚本

用于验证高德天气 API 集成是否正常工作
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core.tools.weather import get_weather, get_weather_forecast
from config import setup_logging, get_logger

# 初始化日志
setup_logging()
logger = get_logger(__name__)


def test_weather_tools():
    """
    测试天气查询工具
    """
    logger.info("=== 开始测试天气查询工具 ===")
    
    # 检查 API Key
    amap_key = os.getenv("AMAP_KEY")
    if not amap_key:
        logger.error("❌ AMAP_KEY 未设置！")
        logger.info("请在 .env 文件中设置 AMAP_KEY")
        logger.info("获取 API Key: https://console.amap.com/")
        return
    
    logger.info(f"✅ 检测到高德 API Key: {amap_key[:8]}...")
    
    # 测试城市列表
    test_cities = [
        ("北京", "110000"),  # 使用城市名称
        ("上海", "310000"),  # 使用城市名称
        ("110101", None),    # 使用 adcode（北京东城区）
        ("深圳", "440300"),  # 使用城市名称
    ]
    
    # 1. 测试实况天气查询
    logger.info("\n" + "="*50)
    logger.info("1️⃣ 测试实况天气查询（extensions=base）")
    logger.info("="*50)
    
    for city, _ in test_cities[:2]:  # 只测试前两个城市
        logger.info(f"\n🌤️ 查询 {city} 的实况天气...")
        try:
            result = get_weather.invoke({"city": city, "extensions": "base"})
            logger.info(f"✅ 查询成功:")
            print(result)
            print()
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}", exc_info=True)
    
    # 2. 测试天气预报查询
    logger.info("\n" + "="*50)
    logger.info("2️⃣ 测试天气预报查询（extensions=all）")
    logger.info("="*50)
    
    for city, _ in test_cities[2:]:  # 测试后两个城市
        logger.info(f"\n🌤️ 查询 {city} 的天气预报...")
        try:
            result = get_weather.invoke({"city": city, "extensions": "all"})
            logger.info(f"✅ 查询成功:")
            print(result)
            print()
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}", exc_info=True)
    
    # 3. 测试便捷的预报函数
    logger.info("\n" + "="*50)
    logger.info("3️⃣ 测试便捷的天气预报函数")
    logger.info("="*50)
    
    logger.info(f"\n🌤️ 使用 get_weather_forecast 查询广州天气...")
    try:
        result = get_weather_forecast.invoke({"city": "广州"})
        logger.info(f"✅ 查询成功:")
        print(result)
        print()
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}", exc_info=True)
    
    # 4. 测试错误处理
    logger.info("\n" + "="*50)
    logger.info("4️⃣ 测试错误处理（无效城市）")
    logger.info("="*50)
    
    logger.info(f"\n🌤️ 查询无效城市...")
    try:
        result = get_weather.invoke({"city": "999999", "extensions": "base"})
        logger.info(f"返回结果:")
        print(result)
        print()
    except Exception as e:
        logger.error(f"捕获到异常: {e}", exc_info=True)
    
    logger.info("\n" + "="*50)
    logger.info("=== 天气查询工具测试完成 ===")
    logger.info("="*50)


if __name__ == "__main__":
    test_weather_tools()

