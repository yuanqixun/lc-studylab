# 📘 LC-StudyLab · LangChain v1.0 × LangGraph × DeepAgents 智能体全家桶

> 🧠 一个涵盖 LangChain v1.0 全核心能力的完整智能体项目，用于学习、研究与快速构建 AI 智能体系统。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-v1.0-green.svg)](https://docs.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-v1.0-orange.svg)](https://docs.langchain.com/oss/python/langgraph/)
[![DeepAgents](https://img.shields.io/badge/DeepAgents-v1.0-purple.svg)](https://docs.langchain.com/oss/python/deep-agents/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## 🚀 项目简介

**LC-StudyLab** 是一个以学习与研究为导向的 LangChain v1.0 全栈示例项目，  
集成了 **LangGraph**、**DeepAgents**、**RAG 检索增强生成**、**Guardrails 安全机制** 与 **流式输出** 等核心特性。

它不仅是一个 “LangChain 学习实验室”，也是一个可扩展的智能体系统模板，  
帮助你系统理解并实践 LangChain v1 生态的全部关键模块。

---

## 🧩 核心特性

| 模块                           | 描述                                                                     |
| ------------------------------ | ------------------------------------------------------------------------ |
| 🤖 **通用 Agent 框架**         | 基于 `create_agent` 封装的智能体系统，支持工具调用、结构化输出与流式推理 |
| 📚 **RAG 知识库系统**          | 从文档加载、切分、向量索引到检索问答的完整链路                           |
| 🔄 **LangGraph 工作流**        | 使用节点/边状态图构建可恢复的学习任务与评测流程                          |
| 🧠 **DeepAgents 深度研究模式** | 多智能体协作执行复杂研究任务，支持长程记忆与文件系统                     |
| 🛡️ **Guardrails 安全层**       | 输入输出过滤、Schema 校验与内容审查机制                                  |
| 🌐 **API 模块化设计**          | 提供统一的 `/chat`、`/rag`、`/workflow`、`/deep-research` 接口           |

---

## ⚙️ 技术栈

- **语言**：Python 3.10+
- **核心库**：LangChain v1、LangGraph、DeepAgents、LangChain-OpenAI
- **数据库**：FAISS / Milvus 向量数据库
- **服务框架**：FastAPI
- **模型支持**：OpenAI / DeepSeek / Anthropic / Ollama 等兼容模型

---

## 🧠 项目结构

```bash
lc-studylab/
  backend/                     # 后端项目
    requirements.txt
    config/
      settings.py              # 模型、向量库、数据路径等统一配置
      logging.py

    core/
      models.py                # openai:gpt-4o, gpt-5 等模型封装
      prompts.py               # 系统提示词、模板
      tools/
        web_search.py          # 网络搜索工具（如 tavily）
        filesystem.py          # 读写本地知识库的工具
        rag_tools.py           # retriever 封装成 tool
        task_tools.py          # 创建学习任务、记录进度之类
      guardrails/
        content_filters.py     # 简单 guardrails，实现输入/输出校验
        schemas.py             # Pydantic / JSON schema 用于结构化输出

    rag/
      loaders.py               # 各种文档加载
      index_builder.py         # text split + embedding + vector store
      retriever.py             # retriever 构造
      agent.py                 # RAG Agent (LangChain create_agent + retriever tool)
      graph.py                 # Agentic RAG 的 LangGraph 图 (可选)

    agents/
      base_agent.py            # 通用 create_agent 封装，带 streaming + guardrails
      study_planner_agent.py   # 学习计划/任务规划 Agent
      coding_helper_agent.py   # 简单代码助手 Agent（练工具调用）

    workflows/  (LangGraph)
      study_flow_graph.py      # 「从问题 → 找资料 → 生成学习计划 → 生成练习题」的图
      eval_quiz_graph.py       # 「答题 → 评分 → 反馈」图（可选）

    deep_research/
      deep_agent.py            # DeepAgents create_deep_agent，深度研究模式
      middleware.py            # subagents / filesystem / 人类在环 中间件配置

    api/
      http_server.py           # FastAPI / Flask 暴露 HTTP 接口
      routers/
        chat.py                # /chat -> 统一入口，内部路由到不同 Agent / Graph / DeepAgent
        rag.py                 # /rag-index, /rag-query
        deep_research.py       # /deep-research

    scripts/
      build_index.py           # 初次构建向量索引
      demo_cli.py              # CLI 入口，方便你本地调试

  frontend/                    # 前端项目
```

---

## 🧩 快速开始

### 1️⃣ 安装依赖

```bash
git clone https://github.com/your-username/lc-studylab.git
cd lc-studylab
cd backend

# 推荐使用 conda 或 venv
conda create -n lc-studylab python=3.10
conda activate lc-studylab

pip install -r requirements.txt
```

### 2️⃣ 设置环境变量

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3️⃣ 启动服务

```bash
python -m api.http_server
```

访问 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

访问接口：

```
http://localhost:8000/chat
http://localhost:8000/rag
http://localhost:8000/deep-research
```

---

## 📘 学习路线建议

本项目分为五个阶段循序渐进（完全覆盖 LangChain v1 文档特性）：

1. **基础 Agent 与工具调用**
2. **RAG 检索增强生成系统**
3. **LangGraph 状态图工作流**
4. **DeepAgents 深度研究多智能体系统**
5. **Guardrails 安全与结构化输出**

每个阶段都对应项目中的独立模块，可单独运行或组合使用。

---

## 💡 适合人群

- 想系统学习 **LangChain v1 / LangGraph / DeepAgents** 的开发者
- 正在构建 **AI 助手、知识问答、教育或研究型应用** 的团队
- 希望从零搭建 **可解释、可扩展的智能体系统** 的工程师

---

## 🪴 未来规划

- ✅ 基于 LangGraph 的任务管理面板（可视化流式推理）
- ✅ DeepAgents + RAG 混合研究模式
- 🧩 LangGraph + FastAPI Stream SSE 实时输出
- 🧠 LlamaIndex 集成版本
- 📊 Web UI 前端（Next.js + Shadcn UI）

---

## 🧾 开源协议

本项目基于 **MIT License** 开源，欢迎学习、修改与二次开发。

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=hefeng6500/lc-studylab&type=Date)](https://star-history.com/#hefeng6500/lc-studylab&Date)
