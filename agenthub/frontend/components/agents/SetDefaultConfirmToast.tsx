"use client";

interface SetDefaultConfirmToastProps {
  agentName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function SetDefaultConfirmToast({
  agentName,
  onConfirm,
  onCancel,
}: SetDefaultConfirmToastProps) {
  return (
    <div
      role="dialog"
      aria-label="设为默认 agent 确认"
      className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-10 bg-paper rounded-lg shadow-lg border border-ink/[0.08] px-4 py-2.5 flex items-center gap-3 font-body text-sm whitespace-nowrap"
    >
      <span className="text-ink/70">
        将 <span className="text-ink font-medium">{agentName}</span> 设为默认？
      </span>
      <div className="flex gap-1.5">
        <button
          type="button"
          onClick={onCancel}
          className="px-2.5 py-1 rounded-md text-ink/50 hover:bg-ink/[0.04] transition-colors"
        >
          取消
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className="px-2.5 py-1 rounded-md bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 transition-colors"
        >
          确定
        </button>
      </div>
    </div>
  );
}
