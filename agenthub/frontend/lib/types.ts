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
