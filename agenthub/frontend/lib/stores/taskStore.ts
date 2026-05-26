import { create } from "zustand";
import type { Task, TaskStatus } from "@/lib/types";

interface TaskStore {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
  getTasksByStatus: (status: TaskStatus) => Task[];
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, status } : t)),
    })),
  getTasksByStatus: (status) => get().tasks.filter((t) => t.status === status),
}));
