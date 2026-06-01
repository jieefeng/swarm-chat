"use client";

import type { MentionCandidate } from "@/lib/types";

interface MentionDropdownProps {
  candidates: MentionCandidate[];
  onSelect: (candidate: MentionCandidate) => void;
}

export function MentionDropdown({
  candidates,
  onSelect,
}: MentionDropdownProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div
      role="listbox"
      aria-label="选择神兽"
      className="bg-white rounded-lg shadow-lg border border-gray-200 py-1"
    >
      {candidates.map((candidate) => (
        <button
          type="button"
          key={candidate.id}
          role="option"
          aria-selected={false}
          onClick={() => onSelect(candidate)}
          className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 transition-colors"
        >
          {/* 头像占位 - 用首字 + 五行色 */}
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
            style={{
              backgroundColor: candidate.color?.primary || "#6B7280",
            }}
          >
            {candidate.beast?.[0] || candidate.label[0]}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-medium text-gray-800">
                {candidate.label}
              </span>
              {candidate.element && (
                <span className="text-xs text-gray-400">
                  {candidate.element}
                </span>
              )}
            </div>
            {candidate.beast && (
              <div className="text-xs text-gray-400 truncate">
                {candidate.beast}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
