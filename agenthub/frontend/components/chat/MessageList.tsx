'use client'

import { useEffect, useRef } from 'react'
import type { Message } from '@/lib/types'
import { MessageBubble } from './MessageBubble'

interface MessageListProps {
  messages: Message[]
}

export function MessageList({ messages }: MessageListProps) {
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div ref={listRef} className="flex-1 overflow-y-auto p-4 bg-gray-50">
      {messages.length === 0 ? (
        <div className="text-center text-gray-400 mt-20">
          暂无消息，开始对话吧
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageBubble
            key={msg.id || `msg-${index}-${msg.timestamp}`}
            message={msg}
          />
        ))
      )}
    </div>
  )
}
