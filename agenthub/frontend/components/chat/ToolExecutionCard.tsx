"use client";

import { useState } from "react";
import type { ToolExecution } from "@/lib/types";

interface ToolExecutionCardProps {
  tool: ToolExecution;
}

export function ToolExecutionCard({ tool }: ToolExecutionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const statusConfig = {
    running: {
      icon: "⏳",
      border: "border-gold/20",
      bg: "bg-gold/[0.05]",
      dot: "bg-gold",
    },
    success: {
      icon: "✅",
      border: "border-wuxing-wood/20",
      bg: "bg-wuxing-wood/[0.05]",
      dot: "bg-wuxing-wood",
    },
    error: {
      icon: "❌",
      border: "border-danger/20",
      bg: "bg-danger/[0.05]",
      dot: "bg-danger",
    },
  }[tool.status];

  return (
    <div
      className={`rounded-lg border p-3 my-2 ${statusConfig.border} ${statusConfig.bg}`}
    >
      <div
        className="flex items-center gap-2 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-sm">🔧</span>
        <span className="text-xs font-body font-medium text-ink/70 flex-1">
          {statusConfig.icon} {tool.command}
        </span>
        {tool.status === "running" && (
          <span
            className={`inline-block w-1.5 h-1.5 ${statusConfig.dot} rounded-full animate-pulse`}
          />
        )}
        {tool.output && (
          <span className="text-[10px] text-ink/30">
            {expanded ? "▲" : "▼"}
          </span>
        )}
      </div>
      {expanded && tool.output && (
        <pre className="mt-2 p-2.5 bg-paper-dark/80 rounded-lg text-[11px] text-ink/60 overflow-x-auto max-h-60 overflow-y-auto whitespace-pre-wrap font-mono border border-ink/[0.06]">
          {tool.output}
        </pre>
      )}
    </div>
  );
}
