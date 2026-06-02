"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent } from "@/lib/types";
import { AgentConfigModal } from "./AgentConfigModal";

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

const PROVIDER_LABELS: Record<string, string> = {
  bailian: "阿里云百炼",
  minimax: "MiniMax",
};

export function AgentList({ agents }: AgentListProps) {
  const [llmConfig, setLlmConfig] = useState<
    Record<string, { llm_provider: string }>
  >({});
  const [saving, setSaving] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [configModalAgent, setConfigModalAgent] = useState<Agent | null>(null);

  useEffect(() => {
    api.getLLMConfig().then(setLlmConfig).catch(console.error);
  }, []);

  const handleProviderChange = async (agentId: string, provider: string) => {
    setSaving(agentId);
    try {
      await api.updateLLMConfig(agentId, provider);
      setLlmConfig((prev) => ({
        ...prev,
        [agentId]: { llm_provider: provider },
      }));
      setToast(`已切换到 ${PROVIDER_LABELS[provider] || provider}`);
      setTimeout(() => setToast(null), 2000);
    } catch (error) {
      console.error("Failed to update LLM config:", error);
      setToast("切换失败，请重试");
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="w-56 bg-white border-r border-gray-200 p-4 overflow-y-auto relative">
      <div className="text-sm font-semibold text-gray-700 pb-3 border-b border-gray-200">
        🐉 五行神兽
      </div>
      {agents.map((agent) => (
        <div
          key={agent.id}
          className="py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors rounded-lg px-2 -mx-2"
        >
          <div className="flex items-center gap-2">
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
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setConfigModalAgent(agent);
                }}
                className="ml-auto p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="设置"
              >
                <svg
                  className="w-4 h-4"
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
              {agent.beast && (
                <div className="text-xs text-gray-400 truncate">
                  {agent.beast}
                </div>
              )}
            </div>
          </div>

          {/* LLM Provider 选择器 */}
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-500">LLM:</span>
            <select
              value={llmConfig[agent.id]?.llm_provider || "bailian"}
              onChange={(e) => handleProviderChange(agent.id, e.target.value)}
              disabled={saving === agent.id}
              className="text-xs border border-gray-200 rounded px-1.5 py-0.5 bg-white disabled:opacity-50"
            >
              <option value="bailian">阿里云百炼</option>
              <option value="minimax">MiniMax</option>
            </select>
          </div>

          {agent.catchphrase && (
            <div className="text-xs text-gray-400 mt-1 italic truncate">
              "{agent.catchphrase}"
            </div>
          )}
        </div>
      ))}

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
        <div className="absolute bottom-4 left-4 right-4 bg-gray-800 text-white text-xs py-2 px-3 rounded shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}
