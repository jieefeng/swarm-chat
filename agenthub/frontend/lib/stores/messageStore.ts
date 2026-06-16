import { create } from "zustand";
import type { Message, ToolExecution } from "@/lib/types";

/** A2A 执行状态 */
interface A2AState {
  isRunning: boolean; // A2A 链是否在执行
  currentAgent: string; // 当前执行的 Agent
  depth: number; // 当前深度
  maxDepth: number; // 最大深度
  canCancel: boolean; // 是否可以取消
}

interface MessageState {
  messages: Message[];
  isStreaming: boolean;
  toolExecutions: Record<string, ToolExecution[]>;
  /** message ID → index in messages[]，O(1) 查找 */
  messageIndex: Record<string, number>;
  a2aState: A2AState;
  addMessage: (msg: Message) => void;
  upsertMessage: (msg: Message) => void;
  appendStreamChunk: (messageId: string, chunk: string) => void;
  setStreaming: (v: boolean) => void;
  addToolExecution: (messageId: string, tool: ToolExecution) => void;
  updateToolExecution: (
    messageId: string,
    toolId: string,
    update: Partial<ToolExecution>,
  ) => void;
  setA2AState: (state: Partial<A2AState>) => void;
  cancelA2A: () => void;
  reset: () => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  isStreaming: false,
  toolExecutions: {},
  messageIndex: {},
  a2aState: {
    isRunning: false,
    currentAgent: "",
    depth: 0,
    maxDepth: 15,
    canCancel: false,
  },
  addMessage: (msg) => {
    set((s) => {
      const newIndex = { ...s.messageIndex, [msg.id]: s.messages.length };
      return { messages: [...s.messages, msg], messageIndex: newIndex };
    });
  },
  upsertMessage: (msg) =>
    set((s) => {
      const idx = s.messageIndex[msg.id];
      if (idx !== undefined) {
        const messages = [...s.messages];
        messages[idx] = msg;
        return { messages };
      }
      const newIndex = { ...s.messageIndex, [msg.id]: s.messages.length };
      return { messages: [...s.messages, msg], messageIndex: newIndex };
    }),
  appendStreamChunk: (id, chunk) => {
    set((s) => {
      const idx = s.messageIndex[id];
      if (idx === undefined) return s;
      const existing = s.messages[idx];
      if (!existing) return s;
      const messages = [...s.messages];
      messages[idx] = { ...existing, content: existing.content + chunk };
      return { messages };
    });
  },
  setStreaming: (v) => set({ isStreaming: v }),
  addToolExecution: (messageId, tool) =>
    set((s) => ({
      toolExecutions: {
        ...s.toolExecutions,
        [messageId]: [...(s.toolExecutions[messageId] || []), tool],
      },
    })),
  updateToolExecution: (messageId, toolId, update) =>
    set((s) => ({
      toolExecutions: {
        ...s.toolExecutions,
        [messageId]: (s.toolExecutions[messageId] || []).map((t) =>
          t.id === toolId ? { ...t, ...update } : t,
        ),
      },
    })),
  setA2AState: (state) =>
    set((s) => ({
      a2aState: { ...s.a2aState, ...state },
    })),
  cancelA2A: () => {
    // 发送取消请求到后端
    // 这里需要调用 API 来取消 A2A 链
    // 暂时只是重置状态
    set((s) => ({
      a2aState: {
        ...s.a2aState,
        isRunning: false,
        currentAgent: "",
        depth: 0,
        canCancel: false,
      },
    }));
  },
  reset: () =>
    set({
      messages: [],
      isStreaming: false,
      toolExecutions: {},
      messageIndex: {},
      a2aState: {
        isRunning: false,
        currentAgent: "",
        depth: 0,
        maxDepth: 15,
        canCancel: false,
      },
    }),
}));
