"use client";

import { useEffect, useState } from "react";
import { AgentList } from "@/components/agents/AgentList";
import { MessageInput } from "@/components/chat/MessageInput";
import { MessageList } from "@/components/chat/MessageList";
import { ModelEditor } from "@/components/chat/ModelEditor";
import { ThreadList } from "@/components/threads/ThreadList";
import { api } from "@/lib/api";
import { useChatStream } from "@/lib/hooks/useChatStream";
import { useAgentStore } from "@/lib/stores/agentStore";
import { useMessageStore } from "@/lib/stores/messageStore";
import { useThreadStore } from "@/lib/stores/threadStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7005";

export default function HomePage() {
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const agents = useAgentStore((s) => s.agents);
  const setAgents = useAgentStore((s) => s.setAgents);
  const messages = useMessageStore((s) => s.messages);
  const { sendMessage, connectionState, lastError } = useChatStream({
    agentId: null,
    baseUrl: API_BASE,
  });

  const handleThreadSelect = async (threadId: string) => {
    useThreadStore.getState().setCurrentThreadId(threadId);
    try {
      const data = await api.getThreadMessages(threadId);
      useMessageStore.getState().reset();
      data.messages?.forEach((m) => {
        useMessageStore.getState().addMessage(m);
      });
    } catch (err) {
      console.error("Failed to load thread messages:", err);
    }
  };

  const handleSendMessage = (content: string) => {
    const mentionMatch = content.match(/@(\w+)/);
    if (mentionMatch?.[1]) {
      setActiveAgentId(mentionMatch[1]);
    }
    sendMessage(content);
  };

  useEffect(() => {
    // 加载初始数据
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents(),
        ]);
        useMessageStore.getState().reset();
        msgsRes.messages?.forEach((m) => {
          useMessageStore.getState().addMessage(m);
        });
        setAgents(agentsRes.agents || []);
      } catch (err) {
        console.error("Failed to load data:", err);
      }
    };
    loadData();
  }, [setAgents]);

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">🐉 AgentHub · 五行神兽</h1>
          {agents.length > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">|</span>
              <span className="text-gray-500">当前模型:</span>
              <ModelEditor
                agentId={
                  activeAgentId && agents.some((a) => a.id === activeAgentId)
                    ? activeAgentId
                    : agents[0]!.id
                }
                agentName={
                  (activeAgentId &&
                    agents.find((a) => a.id === activeAgentId)?.name) ||
                  agents[0]!.name
                }
              />
            </div>
          )}
        </div>
        <div className="text-sm text-gray-500">
          {connectionState === "connected"
            ? "🟢 已连接"
            : connectionState === "connecting"
              ? "🟡 连接中..."
              : "⚪ 空闲"}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* 会话列表侧边栏 */}
        <ThreadList onThreadSelect={handleThreadSelect} />

        {/* 聊天区域 */}
        <div className="flex-1 flex flex-col">
          <AgentList agents={agents} />
          <div className="flex-1 flex flex-col">
            <MessageList messages={messages} agentId={null} />
            <MessageInput
              onSubmit={handleSendMessage}
              disabled={connectionState === "connecting"}
              mentionCandidates={agents.map((a) => ({
                id: a.id,
                label: a.nickname || a.name,
                avatar: a.avatar,
                beast: a.beast,
                element: a.element,
                color: a.color,
              }))}
            />
          </div>
        </div>
      </div>

      {lastError && (
        <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          {lastError}
        </div>
      )}
    </div>
  );
}
