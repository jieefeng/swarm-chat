"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { ClarificationCard } from "@/components/chat/ClarificationCard";
import { DiffViewer } from "@/components/chat/DiffViewer";
import { PreviewCard } from "@/components/chat/PreviewCard";
import { TaskPanel } from "@/components/chat/TaskPanel";
import { ToolExecutionCard } from "@/components/chat/ToolExecutionCard";
import { extractHtmlFromMarkdown, extractTitle } from "@/lib/preview";
import { useMessageStore } from "@/lib/stores/messageStore";
import { useTaskStore } from "@/lib/stores/taskStore";
import type { Message } from "@/lib/types";

const EMPTY_TOOL_EXECUTIONS: never[] = [];

interface MessageBubbleProps {
  message: Message;
  isStreaming: boolean;
  agentColor?: string;
}

export function MessageBubble({
  message,
  isStreaming,
  agentColor,
}: MessageBubbleProps) {
  const isUser = message.type === "user";
  const toolExecutions =
    useMessageStore((s) => s.toolExecutions[message.id]) ||
    EMPTY_TOOL_EXECUTIONS;

  if (message.messageType === "task_panel") {
    const tasks = useTaskStore.getState().tasks;
    return (
      <div
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5 animate-fade-in-up`}
      >
        <div
          className={`max-w-[70%] px-4 py-3 ${
            isUser
              ? "bg-gold/10 border border-gold/15 rounded-xl rounded-br-sm text-ink"
              : "bg-paper-dark/80 border border-ink/[0.08] rounded-xl rounded-bl-sm text-ink/80"
          }`}
        >
          <TaskPanel tasks={tasks} />
        </div>
      </div>
    );
  }

  if (message.messageType === "clarification") {
    return (
      <div
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5 animate-fade-in-up`}
      >
        <div
          className={`max-w-[70%] px-4 py-3 ${
            isUser
              ? "bg-gold/10 border border-gold/15 rounded-xl rounded-br-sm text-ink"
              : "bg-paper-dark/80 border border-ink/[0.08] rounded-xl rounded-bl-sm text-ink/80"
          }`}
        >
          <ClarificationCard
            question={message.content}
            options={(message.metadata?.options as string[]) ?? []}
            onSelect={(option) => {
              window.dispatchEvent(
                new CustomEvent("clarification-select", {
                  detail: { option, messageId: message.id },
                }),
              );
            }}
          />
        </div>
      </div>
    );
  }

  if (message.messageType === "diff") {
    const meta = message.metadata ?? {};
    return (
      <div
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5 animate-fade-in-up`}
      >
        <div
          className={`max-w-[70%] px-4 py-3 ${
            isUser
              ? "bg-gold/10 border border-gold/15 rounded-xl rounded-br-sm text-ink"
              : "bg-paper-dark/80 border border-ink/[0.08] rounded-xl rounded-bl-sm text-ink/80"
          }`}
        >
          <DiffViewer
            filePath={(meta.file_path as string) ?? ""}
            oldContent={(meta.old_content as string) ?? ""}
            newContent={(meta.new_content as string) ?? ""}
          />
        </div>
      </div>
    );
  }

  // HTML preview detection
  const htmlCode = !isUser ? extractHtmlFromMarkdown(message.content) : null;

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-5 animate-fade-in-up`}
    >
      <div
        className={`max-w-[70%] px-4 py-3 ${
          isUser
            ? "bg-gold/10 border border-gold/15 rounded-xl rounded-br-sm text-ink"
            : "bg-paper-dark/80 border border-ink/[0.08] rounded-xl rounded-bl-sm text-ink/80"
        }`}
        style={
          !isUser && agentColor
            ? {
                borderLeftWidth: "2px",
                borderLeftColor: agentColor,
              }
            : undefined
        }
      >
        {!isUser && (
          <div
            className="text-xs font-medium mb-1.5 tracking-wide"
            style={{ color: agentColor || "#6a6a7d" }}
          >
            {message.sender_name || message.sender}
          </div>
        )}
        {toolExecutions.map((tool) => (
          <ToolExecutionCard key={tool.id} tool={tool} />
        ))}
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeSanitize]}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        {htmlCode && (
          <div className="mt-3">
            <PreviewCard
              htmlCode={htmlCode}
              title={extractTitle(message.content)}
              height={300}
            />
          </div>
        )}
        {isStreaming && (
          <span className="inline-block w-1.5 h-3.5 bg-gold/70 ml-1 animate-pulse rounded-sm" />
        )}
      </div>
    </div>
  );
}
