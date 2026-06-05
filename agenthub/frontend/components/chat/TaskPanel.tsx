"use client";

import type { Task } from "@/lib/types";

interface TaskPanelProps {
  tasks: Task[];
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending: { label: "等待中", color: "bg-ink/[0.06] text-ink/40" },
  running: { label: "执行中", color: "bg-gold/15 text-gold-dim" },
  reviewing: { label: "审查中", color: "bg-amber-500/15 text-amber-600" },
  done: { label: "已完成", color: "bg-wuxing-wood/15 text-wuxing-wood" },
  failed: { label: "失败", color: "bg-danger/15 text-danger" },
  escalate: { label: "需介入", color: "bg-orange-500/15 text-orange-600" },
  cancelled: { label: "已取消", color: "bg-ink/[0.04] text-ink/25" },
  skipped: { label: "已跳过", color: "bg-ink/[0.04] text-ink/25" },
};

export function TaskPanel({ tasks }: TaskPanelProps) {
  const completedCount = tasks.filter((t) => t.status === "done").length;
  const progress = tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0;

  return (
    <div className="rounded-lg border border-ink/[0.08] bg-paper-dark/40 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-display font-semibold text-ink/80 tracking-wide">
          任务进度
        </h3>
        <span className="text-xs text-ink/40 font-body">
          {completedCount}/{tasks.length}
        </span>
      </div>
      {/* Progress bar */}
      <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-ink/[0.06]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-gold-dim to-gold transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      {/* Task list */}
      <div className="space-y-2">
        {tasks.map((task) => {
          const config = STATUS_CONFIG[task.status] ?? STATUS_CONFIG.pending;
          const label = config?.label ?? "未知";
          const color = config?.color ?? "bg-ink/[0.06] text-ink/40";
          return (
            <div key={task.id} className="flex items-center gap-2 text-sm">
              <span
                className={`inline-block rounded px-2 py-0.5 text-[10px] font-medium font-body ${color}`}
              >
                {label}
              </span>
              <span className="truncate text-ink/60 font-body text-xs">
                {task.title}
              </span>
              <span className="ml-auto text-[10px] text-ink/25 font-body">
                {task.assigned_to}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
