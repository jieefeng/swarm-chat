const MAX_RETRIES = 5;
const BASE_DELAY = 1000;

// SSE event type constants
export const SSE_EVENT_STREAM_CHUNK = "stream_chunk";
export const SSE_EVENT_TASK_CREATED = "task_created";
export const SSE_EVENT_TASK_UPDATE = "task_update";
export const SSE_EVENT_CLARIFICATION_REQUEST = "clarification_request";
export const SSE_EVENT_ARTIFACT_DIFF = "artifact_diff";

export type SSEEventType =
  | "message"
  | "termination"
  | "error"
  | typeof SSE_EVENT_STREAM_CHUNK
  | typeof SSE_EVENT_TASK_CREATED
  | typeof SSE_EVENT_TASK_UPDATE
  | typeof SSE_EVENT_CLARIFICATION_REQUEST
  | typeof SSE_EVENT_ARTIFACT_DIFF;

export interface SSEMessage {
  id?: string;
  sender?: string;
  sender_name?: string;
  agent_id?: string;
  role?: string;
  content?: string;
  timestamp?: number;
  type?: string;
  keyword?: string;
}

export interface SSEConnectionOptions {
  baseUrl: string;
  onMessage: (data: SSEMessage) => void;
  onTermination: (keyword: string) => void;
  onError: (error: string) => void;
  onConnected?: () => void;
  onStreamChunk?: (data: import("@/lib/types").StreamChunkEvent) => void;
  onTaskCreated?: (data: import("@/lib/types").TaskCreatedEvent) => void;
  onTaskUpdate?: (data: import("@/lib/types").TaskUpdateEvent) => void;
  onClarification?: (
    data: import("@/lib/types").ClarificationRequestEvent,
  ) => void;
  onArtifactDiff?: (data: import("@/lib/types").ArtifactDiffEvent) => void;
}

export function createSSEConnection(options: SSEConnectionOptions) {
  let aborted = false;
  let retryDelay = BASE_DELAY;
  let retryCount = 0;
  let connected = false;
  const abortController = new AbortController();

  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

  const notifyConnected = () => {
    if (options.onConnected && !aborted && !connected) {
      connected = true;
      console.log("[SSE] Connection established, calling onConnected");
      options.onConnected();
    }
  };

  const connect = async () => {
    if (aborted) return;
    try {
      console.log("[SSE] Connecting to:", `${options.baseUrl}/api/events`);
      const response = await fetch(`${options.baseUrl}/api/events`, {
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": API_KEY,
        },
        signal: abortController.signal,
        cache: "no-store",
        credentials: "include",
      });
      console.log("[SSE] Response status:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // 连接已建立，通知调用者
      notifyConnected();

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log("[SSE] Stream completed (done=true)");
          break;
        }
        console.log("[SSE] Raw chunk received:", value.length, "bytes");
        buffer += decoder.decode(value, { stream: true });
        // 按双换行分割，处理完整的 event + data 块
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          const lines = block.split("\n");
          let eventType = "message";
          let dataContent = "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("event:")) {
              eventType = trimmed.slice(6).trim();
            } else if (trimmed.startsWith("data:")) {
              dataContent = trimmed.slice(5).trim();
            }
          }

          if (dataContent) {
            console.log(
              `[SSE] Event: ${eventType}, Data: ${dataContent.substring(0, 100)}...`,
            );
            try {
              const parsed = JSON.parse(dataContent);

              if (eventType === "termination" || parsed.keyword) {
                options.onTermination(parsed.keyword || "");
              } else if (
                eventType === SSE_EVENT_STREAM_CHUNK &&
                options.onStreamChunk
              ) {
                options.onStreamChunk(parsed);
              } else if (
                eventType === SSE_EVENT_TASK_CREATED &&
                options.onTaskCreated
              ) {
                options.onTaskCreated(parsed);
              } else if (
                eventType === SSE_EVENT_TASK_UPDATE &&
                options.onTaskUpdate
              ) {
                options.onTaskUpdate(parsed);
              } else if (
                eventType === SSE_EVENT_CLARIFICATION_REQUEST &&
                options.onClarification
              ) {
                options.onClarification(parsed);
              } else if (
                eventType === SSE_EVENT_ARTIFACT_DIFF &&
                options.onArtifactDiff
              ) {
                options.onArtifactDiff(parsed);
              } else {
                options.onMessage(parsed);
              }
            } catch {
              console.log(
                "[SSE] Parse failed for:",
                dataContent.substring(0, 50),
              );
            }
          }
        }
      }
    } catch (_err) {
      if (aborted) return;

      retryCount++;
      if (retryCount > MAX_RETRIES) {
        options.onError(`连接失败，已达到最大重试次数 (${MAX_RETRIES})`);
        return;
      }

      options.onError(
        `连接断开，${retryDelay / 1000}s 后重试... (${retryCount}/${MAX_RETRIES})`,
      );
      setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 16000);
    }
  };

  connect().catch((err) => {
    if (!aborted) {
      options.onError(
        `连接错误: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  });

  return {
    close: () => {
      aborted = true;
      abortController.abort();
    },
  };
}
