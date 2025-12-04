# LC-StudyLab Backend 学习文档

> **文档版本**: v1.0.0  
> **目标读者**: 新成员、贡献者、系统维护人员  
> **适用场景**: 快速理解项目架构、模块功能和开发流程

---

## 📋 目录

- [1. 项目概览](#1-项目概览)
- [2. 技术栈](#2-技术栈)
- [3. 目录结构详解](#3-目录结构详解)
- [4. 核心模块深入理解](#4-核心模块深入理解)
- [5. 快速上手指南](#5-快速上手指南)
- [6. 开发阶段与功能矩阵](#6-开发阶段与功能矩阵)
- [7. API 接口总览](#7-api-接口总览)
- [8. 配置管理](#8-配置管理)
- [9. 测试与调试](#9-测试与调试)
- [10. 常见问题](#10-常见问题)

---

## 1. 项目概览

### 1.1 系统定位

**LC-StudyLab** 是一个基于 **LangChain 1.0.3** 全家桶构建的智能学习与研究助手系统，提供以下核心能力：

- 🤖 **基础 Agent**: 支持工具调用、流式输出的智能对话代理
- 📚 **RAG 知识库**: 文档问答、知识检索、向量索引管理
- 🔄 **工作流引擎**: 基于 LangGraph 的有状态工作流（学习规划、出题、评分）
- 🔬 **深度研究**: 多代理协作、长时间研究任务（DeepAgents）
- 🛡️ **安全防护**: 输入输出验证、内容过滤（Guardrails）

### 1.2 架构设计理念

- **模块化**: 各功能模块独立封装，低耦合高内聚
- **可配置**: 统一的 Pydantic Settings 配置管理
- **标准化**: 遵循 LangChain 1.0.3 最佳实践
- **可扩展**: 插件式工具设计，易于添加新功能
- **可观测**: 完善的日志系统（Loguru）和请求追踪

---

## 2. 技术栈

### 2.1 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| **LangChain** | 1.0.3 | Agent 框架核心 |
| **LangChain Core** | 1.0.3 | 基础组件和接口 |
| **LangGraph** | 1.0.2 | 有状态工作流引擎 |
| **FastAPI** | 0.121.0 | Web API 框架 |
| **Pydantic** | 2.12.4 | 数据验证和配置管理 |

### 2.2 AI 模型集成

- **OpenAI**: GPT-4O、GPT-3.5-Turbo、Text-Embedding-3-Small
- **Tavily**: Web 搜索工具
- **FAISS**: 高效向量相似度搜索

### 2.3 支持工具

- **日志**: Loguru（异步日志、文件轮转）
- **文档处理**: PyPDF、Unstructured、BeautifulSoup4
- **CLI**: Click、Rich（终端美化）
- **服务器**: Uvicorn（ASGI 服务器）

---

## 3. 目录结构详解

```
backend/
├── 📁 agents/                    # Agent 实现层
│   ├── base_agent.py            # 基础 Agent 封装（LangChain create_agent）
│   └── __init__.py              # Agent 工厂函数导出
│
├── 📁 api/                       # HTTP 接口层
│   ├── http_server.py           # FastAPI 应用主入口
│   └── routers/                 # 路由模块
│       ├── chat.py              # 聊天接口（流式/非流式）
│       ├── rag.py               # RAG 文档问答接口
│       ├── workflow.py          # 学习工作流接口
│       └── deep_research.py     # 深度研究接口
│
├── 📁 config/                    # 配置管理层
│   ├── settings.py              # Pydantic Settings（统一配置）
│   └── logging.py               # Loguru 日志配置
│
├── 📁 core/                      # 核心功能层
│   ├── models.py                # LLM 模型封装（OpenAI）
│   ├── prompts.py               # 提示词模板库
│   ├── extractors.py            # 结构化输出提取器
│   ├── usage_tracker.py         # Token 使用量追踪
│   ├── tools/                   # 工具集合
│   │   ├── time_tools.py        # 时间查询工具
│   │   ├── calculator.py        # 安全计算器
│   │   ├── web_search.py        # Tavily 网络搜索
│   │   ├── weather.py           # 天气查询（高德地图）
│   │   └── filesystem.py        # 文件系统操作工具
│   └── guardrails/              # 安全防护模块
│       ├── input_validators.py  # 输入验证
│       ├── output_validators.py # 输出验证
│       ├── content_filters.py   # 内容过滤
│       ├── middleware.py        # 安全中间件
│       └── schemas.py           # 数据模式定义
│
├── 📁 rag/                       # RAG 知识库模块
│   ├── loaders.py               # 文档加载器（PDF、Markdown、HTML）
│   ├── splitters.py             # 文本分块策略
│   ├── embeddings.py            # Embedding 封装
│   ├── vector_stores.py         # 向量库管理（FAISS）
│   ├── index_manager.py         # 索引构建和管理
│   ├── retrievers.py            # 文档检索器
│   ├── rag_agent.py             # RAG Agent 实现
│   └── safe_rag_agent.py        # 带安全防护的 RAG Agent
│
├── 📁 workflows/                 # LangGraph 工作流
│   ├── state.py                 # 工作流状态定义
│   ├── study_flow_graph.py      # 学习工作流图
│   ├── safe_study_flow.py       # 带安全防护的学习流
│   └── nodes/                   # 工作流节点
│       ├── planner.py           # 规划节点
│       ├── retriever.py         # 检索节点
│       ├── quiz_generator.py    # 出题节点
│       ├── grader.py            # 评分节点
│       └── feedback.py          # 反馈节点
│
├── 📁 deep_research/             # 深度研究模块（第 4 阶段）
│   ├── deep_agent.py            # 深度研究 Agent
│   ├── safe_deep_agent.py       # 带安全防护的深度研究
│   └── subagents.py             # 子代理（搜索、分析、总结）
│
├── 📁 scripts/                   # 工具脚本
│   ├── demo_cli.py              # 交互式 CLI 演示
│   ├── rag_cli.py               # RAG 命令行工具
│   ├── update_index.py          # 索引更新脚本
│   └── test_*.py                # 各模块测试脚本
│
├── 📁 data/                      # 数据存储目录
│   ├── documents/               # 原始文档
│   ├── uploads/                 # 用户上传文件
│   ├── indexes/                 # 向量索引文件
│   └── checkpoints/             # LangGraph 检查点
│
├── 📁 docs/                      # 详细文档
│   ├── stage_01/                # 第 1 阶段文档（基础 Agent）
│   ├── stage_02/                # 第 2 阶段文档（RAG）
│   └── stage_03/                # 第 3 阶段文档（工作流）
│
├── 📁 logs/                      # 日志文件
│
├── 📄 .env                       # 环境变量配置（敏感信息，不入库）
├── 📄 env.example                # 配置示例文件
├── 📄 requirements.txt           # Python 依赖
├── 📄 pyproject.toml             # 项目元数据（uv 管理）
├── 📄 Dockerfile                 # Docker 镜像构建
├── 📄 main.py                    # 入口占位符
├── 📄 start_server.sh            # 启动 API 服务脚本
├── 📄 start_cli.sh               # 启动 CLI 工具脚本
└── 📄 README.md                  # 项目总体说明
```

---

## 4. 核心模块深入理解

### 4.1 Agent 模块 (`agents/`)

**职责**: 封装 LangChain 1.0.3 的 `create_agent` 功能，提供统一的 Agent 接口。

#### 核心文件：`base_agent.py`

**关键类**: `BaseAgent`

**功能特性**：
- ✅ 同步/异步调用支持
- ✅ 流式输出（Streaming）
- ✅ 工具调用（Tool Calling）
- ✅ 多种预设模式（default, coding, research, concise, detailed）
- ✅ 对话历史管理（Memory）

**使用示例**：
```python
from agents import create_base_agent

# 创建 Agent
agent = create_base_agent(mode="coding", use_tools=True)

# 同步调用
response = agent.invoke("现在几点？")
print(response)

# 流式输出
for chunk in agent.stream("讲一个笑话"):
    print(chunk, end="", flush=True)
```

---

### 4.2 API 模块 (`api/`)

**职责**: 提供 RESTful HTTP 接口，支持前端或第三方客户端调用。

#### 主入口：`http_server.py`

**核心功能**：
1. **FastAPI 应用初始化**: 配置 CORS、中间件、异常处理
2. **路由注册**: 聊天、RAG、工作流、深度研究
3. **请求日志**: 记录每个请求的方法、路径、耗时
4. **健康检查**: `/health` 端点用于监控

#### 路由模块：`routers/`

| 路由文件 | 前缀 | 功能 |
|---------|------|------|
| `chat.py` | `/chat` | 基础聊天（流式/非流式） |
| `rag.py` | `/rag` | 文档上传、索引构建、知识问答 |
| `workflow.py` | `/workflow` | 学习工作流执行、状态查询 |
| `deep_research.py` | `/research` | 深度研究任务提交 |

**重要端点**：
- `POST /chat` - 非流式聊天
- `POST /chat/stream` - SSE 流式聊天
- `POST /rag/upload` - 上传文档
- `POST /rag/index/build` - 构建索引
- `POST /rag/query` - RAG 问答
- `POST /workflow/study` - 启动学习工作流
- `GET /workflow/{thread_id}/state` - 查询工作流状态

---

### 4.3 配置管理 (`config/`)

**职责**: 统一管理所有配置项，支持环境变量和 `.env` 文件。

#### `settings.py` - 核心配置类

**采用的技术**：Pydantic Settings v2

**配置优先级**：环境变量 > `.env` 文件 > 默认值

**配置分类**：

1. **OpenAI 配置**
   - `OPENAI_API_KEY`: API 密钥（必需）
   - `OPENAI_API_BASE`: API 基础 URL
   - `OPENAI_MODEL`: 默认模型（gpt-4o）
   - `OPENAI_TEMPERATURE`: 温度参数（0.7）

2. **Tavily 搜索配置**
   - `TAVILY_API_KEY`: Tavily API 密钥（可选）
   - `TAVILY_MAX_RESULTS`: 最大搜索结果数（5）

3. **服务器配置**
   - `SERVER_HOST`: 监听地址（0.0.0.0）
   - `SERVER_PORT`: 监听端口（8000）
   - `SERVER_RELOAD`: 开发模式自动重载（True）

4. **RAG 配置**
   - `EMBEDDING_MODEL`: Embedding 模型（text-embedding-3-small）
   - `CHUNK_SIZE`: 文本分块大小（1000）
   - `CHUNK_OVERLAP`: 分块重叠大小（200）
   - `RETRIEVER_K`: 检索返回文档数（4）

5. **日志配置**
   - `LOG_LEVEL`: 日志级别（INFO）
   - `LOG_FILE`: 日志文件路径（logs/app.log）

**使用方式**：
```python
from config import settings

# 访问配置
print(settings.openai_model)
print(settings.chunk_size)

# 验证配置
settings.validate_required_keys()

# 获取配置字典
openai_config = settings.get_openai_config()
```

#### `logging.py` - 日志配置

**日志框架**: Loguru

**特性**：
- 自动文件轮转（100 MB）
- 保留期限（30 天）
- 分级输出（控制台 + 文件）
- 彩色终端输出

---

### 4.4 核心功能 (`core/`)

#### `models.py` - LLM 模型封装

**核心函数**：
- `get_llm(streaming=False, **kwargs)`: 获取 OpenAI LLM 实例
- `get_chat_model(model=None, **kwargs)`: 获取聊天模型

**封装优势**：
- 统一的模型创建接口
- 自动读取配置
- 支持参数覆盖

#### `prompts.py` - 提示词模板库

**包含的模板**：
1. **DEFAULT_SYSTEM_PROMPT**: 默认学习助手
2. **CODING_ASSISTANT_PROMPT**: 编程学习助手
3. **RESEARCH_ASSISTANT_PROMPT**: 研究助手
4. **CONCISE_MODE_PROMPT**: 简洁模式
5. **DETAILED_MODE_PROMPT**: 详细解释模式
6. **RAG_QA_PROMPT**: RAG 问答提示
7. **WORKFLOW_PLANNER_PROMPT**: 工作流规划提示

**使用方式**：
```python
from core.prompts import PROMPTS

# 获取模板
system_prompt = PROMPTS["default"]
coding_prompt = PROMPTS["coding"]
```

#### `tools/` - 工具集合

**可用工具**：

1. **time_tools.py**
   - `get_current_time()`: 获取当前时间
   - `get_current_date()`: 获取当前日期

2. **calculator.py**
   - `calculator(expression: str)`: 安全的数学表达式计算

3. **web_search.py**
   - `web_search(query: str)`: Tavily 网络搜索
   - `web_search_simple(query: str)`: 简化搜索结果

4. **weather.py**
   - `get_weather(city: str)`: 查询天气（高德地图 API）

5. **filesystem.py**
   - `read_file(path: str)`: 读取文件
   - `write_file(path: str, content: str)`: 写入文件
   - `list_directory(path: str)`: 列出目录

**工具注册**：
```python
from core.tools import ALL_TOOLS

# 使用所有工具
agent = create_base_agent(tools=ALL_TOOLS)

# 使用部分工具
from core.tools import TIME_TOOLS, CALCULATOR_TOOL
agent = create_base_agent(tools=[*TIME_TOOLS, CALCULATOR_TOOL])
```

#### `guardrails/` - 安全防护模块

**职责**: 确保输入输出的安全性和合规性。

**核心组件**：

1. **input_validators.py**
   - 长度限制验证
   - 敏感词检测
   - 格式验证

2. **output_validators.py**
   - 内容质量检查
   - 敏感信息过滤
   - 结构化验证

3. **content_filters.py**
   - 恶意内容过滤
   - PII（个人信息）脱敏
   - 有害信息拦截

4. **middleware.py**
   - 请求前验证
   - 响应后过滤
   - 异常处理

---

### 4.5 RAG 模块 (`rag/`)

**职责**: 实现检索增强生成（Retrieval-Augmented Generation）功能。

#### 模块流程

```
文档上传 → 文档加载 → 文本分块 → Embedding → 向量存储 → 检索 → 生成答案
```

#### 核心文件详解

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `loaders.py` | 文档加载 | `DocumentLoader`, `PDFLoader`, `MarkdownLoader` |
| `splitters.py` | 文本分块 | `get_text_splitter()` |
| `embeddings.py` | Embedding | `get_embeddings()` |
| `vector_stores.py` | 向量库管理 | `VectorStoreManager` |
| `index_manager.py` | 索引构建 | `IndexManager.build_index()` |
| `retrievers.py` | 文档检索 | `get_retriever()` |
| `rag_agent.py` | RAG Agent | `RAGAgent` |
| `safe_rag_agent.py` | 安全 RAG | `SafeRAGAgent` |

#### 使用示例

**构建索引**：
```python
from rag import IndexManager

manager = IndexManager()
manager.build_index(
    collection_name="my_docs",
    documents_path="data/documents/",
    chunk_size=1000,
    chunk_overlap=200
)
```

**RAG 问答**：
```python
from rag import RAGAgent

agent = RAGAgent(collection_name="my_docs")
response = agent.query("什么是 LangChain？")
print(response["answer"])
print(response["source_documents"])
```

---

### 4.6 工作流模块 (`workflows/`)

**职责**: 基于 LangGraph 实现有状态的智能学习工作流。

#### 核心概念

- **StateGraph**: 有状态的工作流图
- **Checkpointing**: 工作流状态持久化（SQLite）
- **Human-in-the-Loop**: 人机交互节点
- **Streaming**: 流式输出工作流进度

#### 学习工作流节点

```
开始 → 规划学习路径 → 知识检索 → 出题测试 → 人工答题 → 自动评分 → 反馈建议 → 结束
```

**节点说明**：

1. **planner.py** - 规划节点
   - 分析学习主题
   - 制定学习计划
   - 确定知识点范围

2. **retriever.py** - 检索节点
   - 从知识库检索相关资料
   - 提供学习参考

3. **quiz_generator.py** - 出题节点
   - 根据主题生成测试题
   - 支持多种题型（选择、填空、简答）

4. **grader.py** - 评分节点
   - 自动评分用户答案
   - 给出评分理由

5. **feedback.py** - 反馈节点
   - 分析学习效果
   - 提供改进建议

#### 使用示例

```python
from workflows import create_study_workflow

# 创建工作流
workflow = create_study_workflow()

# 启动学习会话
thread_id = "session_123"
config = {"configurable": {"thread_id": thread_id}}

# 发送学习主题
inputs = {"topic": "Python 装饰器", "user_id": "user_001"}
for event in workflow.stream(inputs, config):
    print(event)

# 查询当前状态
state = workflow.get_state(config)
print(state.values)
```

---

### 4.7 深度研究模块 (`deep_research/`)

**职责**: 多代理协作完成复杂研究任务。

#### 架构设计

```
主代理（Deep Agent）
├── 搜索子代理（Search Subagent）
├── 分析子代理（Analysis Subagent）
└── 总结子代理（Summary Subagent）
```

**特点**：
- 任务分解
- 并行处理
- 结果聚合
- 长时间运行支持

**使用场景**：
- 学术研究综述
- 技术调研报告
- 竞品分析
- 市场研究

---

## 5. 快速上手指南

### 5.1 环境准备

#### 系统要求
- Python 3.9+
- 8GB+ RAM
- 磁盘空间 2GB+

#### 依赖安装

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 5.2 配置设置

```bash
# 复制配置模板
cp env.example .env

# 编辑 .env 文件
# 必需配置项：
# OPENAI_API_KEY=your_api_key_here
# OPENAI_API_BASE=https://api.openai.com/v1

# 可选配置项：
# TAVILY_API_KEY=your_tavily_key
# AMAP_KEY=your_amap_key
```

### 5.3 启动服务

#### 方式 1：HTTP API 服务器

```bash
# 使用启动脚本
bash start_server.sh

# 或直接运行
python api/http_server.py

# 或使用 uvicorn
uvicorn api.http_server:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 方式 2：CLI 交互工具

```bash
# 基础聊天 CLI
bash start_cli.sh
# 或
python scripts/demo_cli.py

# RAG 专用 CLI
bash start_rag_cli.sh
# 或
python scripts/rag_cli.py
```

### 5.4 快速测试

#### 测试基础聊天

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请介绍一下自己",
    "mode": "default",
    "use_tools": false
  }'
```

#### 测试工具调用

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "现在几点？",
    "use_tools": true
  }'
```

#### 测试流式输出

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "讲一个编程笑话"
  }'
```

#### 测试 RAG 构建索引

```bash
# 1. 上传文档到 data/documents/
cp your_document.pdf data/documents/

# 2. 构建索引
python scripts/update_index.py --collection my_docs --path data/documents/

# 3. 查询
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "文档中提到了什么？",
    "collection_name": "my_docs"
  }'
```

#### 测试学习工作流

```bash
bash scripts/test_workflow.sh
# 或
python scripts/test_workflow.py
```

---

## 6. 开发阶段与功能矩阵

| 阶段 | 状态 | 核心功能 | 关键模块 | 文档位置 |
|------|------|----------|----------|---------|
| **第 1 阶段** | ✅ 已完成 | 基础 Agent + 工具 + 流式输出 | `agents/`, `core/tools/` | `docs/stage_01/` |
| **第 2 阶段** | ✅ 已完成 | RAG 知识库 + 文档问答 | `rag/` | `docs/stage_02/` |
| **第 3 阶段** | ✅ 已完成 | LangGraph 工作流 + 人机交互 | `workflows/` | `docs/stage_03/` |
| **第 4 阶段** | ⏳ 计划中 | DeepAgents 深度研究 | `deep_research/` | - |
| **第 5 阶段** | ⏳ 计划中 | Guardrails 安全防护 | `core/guardrails/` | - |

---

## 7. API 接口总览

### 7.1 聊天接口 (`/chat`)

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| `/chat` | POST | 非流式聊天 | `{message, mode, use_tools}` | JSON |
| `/chat/stream` | POST | SSE 流式聊天 | `{message, mode, use_tools}` | SSE Stream |
| `/chat/modes` | GET | 获取可用模式 | - | JSON |

### 7.2 RAG 接口 (`/rag`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/rag/upload` | POST | 上传文档 |
| `/rag/index/build` | POST | 构建索引 |
| `/rag/index/list` | GET | 列出所有索引 |
| `/rag/query` | POST | RAG 问答 |
| `/rag/collections` | GET | 获取所有集合 |

### 7.3 工作流接口 (`/workflow`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/workflow/study` | POST | 启动学习工作流 |
| `/workflow/{thread_id}/state` | GET | 查询工作流状态 |
| `/workflow/{thread_id}/resume` | POST | 恢复工作流 |
| `/workflow/{thread_id}/cancel` | POST | 取消工作流 |

### 7.4 深度研究接口 (`/research`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/research/submit` | POST | 提交研究任务 |
| `/research/{task_id}/status` | GET | 查询任务状态 |
| `/research/{task_id}/result` | GET | 获取研究结果 |

### 7.5 系统接口

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | API 基本信息 |
| `/health` | GET | 健康检查 |
| `/info` | GET | 系统信息 |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc 文档 |

---

## 8. 配置管理

### 8.1 配置文件说明

- **`.env`**: 本地开发配置（不入库，包含敏感信息）
- **`env.example`**: 配置模板（入库，供参考）
- **`config/settings.py`**: 配置类定义

### 8.2 环境变量列表

#### 必需配置

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

#### 推荐配置

```bash
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
TAVILY_API_KEY=tvly-xxxxxxxxxxxx
```

#### 可选配置

```bash
# 高德地图（天气查询）
AMAP_KEY=xxxxxxxxxxxx

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# RAG 配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVER_K=4
```

### 8.3 配置验证

```python
from config import settings

# 验证必需配置
settings.validate_required_keys()

# 查看配置
print(settings.model_dump())
```

---

## 9. 测试与调试

### 9.1 测试脚本

| 脚本文件 | 测试内容 |
|---------|---------|
| `test_basic.py` | 基础聊天功能 |
| `test_rag_query.py` | RAG 问答 |
| `test_workflow.py` | 学习工作流 |
| `test_deep_research.py` | 深度研究 |
| `test_guardrails.py` | 安全防护 |
| `test_weather.py` | 天气查询工具 |
| `test_safe_rag.py` | 安全 RAG |
| `test_enhanced_stream.py` | 增强流式输出 |

### 9.2 运行测试

```bash
# 运行单个测试
python scripts/test_basic.py

# 运行 RAG 测试
python scripts/test_rag_query.py

# 运行工作流测试
bash scripts/test_workflow.sh
```

### 9.3 调试技巧

#### 启用详细日志

```bash
# 修改 .env
DEBUG=true
LOG_LEVEL=DEBUG
```

#### 查看日志文件

```bash
tail -f logs/app.log
```

#### 使用 Python 调试器

```python
import pdb; pdb.set_trace()
```

#### LangChain 调试模式

```python
from langchain.globals import set_debug
set_debug(True)
```

---

## 10. 常见问题

### 10.1 配置相关

**Q: 启动时报错 "OPENAI_API_KEY 未设置"**

A: 检查 `.env` 文件是否存在且包含有效的 API Key：
```bash
cat .env | grep OPENAI_API_KEY
```

**Q: 如何使用自定义 OpenAI API 端点？**

A: 在 `.env` 中设置：
```bash
OPENAI_API_BASE=https://your-custom-endpoint.com/v1
```

### 10.2 功能相关

**Q: 工具调用不生效？**

A: 确认：
1. `use_tools=True`
2. 已配置 `TAVILY_API_KEY`（网络搜索）
3. 消息中明确要求使用工具

**Q: RAG 检索结果不准确？**

A: 尝试调整参数：
- 增加 `RETRIEVER_K` 值（返回更多文档）
- 调整 `CHUNK_SIZE`（更小的分块）
- 增大 `CHUNK_OVERLAP`（更多上下文）

**Q: 工作流卡在某个节点？**

A: 检查：
1. 日志中的错误信息
2. 工作流状态：`GET /workflow/{thread_id}/state`
3. 是否需要人工输入（Human-in-the-Loop）

### 10.3 性能相关

**Q: API 响应慢？**

A: 优化建议：
1. 使用流式输出（`/chat/stream`）
2. 减少 `retriever_k` 值
3. 使用更快的模型（如 gpt-3.5-turbo）

**Q: 索引构建耗时长？**

A: 正常现象，取决于文档数量和大小。可以：
1. 使用更小的 `CHUNK_SIZE`
2. 减少 `EMBEDDING_BATCH_SIZE`
3. 分批构建索引

### 10.4 部署相关

**Q: 如何使用 Docker 部署？**

A: 
```bash
# 构建镜像
docker build -t lc-studylab-backend .

# 运行容器
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  lc-studylab-backend
```

**Q: 生产环境部署建议？**

A: 
1. 关闭 `DEBUG` 模式
2. 限制 CORS 允许的域名
3. 使用 HTTPS
4. 配置负载均衡器
5. 启用日志监控
6. 定期备份 `data/` 目录

---

## 📚 进阶学习资源

### 官方文档
- [LangChain 1.0.3 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

### 项目内文档
- `README.md` - 项目总览
- `README-ENHANCED-CHAT.md` - 增强聊天功能
- `docs/stage_01/` - 第 1 阶段详细教程
- `docs/stage_02/` - RAG 完整指南
- `docs/stage_03/` - 工作流使用手册

### 代码示例
- `scripts/demo_cli.py` - CLI 交互示例
- `scripts/test_*.py` - 各功能测试示例

---

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范
- 遵循 PEP 8
- 使用类型提示
- 编写文档字符串
- 添加单元测试

---

## 📞 获取帮助

- **Issue 跟踪**: GitHub Issues
- **讨论区**: GitHub Discussions
- **文档**: 查看 `docs/` 目录

---

**文档维护**: 本文档随项目演进持续更新  
**最后更新**: 2025-12-03  
**版本**: v1.0.0
