"use client"

import { AppHeader } from "./app-header"
import { AppSidebar } from "./app-sidebar"

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen flex flex-col">
      <AppHeader />
      <div className="flex-1 flex overflow-hidden">
        <aside className="w-64 flex-shrink-0">
          <AppSidebar />
        </aside>
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

