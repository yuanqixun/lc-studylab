"use client"

import { AppLayout } from "@/components/layout/app-layout"

export default function DeepResearchPage() {
  return (
    <AppLayout>
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold">深度研究</h1>
          <p className="text-muted-foreground">
            DeepAgents 研究会话和报告视图（即将推出）
          </p>
        </div>
      </div>
    </AppLayout>
  )
}

