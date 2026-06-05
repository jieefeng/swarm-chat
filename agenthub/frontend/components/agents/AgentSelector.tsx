"use client";

import { useState } from "react";
import type { Agent } from "@/lib/types";
import { AgentConfigModal } from "./AgentConfigModal";

interface AgentSelectorProps {
  agents: Agent[];
  activeAgentId: string | null;
  onAgentSelect: (agentId: string) => void;
}

const ELEMENT_EMOJI: Record<string, string> = {
  木: "🌿",
  水: "💧",
  金: "⚔️",
  火: "🔥",
  土: "🪨",
};

export function AgentSelector({
  agents,
  activeAgentId,
  onAgentSelect,
}: AgentSelectorProps) {
  const [configModalAgent, setConfigModalAgent] = useState<Agent | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  return (
    <>
      <div className="flex items-center gap-1.5 px-4 py-2">
        {agents.map((agent) => {
          const isActive = agent.id === activeAgentId;
          return (
            <div
              key={agent.id}
              role="button"
              tabIndex={0}
              onClick={() => onAgentSelect(agent.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onAgentSelect(agent.id);
                }
              }}
              className={`
                group relative flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer
                transition-all duration-150
                ${isActive ? "bg-ink/[0.08] shadow-sm" : "hover:bg-ink/[0.04]"}
              `}
            >
              {/* 头像 */}
              <div className="relative shrink-0">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-bold font-display"
                  style={{
                    backgroundColor: agent.color?.primary || "#6B7280",
                  }}
                >
                  {agent.beast?.[0] || agent.name[0]}
                </div>
                {isActive && (
                  <div
                    className="absolute -inset-0.5 rounded-full blur-sm opacity-40 -z-10"
                    style={{
                      backgroundColor: agent.color?.primary || "#6B7280",
                    }}
                  />
                )}
              </div>

              {/* 名称 */}
              <span
                className={`text-xs font-body font-medium truncate max-w-[80px] ${
                  isActive
                    ? "text-ink/90"
                    : "text-ink/50 group-hover:text-ink/70"
                }`}
              >
                {agent.nickname || agent.name}
              </span>

              {/* 元素图标 */}
              {agent.element && (
                <span className="text-[10px] opacity-60" title={agent.element}>
                  {ELEMENT_EMOJI[agent.element] || ""}
                </span>
              )}

              {/* 设置按钮 */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setConfigModalAgent(agent);
                }}
                className="ml-0.5 p-0.5 text-ink/20 hover:text-gold/60 transition-colors opacity-0 group-hover:opacity-100"
                title="设置"
              >
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </button>
            </div>
          );
        })}
      </div>

      {/* 配置 Modal */}
      {configModalAgent && (
        <AgentConfigModal
          agent={configModalAgent}
          onClose={() => setConfigModalAgent(null)}
          onSave={() => {
            setConfigModalAgent(null);
            setToast("配置已更新");
            setTimeout(() => setToast(null), 2000);
          }}
        />
      )}

      {/* Toast 提示 */}
      {toast && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 bg-white/95 text-ink/80 text-xs py-2.5 px-4 rounded-lg shadow-lg border border-ink/[0.1] backdrop-blur-sm font-body animate-fade-in-up z-50">
          {toast}
        </div>
      )}
    </>
  );
}
