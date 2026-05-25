import { create } from 'zustand';
import type { Message } from '@/lib/types';

interface MessageState {
  messages: Message[];
  isStreaming: boolean;
  addMessage: (msg: Message) => void;
  appendStreamChunk: (messageId: string, chunk: string) => void;
  setStreaming: (v: boolean) => void;
  reset: () => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendStreamChunk: (id, chunk) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + chunk } : m,
      ),
    })),
  setStreaming: (v) => set({ isStreaming: v }),
  reset: () => set({ messages: [], isStreaming: false }),
}));
