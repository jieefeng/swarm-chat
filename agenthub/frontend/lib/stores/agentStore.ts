// Stub for Phase 1 - will be replaced in Phase 2 with proper Zustand store
import type { Agent } from '@/lib/types'

interface AgentStore {
  agents: Agent[]
  setAgents: (agents: Agent[]) => void
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type StoreApi<T> = {
  getState: () => T
  setState: (fn: (state: T) => Partial<T>) => void
  subscribe: (listener: () => void) => () => void
}

const createStore = <T>(): StoreApi<T> & { setState: (partial: Partial<T>) => void } => {
  let state: T = {} as T
  const listeners = new Set<() => void>()
  return {
    getState: () => state,
    setState: (partial) => {
      state = { ...state, ...partial }
      listeners.forEach((l) => l())
    },
    subscribe: (listener) => {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
  }
}

const store = createStore<AgentStore>()
const emptyArr: Agent[] = []

// Selector-based hook
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const useAgentStore = <T>(selector: (state: AgentStore) => T): T => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return selector({ agents: emptyArr, setAgents: (_a: Agent[]) => {} } as AgentStore)
}
