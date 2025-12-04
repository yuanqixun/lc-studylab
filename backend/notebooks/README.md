# LC-StudyLab Backend 学习 Notebooks

欢迎使用 LC-StudyLab Backend 学习 Notebooks！本系列 Jupyter Notebook 将帮助你系统地学习和掌握基于 LangChain 1.0.3 构建的智能学习助手系统。

## 📚 Notebook 列表

### 00. 总览
**文件**: `00_overview.ipynb`  
**内容**: 项目总览、学习路线图、快速开始指南

### 第 1 阶段：基础 Agent + 工具调用
**文件**: `stage_01_basic_agent.ipynb`  
**学习内容**:
- 配置加载与验证
- LLM 模型创建与调用
- 工具集成（时间、计算器、网络搜索）
- Agent 基本功能（同步/异步、流式输出）
- 不同模式的 Agent
- 对话历史管理

### 第 2 阶段：RAG 知识库 + 文档问答
**文件**: `stage_02_rag.ipynb`  
**学习内容**:
- 文档加载（PDF、Markdown、HTML）
- 文本分块策略
- Embedding 向量化
- 向量存储与索引管理
- 文档检索
- RAG Agent 问答
- 引用来源追踪

### 第 3 阶段：LangGraph 工作流 + 人机交互
**文件**: `stage_03_workflow.ipynb`  
**学习内容**:
- LangGraph 有状态工作流
- 学习工作流（规划→检索→出题→评分→反馈）
- 检查点（Checkpoint）机制
- 状态持久化与恢复
- 人机交互（Human-in-the-Loop）
- 工作流状态管理
- 流式输出工作流进度

### 第 4 阶段：DeepAgents 深度研究
**文件**: `stage_04_deep_research.ipynb`  
**学习内容**:
- DeepAgent 架构
- 多代理协作
- 网络搜索集成
- 文档分析集成
- 文件系统管理
- 研究报告生成

### 第 5 阶段：Guardrails 安全防护
**文件**: `stage_05_guardrails.ipynb`  
**学习内容**:
- 输入验证
- 输出验证
- 内容过滤
- Prompt Injection 检测
- 结构化输出（Pydantic Schema）
- 安全中间件

## 🚀 快速开始

### 1. 环境准备

确保你已经安装了项目依赖：

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置设置

复制并编辑配置文件：

```bash
cp env.example .env
# 编辑 .env 文件，设置 OPENAI_API_KEY
```

必需配置：
- `OPENAI_API_KEY` - OpenAI API 密钥（必需）

可选配置：
- `TAVILY_API_KEY` - Tavily 搜索 API 密钥（第 4 阶段需要）
- `AMAP_KEY` - 高德地图 API 密钥（天气查询功能）

### 3. 启动 Jupyter

```bash
# 在 backend 目录下启动
jupyter notebook notebooks/

# 或使用 JupyterLab
jupyter lab notebooks/
```

### 4. 开始学习

建议从 `00_overview.ipynb` 开始，然后按顺序学习各阶段的 Notebook。

## 📖 学习建议

### 推荐学习顺序

1. **按顺序学习**: 从第 1 阶段开始，逐步深入
2. **动手实践**: 运行每个 cell，观察输出结果
3. **修改参数**: 尝试修改参数，观察行为变化
4. **查看源码**: 配合源码阅读，理解实现细节
5. **参考文档**: 查看 `LEARNING_GUIDE.md` 获取更多信息

### 学习时间估算

- **第 1 阶段**: 2-3 小时
- **第 2 阶段**: 3-4 小时
- **第 3 阶段**: 4-5 小时
- **第 4 阶段**: 3-4 小时
- **第 5 阶段**: 2-3 小时

**总计**: 约 14-19 小时

### 前置知识要求

- ✅ Python 基础（必需）
- ✅ 异步编程基础（推荐）
- ✅ 机器学习基础概念（推荐）
- ✅ REST API 基础（可选）

## 🔧 常见问题

### Q: 运行 Notebook 时找不到模块？

**A**: 确保在 backend 目录下启动 Jupyter，或者在 Notebook 中正确设置了 Python 路径。每个 Notebook 的第一个 cell 都会自动添加项目路径。

### Q: 提示 API Key 未配置？

**A**: 检查 `.env` 文件是否存在且包含有效的 `OPENAI_API_KEY`。

### Q: 网络搜索功能不可用？

**A**: 网络搜索需要配置 `TAVILY_API_KEY`。如果没有，可以跳过相关测试。

### Q: RAG 功能提示索引不存在？

**A**: 需要先构建索引。可以运行：
```bash
python scripts/update_index.py --collection test_index --path data/documents/test
```

## 📚 相关资源

### 官方文档
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)

### 项目文档
- `../LEARNING_GUIDE.md` - 详细学习指南
- `../README.md` - 项目总览
- `../docs/` - 各阶段详细文档

### 测试脚本
- `../scripts/test_basic.py` - 基础功能测试
- `../scripts/test_rag_query.py` - RAG 测试
- `../scripts/test_workflow.py` - 工作流测试
- `../scripts/test_deep_research.py` - 深度研究测试
- `../scripts/test_guardrails.py` - 安全防护测试

## 🤝 贡献

如果你发现 Notebook 中的问题或有改进建议，欢迎提交 Issue 或 Pull Request。

## 📝 许可

本项目遵循项目主许可证。

---

**祝学习愉快！🚀**

如有问题，请查看 `LEARNING_GUIDE.md` 或提交 Issue。
