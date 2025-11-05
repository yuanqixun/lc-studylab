#!/usr/bin/env python3
"""
基础功能测试脚本
用于验证第 1 阶段的核心功能是否正常工作

测试内容：
1. 配置加载
2. 模型创建
3. 工具调用
4. Agent 基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings, get_logger
from core.models import get_chat_model
from core.tools import BASIC_TOOLS, get_current_time, calculator
from agents import create_base_agent

logger = get_logger(__name__)


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置加载")
    print("=" * 60)
    
    try:
        print(f"✅ 应用名称: {settings.app_name}")
        print(f"✅ 版本: {settings.app_version}")
        print(f"✅ 模型: {settings.openai_model}")
        print(f"✅ API Base: {settings.openai_api_base}")
        
        # 验证必需配置
        settings.validate_required_keys()
        print("✅ 配置验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def test_model():
    """测试模型创建"""
    print("\n" + "=" * 60)
    print("测试 2: 模型创建")
    print("=" * 60)
    
    try:
        model = get_chat_model()
        print(f"✅ 模型创建成功: {model.__class__.__name__}")
        print(f"✅ 模型名称: {settings.openai_model}")
        
        return True
    except Exception as e:
        print(f"❌ 模型创建失败: {e}")
        return False


def test_tools():
    """测试工具调用"""
    print("\n" + "=" * 60)
    print("测试 3: 工具调用")
    print("=" * 60)
    
    try:
        # 测试时间工具
        time_result = get_current_time.invoke({})
        print(f"✅ 时间工具: {time_result}")
        
        # 测试计算器工具
        calc_result = calculator.invoke({"expression": "2 + 2"})
        print(f"✅ 计算器工具: {calc_result}")
        
        # 检查工具列表
        print(f"✅ 基础工具数量: {len(BASIC_TOOLS)}")
        
        return True
    except Exception as e:
        print(f"❌ 工具测试失败: {e}")
        return False


def test_agent():
    """测试 Agent 基本功能"""
    print("\n" + "=" * 60)
    print("测试 4: Agent 基本功能")
    print("=" * 60)
    
    try:
        # 创建 Agent
        agent = create_base_agent(streaming=False)
        print("✅ Agent 创建成功")
        
        # 测试简单对话
        print("\n测试对话: '你好'")
        response = agent.invoke("你好，请用一句话介绍自己")
        print(f"✅ Agent 响应: {response[:100]}...")
        
        # 测试工具调用
        print("\n测试工具调用: '现在几点？'")
        response = agent.invoke("现在几点？")
        print(f"✅ Agent 响应: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Agent 测试失败: {e}")
        logger.error(f"Agent 测试错误: {e}", exc_info=True)
        return False


def main():
    """主测试函数"""
    print("\n" + "🧪 " * 20)
    print("LC-StudyLab 第 1 阶段 - 基础功能测试")
    print("🧪 " * 20 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("配置加载", test_config()))
    results.append(("模型创建", test_model()))
    results.append(("工具调用", test_tools()))
    results.append(("Agent 功能", test_agent()))
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！第 1 阶段功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置和日志。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试程序错误: {e}")
        logger.error(f"测试程序错误: {e}", exc_info=True)
        sys.exit(1)

