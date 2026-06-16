"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import {
  type SendMessageInput,
  sendMessageSchema,
} from "@/lib/schemas/message";
import { useMessageStore } from "@/lib/stores/messageStore";
import type { MentionCandidate } from "@/lib/types";
import { MentionDropdown } from "./MentionDropdown";

interface MessageInputProps {
  onSubmit: (content: string, agentId?: string) => void;
  disabled: boolean;
  mentionCandidates: MentionCandidate[];
  defaultAgentId?: string | null;
}

interface MentionState {
  isActive: boolean;
  filterText: string;
  startIndex: number;
  cursorPos: number;
  /** 当前激活的模式：@ 提及还是 / 命令 */
  mode: "mention" | "command";
}

/** /code 子命令配置 */
const CODE_SUBCOMMANDS: MentionCandidate[] = [
  {
    id: "read",
    label: "read",
    icon: "📄",
    description: "读取文件内容",
    isCommand: true,
  },
  {
    id: "ls",
    label: "ls",
    icon: "📂",
    description: "列出目录",
    isCommand: true,
  },
  {
    id: "run",
    label: "run",
    icon: "⚡",
    description: "执行 shell 命令",
    isCommand: true,
  },
  {
    id: "env",
    label: "env",
    icon: "🔧",
    description: "查看环境信息",
    isCommand: true,
  },
  {
    id: "project",
    label: "project",
    icon: "📊",
    description: "分析项目结构",
    isCommand: true,
  },
  {
    id: "search",
    label: "search",
    icon: "🔍",
    description: "搜索文件内容",
    isCommand: true,
  },
  {
    id: "info",
    label: "info",
    icon: "ℹ️",
    description: "查看文件详情",
    isCommand: true,
  },
];

/** 顶级 / 命令配置 */
const TOP_COMMANDS: MentionCandidate[] = [
  {
    id: "code",
    label: "code",
    icon: "💻",
    description: "本地代码操作",
    isCommand: true,
  },
  {
    id: "help",
    label: "help",
    icon: "❓",
    description: "查看帮助",
    isCommand: true,
  },
];

