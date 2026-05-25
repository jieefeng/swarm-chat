'use client'

import { useState } from 'react'
import { AgentList } from '@/components/agents/AgentList'
import { MessageInput } from '@/components/chat/MessageInput'
import { MessageList } from '@/components/chat/MessageList'
import { useAgentStore } from '@/lib/stores/agentStore'
import type { Message } from '@/lib/types'

export default function HomePage() {
  const agents = useAgentStore((s) => s.agents)
  const [messages, _setMessages] = useState<Message[]>([])

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-xl font-semibold">AgentHub</h1>
        <div className="text-sm text-gray-500">多Agent协作平台</div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        <AgentList agents={agents} />
        <div className="flex-1 flex flex-col">
          <MessageList messages={messages} agentId={null} />
          <MessageInput
            onSubmit={(content) => console.log('submit:', content)}
            disabled={false}
            mentionCandidates={agents}
          />
        </div>
      </div>
    </div>
  )
}
