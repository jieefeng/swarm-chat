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

export function AgentConfigModal({
  agent,
  onClose,
  onSave,
}: AgentConfigModalProps) {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [providerInput, setProviderInput] = useState("bailian");
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
    api
      .getAgentConfig(agent.id)
      .then((data) => {
        if (cancelled) return;
        setConfig(data);
        setProviderInput(data.llm_provider || "bailian");
        setModelInput(data.model || "");
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error("Failed to load config:", err);
        setError("加载配置失败");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [agent.id]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateAgentConfig(agent.id, {
        llm_provider: providerInput,
        model: modelInput,
      });
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
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal 内容 */}
      <div className="relative bg-white border border-ink/[0.1] rounded-xl shadow-2xl shadow-ink/10 w-full max-w-md mx-4 p-6 animate-ink-drop">
        {/* 标题栏 */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display text-lg font-semibold text-ink tracking-wide">
            {agent.nickname || agent.name}（{agent.beast}）配置
          </h2>
          <button
            onClick={onClose}
            className="text-ink/30 hover:text-ink/60 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-ink/30 font-body">加载中…</div>
        ) : (
          <>
            {/* 平台选择 */}
            <div className="mb-4">
              <label className="block text-xs font-body font-medium text-ink/50 mb-1.5 tracking-wide">
                平台
              </label>
              <select
                value={providerInput}
                onChange={(e) => setProviderInput(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-ink/[0.1] rounded-lg text-sm text-ink focus:outline-none focus:border-gold/40 transition-colors font-body"
              >
                {Object.entries(PROVIDER_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* 模型输入框 */}
            <div className="mb-5">
              <label className="block text-xs font-body font-medium text-ink/50 mb-1.5 tracking-wide">
                模型名称
              </label>
              <input
                type="text"
                value={modelInput}
                onChange={(e) => setModelInput(e.target.value)}
                placeholder="留空使用默认模型"
                className="w-full px-3 py-2 bg-white border border-ink/[0.1] rounded-lg text-sm text-ink placeholder:text-ink/30 focus:outline-none focus:border-gold/40 transition-colors font-body"
              />
              <p className="mt-1.5 text-[11px] text-ink/30 font-body">
                {config?.model ? `当前模型: ${config.model}` : "使用默认模型"}
              </p>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body">
                {error}
              </div>
            )}

            {/* 按钮栏 */}
            <div className="flex justify-end gap-3">
              <button
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 text-sm font-body font-medium text-ink/50 bg-ink/[0.04] border border-ink/[0.08] rounded-lg hover:bg-ink/[0.06] disabled:opacity-40 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 text-sm font-body font-medium text-gold bg-gold/15 border border-gold/25 rounded-lg hover:bg-gold/25 disabled:opacity-40 transition-colors"
              >
                {saving ? "保存中…" : "保存"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
