"use client";

import { useEffect, useRef } from "react";
import { useAgentStore } from "@/lib/stores/agentStore";
import type { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  agentId: string | null;
  scrollRef?: React.RefObject<HTMLDivElement> | null;
}

export function MessageList({ messages, scrollRef }: MessageListProps) {
  const internalRef = useRef<HTMLDivElement>(null);
  const ref = scrollRef ?? internalRef;
  const agents = useAgentStore((s) => s.agents);

  // 新消息到达时自动滚动到底部
  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [ref, messages]);

  // 构建 agent_id -> color 映射
  const agentColorMap = new Map<string, string>();
  for (const agent of agents) {
    if (agent.color?.primary) {
      agentColorMap.set(agent.id, agent.color.primary);
    }
  }

  return (
    <div ref={ref} className="flex-1 min-h-0 overflow-y-auto p-5">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="text-4xl mb-4 opacity-30">🐉</div>
          <p className="text-ink/30 font-display text-sm tracking-wider">
            暂无消息，开始对话吧
          </p>
          <p className="text-ink/20 font-body text-xs mt-2">
            输入消息或 @ 某位神兽
          </p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageBubble
            key={msg.id || `msg-${index}-${msg.timestamp}`}
            message={msg}
            isStreaming={false}
            agentColor={
              msg.agent_id ? agentColorMap.get(msg.agent_id) : undefined
            }
          />
        ))
      )}
    </div>
  );
}
