'use client';

import { useState, useEffect, useCallback } from 'react';
import { AgentList } from '@/components/agents/AgentList';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { api, createSSEConnection } from '@/lib/api';
import { Message, Agent } from '@/lib/types';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // 加载初始数据
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents()
        ]);
        setMessages(msgsRes.messages || []);
        setAgents(agentsRes.agents || []);
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };
    loadData();

    // 建立SSE连接
    const eventSource = createSSEConnection(
      (message) => {
        setMessages((prev) => [...prev, message]);
      },
      (keyword) => {
        alert(`已识别终止信号: ${keyword}`);
      }
    );

    return () => {
      eventSource.close();
    };
  }, []);

  const handleSend = useCallback(async (content: string) => {
    setLoading(true);
    try {
      await api.sendMessage(content);
    } catch (err) {
      console.error('Failed to send message:', err);
      alert('发送消息失败');
    } finally {
      setLoading(false);
    }
  }, []);

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
          <MessageInput onSend={handleSend} disabled={loading} agents={agents} />
        </div>
      </div>
    </div>
  );
}