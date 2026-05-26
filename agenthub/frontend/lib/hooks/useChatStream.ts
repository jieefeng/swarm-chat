"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { createSSEConnection } from "@/lib/sse";
import { useMessageStore } from "@/lib/stores/messageStore";
import { useTaskStore } from "@/lib/stores/taskStore";
import type {
  ClarificationRequestEvent,
  Message,
  TaskCreatedEvent,
  TaskUpdateEvent,
} from "@/lib/types";

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
  const addTask = useTaskStore((s) => s.addTask);
  const updateTaskStatus = useTaskStore((s) => s.updateTaskStatus);

  const disconnect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.close();
      connectionRef.current = null;
    }
    setConnectionState("idle");
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      console.log("[DEBUG] sendMessage called with:", content.substring(0, 50));
      // 如果没有选中Agent且消息不是@开头，则拒绝
      if (!agentId && !content.startsWith("@")) {
        console.log("[DEBUG] No agent selected and no @ in message");
        setLastError("请先选择一个 Agent 或使用 @指定Agent");
        setConnectionState("error");
        return;
      }

      // 断开旧连接
      console.log("[DEBUG] Calling disconnect...");
      disconnect();

      // 乐观更新：立即添加用户消息
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
      console.log(
        "[DEBUG] Optimistically adding user message:",
        JSON.stringify(userMessage),
      );
      addMessage(userMessage);

      setConnectionState("connecting");
      setStreaming(true);
      setLastError(null);

      // 建立 SSE 连接接收 agent 回复
      console.log("[DEBUG] Creating SSE connection for agent responses...");
      const conn = createSSEConnection({
        baseUrl,
        onMessage: (data) => {
          console.log("[DEBUG] SSE onMessage:", JSON.stringify(data));
          const normalizedMessage: Message = {
            id: data.id || `msg-${Date.now()}`,
            sender: data.sender || data.role || "unknown",
            sender_name: data.sender_name,
            content: data.content || "",
            timestamp: data.timestamp || Math.floor(Date.now() / 1000),
            type:
              (data.type as "user" | "agent") ||
              (data.role === "user" ? "user" : "agent"),
            agent_id: data.agent_id,
            role: data.role,
          };
          console.log(
            "[DEBUG] Adding message from SSE:",
            JSON.stringify(normalizedMessage),
          );
          addMessage(normalizedMessage);
        },
        onTermination: (_keyword) => {
          console.log("[DEBUG] SSE onTermination");
          setStreaming(false);
          setConnectionState("idle");
        },
        onError: (error) => {
          console.log("[DEBUG] SSE onError:", error);
          setLastError(error);
          setConnectionState("reconnecting");
        },
        onConnected: () => {
          console.log("[DEBUG] SSE onConnected");
          setConnectionState("connected");
        },
        onTaskCreated: (data: TaskCreatedEvent) => {
          console.log("[DEBUG] SSE onTaskCreated:", data.task_id);
          addTask({
            id: data.task_id,
            title: data.title,
            description: "",
            assigned_to: data.assigned_to,
            depends_on: [],
            priority: "medium",
            status: "pending",
            result: null,
            retry_count: 0,
          });
        },
        onTaskUpdate: (data: TaskUpdateEvent) => {
          console.log("[DEBUG] SSE onTaskUpdate:", data.task_id, data.status);
          updateTaskStatus(data.task_id, data.status);
        },
        onClarification: (data: ClarificationRequestEvent) => {
          console.log("[DEBUG] SSE onClarification:", data.question);
          addMessage({
            id: data.message_id || `clarif-${Date.now()}`,
            sender: "system",
            sender_name: "clarification",
            content: JSON.stringify({
              question: data.question,
              options: data.options,
            }),
            timestamp: Math.floor(Date.now() / 1000),
            type: "agent",
          });
        },
      });

      connectionRef.current = conn;

      try {
        console.log("[DEBUG] Calling API sendMessage:", content);
        const result = await api.sendMessage(content, agentId);
        console.log("[DEBUG] API sendMessage result:", JSON.stringify(result));
        if (!result.success) {
          throw new Error("发送消息失败");
        }
      } catch (err) {
        console.log("[DEBUG] API error:", err);
        setLastError(err instanceof Error ? err.message : "发送失败");
        setConnectionState("error");
        setStreaming(false);
        connectionRef.current?.close();
      }
    },
    [
      agentId,
      baseUrl,
      addMessage,
      setStreaming,
      disconnect,
      addTask,
      updateTaskStatus,
    ],
  );

  // 组件卸载时断开连接
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { sendMessage, disconnect, connectionState, lastError };
}
