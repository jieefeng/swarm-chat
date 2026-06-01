import { create } from "zustand";
import type { Message } from "@/lib/types";

interface MessageState {
  messages: Message[];
  isStreaming: boolean;
  addMessage: (msg: Message) => void;
  upsertMessage: (msg: Message) => void;
  appendStreamChunk: (messageId: string, chunk: string) => void;
  setStreaming: (v: boolean) => void;
  reset: () => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (msg) => {
    console.log(
      "[STORE] addMessage:",
      msg.id,
      "type:",
      msg.type,
      "content:",
      msg.content?.substring(0, 50),
    );
    set((s) => ({ messages: [...s.messages, msg] }));
  },
  upsertMessage: (msg) =>
    set((s) => {
      const exists = s.messages.some((m) => m.id === msg.id);
      console.log(
        "[STORE] upsertMessage:",
        msg.id,
        "exists:",
        exists,
        "content preview:",
        msg.content?.substring(0, 50),
      );
      if (exists) {
        return { messages: s.messages.map((m) => (m.id === msg.id ? msg : m)) };
      }
      return { messages: [...s.messages, msg] };
    }),
  appendStreamChunk: (id, chunk) => {
    console.log(
      "[STORE] appendStreamChunk:",
      id,
      "chunk:",
      chunk?.substring(0, 30),
    );
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + chunk } : m,
      ),
    }));
  },
  setStreaming: (v) => set({ isStreaming: v }),
  reset: () => set({ messages: [], isStreaming: false }),
}));
