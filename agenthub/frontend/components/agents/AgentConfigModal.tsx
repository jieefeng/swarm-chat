"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent, AgentConfig } from "@/lib/types";

interface AgentConfigModalProps {
  agent: Agent;
  onClose: () => void;
  onSave: () => void;
}

const PROVIDER_LABELS: Record<string, string> = {
  bailian: "阿里云百炼",
  minimax: "MiniMax",
};

export function AgentConfigModal({ agent, onClose, onSave }: AgentConfigModalProps) {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [modelInput, setModelInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    api.getAgentConfig(agent.id).then((data) => {
      if (cancelled) return;
      setConfig(data);
      setModelInput(data.model || "");
      setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      console.error("Failed to load config:", err);
      setError("加载配置失败");
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [agent.id]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateAgentConfig(agent.id, { model: modelInput });
      onSave();
    } catch (err) {
      console.error("Failed to save config:", err);
      setError("保存失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal 内容 */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        {/* 标题栏 */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">
            {agent.nickname || agent.name}（{agent.beast}）配置
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-gray-500">加载中...</div>
        ) : (
          <>
            {/* 平台显示（只读） */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">平台</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-md text-sm text-gray-600">
                {PROVIDER_LABELS[config?.llm_provider || "bailian"] || config?.llm_provider}
              </div>
            </div>

            {/* 模型输入框 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
              <input
                type="text"
                value={modelInput}
                onChange={(e) => setModelInput(e.target.value)}
                placeholder="留空使用默认模型"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">
                {config?.model ? `当前模型: ${config.model}` : "使用默认模型"}
              </p>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-600">
                {error}
              </div>
            )}

            {/* 按钮栏 */}
            <div className="flex justify-end gap-3">
              <button
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? "保存中..." : "保存"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
