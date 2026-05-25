const MAX_RETRIES = 5
const BASE_DELAY = 1000

export type SSEEventType = 'message' | 'termination' | 'error'

export interface SSEMessage {
  id?: string
  sender?: string
  sender_name?: string
  agent_id?: string
  role?: string
  content?: string
  timestamp?: number
  type?: string
  keyword?: string
}

export interface SSEConnectionOptions {
  baseUrl: string
  onMessage: (data: SSEMessage) => void
  onTermination: (keyword: string) => void
  onError: (error: string) => void
}

export function createSSEConnection(options: SSEConnectionOptions) {
  let aborted = false
  let retryDelay = BASE_DELAY
  let retryCount = 0

  const API_KEY = 'dev-secret-key'

  const connect = async () => {
    try {
      const response = await fetch(`${options.baseUrl}/api/events`, {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        cache: 'no-store',
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith(':')) continue

          if (trimmed.startsWith('data:')) {
            const data = trimmed.slice(5).trim()
            if (data) {
              try {
                const parsed = JSON.parse(data)
                if (parsed.keyword || parsed.type === 'termination') {
                  options.onTermination(parsed.keyword || '')
                } else {
                  options.onMessage(parsed)
                }
              } catch {
                options.onMessage(data as unknown as SSEMessage)
              }
            }
          }
        }
      }
    } catch (_err) {
      if (aborted) return

      retryCount++
      if (retryCount > MAX_RETRIES) {
        options.onError(`连接失败，已达到最大重试次数 (${MAX_RETRIES})`)
        return
      }

      options.onError(
        `连接断开，${retryDelay / 1000}s 后重试... (${retryCount}/${MAX_RETRIES})`,
      )
      setTimeout(connect, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 16000)
    }
  }

  connect()

  return {
    close: () => {
      aborted = true
    },
  }
}
