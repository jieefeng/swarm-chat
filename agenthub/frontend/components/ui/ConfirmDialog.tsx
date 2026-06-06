"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  isLoading?: boolean;
  error?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "确定",
  cancelText = "取消",
  danger = true,
  isLoading = false,
  error,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  // ESC 键关闭（isLoading 时忽略）
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onCancel]);

  if (!open) return null;

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

      {/* 弹窗本体 */}
      <div
        role="dialog"
        aria-label={title}
        className="relative bg-paper rounded-xl shadow-2xl shadow-ink/20 border border-ink/[0.08] w-[500px] max-w-[90vw] p-7 animate-ink-drop"
      >
        {/* 标题区：印章 + 标题 + 金线 */}
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-md bg-danger text-white text-[18px] font-display font-semibold shadow-md shadow-danger/30 rotate-[-4deg]">
            慎
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-display text-lg font-semibold text-ink">
              {title}
            </h2>
            <div className="mt-2 h-px bg-gradient-to-r from-gold/0 via-gold/40 to-gold/0" />
          </div>
        </div>

        {/* 消息区 */}
        <div className="text-sm text-ink/65 font-body leading-relaxed mt-4">
          {message}
        </div>

        {/* 错误条 */}
        {error && (
          <div
            role="alert"
            className="mb-4 mt-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body"
          >
            {error}
          </div>
        )}

        {/* 按钮组 */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-body font-medium text-ink/60 bg-ink/[0.04] border border-ink/[0.08] rounded-lg hover:bg-ink/[0.07] disabled:opacity-40 transition-colors"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-4 py-2 text-sm font-body font-medium rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
              danger
                ? "text-white bg-danger border border-danger hover:bg-danger/90"
                : "text-white bg-gold border border-gold hover:bg-gold/90"
            }`}
          >
            {isLoading ? "处理中…" : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
