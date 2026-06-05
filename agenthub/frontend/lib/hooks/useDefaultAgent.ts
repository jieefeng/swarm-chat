"use client";

/**
 * Synchronously reads the default agent ID from localStorage for a given thread.
 * Used by handleThreadSelect for synchronous checks without depending on React state.
 */

import { useCallback, useEffect, useState } from "react";

const STORAGE_PREFIX = "agenthub_default_agent_";

function getStorageKey(threadId: string): string {
  return `${STORAGE_PREFIX}${threadId}`;
}

/**
 * 同步读取 localStorage 中指定线程的默认 Agent ID
 * 供 handleThreadSelect 同步检查使用，不依赖 React 状态
 */
export function getStoredDefaultAgentId(threadId: string): string | null {
  if (!threadId) return null;
  try {
    return localStorage.getItem(getStorageKey(threadId));
  } catch {
    return null;
  }
}

export function useDefaultAgent(threadId: string | null) {
  const [defaultAgentId, setDefaultAgentIdState] = useState<string | null>(
    null,
  );

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
    [threadId],
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
