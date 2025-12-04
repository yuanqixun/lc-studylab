# 故障排查指南

## Python 版本兼容性问题

### 问题描述

在 Python 3.12 环境下运行项目时,会遇到以下错误:

```
TypeError: ForwardRef._evaluate() got an unexpected keyword argument 'type_params'
```

### 根本原因

- **Python 3.12** 修改了 `ForwardRef._evaluate()` 方法的签名,不再接受 `type_params` 参数
- `langsmith` 包(LangChain 的依赖)内部使用了 `pydantic v1` 兼容层
- `pydantic v1` 在 Python 3.12 下尝试传递 `type_params` 参数,导致 `TypeError`

### 解决方案

**使用 Python 3.11** (推荐)

1. 删除现有虚拟环境:
   ```bash
   rm -rf .venv
   ```

2. 使用 Python 3.11 创建新的虚拟环境:
   ```bash
   # 使用 conda
   /opt/anaconda3/envs/py311/bin/python -m venv .venv
   
   # 或使用 pyenv
   pyenv install 3.11.0
   pyenv local 3.11.0
   python -m venv .venv
   ```

3. 激活虚拟环境并安装依赖:
   ```bash
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. 验证安装:
   ```bash
   python -c "from core.models import get_chat_model; print('导入成功!')"
   ```

### 版本要求

- **Python**: `>=3.11,<3.12`
- **pydantic**: `2.12.4`
- **langsmith**: `0.4.53`
- **langchain**: `>=1.1.0`

### 相关链接

- [Pydantic v1 与 Python 3.12 兼容性问题](https://github.com/pydantic/pydantic/issues/8705)
- [LangSmith GitHub Issues](https://github.com/langchain-ai/langsmith-sdk/issues)

## 其他常见问题

### 环境变量配置

确保 `.env` 文件包含必要的配置:

```env
# OpenAI API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1  # 可选

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Tavily 搜索 API (可选)
TAVILY_API_KEY=your_tavily_key_here
```

### 依赖安装失败

如果遇到依赖安装失败,尝试:

1. 清理 pip 缓存:
   ```bash
   pip cache purge
   ```

2. 使用国内镜像源(可选):
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Jupyter Notebook 内核配置

如果在 Jupyter Notebook 中使用,需要安装 ipykernel:

```bash
source .venv/bin/activate
pip install ipykernel
python -m ipykernel install --user --name=lc-studylab --display-name "Python (lc-studylab)"
```

然后在 Jupyter 中选择 "Python (lc-studylab)" 内核。
