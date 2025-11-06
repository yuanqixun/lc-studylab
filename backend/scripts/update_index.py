#!/usr/bin/env python3
"""
智能索引更新脚本

功能：
1. 检测文档目录中的新文档
2. 只处理新增的文档（避免重复）
3. 自动分块和向量化
4. 更新索引并保存

使用方法：
    # 基本用法（推荐）- 只添加新文档
    python scripts/update_index.py test_index data/documents/test
    
    # 强制重建整个索引
    python scripts/update_index.py test_index data/documents/test --rebuild
    
    # 查看帮助
    python scripts/update_index.py --help

示例：
    # 1. 添加新文档到目录
    cp new_doc.md data/documents/test/
    
    # 2. 更新索引
    python scripts/update_index.py test_index data/documents/test
    
    # 3. 查询验证
    python scripts/rag_cli.py query test_index "新文档的内容"

注意事项：
    - 脚本会自动跟踪已索引的文档
    - 只有新文档会被处理（节省时间和成本）
    - 使用 --rebuild 可以强制重建整个索引
    - 建议定期备份索引数据
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Set, List

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from rag import (
    IndexManager,
    load_directory,
    load_document,
    split_documents,
    get_embeddings,
    get_supported_extensions,
)


class SmartIndexUpdater:
    """智能索引更新器"""
    
    def __init__(self, index_name: str, document_dir: str):
        self.index_name = index_name
        self.document_dir = Path(document_dir)
        self.manager = IndexManager()
        self.tracking_file = self.manager.base_path / index_name / "tracked_files.json"
        
    def get_tracked_files(self) -> Set[str]:
        """获取已跟踪的文件列表"""
        if not self.tracking_file.exists():
            return set()
        
        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('files', []))
        except Exception as e:
            print(f"⚠️  读取跟踪文件失败: {e}")
            return set()
    
    def save_tracked_files(self, files: Set[str]):
        """保存已跟踪的文件列表"""
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'files': sorted(list(files)),
            'last_updated': datetime.now().isoformat(),
            'total_files': len(files),
        }
        
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_all_document_files(self) -> Set[str]:
        """获取目录中所有支持的文档文件"""
        if not self.document_dir.exists():
            raise FileNotFoundError(f"文档目录不存在: {self.document_dir}")
        
        supported_exts = get_supported_extensions()
        all_files = set()
        
        for ext in supported_exts.keys():
            files = self.document_dir.glob(f"**/*{ext}")
            all_files.update(str(f.relative_to(self.document_dir)) for f in files)
        
        return all_files
    
    def find_new_files(self) -> List[str]:
        """查找新增的文档文件"""
        tracked = self.get_tracked_files()
        current = self.get_all_document_files()
        new_files = current - tracked
        return sorted(list(new_files))
    
    def update_index(self, rebuild: bool = False):
        """更新索引"""
        print("\n" + "="*60)
        print("📚 智能索引更新工具")
        print("="*60)
        print(f"索引名称: {self.index_name}")
        print(f"文档目录: {self.document_dir}")
        print(f"模式: {'重建' if rebuild else '增量更新'}")
        print("="*60 + "\n")
        
        # 检查索引是否存在
        if not self.manager.index_exists(self.index_name):
            print(f"❌ 索引不存在: {self.index_name}")
            print(f"\n💡 提示: 请先创建索引:")
            print(f"   python scripts/rag_cli.py index create {self.index_name} {self.document_dir}")
            return False
        
        if rebuild:
            # 重建模式：处理所有文档
            print("🔄 重建模式：处理所有文档...\n")
            return self._rebuild_index()
        else:
            # 增量模式：只处理新文档
            print("➕ 增量模式：只处理新文档...\n")
            return self._incremental_update()
    
    def _rebuild_index(self) -> bool:
        """重建整个索引"""
        try:
            # 1. 加载所有文档
            print("1️⃣  加载所有文档...")
            documents = load_directory(str(self.document_dir), show_progress=True)
            
            if not documents:
                print("⚠️  没有找到文档")
                return False
            
            print(f"✅ 加载了 {len(documents)} 个文档\n")
            
            # 2. 分块
            print("2️⃣  分块文档...")
            chunks = split_documents(documents)
            print(f"✅ 生成了 {len(chunks)} 个文本块\n")
            
            # 3. 创建 embeddings
            print("3️⃣  创建 embeddings...")
            embeddings = get_embeddings()
            print("✅ Embeddings 准备完成\n")
            
            # 4. 重建索引（覆盖）
            print("4️⃣  重建索引...")
            self.manager.create_index(
                name=self.index_name,
                documents=chunks,
                embeddings=embeddings,
                description=f"重建于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                overwrite=True,
            )
            print("✅ 索引重建成功\n")
            
            # 5. 更新跟踪文件
            all_files = self.get_all_document_files()
            self.save_tracked_files(all_files)
            print(f"📝 已跟踪 {len(all_files)} 个文件\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 重建索引失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _incremental_update(self) -> bool:
        """增量更新索引"""
        try:
            # 1. 查找新文档
            print("1️⃣  检测新文档...")
            new_files = self.find_new_files()
            
            if not new_files:
                print("✅ 没有新文档需要添加")
                print("\n💡 提示:")
                print("   - 所有文档都已索引")
                print("   - 如果要重建索引，使用: --rebuild")
                return True
            
            print(f"📄 发现 {len(new_files)} 个新文档:")
            for i, file in enumerate(new_files, 1):
                print(f"   {i}. {file}")
            print()
            
            # 2. 加载新文档
            print("2️⃣  加载新文档...")
            documents = []
            success_count = 0
            
            for file in new_files:
                file_path = self.document_dir / file
                try:
                    docs = load_document(str(file_path))
                    documents.extend(docs)
                    success_count += 1
                except Exception as e:
                    print(f"   ⚠️  加载失败: {file} - {e}")
            
            if not documents:
                print("❌ 没有成功加载任何文档")
                return False
            
            print(f"✅ 成功加载 {success_count}/{len(new_files)} 个文档\n")
            
            # 3. 分块
            print("3️⃣  分块文档...")
            chunks = split_documents(documents)
            print(f"✅ 生成了 {len(chunks)} 个文本块\n")
            
            # 4. 创建 embeddings
            print("4️⃣  创建 embeddings...")
            embeddings = get_embeddings()
            print("✅ Embeddings 准备完成\n")
            
            # 5. 更新索引
            print("5️⃣  更新索引...")
            self.manager.update_index(self.index_name, chunks, embeddings)
            print("✅ 索引更新成功\n")
            
            # 6. 更新跟踪文件
            tracked = self.get_tracked_files()
            tracked.update(new_files)
            self.save_tracked_files(tracked)
            print(f"📝 已跟踪 {len(tracked)} 个文件（新增 {len(new_files)} 个）\n")
            
            # 7. 显示索引信息
            info = self.manager.get_index_info(self.index_name)
            if info:
                print("📊 索引统计:")
                print(f"   总文档数: {info.get('num_documents', 'N/A')}")
                print(f"   更新时间: {info.get('updated_at', 'N/A')}")
                if 'size_mb' in info:
                    print(f"   索引大小: {info['size_mb']:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 更新索引失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def show_help():
    """显示帮助信息"""
    help_text = """
