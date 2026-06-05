"use client";

import { XMarkIcon } from "@heroicons/react/24/outline";
import { useEffect, useState } from "react";

interface CleanupConfirmModalProps {
  open: boolean;
  deletableCount: number;
  keepThreadTitle: string;
  isLoading: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function CleanupConfirmModal({
  open,
  deletableCount,
  keepThreadTitle,
  isLoading,
  error,
  onCancel,
  onConfirm,
}: CleanupConfirmModalProps) {
  const [confirmText, setConfirmText] = useState("");

  // 打开时清空输入框
  useEffect(() => {
    if (open) {
      setConfirmText("");
    }
  }, [open]);

  // ESC 键关闭
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onCancel]);

  if (!open) return null;

  const canConfirm = confirmText === "确认" && !isLoading;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <button
        type="button"
        aria-label="关闭"
        disabled={isLoading}
        onClick={onCancel}
        className="absolute inset-0 bg-ink/30 backdrop-blur-sm cursor-default disabled:cursor-not-allowed"
      />

      {/* Modal 内容 */}
      <div className="relative bg-paper rounded-2xl shadow-2xl shadow-ink/10 border border-ink/[0.08] w-[480px] max-w-[90vw] p-6 animate-ink-drop">
        {/* 标题栏 */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-lg font-semibold text-ink tracking-wide">
            清理其他会话
          </h2>
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="text-ink/30 hover:text-ink/60 transition-colors disabled:opacity-30"
            aria-label="关闭"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* 副文本 */}
        <div className="mb-5 text-sm text-ink/60 font-body leading-relaxed">
          <p>
            将删除{" "}
            <span className="font-semibold text-danger">{deletableCount}</span>{" "}
            个会话（包括置顶的）。
          </p>
          <p className="mt-2">
            当前会话「
            <span className="font-semibold text-ink/80">{keepThreadTitle}</span>
            」将保留。
          </p>
          <p className="mt-3 text-danger/80 font-semibold">此操作不可撤销。</p>
        </div>

        {/* 输入框 */}
        <div className="mb-5">
          <label
            htmlFor="cleanup-confirm-input"
            className="block text-xs font-body font-medium text-ink/50 mb-1.5 tracking-wide"
          >
            请输入「确认」以启用按钮
          </label>
          <input
            id="cleanup-confirm-input"
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="确认"
            disabled={isLoading}
            className="w-full px-3 py-2 bg-white border border-ink/[0.1] rounded-lg text-sm text-ink placeholder:text-ink/30 focus:outline-none focus:border-gold/40 transition-colors font-body disabled:opacity-50"
          />
        </div>

        {/* 错误条 */}
        {error && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body">
            {error}
          </div>
        )}

        {/* 按钮组 */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-body font-medium text-ink/50 bg-ink/[0.04] border border-ink/[0.08] rounded-lg hover:bg-ink/[0.06] disabled:opacity-40 transition-colors"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={!canConfirm}
            className={`px-4 py-2 text-sm font-body font-medium rounded-lg transition-colors ${
              canConfirm
                ? "text-danger bg-danger/10 border border-danger/30 hover:bg-danger/20"
                : "text-ink/25 bg-ink/[0.03] border border-ink/[0.08] cursor-not-allowed"
            }`}
          >
            {isLoading ? "清理中…" : "确定清理"}
          </button>
        </div>
      </div>
    </div>
  );
}
