"use client"

import { AppLayout } from "@/components/layout/app-layout"

export default function SettingsPage() {
  return (
    <AppLayout>
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold">设置</h1>
          <p className="text-muted-foreground">
            模型配置、后端设置和 Guardrails 策略（即将推出）
          </p>
        </div>
      </div>
    </AppLayout>
  )
}

