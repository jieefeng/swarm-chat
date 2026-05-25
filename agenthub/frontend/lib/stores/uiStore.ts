import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  activeAgentId: string | null
  toggleSidebar: () => void
  setActiveAgent: (id: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeAgentId: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setActiveAgent: (id) => set({ activeAgentId: id }),
}))
