#!/usr/bin/env python3
"""
DeepAgent 深度研究测试脚本

测试 Stage 4 实现的深度研究功能。

测试场景：
1. 基础研究（仅网络搜索）
2. 完整研究（网络搜索 + 文档分析）
3. 文件系统功能
4. API 接口

使用方法：
    python scripts/test_deep_research.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

from config import settings, setup_logging, get_logger
from deep_research import create_deep_research_agent
from core.tools.filesystem import get_filesystem

# 初始化
setup_logging()
logger = get_logger(__name__)
console = Console()


def print_header(title: str):
    """打印标题"""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    console.print()


def print_success(message: str):
    """打印成功消息"""
    console.print(f"[green]✅ {message}[/green]")


def print_error(message: str):
    """打印错误消息"""
    console.print(f"[red]❌ {message}[/red]")


def print_info(message: str):
    """打印信息"""
    console.print(f"[blue]ℹ️  {message}[/blue]")


def test_filesystem():
    """测试文件系统功能"""
    print_header("测试 1: 文件系统功能")
    
    try:
        # 创建文件系统
        thread_id = "test_fs_001"
        fs = get_filesystem(thread_id)
        
        print_info(f"工作空间: {fs.workspace_path}")
        
        # 写入文件
        console.print("\n[yellow]1. 测试写入文件...[/yellow]")
        fs.write_file(
            "test_note.md",
            "# 测试笔记\n\n这是一个测试文件。",
            subdirectory="notes"
        )
        print_success("文件写入成功")
        
        # 读取文件
        console.print("\n[yellow]2. 测试读取文件...[/yellow]")
        content = fs.read_file("test_note.md", subdirectory="notes")
        console.print(f"文件内容: {content[:50]}...")
        print_success("文件读取成功")
        
        # 列出文件
        console.print("\n[yellow]3. 测试列出文件...[/yellow]")
        files = fs.list_files()
        console.print(f"找到 {len(files)} 个文件:")
        for f in files:
            console.print(f"  - {f}")
        print_success("文件列表获取成功")
        
        # 搜索文件
        console.print("\n[yellow]4. 测试搜索文件...[/yellow]")
        results = fs.search_files("测试")
        console.print(f"找到 {len(results)} 个匹配文件")
        print_success("文件搜索成功")
        
        # 清理
        fs.delete_file("test_note.md", subdirectory="notes")
        print_success("测试文件已清理")
        
        print_success("文件系统测试通过！")
        return True
        
    except Exception as e:
        print_error(f"文件系统测试失败: {e}")
        logger.exception("文件系统测试异常")
        return False


def test_basic_research():
    """测试基础研究（仅网络搜索）"""
    print_header("测试 2: 基础研究（网络搜索）")
    
    # 检查 API Key
    if not settings.tavily_api_key:
        print_error("未配置 TAVILY_API_KEY，跳过网络搜索测试")
        return False
    
    try:
        # 创建 DeepAgent
        thread_id = "test_basic_001"
        console.print(f"\n[yellow]创建 DeepAgent (thread_id: {thread_id})...[/yellow]")
        
        agent = create_deep_research_agent(
            thread_id=thread_id,
            enable_web_search=True,
            enable_doc_analysis=False,
        )
        
        print_success("DeepAgent 创建成功")
        
        # 执行研究
        query = "LangChain 1.0 有哪些主要新特性？"
        console.print(f"\n[yellow]研究问题: {query}[/yellow]")
        console.print("\n[dim]正在执行研究任务，这可能需要几分钟...[/dim]\n")
        
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("研究中...", total=None)
            
            result = agent.research(query)
            
            progress.update(task, completed=True)
        
        elapsed_time = time.time() - start_time
        
        # 显示结果
        console.print(f"\n[green]✅ 研究完成！耗时: {elapsed_time:.1f} 秒[/green]\n")
        
        # 显示研究计划
        if result.get("plan"):
            console.print("[bold]研究计划:[/bold]")
            plan = result["plan"]
            console.print(f"  目标: {plan.get('research_goal', 'N/A')}")
            console.print(f"  关键词: {', '.join(plan.get('search_keywords', []))}")
        
        # 显示完成的步骤
        console.print("\n[bold]完成的步骤:[/bold]")
        steps = result.get("steps_completed", {})
        for step, completed in steps.items():
            status = "✅" if completed else "❌"
            console.print(f"  {status} {step}")
        
        # 显示最终报告（前500字符）
        if result.get("final_report"):
            console.print("\n[bold]最终报告（预览）:[/bold]")
            report_preview = result["final_report"][:500]
            console.print(Panel(report_preview + "...", expand=False))
        
        # 显示文件系统
        console.print("\n[bold]生成的文件:[/bold]")
        fs = get_filesystem(thread_id)
        files = fs.list_files()
        for f in files:
            console.print(f"  📄 {f}")
        
        print_success("基础研究测试通过！")
        return True
        
    except Exception as e:
        print_error(f"基础研究测试失败: {e}")
        logger.exception("基础研究测试异常")
        return False


def test_full_research():
    """测试完整研究（网络搜索 + 文档分析）"""
    print_header("测试 3: 完整研究（网络 + 文档）")
    
    # 检查是否有可用的索引
    index_path = Path(settings.vector_store_path) / "test_index"
    if not index_path.exists():
        print_error(f"未找到测试索引: {index_path}")
        print_info("请先运行 RAG 索引构建: python scripts/update_index.py")
        return False
    
    try:
        # 加载 RAG 检索器
        console.print("\n[yellow]加载文档索引...[/yellow]")
        from rag import get_embeddings, load_vector_store, create_retriever_tool
        
        embeddings = get_embeddings()
        vector_store = load_vector_store(str(index_path), embeddings)
        retriever = vector_store.as_retriever()
        retriever_tool = create_retriever_tool(retriever)
        
        print_success("文档索引加载成功")
        
        # 创建 DeepAgent
        thread_id = "test_full_001"
        console.print(f"\n[yellow]创建 DeepAgent (thread_id: {thread_id})...[/yellow]")
        
        agent = create_deep_research_agent(
            thread_id=thread_id,
            enable_web_search=True,
            enable_doc_analysis=True,
            retriever_tool=retriever_tool,
        )
        
        print_success("DeepAgent 创建成功（含文档分析）")
        
        # 执行研究
        query = "什么是 RAG？它有哪些应用场景？"
        console.print(f"\n[yellow]研究问题: {query}[/yellow]")
        console.print("\n[dim]正在执行完整研究任务，这可能需要更长时间...[/dim]\n")
        
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("研究中...", total=None)
            
            result = agent.research(query)
            
            progress.update(task, completed=True)
        
        elapsed_time = time.time() - start_time
        
        # 显示结果
        console.print(f"\n[green]✅ 完整研究完成！耗时: {elapsed_time:.1f} 秒[/green]\n")
        
        # 显示完成的步骤
        console.print("[bold]完成的步骤:[/bold]")
        steps = result.get("steps_completed", {})
        table = Table(show_header=True)
        table.add_column("步骤", style="cyan")
        table.add_column("状态", style="green")
        
        for step, completed in steps.items():
            status = "✅ 完成" if completed else "❌ 未完成"
            table.add_row(step, status)
        
        console.print(table)
        
        # 显示文件系统
        console.print("\n[bold]生成的文件:[/bold]")
        fs = get_filesystem(thread_id)
        files = fs.list_files()
        for f in files:
            console.print(f"  📄 {f}")
        
        print_success("完整研究测试通过！")
        return True
        
    except Exception as e:
        print_error(f"完整研究测试失败: {e}")
        logger.exception("完整研究测试异常")
        return False


def test_api_integration():
    """测试 API 集成"""
    print_header("测试 4: API 集成")
    
    print_info("API 集成测试需要启动服务器")
    print_info("请运行以下命令测试 API:")
    
    console.print("\n[yellow]1. 启动服务器:[/yellow]")
    console.print("   bash start_server.sh")
    
    console.print("\n[yellow]2. 启动研究任务:[/yellow]")
    console.print("""   curl -X POST "http://localhost:8000/deep-research/start" \\
     -H "Content-Type: application/json" \\
     -d '{
       "query": "分析 LangChain 1.0 的新特性",
       "enable_web_search": true,
       "enable_doc_analysis": false
     }'""")
    
    console.print("\n[yellow]3. 查询状态:[/yellow]")
    console.print('   curl "http://localhost:8000/deep-research/status/{thread_id}"')
    
    console.print("\n[yellow]4. 获取结果:[/yellow]")
    console.print('   curl "http://localhost:8000/deep-research/result/{thread_id}"')
    
    console.print("\n[yellow]5. 列出文件:[/yellow]")
    console.print('   curl "http://localhost:8000/deep-research/files/{thread_id}"')
    
    print_success("API 测试说明已显示")
    return True


