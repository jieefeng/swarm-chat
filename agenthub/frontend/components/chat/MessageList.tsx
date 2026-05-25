"use client";

import { useEffect, useRef } from "react";
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

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [ref]);

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
          />
        ))
      )}
    </div>
  );
}
