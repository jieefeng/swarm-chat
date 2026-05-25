'use client'

import type { Agent } from '@/lib/types'

interface MentionDropdownProps {
  options: Agent[]
  onSelect: (agent: Agent) => void
}

export function MentionDropdown({ options, onSelect }: MentionDropdownProps) {
  if (options.length === 0) {
    return (
      <div className="absolute bottom-full mb-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 p-4 text-center text-gray-500 text-sm">
        无匹配Agent
      </div>
    )
  }

  return (
    <div className="absolute bottom-full mb-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden z-50">
      {options.slice(0, 5).map((agent) => (
        <button
          key={agent.id}
          onClick={() => onSelect(agent)}
          className="w-full px-4 py-3 text-left hover:bg-blue-50 flex items-center gap-3 transition-colors"
        >
          <div className="flex-1">
            <div className="font-medium text-gray-800">{agent.name}</div>
            <div className="text-xs text-gray-500">{agent.role}</div>
          </div>
        </button>
      ))}
    </div>
  )
}
