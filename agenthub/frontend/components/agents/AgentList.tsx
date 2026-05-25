'use client'

import type { Agent } from '@/lib/types'

interface AgentListProps {
  agents: Agent[]
}

export function AgentList({ agents }: AgentListProps) {
  return (
    <div className="w-48 bg-white border-r border-gray-200 p-4">
      <div className="text-sm font-semibold text-gray-700 pb-3 border-b border-gray-200">
        Agent 列表
      </div>
      {agents.map((agent) => (
        <div key={agent.id} className="py-3 border-b border-gray-100">
          <div className="text-sm font-medium text-gray-800">{agent.name}</div>
          <div className="text-xs text-gray-500 mt-0.5">{agent.role}</div>
        </div>
      ))}
    </div>
  )
}
