export interface Message {
  id: string;
  sender: string;
  sender_name: string;
  content: string;
  timestamp: number;
  type: 'user' | 'agent';
}

export interface Agent {
  id: string;
  name: string;
  role: string;
}

export interface SendMessageResponse {
  success: boolean;
  message_id: string;
  is_broadcast?: boolean;
  is_termination?: boolean;
}