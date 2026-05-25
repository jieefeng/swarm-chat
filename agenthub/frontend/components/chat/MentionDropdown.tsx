'use client'

import type { MentionCandidate } from '@/lib/types'

interface MentionDropdownProps {
  candidates: MentionCandidate[]
  query: string
  onSelect: (candidate: MentionCandidate) => void
  onClose: () => void
  anchorRect: DOMRect | null
}

export function MentionDropdown({
  candidates,
  onSelect,
  onClose,
}: MentionDropdownProps) {
  if (candidates.length === 0) {
    return null
  }

  return (
    <div
      role="listbox"
      aria-label="选择 Agent"
      className="bg-white rounded-lg shadow-lg border border-gray-200 py-1"
    >
      {candidates.map((candidate) => (
        <button
          key={candidate.id}
          role="option"
          aria-selected={false}
          onClick={() => onSelect(candidate)}
          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2"
        >
          {candidate.avatar && (
            <img
              src={candidate.avatar}
              alt=""
              className="w-6 h-6 rounded-full"
            />
          )}
          <span className="text-sm font-medium text-gray-800">
            {candidate.label}
          </span>
        </button>
      ))}
    </div>
  )
}
