#!/usr/bin/env python3
"""
测试增强的流式输出
验证后端 SSE 输出包含所有必要的元数据
"""

import asyncio
import json
import sys
import httpx
from typing import Dict, Any

# 添加父目录到路径
sys.path.insert(0, '/Users/longyang/development/python-workspace/lc-studylab/backend')


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


async def test_basic_chat():
    """测试基础对话（无工具）"""
    print(f"\n{Colors.HEADER}=== 测试1: 基础对话 ==={Colors.ENDC}")
    
    request = {
        "message": "你好，请简单介绍一下自己",
        "mode": "default",
        "use_tools": False,
    }
    
    chunks_received = {
        'start': 0,
        'chunk': 0,
        'context': 0,
        'end': 0,
    }
    
    content_buffer = ""
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:8000/chat/stream",
                json=request,
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        chunk_type = data.get('type')
                        
                        if chunk_type in chunks_received:
                            chunks_received[chunk_type] += 1
                        
                        if chunk_type == 'start':
                            print(f"{Colors.OKGREEN}✓ 收到开始事件{Colors.ENDC}")
                        
                        elif chunk_type == 'chunk':
                            content = data.get('content', '')
                            content_buffer += content
                            print(content, end='', flush=True)
                        
                        elif chunk_type == 'context':
                            print(f"\n{Colors.OKCYAN}✓ 收到 Context 数据:{Colors.ENDC}")
                            context_data = data.get('data', {})
                            print(f"  - 使用 Token: {context_data.get('usedTokens')}/{context_data.get('maxTokens')}")
                            print(f"  - 模型: {context_data.get('modelId')}")
                            print(f"  - 使用率: {context_data.get('percentage', 0)*100:.2f}%")
                        
                        elif chunk_type == 'end':
                            print(f"\n{Colors.OKGREEN}✓ 收到结束事件{Colors.ENDC}")
        
        except Exception as e:
            print(f"\n{Colors.FAIL}✗ 错误: {e}{Colors.ENDC}")
            return False
    
    # 验证
    print(f"\n{Colors.BOLD}统计:{Colors.ENDC}")
    for chunk_type, count in chunks_received.items():
        print(f"  - {chunk_type}: {count}")
    
    success = (
        chunks_received['start'] > 0 and
        chunks_received['chunk'] > 0 and
        chunks_received['context'] > 0 and
        chunks_received['end'] > 0 and
        len(content_buffer) > 0
    )
    
    if success:
        print(f"{Colors.OKGREEN}✓ 测试通过{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ 测试失败{Colors.ENDC}")
    
    return success


async def test_tool_calling():
    """测试工具调用"""
    print(f"\n{Colors.HEADER}=== 测试2: 工具调用 ==={Colors.ENDC}")
    
    request = {
        "message": "现在几点？",
        "mode": "default",
        "use_tools": True,
    }
    
    tool_calls = []
    tool_results = []
    content_buffer = ""
    has_context = False
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:8000/chat/stream",
                json=request,
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        chunk_type = data.get('type')
                        
                        if chunk_type == 'start':
                            print(f"{Colors.OKGREEN}✓ 开始生成{Colors.ENDC}")
                        
                        elif chunk_type == 'chunk':
                            content = data.get('content', '')
                            content_buffer += content
                            print(content, end='', flush=True)
                        
                        elif chunk_type == 'tool':
                            tool_data = data.get('data', {})
                            tool_calls.append(tool_data)
                            print(f"\n{Colors.OKBLUE}🔧 工具调用:{Colors.ENDC}")
                            print(f"  - 名称: {tool_data.get('name')}")
                            print(f"  - 状态: {tool_data.get('state')}")
                            print(f"  - 参数: {json.dumps(tool_data.get('parameters', {}), ensure_ascii=False)}")
                        
                        elif chunk_type == 'tool_result':
                            result_data = data.get('data', {})
                            tool_results.append(result_data)
                            print(f"\n{Colors.OKBLUE}✓ 工具结果:{Colors.ENDC}")
                            print(f"  - 状态: {result_data.get('state')}")
                            result = result_data.get('result', '')
                            if isinstance(result, str):
                                print(f"  - 结果: {result[:100]}...")
                            else:
                                print(f"  - 结果: {result}")
                        
                        elif chunk_type == 'reasoning':
                            print(f"\n{Colors.OKCYAN}💭 推理过程:{Colors.ENDC}")
                            reasoning_data = data.get('data', {})
                            print(f"  - 内容: {reasoning_data.get('content', '')[:100]}...")
                            print(f"  - 耗时: {reasoning_data.get('duration', 0)}秒")
                        
                        elif chunk_type == 'context':
                            has_context = True
                            context_data = data.get('data', {})
                            print(f"\n{Colors.OKCYAN}📊 Context:{Colors.ENDC}")
                            print(f"  - Token使用: {context_data.get('usedTokens')}/{context_data.get('maxTokens')}")
                        
                        elif chunk_type == 'end':
                            print(f"\n{Colors.OKGREEN}✓ 生成完成{Colors.ENDC}")
        
        except Exception as e:
            print(f"\n{Colors.FAIL}✗ 错误: {e}{Colors.ENDC}")
            return False
    
    # 验证
    print(f"\n{Colors.BOLD}统计:{Colors.ENDC}")
    print(f"  - 工具调用: {len(tool_calls)}")
    print(f"  - 工具结果: {len(tool_results)}")
    print(f"  - 生成内容: {len(content_buffer)} 字符")
    print(f"  - Context信息: {'是' if has_context else '否'}")
    
    success = (
        len(tool_calls) > 0 and
        len(tool_results) > 0 and
        len(content_buffer) > 0 and
        has_context
    )
    
    if success:
        print(f"{Colors.OKGREEN}✓ 测试通过{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ 测试失败{Colors.ENDC}")
    
    return success


