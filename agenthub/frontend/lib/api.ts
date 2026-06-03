import type {
  Agent,
  AgentConfig,
  Message,
  SendMessageResponse,
  Thread,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7005";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

export const api = {
  async sendMessage(content: string): Promise<SendMessageResponse> {
    const res = await fetch(`${API_BASE}/api/messages`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        content,
        sender: "user",
        sender_name: "用户",
      }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getMessages(limit: number = 50): Promise<{ messages: Message[] }> {
    const res = await fetch(`${API_BASE}/api/messages?limit=${limit}`, {
      headers,
    });
    return res.json();
  },

  async getAgents(): Promise<{ agents: Agent[] }> {
    const res = await fetch(`${API_BASE}/api/agents`, { headers });
    return res.json();
  },

  async getLLMConfig(): Promise<Record<string, { llm_provider: string }>> {
    const res = await fetch(`${API_BASE}/api/agents/llm-config`, { headers });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
  },

  async updateLLMConfig(
    agentId: string,
    provider: string,
  ): Promise<{ agent_id: string; llm_provider: string }> {
    const res = await fetch(`${API_BASE}/api/agents/${agentId}/llm-config`, {
      method: "PUT",
      headers,
      body: JSON.stringify({ llm_provider: provider }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getAgentConfig(agentId: string): Promise<AgentConfig> {
    const res = await fetch(`${API_BASE}/api/agents/${agentId}/config`, {
      headers,
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
  },

  async updateAgentConfig(
    agentId: string,
    config: { llm_provider?: string; model?: string },
  ): Promise<AgentConfig> {
    const res = await fetch(`${API_BASE}/api/agents/${agentId}/config`, {
      method: "PUT",
      headers,
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getThreads(limit: number = 50): Promise<{ threads: Thread[] }> {
    const res = await fetch(`${API_BASE}/api/threads?limit=${limit}`, {
      headers,
    });
    return res.json();
  },

  async createThread(title?: string): Promise<Thread> {
    const res = await fetch(`${API_BASE}/api/threads`, {
      method: "POST",
      headers,
      body: JSON.stringify({ title }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async deleteThread(threadId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/threads/${threadId}`, {
      method: "DELETE",
      headers,
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  async getThreadMessages(
    threadId: string,
    limit: number = 50,
  ): Promise<{ messages: Message[] }> {
    const res = await fetch(
      `${API_BASE}/api/threads/${threadId}/messages?limit=${limit}`,
      { headers },
    );
    return res.json();
  },
};
