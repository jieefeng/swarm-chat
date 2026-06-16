import { create } from "zustand";
import type { Thread } from "@/lib/types";

const THREAD_STORAGE_KEY = "agenthub_current_thread_id";

/** 从 localStorage 读取上次选中的 thread ID */
function getStoredThreadId(): string | null {
  try {
    return localStorage.getItem(THREAD_STORAGE_KEY);
  } catch {
    return null;
  }
}

/** 将 thread ID 持久化到 localStorage */
function storeThreadId(id: string | null): void {
  try {
    if (id) {
      localStorage.setItem(THREAD_STORAGE_KEY, id);
    } else {
      localStorage.removeItem(THREAD_STORAGE_KEY);
    }
  } catch {
    // localStorage 不可用时静默失败
  }
}

interface ThreadState {
  threads: Thread[];
  currentThreadId: string | null;
  isLoading: boolean;
  setThreads: (threads: Thread[]) => void;
  addThread: (thread: Thread) => void;
  updateThread: (id: string, updates: Partial<Thread>) => void;
  removeThread: (id: string) => void;
  setCurrentThreadId: (id: string | null) => void;
  setLoading: (v: boolean) => void;
}

export const useThreadStore = create<ThreadState>((set) => ({
  threads: [],
  currentThreadId: getStoredThreadId(), // 从 localStorage 恢复
  isLoading: false,
  setThreads: (threads) => set({ threads }),
  addThread: (thread) => set((s) => ({ threads: [thread, ...s.threads] })),
  updateThread: (id, updates) =>
    set((s) => ({
      threads: s.threads.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  removeThread: (id) =>
    set((s) => {
      const nextId = s.currentThreadId === id ? null : s.currentThreadId;
      storeThreadId(nextId); // 同步更新 localStorage
      return {
        threads: s.threads.filter((t) => t.id !== id),
        currentThreadId: nextId,
      };
    }),
  setCurrentThreadId: (id) => {
    storeThreadId(id); // 同步更新 localStorage
    set({ currentThreadId: id });
  },
  setLoading: (v) => set({ isLoading: v }),
}));
