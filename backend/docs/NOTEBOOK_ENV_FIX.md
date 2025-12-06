# 🔧 Notebook 环境变量加载问题解决方案

## 问题描述

在 Jupyter Notebook 中运行 `stage_03_workflow.ipynb` 时，出现 OpenAI API Key 未设置的错误：

```
AuthenticationError: Error code: 401 - You didn't provide an API key
```

## 根本原因

虽然已经配置了 `.env` 文件，但 Jupyter Notebook 在运行时没有自动从正确的路径加载 `.env` 文件。

## 解决方案

### ✅ 方案 1：修改配置文件（已完成）

我已经修改了 `config/settings.py`，添加了动态查找 `.env` 文件的功能。现在配置系统会自动：

1. 从 `backend/` 目录查找 `.env`
2. 从当前工作目录查找 `.env`
3. 从父目录查找 `.env`（处理从 `notebooks/` 运行的情况）

### ✅ 方案 2：在 Notebook 中手动加载（推荐）

如果方案 1 还有问题，可以在 notebook 的第一个 cell **之前**添加一个新的 cell：

```python
# 🔑 加载环境变量（在导入其他模块之前运行）
from dotenv import load_dotenv
from pathlib import Path
import os

# 获取项目根目录
backend_dir = Path.cwd()
if backend_dir.name == 'notebooks':
    backend_dir = backend_dir.parent

# 加载 .env 文件
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量: {env_path}")
    
    # 验证关键环境变量
    if os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY")
        masked_key = api_key[:8] + "..." + api_key[-4:]
        print(f"✅ OPENAI_API_KEY 已设置: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY 未设置！")
else:
    print(f"⚠️  未找到 .env 文件: {env_path}")
```

## 验证

运行以下命令验证环境变量是否正确加载：

```bash
cd /Users/yuan/dev/ai-projects/lc-studylab/backend
source .venv/bin/activate
python test_env.py
```

应该看到：

```
✅ OPENAI_API_KEY: 已设置 (sk-oomuy...tlxx)
✅ API 连接正常
```

## 在 Notebook 中使用

### 步骤 1：重启 Jupyter Kernel

在 Jupyter Notebook 中：
1. 点击菜单 `Kernel` → `Restart Kernel`
2. 确认重启

### 步骤 2：重新运行 Cell

从第一个 cell 开始依次运行。现在应该能正确加载环境变量了。

### 步骤 3：验证

在第一个 cell 运行后，你应该看到：

```
✅ 项目根目录: /Users/yuan/dev/ai-projects/lc-studylab/backend
📝 日志系统初始化完成 - 级别: INFO, 文件: logs/app.log
```

如果没有看到错误，说明环境变量已正确加载。

## 常见问题

### Q: 为什么直接运行 Python 脚本没问题，但 Notebook 有问题？

A: 因为 Python 脚本从 `backend/` 目录运行，而 Notebook 可能从 `notebooks/` 目录运行，导致相对路径不同。

### Q: 我需要每次都手动加载环境变量吗？

A: 不需要。修改配置文件后，只需要重启 Jupyter Kernel 即可。

### Q: 如何确认环境变量已加载？

A: 运行 `test_env.py` 脚本，或在 notebook 中运行：

```python
from config import settings
print(f"API Key: {settings.openai_api_key[:8]}...")
```

## 相关文件

- `config/settings.py` - 配置管理（已修改）
- `test_env.py` - 环境变量测试脚本（新增）
- `.env` - 环境变量配置文件
