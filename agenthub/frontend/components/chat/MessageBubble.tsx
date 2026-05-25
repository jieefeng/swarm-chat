'use client'

import ReactMarkdown from 'react-markdown'
import type { Message } from '@/lib/types'

interface MessageBubbleProps {
  message: Message
  isStreaming: boolean
  onCopySuccess?: () => void
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.type === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 ${
          isUser
            ? 'bg-primary text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        {!isUser && (
          <div className="text-xs font-medium text-gray-500 mb-1">
            {message.sender_name || message.sender}
          </div>
        )}
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
        )}
      </div>
    </div>
  )
}
