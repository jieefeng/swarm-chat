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
      className="bg-white/95 border border-ink/[0.1] rounded-xl shadow-xl shadow-ink/10 py-1.5 backdrop-blur-md"
    >
      {candidates.map((candidate) => (
        <button
          type="button"
          key={candidate.id}
          role="option"
          aria-selected={false}
          onClick={() => onSelect(candidate)}
          className="w-full px-4 py-2.5 text-left hover:bg-ink/[0.04] flex items-center gap-3 transition-colors"
        >
          <div className="relative shrink-0">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold font-display"
              style={{
                backgroundColor: candidate.color?.primary || "#6B7280",
              }}
            >
              {candidate.beast?.[0] || candidate.label[0]}
            </div>
            <div
              className="absolute -inset-0.5 rounded-full blur-sm opacity-25 -z-10"
              style={{
                backgroundColor: candidate.color?.primary || "#6B7280",
              }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-body font-medium text-ink/80">
                {candidate.label}
              </span>
              {candidate.element && (
                <span className="text-[10px] text-ink/30">
                  {candidate.element}
                </span>
              )}
            </div>
            {candidate.beast && (
              <div className="text-[11px] text-ink/25 truncate font-body">
                {candidate.beast}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
