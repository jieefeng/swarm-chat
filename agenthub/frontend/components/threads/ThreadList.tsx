"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";
import { useThreadStore } from "@/lib/stores/threadStore";
import { NewThreadButton } from "./NewThreadButton";
import { ThreadItem } from "./ThreadItem";

interface ThreadListProps {
  onThreadSelect: (threadId: string) => void;
  onThreadCreate?: () => void;
}

export function ThreadList({
  onThreadSelect,
  onThreadCreate,
}: ThreadListProps) {
  const {
    threads,
    currentThreadId,
    isLoading,
    setThreads,
    setCurrentThreadId,
    removeThread,
    setLoading,
  } = useThreadStore();

  const loadThreads = async () => {
    setLoading(true);
    try {
      const data = await api.getThreads();
      setThreads(data.threads || []);
      if (!currentThreadId && data.threads && data.threads.length > 0) {
        setCurrentThreadId(data.threads[0]?.id ?? "");
        onThreadSelect(data.threads[0]?.id ?? "");
      }
    } catch (err) {
      console.error("Failed to load threads:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  const handleCreateThread = async () => {
    if (onThreadCreate) {
      onThreadCreate();
      return;
    }

    try {
      const newThread = await api.createThread();
      setThreads([newThread, ...threads]);
      setCurrentThreadId(newThread.id);
      onThreadSelect(newThread.id);
    } catch (err) {
      console.error("Failed to create thread:", err);
    }
  };

  const handleDeleteThread = async (threadId: string) => {
    if (!confirm("确定删除这个会话吗？")) return;
    try {
      await api.deleteThread(threadId);
      removeThread(threadId);
      if (currentThreadId === threadId && threads.length > 1) {
        const nextThread = threads.find((t) => t.id !== threadId);
        if (nextThread) {
          setCurrentThreadId(nextThread.id);
          onThreadSelect(nextThread.id);
        }
      }
    } catch (err) {
      console.error("Failed to delete thread:", err);
    }
  };

  const handleThreadClick = (threadId: string) => {
    setCurrentThreadId(threadId);
    onThreadSelect(threadId);
  };

  return (
    <div className="w-64 flex flex-col border-r border-ink/[0.08] bg-paper-dark/50">
      {/* Header */}
      <div className="p-4 border-b border-ink/[0.08]">
        <h2 className="font-display text-sm font-semibold text-ink/80 mb-3 tracking-wide">
          会话列表
        </h2>
        <NewThreadButton onClick={handleCreateThread} disabled={isLoading} />
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {isLoading ? (
          <div className="text-center text-xs text-ink/30 py-6 font-body">
            加载中…
          </div>
        ) : threads.length === 0 ? (
          <div className="text-center text-xs text-ink/25 py-6 font-body">
            暂无会话，点击上方按钮创建
          </div>
        ) : (
          threads.map((thread) => (
            <ThreadItem
              key={thread.id}
              thread={thread}
              isActive={thread.id === currentThreadId}
              onClick={() => handleThreadClick(thread.id)}
              onDelete={() => handleDeleteThread(thread.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