async def test_multiple_tools():
    """测试多工具调用"""
    print(f"\n{Colors.HEADER}=== 测试3: 多工具调用 ==={Colors.ENDC}")
    
    request = {
        "message": "现在几点？帮我计算 123 + 456",
        "mode": "default",
        "use_tools": True,
    }
    
    tool_calls = []
    tool_results = []
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:8000/chat/stream",
                json=request,
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        chunk_type = data.get('type')
                        
                        if chunk_type == 'chunk':
                            print(data.get('content', ''), end='', flush=True)
                        
                        elif chunk_type == 'tool':
                            tool_data = data.get('data', {})
                            tool_calls.append(tool_data)
                            print(f"\n{Colors.OKBLUE}🔧 [{len(tool_calls)}] {tool_data.get('name')}{Colors.ENDC}")
                        
                        elif chunk_type == 'tool_result':
                            result_data = data.get('data', {})
                            tool_results.append(result_data)
                            print(f"{Colors.OKBLUE}✓ [{len(tool_results)}] 完成{Colors.ENDC}")
        
        except Exception as e:
            print(f"\n{Colors.FAIL}✗ 错误: {e}{Colors.ENDC}")
            return False
    
    # 验证
    print(f"\n{Colors.BOLD}统计:{Colors.ENDC}")
    print(f"  - 工具调用: {len(tool_calls)}")
    print(f"  - 工具结果: {len(tool_results)}")
    
    # 列出工具
    if tool_calls:
        print(f"\n{Colors.BOLD}工具列表:{Colors.ENDC}")
        for idx, tool in enumerate(tool_calls, 1):
            print(f"  {idx}. {tool.get('name')}")
    
    success = len(tool_calls) >= 2 and len(tool_results) >= 2
    
    if success:
        print(f"{Colors.OKGREEN}✓ 测试通过{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ 测试失败 (期望至少2个工具调用){Colors.ENDC}")
    
    return success


async def main():
    """运行所有测试"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("增强流式输出测试")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    
    tests = [
        ("基础对话", test_basic_chat),
        ("工具调用", test_tool_calling),
        ("多工具调用", test_multiple_tools),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}测试中断{Colors.ENDC}")
            break
        except Exception as e:
            print(f"\n{Colors.FAIL}测试异常: {e}{Colors.ENDC}")
            results.append((name, False))
        
        # 等待一下，避免请求太快
        await asyncio.sleep(1)
    
    # 总结
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.OKGREEN}✓ 通过{Colors.ENDC}" if result else f"{Colors.FAIL}✗ 失败{Colors.ENDC}"
        print(f"  {name}: {status}")
    
    print(f"\n{Colors.BOLD}总计: {passed}/{total} 通过{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.OKGREEN}🎉 所有测试通过!{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}❌ 部分测试失败{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

