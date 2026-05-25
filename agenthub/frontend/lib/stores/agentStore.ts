import { create } from 'zustand'
import type { Agent } from '@/lib/types'

interface AgentState {
  agents: Agent[]
  setAgents: (agents: Agent[]) => void
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  setAgents: (agents) => set({ agents }),
}))
