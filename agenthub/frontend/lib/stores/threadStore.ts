import { create } from "zustand";
import type { Thread } from "@/lib/types";

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
  currentThreadId: null,
  isLoading: false,
  setThreads: (threads) => set({ threads }),
  addThread: (thread) => set((s) => ({ threads: [thread, ...s.threads] })),
  updateThread: (id, updates) =>
    set((s) => ({
      threads: s.threads.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  removeThread: (id) =>
    set((s) => ({
      threads: s.threads.filter((t) => t.id !== id),
      currentThreadId: s.currentThreadId === id ? null : s.currentThreadId,
    })),
  setCurrentThreadId: (id) => set({ currentThreadId: id }),
  setLoading: (v) => set({ isLoading: v }),
}));