export function MessageInput({
  onSubmit,
  disabled,
  mentionCandidates,
  defaultAgentId,
}: MessageInputProps) {
  const [input, setInput] = useState("");
  const [mentionState, setMentionState] = useState<MentionState>({
    isActive: false,
    filterText: "",
    startIndex: -1,
    cursorPos: 0,
    mode: "mention",
  });
  const inputRef = useRef<HTMLInputElement>(null);

  // A2A 状态
  const { a2aState, cancelA2A } = useMessageStore();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    reset,
  } = useForm<SendMessageInput>({
    resolver: zodResolver(sendMessageSchema),
  });

  // 根据模式过滤候选项
  const filteredCandidates = mentionState.isActive
    ? mentionState.mode === "command"
      ? (() => {
          // /code 后面过滤子命令，/ 后面过滤顶级命令
          const textBeforeCursor = input.slice(0, mentionState.cursorPos);
          const isCodeSubcommand = textBeforeCursor.startsWith("/code ");
          const source = isCodeSubcommand ? CODE_SUBCOMMANDS : TOP_COMMANDS;
          return source.filter((cmd) =>
            cmd.label
              .toLowerCase()
              .includes(mentionState.filterText.toLowerCase()),
          );
        })()
      : mentionCandidates.filter((agent) =>
          agent.label
            .toLowerCase()
            .includes(mentionState.filterText.toLowerCase()),
        )
    : [];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart ?? 0;

    setInput(value);
    setValue("content", value, { shouldValidate: false });

    const textBeforeCursor = value.slice(0, cursorPos);

    // 检测 @ 提及
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(" ")) {
        setMentionState({
          isActive: true,
          filterText: textAfterAt,
          startIndex: lastAtIndex,
          cursorPos: cursorPos,
          mode: "mention",
        });
        return;
      }
    }

    // 检测 / 命令（仅在输入开头触发）
    if (textBeforeCursor.startsWith("/")) {
      const textAfterSlash = textBeforeCursor.slice(1);
      // 如果已经输入了空格（如 /code read），不再触发补全
      if (!textAfterSlash.includes(" ")) {
        setMentionState({
          isActive: true,
          filterText: textAfterSlash,
          startIndex: 0,
          cursorPos: cursorPos,
          mode: "command",
        });
        return;
      }
      // /code 后还没输入空格时，触发子命令补全
      if (
        textBeforeCursor.startsWith("/code ") ||
        textBeforeCursor === "/code"
      ) {
        const afterCode = textBeforeCursor.slice(5); // 去掉 "/code"
        if (
          afterCode.trim() === "" ||
          (!afterCode.includes(" ") && afterCode.trim().length > 0)
        ) {
          setMentionState({
            isActive: true,
            filterText: afterCode.trim(),
            startIndex: 5,
            cursorPos: cursorPos,
            mode: "command",
          });
          return;
        }
      }
    }

    setMentionState({
      isActive: false,
      filterText: "",
      startIndex: -1,
      cursorPos: 0,
      mode: "mention",
    });
  };

  const handleSelect = (candidate: MentionCandidate) => {
    if (mentionState.startIndex === -1) return;

    const beforeMention = input.slice(0, mentionState.startIndex);
    const afterMention = input.slice(mentionState.cursorPos);

    let insertText: string;
    if (mentionState.mode === "command") {
      // 命令模式：判断是顶级命令还是子命令
      if (candidate.id === "code") {
        insertText = "/code ";
      } else if (beforeMention === "/" || beforeMention === "") {
        // 顶级命令（非 code）
        insertText = `/${candidate.label} `;
      } else {
        // /code 子命令
        insertText = `/code ${candidate.label} `;
      }
    } else {
      insertText = `@${candidate.label} `;
    }

    const newValue = beforeMention + insertText + afterMention;
    setInput(newValue);
    setValue("content", newValue, { shouldValidate: false });
    setMentionState({
      isActive: false,
      filterText: "",
      startIndex: -1,
      cursorPos: 0,
      mode: "mention",
    });

    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = beforeMention.length + insertText.length;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const onFormSubmit = (data: SendMessageInput) => {
    // 检查是否有@指令
    const mentionMatch = data.content.match(/@(\w+)/);
    if (mentionMatch?.[1]) {
      onSubmit(data.content);
    } else {
      onSubmit(data.content, defaultAgentId || undefined);
    }
    setInput("");
    reset();
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mentionState.isActive && inputRef.current) {
        const target = e.target as HTMLElement;
        if (
          !inputRef.current.contains(target) &&
          !target.closest(".mention-dropdown")
        ) {
          setMentionState({
            isActive: false,
            filterText: "",
            startIndex: -1,
            cursorPos: 0,
            mode: "mention",
          });
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [mentionState.isActive]);

  const dropdownTitle =
    mentionState.mode === "command"
      ? input.startsWith("/code ")
        ? "/code 子命令"
        : "命令"
      : "选择神兽";

  return (
    <form
      onSubmit={handleSubmit(onFormSubmit)}
      className="flex p-4 border-t border-ink/[0.06] bg-paper/60 backdrop-blur-sm"
    >
      <div className="flex-1 relative">
        <input
          {...register("content")}
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          placeholder={
            disabled ? "等待回复…" : "输入消息，@某人定向发送，/ 查看命令"
          }
          disabled={disabled}
          className="focus-ink w-full px-5 py-3 bg-white border border-ink/[0.1] rounded-xl text-ink placeholder:text-ink/30 focus:border-gold/40 focus:bg-white transition-all duration-200 font-body text-sm"
        />
        {errors.content && (
          <p className="text-danger text-xs mt-1.5 font-body">
            {errors.content.message}
          </p>
        )}
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              candidates={filteredCandidates}
              onSelect={handleSelect}
              title={dropdownTitle}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className={`focus-ink ml-3 px-6 py-3 rounded-xl font-display font-medium text-sm transition-all duration-200 ${
          input.trim() && !disabled
            ? "bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 hover:shadow-lg hover:shadow-gold/10"
            : "bg-ink/[0.03] text-ink/25 border border-ink/[0.08] cursor-not-allowed"
        }`}
      >
        发送
      </button>

      {/* A2A Stop 按钮 */}
      {a2aState.isRunning && (
        <button
          type="button"
          onClick={cancelA2A}
          className="focus-ink ml-3 px-6 py-3 rounded-xl font-display font-medium text-sm transition-all duration-200 bg-danger/15 text-danger border border-danger/25 hover:bg-danger/25 hover:shadow-lg hover:shadow-danger/10"
        >
          ⏹ 停止（{a2aState.currentAgent} 执行中，深度 {a2aState.depth}/
          {a2aState.maxDepth}）
        </button>
      )}
    </form>
  );
}
