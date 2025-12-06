# 🔧 嵌入模型配置指南

## 问题说明

你在运行 notebook 时看到日志：

```
rag.embeddings:get_embeddings:162 | 🔢 创建 Embedding 模型: text-embedding-3-small
```

这是因为系统使用了默认的嵌入模型 `text-embedding-3-small`，但你的 API 服务商（SiliconFlow）可能不支持这个模型。

## 解决方案

### 方案 1：在 .env 文件中配置嵌入模型（推荐）

在 `.env` 文件中添加 `EMBEDDING_MODEL` 配置项：

```bash
# 如果你使用 SiliconFlow，可能需要使用他们支持的模型
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# 或者使用其他兼容的模型
# EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
# EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
```

### 方案 2：查询 SiliconFlow 支持的嵌入模型

访问 SiliconFlow 的文档或 API 列表，查看支持的嵌入模型：

```bash
# 常见的中文嵌入模型（SiliconFlow 可能支持）
BAAI/bge-large-zh-v1.5      # 大型中文模型，1024维
BAAI/bge-base-zh-v1.5       # 基础中文模型，768维
BAAI/bge-small-zh-v1.5      # 小型中文模型，512维
```

### 方案 3：临时禁用 RAG 功能

如果暂时不需要 RAG（知识检索）功能，可以跳过相关步骤。

## 完整的 .env 配置示例

```bash
# ==================== OpenAI 配置 ====================
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/Qwen3-8B

# ==================== Embedding 模型配置 ====================
# ⚠️ 重要：使用 SiliconFlow 支持的嵌入模型
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_BATCH_SIZE=100
```

## 验证配置

### 1. 更新 .env 文件

在 `.env` 文件中添加：

```bash
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

### 2. 重启 Jupyter Kernel

在 Jupyter Notebook 中：
- 点击 `Kernel` → `Restart Kernel`

### 3. 测试嵌入模型

运行测试脚本：

```bash
cd /Users/yuan/dev/ai-projects/lc-studylab/backend
source .venv/bin/activate
python -c "
from config import settings
print(f'Embedding Model: {settings.embedding_model}')

from rag.embeddings import get_embeddings
embeddings = get_embeddings()
vector = embeddings.embed_query('测试文本')
print(f'向量维度: {len(vector)}')
"
```

### 4. 在 Notebook 中验证

在 notebook 的某个 cell 中运行：

```python
from config import settings
print(f"当前嵌入模型: {settings.embedding_model}")

from rag.embeddings import get_embeddings
embeddings = get_embeddings()
print("✅ 嵌入模型创建成功")
```

## 常见问题

### Q1: 如何知道 SiliconFlow 支持哪些嵌入模型？

A: 访问 SiliconFlow 的文档或使用以下方法查询：

```python
# 方法 1：查看 SiliconFlow 文档
# https://docs.siliconflow.cn/

# 方法 2：尝试列出可用模型（如果 API 支持）
import openai
client = openai.OpenAI(
    api_key="your-api-key",
    base_url="https://api.siliconflow.cn/v1"
)
models = client.models.list()
for model in models:
    print(model.id)
```

### Q2: 不同嵌入模型的向量维度不同，会有问题吗？

A: 是的！如果你已经使用 `text-embedding-3-small` (1536维) 创建了向量索引，然后切换到 `BAAI/bge-large-zh-v1.5` (1024维)，会导致维度不匹配错误。

**解决方法**：
1. 删除旧的向量索引：`rm -rf data/indexes/*`
2. 使用新模型重新创建索引

### Q3: 我可以使用 OpenAI 官方的嵌入模型吗？

A: 可以，但需要：
1. 使用 OpenAI 官方的 API Key
2. 设置 `OPENAI_API_BASE=https://api.openai.com/v1`
3. 设置 `EMBEDDING_MODEL=text-embedding-3-small`

### Q4: 如何选择合适的嵌入模型？

| 模型 | 维度 | 特点 | 适用场景 |
|------|------|------|----------|
| text-embedding-3-small | 1536 | OpenAI官方，快速便宜 | 开发测试 |
| text-embedding-3-large | 3072 | OpenAI官方，高质量 | 生产环境 |
| BAAI/bge-large-zh-v1.5 | 1024 | 中文优化，开源 | 中文场景 |
| BAAI/bge-base-zh-v1.5 | 768 | 中文优化，平衡 | 中文场景 |
| BAAI/bge-small-zh-v1.5 | 512 | 中文优化，快速 | 快速检索 |

## 推荐配置

### 如果使用 SiliconFlow

```bash
OPENAI_API_KEY=sk-your-siliconflow-key
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/Qwen3-8B
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

### 如果使用 OpenAI 官方

```bash
OPENAI_API_KEY=sk-your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
```

## 下一步

1. 更新 `.env` 文件，添加 `EMBEDDING_MODEL` 配置
2. 重启 Jupyter Kernel
3. 重新运行 notebook

如果还有问题，请提供：
- SiliconFlow 支持的嵌入模型列表
- 完整的错误信息
