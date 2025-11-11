#!/bin/bash

# LC-StudyLab 前端开发服务器启动脚本

echo "🚀 启动 LC-StudyLab 前端开发服务器..."

# 检查是否安装了依赖
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    pnpm install
fi

# 检查环境变量文件
if [ ! -f ".env.local" ]; then
    echo "⚠️  未找到 .env.local 文件"
    echo "📝 创建默认配置..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo "✅ 已创建 .env.local 文件"
fi

# 启动开发服务器
echo "🎨 启动 Next.js 开发服务器..."
pnpm dev

