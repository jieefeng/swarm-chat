'use client';

import ReactMarkdown from 'react-markdown';
import { Message } from '@/lib/types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAgent = message.type === 'agent';
  const isPM = message.sender === 'pm';

  return (
    <div className={`flex ${isAgent ? 'items-start' : 'items-end'} mb-4`}>
      <div
        className={`max-w-[70%] px-4 py-3 rounded-2xl ${
          isPM
            ? 'bg-blue-100 border border-blue-300 rounded-tl-none'
            : isAgent
            ? 'bg-green-100 border border-green-300 rounded-tl-none'
            : 'bg-gray-100 border border-gray-300 rounded-tr-none'
        }`}
      >
        <div className="text-xs font-semibold text-gray-600 mb-1">
          {message.sender_name}
        </div>
        <div className="text-sm leading-relaxed">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
      <div className="text-xs text-gray-400 mt-1 mx-2">
        {new Date(message.timestamp * 1000).toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })}
      </div>
    </div>
  );
}