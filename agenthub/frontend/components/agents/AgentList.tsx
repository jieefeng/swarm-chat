"use client";

import type { Agent } from "@/lib/types";

interface AgentListProps {
  agents: Agent[];
}

const ELEMENT_EMOJI: Record<string, string> = {
  木: "🌿",
  水: "💧",
  金: "⚔️",
  火: "🔥",
  土: "🪨",
};

export function AgentList({ agents }: AgentListProps) {
  return (
    <div className="w-56 bg-white border-r border-gray-200 p-4 overflow-y-auto">
      <div className="text-sm font-semibold text-gray-700 pb-3 border-b border-gray-200">
        🐉 五行神兽
      </div>
      {agents.map((agent) => (
        <div
          key={agent.id}
          className="py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors rounded-lg px-2 -mx-2"
        >
          <div className="flex items-center gap-2">
            {/* 头像占位 - 后续替换为真实图片 */}
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
              style={{ backgroundColor: agent.color?.primary || "#6B7280" }}
            >
              {agent.beast?.[0] || agent.name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {agent.nickname || agent.name}
                </span>
                {agent.element && (
                  <span className="text-xs" title={agent.element}>
                    {ELEMENT_EMOJI[agent.element] || ""}
                  </span>
                )}
              </div>
              {agent.beast && (
                <div className="text-xs text-gray-400 truncate">
                  {agent.beast}
                </div>
              )}
            </div>
          </div>
          {agent.catchphrase && (
            <div className="text-xs text-gray-400 mt-1 italic truncate">
              "{agent.catchphrase}"
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
