"use client";

import { useEffect, useState } from "react";
import { AgentSelector } from "@/components/agents/AgentSelector";
import { DefaultAgentModal } from "@/components/agents/DefaultAgentModal";
import { SetDefaultConfirmToast } from "@/components/agents/SetDefaultConfirmToast";
import { MessageInput } from "@/components/chat/MessageInput";
import { MessageList } from "@/components/chat/MessageList";
import { ModelEditor } from "@/components/chat/ModelEditor";
import { ThreadList } from "@/components/threads/ThreadList";
import { api } from "@/lib/api";
import { useChatStream } from "@/lib/hooks/useChatStream";
import {
  getStoredDefaultAgentId,
  useDefaultAgent,
} from "@/lib/hooks/useDefaultAgent";
import { useAgentStore } from "@/lib/stores/agentStore";
import { useMessageStore } from "@/lib/stores/messageStore";
import { useThreadStore } from "@/lib/stores/threadStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7005";

export default function HomePage() {
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [pendingThreadId, setPendingThreadId] = useState<string | null>(null);
  const [pendingDefaultAgentId, setPendingDefaultAgentId] = useState<
    string | null
  >(null);

  const agents = useAgentStore((s) => s.agents);
  const setAgents = useAgentStore((s) => s.setAgents);
  const messages = useMessageStore((s) => s.messages);
  const currentThreadId = useThreadStore((s) => s.currentThreadId);

  const { defaultAgentId, setDefaultAgentId } =
    useDefaultAgent(currentThreadId);

  const { sendMessage, connectionState, lastError } = useChatStream({
    agentId: null,
    baseUrl: API_BASE,
  });

  const handleThreadSelect = async (threadId: string) => {
    // 同步检查 localStorage 中是否有默认 Agent
    const storedDefaultAgent = getStoredDefaultAgentId(threadId);

    if (!storedDefaultAgent) {
      // 无默认 Agent → 弹窗，用户选择后再切换
      setPendingThreadId(threadId);
      setShowAgentModal(true);
      return;
    }

    // 有默认 Agent → 正常切换
    useThreadStore.getState().setCurrentThreadId(threadId);
    setActiveAgentId(storedDefaultAgent);
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

  const handleThreadCreate = async () => {
    try {
      const newThread = await api.createThread();
      useThreadStore.getState().addThread(newThread);
      useThreadStore.getState().setCurrentThreadId(newThread.id);
      setPendingThreadId(newThread.id);
      setShowAgentModal(true);
    } catch (err) {
      console.error("Failed to create thread:", err);
    }
  };

  const handleAgentSelect = (agentId: string) => {
    setDefaultAgentId(agentId);
    setActiveAgentId(agentId);
    setShowAgentModal(false);

    if (pendingThreadId) {
      handleThreadSelect(pendingThreadId);
      setPendingThreadId(null);
    }
  };

  const handleAgentModalSkip = () => {
    setShowAgentModal(false);

    if (pendingThreadId) {
      handleThreadSelect(pendingThreadId);
      setPendingThreadId(null);
    }
  };

  const handleSendMessage = (content: string) => {
    const mentionMatch = content.match(/@(\w+)/);
    if (mentionMatch?.[1]) {
      setActiveAgentId(mentionMatch[1]);
      sendMessage(content);
    } else {
      // 使用默认 Agent
      const agentId =
        defaultAgentId || (agents.length > 0 ? agents[0]?.id : undefined);
      sendMessage(content, agentId);
    }
  };

  useEffect(() => {
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

  // 切换 thread 时清掉"设为默认"待处理状态，避免跨 thread 误操作
  useEffect(() => {
    setPendingDefaultAgentId(null);
  }, [currentThreadId]);

  const connectionLabel = {
    connected: {
      dot: "bg-emerald-400",
      text: "已连接",
      glow: "shadow-emerald-400/40",
    },
    connecting: {
      dot: "bg-amber-400",
      text: "连接中…",
      glow: "shadow-amber-400/40",
    },
    reconnecting: {
      dot: "bg-amber-400",
      text: "重连中…",
      glow: "shadow-amber-400/40",
    },
    error: { dot: "bg-red-400", text: "连接失败", glow: "shadow-red-400/40" },
    idle: { dot: "bg-gray-500", text: "空闲", glow: "" },
  }[connectionState] ?? { dot: "bg-gray-500", text: "空闲", glow: "" };

  return (
    <div className="flex flex-col h-screen">
      {/* ── 顶部栏 ── */}
      <header className="flex justify-between items-center px-6 py-3 border-b border-ink/[0.08] bg-paper/80 backdrop-blur-sm">
        <div className="flex items-center gap-5">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <span className="text-2xl leading-none">🐉</span>
              <div className="absolute -inset-1 bg-gold/10 rounded-full blur-md -z-10" />
            </div>
            <div>
              <h1 className="font-display text-lg font-semibold text-ink tracking-wide">
                AgentHub
              </h1>
              <p className="font-display text-[10px] text-gold-dim/60 tracking-[0.3em] -mt-0.5">
                五行神兽
              </p>
            </div>
          </div>

          {/* 模型编辑器 */}
          {agents.length > 0 && (
            <div className="flex items-center gap-2 pl-5 border-l border-ink/[0.08]">
              <span className="text-xs text-ink/40 font-body">模型</span>
              <ModelEditor
                agentId={
                  activeAgentId && agents.some((a) => a.id === activeAgentId)
                    ? activeAgentId
                    : (agents[0]?.id ?? "")
                }
                agentName={
                  ((activeAgentId &&
                    agents.find((a) => a.id === activeAgentId)?.name) ||
                    agents[0]?.name) ??
                  ""
                }
              />
            </div>
          )}
        </div>

        {/* 连接状态 */}
        <div className="flex items-center gap-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${connectionLabel.dot} shadow-sm ${connectionLabel.glow}`}
          />
          <span className="text-xs text-ink/50 font-body">
            {connectionLabel.text}
          </span>
        </div>
      </header>

      {/* ── 主内容区 ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* 会话列表 */}
        <ThreadList
          onThreadSelect={handleThreadSelect}
          onThreadCreate={handleThreadCreate}
        />

        {/* 聊天区域 */}
        <div className="flex-1 flex flex-col bg-paper relative">
          {/* 微妙的光晕背景 */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gold/[0.04] rounded-full blur-[100px]" />
          </div>

          <div className="relative flex-shrink-0 border-b border-ink/[0.06]">
            <AgentSelector
              agents={agents}
              activeAgentId={activeAgentId}
              defaultAgentId={defaultAgentId}
              onAgentSelect={setActiveAgentId}
              onSetDefault={setPendingDefaultAgentId}
            />
          </div>
          <div className="relative flex-1 flex flex-col">
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

      {/* 默认 Agent 选择弹窗 */}
      {showAgentModal && (
        <DefaultAgentModal
          agents={agents}
          onSelect={handleAgentSelect}
          onSkip={handleAgentModalSkip}
        />
      )}

      {/* 「设为默认」居中确认 modal */}
      {pendingDefaultAgentId &&
        (() => {
          const pendingAgent = agents.find(
            (a) => a.id === pendingDefaultAgentId,
          );
          if (!pendingAgent) return null;
          return (
            <SetDefaultConfirmToast
              agentName={pendingAgent.nickname || pendingAgent.name}
              onConfirm={() => {
                setDefaultAgentId(pendingDefaultAgentId);
                setPendingDefaultAgentId(null);
              }}
              onCancel={() => setPendingDefaultAgentId(null)}
            />
          );
        })()}

      {/* 错误提示 */}
      {lastError && (
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2 bg-danger/90 text-white px-5 py-2.5 rounded-lg shadow-lg shadow-danger/20 backdrop-blur-sm border border-danger/30 font-body text-sm animate-fade-in-up">
          {lastError}
        </div>
      )}
    </div>
  );
}
