#!/usr/bin/env python3
"""
RAG CLI 工具

命令行工具，用于管理 RAG 索引和进行查询。

使用方法：
    # 创建索引
    python scripts/rag_cli.py index create my_docs data/documents/test --description "测试文档"
    
    # 列出索引
    python scripts/rag_cli.py index list
    
    # 查看索引信息
    python scripts/rag_cli.py index info my_docs
    
    # 删除索引
    python scripts/rag_cli.py index delete my_docs
    
    # 查询
    python scripts/rag_cli.py query my_docs "什么是机器学习？"
    
    # 检索（不生成回答）
    python scripts/rag_cli.py search my_docs "机器学习"
    
    # 交互模式
    python scripts/rag_cli.py interactive my_docs
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import setup_logging, get_logger
from rag import (
    IndexManager,
    load_directory,
    split_documents,
    get_embeddings,
    create_retriever,
    create_rag_agent,
    query_rag_agent,
)
from rag.vector_stores import search_vector_store

# 初始化日志
setup_logging()
logger = get_logger(__name__)

# Rich Console
console = Console()


# ==================== 索引管理命令 ====================

@click.group()
def cli():
    """RAG CLI - 命令行 RAG 工具"""
    pass


@cli.group()
def index():
    """索引管理命令"""
    pass


@index.command("create")
@click.argument("name")
@click.argument("directory")
@click.option("--description", "-d", default="", help="索引描述")
@click.option("--chunk-size", type=int, default=None, help="分块大小")
@click.option("--chunk-overlap", type=int, default=None, help="分块重叠")
@click.option("--overwrite", is_flag=True, help="覆盖已存在的索引")
def create_index(name, directory, description, chunk_size, chunk_overlap, overwrite):
    """
    创建新索引
    
    NAME: 索引名称
    DIRECTORY: 文档目录路径
    """
    try:
        console.print(f"\n[bold blue]📝 创建索引: {name}[/bold blue]\n")
        
        # 检查目录
        directory_path = Path(directory)
        if not directory_path.exists():
            console.print(f"[red]❌ 目录不存在: {directory}[/red]")
            sys.exit(1)
        
        # 创建索引管理器
        manager = IndexManager()
        
        # 检查索引是否已存在
        if manager.index_exists(name) and not overwrite:
            console.print(f"[red]❌ 索引已存在: {name}[/red]")
            console.print("[yellow]提示: 使用 --overwrite 来覆盖[/yellow]")
            sys.exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 加载文档
            task = progress.add_task("📂 加载文档...", total=None)
            documents = load_directory(str(directory_path), show_progress=False)
            progress.update(task, description=f"✅ 加载了 {len(documents)} 个文档")
            
            if not documents:
                console.print("[red]❌ 没有找到支持的文档[/red]")
                sys.exit(1)
            
            # 分块
            task = progress.add_task("✂️  分块文档...", total=None)
            chunks = split_documents(
                documents,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            progress.update(task, description=f"✅ 生成了 {len(chunks)} 个文本块")
            
            # 创建 embeddings
            task = progress.add_task("🔢 创建 embeddings...", total=None)
            embeddings = get_embeddings()
            progress.update(task, description="✅ Embeddings 准备完成")
            
            # 创建索引
            task = progress.add_task("🗄️  创建向量索引...", total=None)
            manager.create_index(
                name=name,
                documents=chunks,
                embeddings=embeddings,
                description=description,
                overwrite=overwrite,
            )
            progress.update(task, description="✅ 索引创建完成")
        
        console.print(f"\n[green]✅ 索引创建成功: {name}[/green]\n")
        
        # 显示索引信息
        info = manager.get_index_info(name)
        table = Table(title="索引信息")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("名称", info["name"])
        table.add_row("描述", info["description"])
        table.add_row("文档数", str(info["num_documents"]))
        table.add_row("创建时间", info["created_at"])
        
        console.print(table)
        
    except Exception as e:
        console.print(f"\n[red]❌ 创建索引失败: {e}[/red]\n")
        logger.error(f"创建索引失败: {e}", exc_info=True)
        sys.exit(1)


@index.command("list")
def list_indexes():
    """列出所有索引"""
    try:
        manager = IndexManager()
        indexes = manager.list_indexes()
        
        if not indexes:
            console.print("\n[yellow]没有找到索引[/yellow]\n")
            return
        
        table = Table(title=f"索引列表 ({len(indexes)} 个)")
        table.add_column("名称", style="cyan")
        table.add_column("描述", style="white")
        table.add_column("文档数", style="green")
        table.add_column("创建时间", style="blue")
        
        for idx in indexes:
            table.add_row(
                idx["name"],
                idx["description"] or "N/A",
                str(idx["num_documents"]),
                idx.get("created_at", "N/A"),
            )
        
        console.print("\n")
        console.print(table)
        console.print("\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ 列出索引失败: {e}[/red]\n")
        sys.exit(1)


@index.command("info")
@click.argument("name")
def show_index_info(name):
    """
    显示索引详细信息
    
    NAME: 索引名称
    """
    try:
        manager = IndexManager()
        
        if not manager.index_exists(name):
            console.print(f"\n[red]❌ 索引不存在: {name}[/red]\n")
            sys.exit(1)
        
        info = manager.get_index_info(name)
        
        table = Table(title=f"索引信息: {name}")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("名称", info["name"])
        table.add_row("描述", info["description"])
        table.add_row("文档数", str(info["num_documents"]))
        table.add_row("向量库类型", info.get("store_type", "N/A"))
        table.add_row("Embedding 模型", info.get("embedding_model", "N/A"))
        table.add_row("创建时间", info.get("created_at", "N/A"))
        table.add_row("更新时间", info.get("updated_at", "N/A"))
        table.add_row("路径", info.get("path", "N/A"))
        
        if "size_mb" in info:
            table.add_row("大小", f"{info['size_mb']:.2f} MB")
        
        console.print("\n")
        console.print(table)
        console.print("\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ 获取索引信息失败: {e}[/red]\n")
        sys.exit(1)


@index.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="确定要删除这个索引吗？")
def delete_index(name):
    """
    删除索引
    
    NAME: 索引名称
    """
    try:
        manager = IndexManager()
        
        if not manager.index_exists(name):
            console.print(f"\n[red]❌ 索引不存在: {name}[/red]\n")
            sys.exit(1)
        
        manager.delete_index(name)
        console.print(f"\n[green]✅ 索引已删除: {name}[/green]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ 删除索引失败: {e}[/red]\n")
        sys.exit(1)


# ==================== 查询命令 ====================

@cli.command()
@click.argument("index_name")
@click.argument("query")
@click.option("--k", type=int, default=4, help="返回文档数量")
@click.option("--show-sources", is_flag=True, help="显示来源文档")
def query(index_name, query, k, show_sources):
    """
    RAG 查询
    
    INDEX_NAME: 索引名称
    QUERY: 查询问题
    """
    try:
        console.print(f"\n[bold blue]🔍 查询: {query}[/bold blue]\n")
        
        # 检查索引
        manager = IndexManager()
        if not manager.index_exists(index_name):
            console.print(f"[red]❌ 索引不存在: {index_name}[/red]")
            sys.exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 加载索引
            task = progress.add_task("📂 加载索引...", total=None)
            embeddings = get_embeddings()
            vector_store = manager.load_index(index_name, embeddings)
            progress.update(task, description="✅ 索引加载完成")
            
            # 创建检索器和 Agent
            task = progress.add_task("🤖 创建 RAG Agent...", total=None)
            retriever = create_retriever(vector_store, k=k)
            agent = create_rag_agent(retriever, streaming=False)
            progress.update(task, description="✅ Agent 准备完成")
            
            # 查询
            task = progress.add_task("💭 生成回答...", total=None)
            result = query_rag_agent(agent, query, return_sources=True)
            progress.update(task, description="✅ 回答生成完成")
        
        # 显示回答
        console.print("\n")
        console.print(Panel(
            Markdown(result["answer"]),
            title="[bold green]回答[/bold green]",
            border_style="green",
        ))
        
        # 显示来源
        if show_sources and result.get("sources"):
            console.print("\n[bold cyan]📚 参考来源:[/bold cyan]")
            for i, source in enumerate(result["sources"], 1):
                console.print(f"  {i}. {source}")
        
        console.print("\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ 查询失败: {e}[/red]\n")
        logger.error(f"查询失败: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument("index_name")
@click.argument("query")
@click.option("--k", type=int, default=4, help="返回文档数量")
def search(index_name, query, k):
    """
    纯检索（不生成回答）
    
    INDEX_NAME: 索引名称
    QUERY: 检索查询
    """
    try:
        console.print(f"\n[bold blue]🔍 检索: {query}[/bold blue]\n")
        
        # 检查索引
        manager = IndexManager()
        if not manager.index_exists(index_name):
            console.print(f"[red]❌ 索引不存在: {index_name}[/red]")
            sys.exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 加载索引
            task = progress.add_task("📂 加载索引...", total=None)
            embeddings = get_embeddings()
            vector_store = manager.load_index(index_name, embeddings)
            progress.update(task, description="✅ 索引加载完成")
            
            # 检索
            task = progress.add_task("🔎 检索文档...", total=None)
            results = search_vector_store(vector_store, query, k=k)
            progress.update(task, description=f"✅ 找到 {len(results)} 个文档")
        
        # 显示结果
        console.print(f"\n[bold green]找到 {len(results)} 个相关文档:[/bold green]\n")
        
        for i, (doc, score) in enumerate(results, 1):
            console.print(Panel(
                f"[cyan]相似度:[/cyan] {score:.4f}\n\n{doc.page_content[:300]}...",
                title=f"[bold]文档 {i}[/bold]",
                border_style="blue",
            ))
            
            if doc.metadata:
                console.print(f"[dim]元数据: {doc.metadata}[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[red]❌ 检索失败: {e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.argument("index_name")
def interactive(index_name):
    """
    交互式查询模式
    
    INDEX_NAME: 索引名称
    """
    try:
        # 检查索引
        manager = IndexManager()
        if not manager.index_exists(index_name):
            console.print(f"\n[red]❌ 索引不存在: {index_name}[/red]\n")
            sys.exit(1)
        
        console.print(f"\n[bold green]🤖 RAG 交互模式[/bold green]")
        console.print(f"[cyan]索引: {index_name}[/cyan]")
        console.print("[dim]输入 /quit 或 /exit 退出[/dim]\n")
        
        # 加载索引
        with console.status("[bold green]加载索引..."):
            embeddings = get_embeddings()
            vector_store = manager.load_index(index_name, embeddings)
            retriever = create_retriever(vector_store)
            agent = create_rag_agent(retriever, streaming=False)
        
        console.print("[green]✅ 准备完成，开始提问吧！[/green]\n")
        
        # 交互循环
        while True:
            try:
                # 获取用户输入
                user_input = console.input("[bold blue]你:[/bold blue] ")
                
                if not user_input.strip():
                    continue
                
                # 检查退出命令
                if user_input.strip().lower() in ["/quit", "/exit", "/q"]:
                    console.print("\n[yellow]👋 再见！[/yellow]\n")
                    break
                
                # 查询
                with console.status("[bold green]思考中..."):
                    result = query_rag_agent(agent, user_input, return_sources=True)
                
                # 显示回答
                console.print("\n[bold green]助手:[/bold green]")
                console.print(Markdown(result["answer"]))
                
                # 显示来源
                if result.get("sources"):
                    console.print(f"\n[dim]来源: {', '.join(result['sources'])}[/dim]")
                
                console.print("\n")
                
            except KeyboardInterrupt:
                console.print("\n\n[yellow]👋 再见！[/yellow]\n")
                break
            except Exception as e:
                console.print(f"\n[red]❌ 错误: {e}[/red]\n")
                continue
        
    except Exception as e:
        console.print(f"\n[red]❌ 启动交互模式失败: {e}[/red]\n")
        sys.exit(1)


if __name__ == "__main__":
    cli()

