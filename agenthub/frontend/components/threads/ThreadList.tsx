"use client";

import { TrashIcon } from "@heroicons/react/24/outline";
import { useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
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

  const [showCleanupModal, setShowCleanupModal] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);
  const [isCleanupLoading, setIsCleanupLoading] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [deleteTargetTitle, setDeleteTargetTitle] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
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

    loadThreads();
  }, []); // 只在挂载时执行一次

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

  const handleDeleteThread = async () => {
    if (!deleteTargetId) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteThread(deleteTargetId);

      // 先获取当前状态，再更新 store
      const currentThreads = threads;
      const wasCurrentThread = currentThreadId === deleteTargetId;

      removeThread(deleteTargetId);

      // 如果删除的是当前会话，切换到下一个会话
      if (wasCurrentThread && currentThreads.length > 1) {
        const nextThread = currentThreads.find((t) => t.id !== deleteTargetId);
        if (nextThread) {
          setCurrentThreadId(nextThread.id);
          onThreadSelect(nextThread.id);
        }
      }
      setDeleteTargetId(null);
    } catch (err) {
      console.error("Failed to delete thread:", err);
      setDeleteError(err instanceof Error ? err.message : "删除失败，请重试");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleThreadClick = (threadId: string) => {
    setCurrentThreadId(threadId);
    onThreadSelect(threadId);
  };

  const handleCleanupAll = async () => {
    if (!currentThreadId) return;
    setCleanupError(null);
    setIsCleanupLoading(true);
    try {
      await api.deleteAllThreads(currentThreadId);
      const keepThread = threads.find((t) => t.id === currentThreadId);
      setThreads(keepThread ? [keepThread] : []);
      setShowCleanupModal(false);
    } catch (err) {
      console.error("Failed to cleanup threads:", err);
      setCleanupError(err instanceof Error ? err.message : "清理失败，请重试");
    } finally {
      setIsCleanupLoading(false);
    }
  };

  const keepThreadTitle =
    threads.find((t) => t.id === currentThreadId)?.title ?? "当前会话";
  const deletableCount = Math.max(0, threads.length - 1);

  return (
    <div className="w-64 flex flex-col border-r border-ink/[0.08] bg-paper-dark/50">
      {/* Header */}
      <div className="p-4 border-b border-ink/[0.08]">
        <h2 className="font-display text-sm font-semibold text-ink/80 mb-3 tracking-wide">
          会话列表
        </h2>
        <div className="flex items-center gap-2">
          {threads.length > 1 && currentThreadId && (
            <button
              onClick={() => setShowCleanupModal(true)}
              disabled={isLoading}
              title="清理其他会话"
              aria-label="清理其他会话"
              className="flex-shrink-0 p-2 text-ink/30 hover:text-danger border border-ink/[0.08] hover:border-danger/30 rounded-lg transition-colors disabled:opacity-40"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          )}
          <div className="flex-1">
            <NewThreadButton
              onClick={handleCreateThread}
              disabled={isLoading}
            />
          </div>
        </div>
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
              onDelete={() => {
                setDeleteTargetId(thread.id);
                setDeleteTargetTitle(thread.title);
              }}
            />
          ))
        )}
      </div>

      <ConfirmDialog
        open={deleteTargetId !== null}
        title="删除会话？"
        message={
          <>
            会话「
            <span className="font-semibold text-ink/80">
              {deleteTargetTitle}
            </span>
            」及所有消息将被永久删除。
            <p className="text-danger/85 font-semibold text-xs mt-2">
              此操作不可撤销。
            </p>
          </>
        }
        confirmText="删除"
        isLoading={isDeleting}
        error={deleteError}
        onCancel={() => {
          setDeleteTargetId(null);
          setDeleteError(null);
        }}
        onConfirm={handleDeleteThread}
      />

      <ConfirmDialog
        open={showCleanupModal}
        title="清理其他会话"
        message={
          <>
            <p>
              将删除{" "}
              <span className="font-semibold text-danger">
                {deletableCount}
              </span>{" "}
              个会话（包括置顶的）。
            </p>
            <p className="mt-1">
              当前会话「
              <span className="font-semibold text-ink/80">
                {keepThreadTitle}
              </span>
              」将保留。
            </p>
            <p className="text-danger/85 font-semibold text-xs mt-2">
              此操作不可撤销。
            </p>
          </>
        }
        confirmText="确定清理"
        isLoading={isCleanupLoading}
        error={cleanupError}
        onCancel={() => {
          setShowCleanupModal(false);
          setCleanupError(null);
        }}
        onConfirm={handleCleanupAll}
      />
    </div>
  );
}
