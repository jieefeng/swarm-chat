"use client";

import { useState } from "react";
import type { Agent } from "@/lib/types";
import { WUXING_BEASTS } from "@/lib/wuxing";

// 五行神兽 fallback SVG
const BEAST_SVGS: Record<string, string> = {
  pm: "龙",
  architect: "龟",
  developer: "虎",
  qa: "雀",
  orchestrator: "麟",
};

// 颜色从 wuxing.ts 取，按 element 索引
const ELEMENT_COLOR_MAP: Record<
  string,
  { primary: string; secondary: string }
> = Object.fromEntries(WUXING_BEASTS.map((b) => [b.element, b.color]));

interface DefaultAgentModalProps {
  agents: Agent[];
  onSelect: (agentId: string) => void;
  onSkip?: () => void;
}

export function DefaultAgentModal({
  agents,
  onSelect,
  onSkip,
}: DefaultAgentModalProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleConfirm = () => {
    if (selectedId) {
      onSelect(selectedId);
    }
  };

  const handleSkip = () => {
    // 默认选择第一个 Agent
    if (agents.length > 0) {
      onSelect(agents[0]?.id ?? "");
    }
    onSkip?.();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm">
      <div className="bg-paper rounded-2xl shadow-2xl shadow-ink/10 border border-ink/[0.08] p-6 w-[480px] max-w-[90vw]">
        {/* 标题 */}
        <div className="text-center mb-6">
          <h2 className="font-display text-xl font-semibold text-ink">
            选择默认 Agent
          </h2>
          <p className="font-body text-sm text-ink/50 mt-2">
            选择一个 Agent 作为当前会话的默认对话对象
          </p>
        </div>

        {/* Agent 卡片列表 */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => setSelectedId(agent.id)}
              className={`flex flex-col items-center p-4 rounded-xl border-2 transition-all duration-200 ${
                selectedId === agent.id
                  ? "border-gold/50 bg-gold/5 shadow-lg shadow-gold/10"
                  : "border-ink/[0.08] hover:border-ink/[0.15] hover:bg-ink/[0.02]"
              }`}
            >
              {/* Avatar */}
              <div className="w-16 h-16 mb-2 flex items-center justify-center">
                <AvatarFallback
                  agentId={agent.id}
                  element={agent.element}
                  beast={BEAST_SVGS[agent.id]}
                />
              </div>

              {/* Name */}
              <div className="font-display text-sm font-medium text-ink">
                {agent.nickname || agent.name}
              </div>

              {/* Role */}
              <div className="font-body text-xs text-ink/40 mt-1">
                {agent.role}
              </div>

              {/* Element badge */}
              {agent.element && (
                <div className="mt-2 px-2 py-0.5 rounded-full bg-ink/[0.05] text-ink/30 text-[10px] font-body">
                  {agent.element}
                </div>
              )}
            </button>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3">
          {onSkip && (
            <button
              type="button"
              onClick={handleSkip}
              className="flex-1 px-4 py-2.5 rounded-xl border border-ink/[0.1] text-ink/50 font-body text-sm hover:bg-ink/[0.02] transition-colors"
            >
              跳过（使用默认）
            </button>
          )}
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!selectedId}
            className={`flex-1 px-4 py-2.5 rounded-xl font-display text-sm font-medium transition-all duration-200 ${
              selectedId
                ? "bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 hover:shadow-lg hover:shadow-gold/10"
                : "bg-ink/[0.03] text-ink/25 border border-ink/[0.08] cursor-not-allowed"
            }`}
          >
            确认选择
          </button>
        </div>
      </div>
    </div>
  );
}

// 内联 SVG 头像组件
function AvatarFallback({
  agentId,
  element,
  beast,
}: {
  agentId: string;
  element?: string;
  beast?: string;
}) {
  const color = element
    ? ELEMENT_COLOR_MAP[element]?.primary || "#6B7280"
    : "#6B7280";
  const char = beast || agentId[0]?.toUpperCase() || "?";

  return (
    <svg viewBox="0 0 128 128" className="w-full h-full">
      <defs>
        <radialGradient id={`grad-${agentId}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={color} stopOpacity="0.8" />
          <stop offset="100%" stopColor={color} />
        </radialGradient>
      </defs>
      <circle cx="64" cy="64" r="60" fill={`url(#grad-${agentId})`} />
      <text
        x="64"
        y="80"
        textAnchor="middle"
        fontSize="64"
        fontFamily="serif"
        fill="white"
        fontWeight="bold"
      >
        {char}
      </text>
    </svg>
  );
}
