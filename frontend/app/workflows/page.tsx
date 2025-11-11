"use client"

import { AppLayout } from "@/components/layout/app-layout"

export default function WorkflowsPage() {
  return (
    <AppLayout>
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold">学习工作流</h1>
          <p className="text-muted-foreground">
            LangGraph 工作流运行流程和状态可视化（即将推出）
          </p>
        </div>
      </div>
    </AppLayout>
  )
}

