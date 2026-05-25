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

/**
 * Fetch-based EventSource implementation that supports custom headers.
 * Native EventSource cannot send custom headers like X-API-Key.
 */
export function createSSEConnection(
  onMessage: (message: Message) => void,
  onTermination: (keyword: string) => void,
) {
  let aborted = false
  let retryDelay = 1000

  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  }

  const connect = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/events`, {
        headers,
        // Disable caching, enable streaming
        cache: 'no-store',
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      // Read the stream as it comes in
      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith(':')) continue

          if (trimmed.startsWith('data:')) {
            const data = trimmed.slice(5).trim()
            if (data) {
              try {
                const parsed = JSON.parse(data)
                if (parsed.type === 'termination' || parsed.keyword) {
                  onTermination(parsed.keyword || '')
                } else {
                  onMessage(parsed)
                }
              } catch {
                // If not JSON, treat as plain message
                onMessage(data as any)
              }
            }
          }
        }
      }
    } catch (err) {
      if (aborted) return
      console.error('SSE error:', err)
      // Reconnect after delay
      setTimeout(connect, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 30000)
    }
  }

  connect()

  return {
    close: () => {
      aborted = true
    },
  }
}
