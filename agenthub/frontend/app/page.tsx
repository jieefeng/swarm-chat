'use client'

import { useCallback, useEffect, useState } from 'react'
import { AgentList } from '@/components/agents/AgentList'
import { MessageInput } from '@/components/chat/MessageInput'
import { MessageList } from '@/components/chat/MessageList'
import { api, createSSEConnection } from '@/lib/api'
import type { Agent, Message } from '@/lib/types'

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(false)

  // 用于跟踪已处理的消息ID，防止重复添加
  const processedMessageIds = useRef<Set<string>>(new Set())
  // 用于跟踪待替换的temp消息: {tempId: {content, timestamp}}
  const pendingTempMessages = useRef<
    Map<string, { content: string; timestamp: number }>
  >(new Map())

  useEffect(() => {
    // 加载初始数据
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents(),
        ])
        setMessages(msgsRes.messages || [])
        setAgents(agentsRes.agents || [])
      } catch (err) {
        console.error('Failed to load data:', err)
      }
    }
    loadData()

    // 建立SSE连接
    const eventSource = createSSEConnection(
      (message) => {
        // 跳过已处理的消息ID，防止重复
        if (message.id && processedMessageIds.current.has(message.id)) {
          return
        }
        if (message.id) {
          processedMessageIds.current.add(message.id)
        }

        const newMessage: Message = {
          id: message.id || `msg-${Date.now()}`,
          sender: message.role || 'user',
          sender_name:
            message.sender_name || message.agent_id || message.role || '用户',
          content: message.content || '',
          timestamp: message.timestamp || Math.floor(Date.now() / 1000),
          type: message.role === 'user' ? 'user' : 'agent',
        }

        setMessages((prev) => {
          // 检查是否有待替换的temp消息（通过content和时间戳匹配用户消息）
          if (message.role === 'user') {
            // 找到匹配的temp消息（内容相同且时间戳接近）
            for (const [
              tempId,
              pending,
            ] of pendingTempMessages.current.entries()) {
              if (
                pending.content === message.content &&
                Math.abs(pending.timestamp - (message.timestamp || 0)) < 5000
              ) {
                // 找到temp消息，用真实消息替换它
                pendingTempMessages.current.delete(tempId)
                return prev.map((m) => (m.id === tempId ? newMessage : m))
              }
            }
          }
          // 没有匹配的temp消息，直接添加
          return [...prev, newMessage]
        })
      },
      (keyword) => {
        alert(`已识别终止信号: ${keyword}`)
      },
    )

    return () => {
      eventSource.close()
    }
  }, [])

  const handleSend = useCallback(async (content: string) => {
    // 乐观更新：立即将用户消息添加到本地状态
    const tempId = `temp-${Date.now()}`
    const timestamp = Math.floor(Date.now() / 1000)
    const optimisticMessage: Message = {
      id: tempId,
      sender: 'user',
      sender_name: '用户',
      content,
      timestamp,
      type: 'user',
    }

    // 注册temp消息，用于SSE返回时替换（使用唯一tempId作为key）
    pendingTempMessages.current.set(tempId, { content, timestamp })

    setMessages((prev) => [...prev, optimisticMessage])

    setLoading(true)
    try {
      const result = await api.sendMessage(content)
      if (!result.success) {
        alert('发送消息失败')
      }
    } catch (err) {
      console.error('Failed to send message:', err)
      alert('发送消息失败，请检查网络连接')
      // 发送失败时移除乐观添加的消息
      setMessages((prev) => prev.filter((m) => m.id !== tempId))
      pendingTempMessages.current.delete(tempId)
    } finally {
      setLoading(false)
    }
  }, [])

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-xl font-semibold">AgentHub</h1>
        <div className="text-sm text-gray-500">多Agent协作平台</div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        <AgentList agents={agents} />
        <div className="flex-1 flex flex-col">
          <MessageList messages={messages} />
          <MessageInput
            onSend={handleSend}
            disabled={loading}
            agents={agents}
          />
        </div>
      </div>
    </div>
  )
}
