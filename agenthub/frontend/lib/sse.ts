const MAX_RETRIES = 5;
const BASE_DELAY = 1000;

// SSE event type constants
export const SSE_EVENT_STREAM_CHUNK = "stream_chunk";
export const SSE_EVENT_TASK_CREATED = "task_created";
export const SSE_EVENT_TASK_UPDATE = "task_update";
export const SSE_EVENT_CLARIFICATION_REQUEST = "clarification_request";
export const SSE_EVENT_ARTIFACT_DIFF = "artifact_diff";
export const SSE_EVENT_TOOL_START = "tool_start";
export const SSE_EVENT_TOOL_PROGRESS = "tool_progress";
export const SSE_EVENT_TOOL_RESULT = "tool_result";
// A2A 事件类型
export const SSE_EVENT_A2A_START = "a2a_start";
export const SSE_EVENT_A2A_PROGRESS = "a2a_progress";
export const SSE_EVENT_A2A_DONE = "a2a_done";
export const SSE_EVENT_A2A_CANCELLED = "a2a_cancelled";
export const SSE_EVENT_A2A_ERROR = "a2a_error";

export type SSEEventType =
  | "message"
  | "termination"
  | "error"
  | typeof SSE_EVENT_STREAM_CHUNK
  | typeof SSE_EVENT_TASK_CREATED
  | typeof SSE_EVENT_TASK_UPDATE
  | typeof SSE_EVENT_CLARIFICATION_REQUEST
  | typeof SSE_EVENT_ARTIFACT_DIFF
  | typeof SSE_EVENT_TOOL_START
  | typeof SSE_EVENT_TOOL_PROGRESS
  | typeof SSE_EVENT_TOOL_RESULT
  | typeof SSE_EVENT_A2A_START
  | typeof SSE_EVENT_A2A_PROGRESS
  | typeof SSE_EVENT_A2A_DONE
  | typeof SSE_EVENT_A2A_CANCELLED
  | typeof SSE_EVENT_A2A_ERROR;

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
  threadId?: string;
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
  onToolStart?: (data: import("@/lib/types").ToolStartEvent) => void;
  onToolProgress?: (data: import("@/lib/types").ToolProgressEvent) => void;
  onToolResult?: (data: import("@/lib/types").ToolResultEvent) => void;
  // A2A 事件回调
  onA2AStart?: (data: { agent_id: string; depth: number }) => void;
  onA2AProgress?: (data: { agent_id: string; depth: number }) => void;
  onA2ADone?: (data: { is_final: boolean }) => void;
  onA2ACancelled?: (data: { reason: string }) => void;
  onA2AError?: (data: { error: string }) => void;
}

export function createSSEConnection(options: SSEConnectionOptions) {
  let aborted = false;
  let retryDelay = BASE_DELAY;
  let retryCount = 0;
  let connected = false;
  const abortController = new AbortController();

  const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

  // 连接就绪的 Promise，调用方可 await 确保连接建立后再发请求
  let resolveReady: () => void;
  const ready = new Promise<void>((resolve) => {
    resolveReady = resolve;
  });

  const notifyConnected = () => {
    if (!aborted && !connected) {
      connected = true;
      console.log("[SSE] Connection established, resolving ready promise");
      resolveReady();
      options.onConnected?.();
    } else {
      console.log(
        "[SSE] notifyConnected skipped: aborted=",
        aborted,
        "connected=",
        connected,
      );
    }
  };

  const connect = async () => {
    if (aborted) return;
    try {
      const params = options.threadId
        ? `?thread_id=${encodeURIComponent(options.threadId)}`
        : "";
      const eventsUrl = `${options.baseUrl}/api/events${params}`;
      console.log("[SSE] Connecting to:", eventsUrl);
      const response = await fetch(eventsUrl, {
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
        const raw = decoder.decode(value, { stream: true });
        buffer += raw;
        // sse-starlette 使用 CRLF (\r\n) 行尾，先规范化为 LF (\n) 再按 \n\n 分割
        const normalized = buffer.replace(/\r\n/g, "\n");
        const blocks = normalized.split("\n\n");
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
            // 忽略 keepalive 心跳事件
            if (eventType === "keepalive") {
              continue;
            }

            console.log(
              `[SSE] Parsed event: type=${eventType}, dataLength=${dataContent.length}, preview=${dataContent.substring(0, 80)}`,
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
              } else if (
                eventType === SSE_EVENT_TOOL_START &&
                options.onToolStart
              ) {
                options.onToolStart(parsed);
              } else if (
                eventType === SSE_EVENT_TOOL_PROGRESS &&
                options.onToolProgress
              ) {
                options.onToolProgress(parsed);
              } else if (
                eventType === SSE_EVENT_TOOL_RESULT &&
                options.onToolResult
              ) {
                options.onToolResult(parsed);
              } else if (
                eventType === SSE_EVENT_A2A_START &&
                options.onA2AStart
              ) {
                options.onA2AStart(parsed);
              } else if (
                eventType === SSE_EVENT_A2A_PROGRESS &&
                options.onA2AProgress
              ) {
                options.onA2AProgress(parsed);
              } else if (
                eventType === SSE_EVENT_A2A_DONE &&
                options.onA2ADone
              ) {
                options.onA2ADone(parsed);
              } else if (
                eventType === SSE_EVENT_A2A_CANCELLED &&
                options.onA2ACancelled
              ) {
                options.onA2ACancelled(parsed);
              } else if (
                eventType === SSE_EVENT_A2A_ERROR &&
                options.onA2AError
              ) {
                options.onA2AError(parsed);
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
    ready,
  };
}
