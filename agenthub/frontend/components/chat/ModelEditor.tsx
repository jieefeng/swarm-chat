"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";

interface ModelEditorProps {
  agentId: string;
  agentName: string;
}

export function ModelEditor({ agentId, agentName }: ModelEditorProps) {
  const [model, setModel] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const isCancelling = useRef(false);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await api.getAgentConfig(agentId);
        setModel(config.model || "");
      } catch (err) {
        console.error("Failed to load agent config:", err);
      }
    };
    loadConfig();
  }, [agentId]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await api.updateAgentConfig(agentId, { model: model || undefined });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
      setIsEditing(false);  // 保存成功后才退出
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
      // 保持编辑模式，让用户看到错误
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      isCancelling.current = true;
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          onBlur={() => {
            if (!isCancelling.current) {
              handleSave();
            }
            isCancelling.current = false;
          }}
          onKeyDown={handleKeyDown}
          placeholder="输入模型名称"
          className="px-2 py-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        {isLoading && <span className="text-xs text-gray-500">保存中...</span>}
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }

  return (
    <button
      onClick={() => setIsEditing(true)}
      className="text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 px-2 py-1 rounded transition-colors"
      title="点击编辑模型"
    >
      {model || "默认模型"}
      {success && <span className="ml-2 text-green-500">✓</span>}
    </button>
  );
}