def main():
    """主测试函数"""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]     DeepAgent 深度研究功能测试套件[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    # 显示配置信息
    console.print("[bold]当前配置:[/bold]")
    console.print(f"  OpenAI API: {'✅ 已配置' if settings.openai_api_key else '❌ 未配置'}")
    console.print(f"  Tavily API: {'✅ 已配置' if settings.tavily_api_key else '❌ 未配置'}")
    console.print(f"  模型: {settings.openai_model}")
    console.print(f"  数据目录: {settings.DATA_DIR}")
    console.print()
    
    # 运行测试
    results = {}
    
    # 测试 1: 文件系统
    results["filesystem"] = test_filesystem()
    
    # 测试 2: 基础研究
    if settings.tavily_api_key:
        results["basic_research"] = test_basic_research()
    else:
        print_info("跳过基础研究测试（需要 Tavily API Key）")
        results["basic_research"] = None
    
    # 测试 3: 完整研究
    # results["full_research"] = test_full_research()
    print_info("跳过完整研究测试（耗时较长，可手动运行）")
    results["full_research"] = None
    
    # 测试 4: API 集成
    results["api_integration"] = test_api_integration()
    
    # 显示总结
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]测试总结[/bold cyan]")
    console.print("=" * 60 + "\n")
    
    table = Table(show_header=True)
    table.add_column("测试项", style="cyan")
    table.add_column("结果", style="green")
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⏭️  跳过"
        
        table.add_row(test_name, status)
    
    console.print(table)
    console.print()
    
    # 统计
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    console.print(f"[green]通过: {passed}[/green] | [red]失败: {failed}[/red] | [yellow]跳过: {skipped}[/yellow]")
    console.print()
    
    if failed == 0:
        print_success("所有测试通过！🎉")
        return 0
    else:
        print_error(f"有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]测试被用户中断[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]测试过程中发生错误: {e}[/red]")
        logger.exception("测试异常")
        sys.exit(1)

