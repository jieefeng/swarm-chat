"use client";

import { useState } from "react";
import {
  type BeastId,
  WUXING_BEASTS,
  WUXING_FLOW_INDEX,
  WUXING_FLOW_ORDER,
} from "@/lib/wuxing";

const CENTER_X = 200;
const CENTER_Y = 200;
const RADIUS = 130;
const NODE_R = 38;

function nodePosition(index: number, total: number) {
  // 5 个节点从顶部开始顺时针排布
  const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
  return {
    x: CENTER_X + RADIUS * Math.cos(angle),
    y: CENTER_Y + RADIUS * Math.sin(angle),
  };
}

export function WuxingFlow() {
  const [hovered, setHovered] = useState<BeastId | null>(null);

  // 实时示例对话步骤（基于 WUXING_FLOW_ORDER）
  const flowSteps = WUXING_FLOW_ORDER.map((id) => {
    const b = WUXING_BEASTS.find((beast) => beast.id === id)!;
    return { id, beast: b };
  });

  return (
    <section className="px-6 py-16 md:py-20 max-w-5xl mx-auto">
      <div className="text-center mb-10">
        <h2 className="font-display text-2xl md:text-3xl font-semibold text-ink">
          五行流转
        </h2>
        <p className="font-body text-sm text-ink/50 mt-2">
          每一步是上一段的果，是下一段的因
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-10 items-center">
        {/* SVG 转盘 */}
        <div className="flex justify-center">
          <svg
            viewBox="0 0 400 400"
            className="w-full max-w-[400px] h-auto"
            aria-label="五行流转图"
          >
            {/* 相生箭头（5 条曲线） */}
            {flowSteps.map((step, i) => {
              const next = flowSteps[(i + 1) % flowSteps.length]!;
              const p1 = nodePosition(i, flowSteps.length);
              const p2 = nodePosition(
                (i + 1) % flowSteps.length,
                flowSteps.length,
              );
              const midX = (p1.x + p2.x) / 2;
              const midY = (p1.y + p2.y) / 2;
              // 切线偏移让曲线略外凸（垂直于弦方向，指向远离圆心）
              const dx = p2.x - p1.x;
              const dy = p2.y - p1.y;
              const nx = dy * 0.18;
              const ny = -dx * 0.18;
              return (
                <path
                  key={`arrow-${step.id}`}
                  d={`M ${p1.x} ${p1.y} Q ${midX + nx} ${midY + ny} ${p2.x} ${p2.y}`}
                  fill="none"
                  stroke={step.beast.color.primary}
                  strokeWidth={1.5}
                  strokeOpacity={0.4}
                  strokeDasharray="3 4"
                />
              );
            })}

            {/* 中心 "议事" 字样 */}
            <text
              x={CENTER_X}
              y={CENTER_Y - 8}
              textAnchor="middle"
              className="font-display"
              fontSize={28}
              fill="#2c2c3a"
              fontWeight={500}
            >
              议事
            </text>
            <text
              x={CENTER_X}
              y={CENTER_Y + 18}
              textAnchor="middle"
              className="font-body"
              fontSize={11}
              fill="#2c2c3a"
              opacity={0.5}
            >
              五行自转
            </text>

            {/* 5 节点 */}
            {flowSteps.map((step, i) => {
              const p = nodePosition(i, flowSteps.length);
              const isHovered = hovered === step.id;
              return (
                <g
                  key={step.id}
                  role="button"
                  tabIndex={0}
                  aria-label={step.beast.nickname}
                  className="reveal-beast"
                  style={{
                    cursor: "pointer",
                    animationDelay: `${WUXING_FLOW_INDEX[step.id] * 140}ms`,
                  }}
                  onMouseEnter={() => setHovered(step.id)}
                  onMouseLeave={() => setHovered(null)}
                  onFocus={() => setHovered(step.id)}
                  onBlur={() => setHovered(null)}
                >
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={isHovered ? NODE_R + 4 : NODE_R}
                    fill={step.beast.color.secondary}
                    stroke={step.beast.color.primary}
                    strokeWidth={isHovered ? 3 : 2}
                    style={{ transition: "all 0.2s ease" }}
                  />
                  <text
                    x={p.x}
                    y={p.y + 4}
                    textAnchor="middle"
                    className="font-display"
                    fontSize={18}
                    fill={step.beast.color.primary}
                    fontWeight={600}
                  >
                    {step.beast.verb}
                  </text>
                  <text
                    x={p.x}
                    y={p.y + NODE_R + 18}
                    textAnchor="middle"
                    className="font-display"
                    fontSize={13}
                    fill="#2c2c3a"
                  >
                    {step.beast.nickname}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* 右侧：当前 hover 详情 / 默认示例 */}
        <div className="space-y-4">
          {hovered ? (
            (() => {
              const b = WUXING_BEASTS.find((beast) => beast.id === hovered)!;
              return (
                <div
                  className="prose-ink rounded-2xl p-6 border-2"
                  style={{
                    borderColor: b.color.primary,
                    backgroundColor: b.color.secondary,
                  }}
                >
                  <div className="font-display text-xl text-ink mb-1 leading-tight tracking-display">
                    {b.nickname} · {b.verb}
                  </div>
                  <div className="font-body text-xs text-ink/60 mb-3">
                    {b.role} · {b.element} · {b.direction} · {b.season}
                  </div>
                  <p className="font-body text-sm text-ink/80 italic mb-3 leading-normal">
                    「{b.catchphrase}」
                  </p>
                  <p className="font-body text-xs text-ink/60 leading-normal">
                    擅长：{b.strengths.join("、")}
                  </p>
                </div>
              );
            })()
          ) : (
            <div className="rounded-2xl p-6 border border-ink/10 bg-paper">
              <div className="font-display text-sm text-ink/70 mb-3">
                真实示例
              </div>
              <pre className="font-mono text-xs text-ink/70 whitespace-pre-wrap leading-relaxed">
                {`@瑞麟 加个深色模式
  → 瑞麟拆解任务
  → @苍龙 厘清需求
  → @啸风 实现
  → @炎翎 试火
  → @玄冥 复查架构
  → 完事`}
              </pre>
              <p className="font-body text-[11px] text-ink/40 mt-3">
                鼠标 hover 转盘节点看每个神兽的细节
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
