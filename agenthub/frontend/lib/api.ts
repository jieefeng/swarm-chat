import type { Agent, Message, SendMessageResponse } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7005'
const API_KEY = 'dev-secret-key'

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
}

export const api = {
  async sendMessage(content: string): Promise<SendMessageResponse> {
    const res = await fetch(`${API_BASE}/api/messages`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        content,
        sender: 'user',
        sender_name: '用户',
      }),
    })
    return res.json()
  },

  async getMessages(limit: number = 50): Promise<{ messages: Message[] }> {
    const res = await fetch(`${API_BASE}/api/messages?limit=${limit}`, {
      headers,
    })
    return res.json()
  },

  async getAgents(): Promise<{ agents: Agent[] }> {
    const res = await fetch(`${API_BASE}/api/agents`, { headers })
    return res.json()
  },
}
