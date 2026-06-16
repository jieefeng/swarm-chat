"use client";

import type { MentionCandidate } from "@/lib/types";

interface MentionDropdownProps {
  candidates: MentionCandidate[];
  onSelect: (candidate: MentionCandidate) => void;
  /** 下拉框标题，默认 "选择神兽" */
  title?: string;
}

export function MentionDropdown({
  candidates,
  onSelect,
  title,
}: MentionDropdownProps) {
  if (candidates.length === 0) {
    return null;
  }

  const isCommandMode = candidates[0]?.isCommand ?? false;
  const ariaLabel = title || (isCommandMode ? "选择命令" : "选择神兽");

  return (
    <div
      role="listbox"
      aria-label={ariaLabel}
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
          {/* 图标区域 */}
          <div className="relative shrink-0">
            <div
              className={`w-7 h-7 flex items-center justify-center text-xs font-bold font-display ${
                isCommandMode
                  ? "rounded-lg bg-ink/[0.06] text-ink/50"
                  : "rounded-full text-white"
              }`}
              style={
                !isCommandMode
                  ? {
                      backgroundColor: candidate.color?.primary || "#6B7280",
                    }
                  : undefined
              }
            >
              {isCommandMode
                ? candidate.icon || (candidate.label[0] ?? "").toUpperCase()
                : candidate.beast?.[0] || candidate.label[0] || ""}
            </div>
            {!isCommandMode && (
              <div
                className="absolute -inset-0.5 rounded-full blur-sm opacity-25 -z-10"
                style={{
                  backgroundColor: candidate.color?.primary || "#6B7280",
                }}
              />
            )}
          </div>

          {/* 文本区域 */}
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
            {/* 命令模式显示 description，Agent 模式显示 beast */}
            {isCommandMode && candidate.description ? (
              <div className="text-[11px] text-ink/40 truncate font-body">
                {candidate.description}
              </div>
            ) : candidate.beast ? (
              <div className="text-[11px] text-ink/25 truncate font-body">
                {candidate.beast}
              </div>
            ) : null}
          </div>
        </button>
      ))}
    </div>
  );
}
