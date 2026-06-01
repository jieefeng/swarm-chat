"use client";

import { useState, useEffect } from "react";
import { ThreadItem } from "./ThreadItem";
import { CreateThreadDialog } from "./CreateThreadDialog";

interface Thread {
  id: string;
  title: string;
  description: string | null;
  status: string;
  participants: string[];
  created_at: string;
}

interface ThreadListProps {
  activeThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onCreateThread: (title: string, description?: string) => void;
}

export function ThreadList({ activeThreadId, onSelectThread, onCreateThread }: ThreadListProps) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  useEffect(() => {
    fetchThreads();
  }, []);

  const fetchThreads = async () => {
    const response = await fetch("/api/threads");
    const data = await response.json();
    setThreads(data.threads || []);
  };

  const handleCreate = async (title: string, description?: string) => {
    await onCreateThread(title, description);
    setShowCreateDialog(false);
    fetchThreads();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-semibold">线程</h2>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          新建
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {threads.map((thread) => (
          <ThreadItem
            key={thread.id}
            thread={thread}
            isActive={thread.id === activeThreadId}
            onClick={() => onSelectThread(thread.id)}
          />
        ))}

        {threads.length === 0 && (
          <div className="p-4 text-center text-gray-500">
            暂无线程，点击"新建"创建
          </div>
        )}
      </div>

      {showCreateDialog && (
        <CreateThreadDialog
          onSubmit={handleCreate}
          onCancel={() => setShowCreateDialog(false)}
        />
      )}
    </div>
  );
}
