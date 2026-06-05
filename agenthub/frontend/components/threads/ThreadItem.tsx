"use client";

import { TrashIcon } from "@heroicons/react/24/outline";
import type { Thread } from "@/lib/types";

interface ThreadItemProps {
  thread: Thread;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
}

export function ThreadItem({
  thread,
  isActive,
  onClick,
  onDelete,
}: ThreadItemProps) {
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffDays === 1) {
      return "昨天";
    } else if (diffDays < 7) {
      return `${diffDays} 天前`;
    } else {
      return date.toLocaleDateString("zh-CN", {
        month: "short",
        day: "numeric",
      });
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200 ${
        isActive
          ? "bg-gold/10 border border-gold/15"
          : "hover:bg-ink/[0.03] border border-transparent"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-body truncate ${isActive ? "text-gold-dim" : "text-ink/70"}`}
          >
            {thread.title}
          </span>
          {thread.is_pinned && (
            <span className="text-[10px] text-gold/60">📌</span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[11px] text-ink/35 font-body">
            {formatDate(thread.updated_at)}
          </span>
          <span className="text-[11px] text-ink/25 font-body">
            {thread.message_count} 条
          </span>
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="opacity-0 group-hover:opacity-100 p-1 text-ink/25 hover:text-danger transition-all duration-200"
      >
        <TrashIcon className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
