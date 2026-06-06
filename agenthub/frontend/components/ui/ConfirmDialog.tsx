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
  isLoading = false,
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
    <div role="dialog" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="bg-paper p-7 w-[500px] max-w-[90vw]">
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <div className="text-sm text-ink/65 font-body leading-relaxed mt-4">{message}</div>
        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={onCancel} disabled={isLoading}>
            {cancelText}
          </button>
          <button type="button" onClick={onConfirm} disabled={isLoading}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