智能索引更新工具 - 使用说明

基本用法：
    python scripts/update_index.py <索引名> <文档目录> [选项]

参数说明：
    索引名        已存在的索引名称（如: test_index）
    文档目录      文档所在目录（如: data/documents/test）
    
选项：
    --rebuild    强制重建整个索引（处理所有文档）
    --help       显示此帮助信息

使用示例：

    1. 增量更新（推荐）- 只添加新文档
       python scripts/update_index.py test_index data/documents/test
    
    2. 强制重建 - 重新处理所有文档
       python scripts/update_index.py test_index data/documents/test --rebuild
    
    3. 查看索引列表
       python scripts/rag_cli.py index list
    
    4. 查看索引信息
       python scripts/rag_cli.py index info test_index

工作流程：

    步骤 1: 添加新文档
        cp new_document.md data/documents/test/
    
    步骤 2: 更新索引
        python scripts/update_index.py test_index data/documents/test
    
    步骤 3: 验证查询
        python scripts/rag_cli.py query test_index "新文档的内容"

注意事项：

    ✅ 增量更新模式：
       - 自动检测新文档
       - 只处理未索引的文档
       - 节省时间和 API 成本
       - 适合日常使用
    
    ⚠️  重建模式：
       - 重新处理所有文档
       - 耗时较长，成本较高
       - 适合索引损坏或需要完全重建时使用
    
    📝 跟踪文件：
       - 位置: data/indexes/<索引名>/tracked_files.json
       - 记录已索引的文档列表
       - 自动维护，无需手动编辑

更多信息：
    查看完整文档: docs/stage_02/README.md
"""
    print(help_text)


def main():
    """主函数"""
    # 检查帮助
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return 0
    
    # 检查参数
    if len(sys.argv) < 3:
        print("❌ 参数不足\n")
        print("用法: python scripts/update_index.py <索引名> <文档目录> [--rebuild]")
        print("示例: python scripts/update_index.py test_index data/documents/test")
        print("\n使用 --help 查看详细帮助")
        return 1
    
    index_name = sys.argv[1]
    directory = sys.argv[2]
    rebuild = '--rebuild' in sys.argv
    
    # 执行更新
    updater = SmartIndexUpdater(index_name, directory)
    success = updater.update_index(rebuild=rebuild)
    
    if success:
        print("\n" + "="*60)
        print("✅ 更新完成！")
        print("="*60)
        print("\n💡 下一步:")
        print(f"   python scripts/rag_cli.py query {index_name} \"你的问题\"")
        print(f"   python scripts/rag_cli.py interactive {index_name}")
        print()
        return 0
    else:
        print("\n" + "="*60)
        print("❌ 更新失败")
        print("="*60)
        print("\n💡 请检查:")
        print("   1. 索引是否存在")
        print("   2. 文档目录是否正确")
        print("   3. 文档格式是否支持")
        print("   4. 查看详细错误信息")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())