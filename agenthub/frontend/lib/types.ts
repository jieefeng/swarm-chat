export interface Message {
  id: string
  sender: string
  sender_name?: string
  content: string
  timestamp: number
  type: 'user' | 'agent'
  agent_id?: string
  role?: string // SSE message uses role instead of sender
}

export interface MentionCandidate {
  id: string
  label: string
  avatar?: string
}

export interface Agent {
  id: string
  name: string
  role: string
}

export interface SendMessageResponse {
  success: boolean
  message_id: string
  is_broadcast?: boolean
  is_termination?: boolean
}
