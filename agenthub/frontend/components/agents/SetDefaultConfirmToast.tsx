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
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm"
    >
      <div className="bg-paper rounded-2xl shadow-2xl shadow-ink/10 border border-ink/[0.08] p-6 w-[420px] max-w-[90vw] font-body">
        {/* 标题 */}
        <div className="text-center mb-5">
          <h2 className="font-display text-lg font-semibold text-ink">
            修改默认 Agent
          </h2>
          <p className="text-sm text-ink/50 mt-2">
            将 <span className="text-ink font-medium">{agentName}</span> 设为该
            会话的默认对话对象？
          </p>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 rounded-xl border border-ink/[0.1] text-ink/50 text-sm hover:bg-ink/[0.02] transition-colors"
          >
            拒绝
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 rounded-xl bg-gold/15 text-gold-dim border border-gold/25 text-sm font-medium hover:bg-gold/25 hover:shadow-lg hover:shadow-gold/10 transition-all"
          >
            确认
          </button>
        </div>
      </div>
    </div>
  );
}
