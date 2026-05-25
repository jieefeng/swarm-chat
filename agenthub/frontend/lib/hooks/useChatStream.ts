"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { createSSEConnection } from "@/lib/sse";
import { useMessageStore } from "@/lib/stores/messageStore";
import type { Message } from "@/lib/types";

interface UseChatStreamOptions {
  agentId: string | null;
  baseUrl: string;
}

interface UseChatStreamReturn {
  sendMessage: (content: string) => Promise<void>;
  disconnect: () => void;
  connectionState:
    | "idle"
    | "connecting"
    | "connected"
    | "reconnecting"
    | "error";
  lastError: string | null;
}

export function useChatStream(
  options: UseChatStreamOptions,
): UseChatStreamReturn {
  const { agentId, baseUrl } = options;
  const [connectionState, setConnectionState] = useState<
    "idle" | "connecting" | "connected" | "reconnecting" | "error"
  >("idle");
  const [lastError, setLastError] = useState<string | null>(null);
  const connectionRef = useRef<ReturnType<typeof createSSEConnection> | null>(
    null,
  );

  const addMessage = useMessageStore((s) => s.addMessage);
  const setStreaming = useMessageStore((s) => s.setStreaming);

  const disconnect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.close();
      connectionRef.current = null;
    }
    setConnectionState("idle");
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!agentId) {
        setLastError("请先选择一个 Agent");
        setConnectionState("error");
        return;
      }

      // 乐观更新：添加用户消息
      const tempId = `temp-${Date.now()}`;
      const timestamp = Math.floor(Date.now() / 1000);
      const userMessage: Message = {
        id: tempId,
        sender: "user",
        sender_name: "用户",
        content,
        timestamp,
        type: "user",
      };
      addMessage(userMessage);

      // 断开旧连接
      disconnect();

      setConnectionState("connecting");
      setStreaming(true);
      setLastError(null);

      try {
        const result = await api.sendMessage(content);
        if (!result.success) {
          throw new Error("发送消息失败");
        }

        setConnectionState("connected");

        // 建立 SSE 连接
        connectionRef.current = createSSEConnection({
          baseUrl,
          onMessage: (data) => {
            if (data.id && data.content) {
              // 检查是否有待替换的 temp 消息
              const currentMessages = useMessageStore.getState().messages;
              const existingIndex = currentMessages.findIndex(
                (m) => m.id.startsWith("temp-") && m.content === content,
              );
              if (existingIndex >= 0) {
                // 替换 temp 消息
                useMessageStore.setState((s) => ({
                  messages: s.messages.map((m, i) =>
                    i === existingIndex ? (data as Message) : m,
                  ),
                }));
              } else {
                addMessage(data as Message);
              }
            }
          },
          onTermination: (_keyword) => {
            setStreaming(false);
            setConnectionState("idle");
          },
          onError: (error) => {
            setLastError(error);
            setConnectionState("reconnecting");
          },
        });
      } catch (err) {
        setLastError(err instanceof Error ? err.message : "发送失败");
        setConnectionState("error");
        setStreaming(false);
      }
    },
    [agentId, baseUrl, addMessage, setStreaming, disconnect],
  );

  // 组件卸载时断开连接
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { sendMessage, disconnect, connectionState, lastError };
}
