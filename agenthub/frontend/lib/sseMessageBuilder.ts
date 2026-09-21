import type { ClarificationRequestEvent, Message } from "@/lib/types";

/**
 * 将 SSE clarification_request 事件转换为聊天消息
 * （MessageBubble 按 messageType="clarification" 渲染 ClarificationCard）
 */
export function buildClarificationMessage(
  data: ClarificationRequestEvent,
): Message {
  return {
    id: `clarification-${data.message_id}`,
    sender: "system",
    sender_name: "系统",
    content: data.question,
    timestamp: Math.floor(Date.now() / 1000),
    type: "agent",
    messageType: "clarification",
    metadata: {
      options: data.options,
      messageId: data.message_id,
    },
  };
}
