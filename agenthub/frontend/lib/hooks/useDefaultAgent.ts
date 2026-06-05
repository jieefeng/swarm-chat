"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_PREFIX = "agenthub_default_agent_";

function getStorageKey(threadId: string): string {
  return `${STORAGE_PREFIX}${threadId}`;
}

export function useDefaultAgent(threadId: string | null) {
  const [defaultAgentId, setDefaultAgentIdState] = useState<string | null>(null);

  // 从 localStorage 读取
  useEffect(() => {
    if (!threadId) {
      setDefaultAgentIdState(null);
      return;
    }

    try {
      const stored = localStorage.getItem(getStorageKey(threadId));
      setDefaultAgentIdState(stored || null);
    } catch (err) {
      console.error("Failed to read default agent from localStorage:", err);
      setDefaultAgentIdState(null);
    }
  }, [threadId]);

  // 设置默认 Agent
  const setDefaultAgentId = useCallback(
    (agentId: string) => {
      if (!threadId) return;

      try {
        localStorage.setItem(getStorageKey(threadId), agentId);
        setDefaultAgentIdState(agentId);
      } catch (err) {
        console.error("Failed to save default agent to localStorage:", err);
      }
    },
    [threadId]
  );

  // 清除默认 Agent
  const clearDefaultAgentId = useCallback(() => {
    if (!threadId) return;

    try {
      localStorage.removeItem(getStorageKey(threadId));
      setDefaultAgentIdState(null);
    } catch (err) {
      console.error("Failed to clear default agent from localStorage:", err);
    }
  }, [threadId]);

  return {
    defaultAgentId,
    setDefaultAgentId,
    clearDefaultAgentId,
  };
}
