export interface Message {
  id: string;
  sender: string;
  sender_name?: string;
  content: string;
  timestamp: number;
  type: "user" | "agent";
  agent_id?: string;
  role?: string; // SSE message uses role instead of sender
  messageType?: "text" | "task_panel" | "clarification" | "diff";
  metadata?: Record<string, unknown>;
}

export interface MentionCandidate {
  id: string;
  label: string;
  avatar?: string;
  beast?: string;
  element?: string;
  color?: { primary: string; secondary: string };
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  beast?: string;
  nickname?: string;
  element?: string;
  avatar?: string;
  color?: { primary: string; secondary: string };
  personality?: string;
  catchphrase?: string;
  strengths?: string[];
  caution?: string;
  bonds?: { partner: string; relation: string };
  speechStyle?: { tone: string; quirks: string[] };
}

export interface SendMessageResponse {
  success: boolean;
  message_id: string;
  is_broadcast?: boolean;
  is_termination?: boolean;
}

// Task types
export type TaskStatus =
  | "pending"
  | "running"
  | "reviewing"
  | "done"
  | "failed"
  | "escalate"
  | "cancelled"
  | "skipped";

export interface Task {
  id: string;
  title: string;
  description: string;
  assigned_to: string;
  depends_on: string[];
  priority: string;
  status: TaskStatus;
  result: string | null;
  retry_count: number;
}

// SSE extended event types
export interface StreamChunkEvent {
  message_id: string;
  chunk: string;
  seq: number;
}

export interface TaskCreatedEvent {
  task_id: string;
  title: string;
  assigned_to: string;
}

export interface TaskUpdateEvent {
  task_id: string;
  status: TaskStatus;
  title: string;
}

export interface ClarificationRequestEvent {
  message_id: string;
  question: string;
  options: string[];
}

export interface ArtifactDiffEvent {
  task_id: string;
  file_path: string;
  old_content: string;
  new_content: string;
}

export interface AgentConfig {
  agent_id: string;
  llm_provider: string;
  model: string | null;
}

// Thread (会话) types
export interface Thread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

// Tool execution types
export interface ToolExecution {
  id: string;
  command: string;
  status: "running" | "success" | "error";
  output?: string;
}

export interface ToolStartEvent {
  agent_id: string;
  command: string;
  message_id: string;
}

export interface ToolProgressEvent {
  agent_id: string;
  output: string;
  message_id: string;
}

export interface ToolResultEvent {
  agent_id: string;
  content: string;
  success: boolean;
  message_id: string;
}
