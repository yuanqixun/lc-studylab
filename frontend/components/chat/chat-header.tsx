"use client"

import { AgentMode } from "@/lib/types"
import { ChatModeSelector } from "./chat-mode-selector"
import { Button } from "@/components/ui/button"
import { Settings, Bug } from "lucide-react"
import { ModelSelector } from "@/components/ai-elements/model-selector"

interface ChatHeaderProps {
  mode: AgentMode
  onModeChange: (mode: AgentMode) => void
  onDebugToggle?: () => void
  showDebug?: boolean
}

export function ChatHeader({ 
  mode, 
  onModeChange, 
  onDebugToggle,
  showDebug = false 
}: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b bg-background/95 backdrop-blur">
      <div className="flex items-center gap-4">
        <ChatModeSelector value={mode} onChange={onModeChange} />
        <ModelSelector />
      </div>

      <div className="flex items-center gap-2">
        {onDebugToggle && (
          <Button
            variant={showDebug ? "default" : "ghost"}
            size="icon"
            onClick={onDebugToggle}
            title="调试面板"
          >
            <Bug className="h-4 w-4" />
          </Button>
        )}
        <Button variant="ghost" size="icon" title="设置">
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

