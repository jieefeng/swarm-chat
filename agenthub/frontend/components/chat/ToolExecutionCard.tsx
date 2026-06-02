"use client";

import { useState } from "react";
import type { ToolExecution } from "@/lib/types";

interface ToolExecutionCardProps {
  tool: ToolExecution;
}

export function ToolExecutionCard({ tool }: ToolExecutionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const statusIcon = {
    running: "⏳",
    success: "✅",
    error: "❌",
  }[tool.status];

  const statusColor = {
    running: "border-blue-300 bg-blue-50",
    success: "border-green-300 bg-green-50",
    error: "border-red-300 bg-red-50",
  }[tool.status];

  return (
    <div className={`rounded-lg border p-3 my-2 ${statusColor}`}>
      <div
        className="flex items-center gap-2 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-sm">🔧</span>
        <span className="text-xs font-medium text-gray-700 flex-1">
          {statusIcon} {tool.command}
        </span>
        {tool.status === "running" && (
          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        )}
        {tool.output && (
          <span className="text-xs text-gray-400">
            {expanded ? "▲" : "▼"}
          </span>
        )}
      </div>
      {expanded && tool.output && (
        <pre className="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-700 overflow-x-auto max-h-60 overflow-y-auto whitespace-pre-wrap">
          {tool.output}
        </pre>
      )}
    </div>
  );
}
