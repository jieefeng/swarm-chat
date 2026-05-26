"use client";

import type { Task } from "@/lib/types";

interface TaskPanelProps {
  tasks: Task[];
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending: { label: "等待中", color: "bg-gray-100 text-gray-600" },
  running: { label: "执行中", color: "bg-blue-100 text-blue-700" },
  reviewing: { label: "审查中", color: "bg-yellow-100 text-yellow-700" },
  done: { label: "已完成", color: "bg-green-100 text-green-700" },
  failed: { label: "失败", color: "bg-red-100 text-red-700" },
  escalate: { label: "需介入", color: "bg-orange-100 text-orange-700" },
  cancelled: { label: "已取消", color: "bg-gray-100 text-gray-400" },
  skipped: { label: "已跳过", color: "bg-gray-100 text-gray-400" },
};

export function TaskPanel({ tasks }: TaskPanelProps) {
  const completedCount = tasks.filter((t) => t.status === "done").length;
  const progress = tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800">任务进度</h3>
        <span className="text-xs text-gray-500">
          {completedCount}/{tasks.length}
        </span>
      </div>
      {/* Progress bar */}
      <div className="mb-4 h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      {/* Task list */}
      <div className="space-y-2">
        {tasks.map((task) => {
          const config = STATUS_CONFIG[task.status] ?? STATUS_CONFIG.pending;
          const label = config?.label ?? "未知";
          const color = config?.color ?? "bg-gray-100 text-gray-600";
          return (
            <div key={task.id} className="flex items-center gap-2 text-sm">
              <span
                className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${color}`}
              >
                {label}
              </span>
              <span className="truncate text-gray-700">{task.title}</span>
              <span className="ml-auto text-xs text-gray-400">
                {task.assigned_to}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
