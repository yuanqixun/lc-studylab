"use client"

import { AppLayout } from "@/components/layout/app-layout"

export default function RagPage() {
  return (
    <AppLayout>
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold">RAG 知识库</h1>
          <p className="text-muted-foreground">
            文档库管理和问答历史可视化（即将推出）
          </p>
        </div>
      </div>
    </AppLayout>
  )
}

