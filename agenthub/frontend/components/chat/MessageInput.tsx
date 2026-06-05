"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import {
  type SendMessageInput,
  sendMessageSchema,
} from "@/lib/schemas/message";
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
}

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
  });
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    reset,
  } = useForm<SendMessageInput>({
    resolver: zodResolver(sendMessageSchema),
  });

  const filteredAgents = mentionState.isActive
    ? mentionCandidates.filter((agent) =>
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
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(" ")) {
        setMentionState({
          isActive: true,
          filterText: textAfterAt,
          startIndex: lastAtIndex,
          cursorPos: cursorPos,
        });
        return;
      }
    }

    setMentionState({
      isActive: false,
      filterText: "",
      startIndex: -1,
      cursorPos: 0,
    });
  };

  const handleSelect = (candidate: MentionCandidate) => {
    if (mentionState.startIndex === -1) return;

    const beforeMention = input.slice(0, mentionState.startIndex);
    const afterMention = input.slice(mentionState.cursorPos);
    const mentionInsert = `@${candidate.label} `;

    const newValue = beforeMention + mentionInsert + afterMention;
    setInput(newValue);
    setValue("content", newValue, { shouldValidate: false });
    setMentionState({
      isActive: false,
      filterText: "",
      startIndex: -1,
      cursorPos: 0,
    });

    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = beforeMention.length + mentionInsert.length;
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
          });
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [mentionState.isActive]);

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
          placeholder={disabled ? "等待回复…" : "输入消息，@某人可定向发送"}
          disabled={disabled}
          className="w-full px-5 py-3 bg-white border border-ink/[0.1] rounded-xl text-ink placeholder:text-ink/30 focus:outline-none focus:border-gold/40 focus:bg-white transition-all duration-200 font-body text-sm"
        />
        {errors.content && (
          <p className="text-danger text-xs mt-1.5 font-body">
            {errors.content.message}
          </p>
        )}
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              candidates={filteredAgents}
              onSelect={handleSelect}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className={`ml-3 px-6 py-3 rounded-xl font-display font-medium text-sm transition-all duration-200 ${
          input.trim() && !disabled
            ? "bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 hover:shadow-lg hover:shadow-gold/10"
            : "bg-ink/[0.03] text-ink/25 border border-ink/[0.08] cursor-not-allowed"
        }`}
      >
        发送
      </button>
    </form>
  );
}
