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

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [ref]);

  // 构建 agent_id -> color 映射
  const agentColorMap = new Map<string, string>();
  for (const agent of agents) {
    if (agent.color?.primary) {
      agentColorMap.set(agent.id, agent.color.primary);
    }
  }

  return (
    <div ref={ref} className="flex-1 overflow-y-auto p-4 bg-gray-50">
      {messages.length === 0 ? (
        <div className="text-center text-gray-400 mt-20">
          暂无消息，开始对话吧
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
