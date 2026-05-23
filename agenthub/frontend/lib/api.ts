import { Message, Agent, SendMessageResponse } from './types';

const API_BASE = '/api';

export const api = {
  async sendMessage(content: string): Promise<SendMessageResponse> {
    const res = await fetch(`${API_BASE}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        sender: 'user',
        sender_name: '用户'
      })
    });
    return res.json();
  },

  async getMessages(limit: number = 50): Promise<{ messages: Message[] }> {
    const res = await fetch(`${API_BASE}/messages?limit=${limit}`);
    return res.json();
  },

  async getAgents(): Promise<{ agents: Agent[] }> {
    const res = await fetch(`${API_BASE}/agents`);
    return res.json();
  }
};

export function createSSEConnection(
  onMessage: (message: Message) => void,
  onTermination: (keyword: string) => void
) {
  const eventSource = new EventSource(`${API_BASE}/events`);

  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  });

  eventSource.addEventListener('termination', (event) => {
    const data = JSON.parse(event.data);
    onTermination(data.keyword);
  });

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
  };

  return eventSource;
}