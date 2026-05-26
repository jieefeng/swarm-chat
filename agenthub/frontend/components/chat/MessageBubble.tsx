"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { ClarificationCard } from "@/components/chat/ClarificationCard";
import { DiffViewer } from "@/components/chat/DiffViewer";
import { TaskPanel } from "@/components/chat/TaskPanel";
import { useTaskStore } from "@/lib/stores/taskStore";
import type { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
  isStreaming: boolean;
  onCopySuccess?: () => void;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.type === "user";

  if (message.messageType === "task_panel") {
    const tasks = useTaskStore.getState().tasks;
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            isUser
              ? "bg-primary text-white"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          <TaskPanel tasks={tasks} />
        </div>
      </div>
    );
  }

  if (message.messageType === "clarification") {
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            isUser
              ? "bg-primary text-white"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          <ClarificationCard
            question={message.content}
            options={(message.metadata?.options as string[]) ?? []}
            onSelect={(option) => {
              // Dispatch a custom event so parent can handle sending the selected option
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
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            isUser
              ? "bg-primary text-white"
              : "bg-white text-gray-800 border border-gray-200"
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

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 ${
          isUser
            ? "bg-primary text-white"
            : "bg-white text-gray-800 border border-gray-200"
        }`}
      >
        {!isUser && (
          <div className="text-xs font-medium text-gray-500 mb-1">
            {message.sender_name || message.sender}
          </div>
        )}
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeSanitize]}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
        )}
      </div>
    </div>
  );
}
