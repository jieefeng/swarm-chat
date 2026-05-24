'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Agent } from '@/lib/types';
import { MentionDropdown } from './MentionDropdown';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  agents?: Agent[];
}

interface MentionState {
  isActive: boolean;
  filterText: string;
  startIndex: number;
}

export function MessageInput({ onSend, disabled, agents = [] }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [mentionState, setMentionState] = useState<MentionState>({
    isActive: false,
    filterText: '',
    startIndex: -1,
  });
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredAgents = mentionState.isActive
    ? agents.filter((agent) =>
        agent.name.includes(mentionState.filterText) ||
        agent.role.includes(mentionState.filterText)
      )
    : [];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart ?? 0;

    setInput(value);

    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(' ')) {
        setMentionState({
          isActive: true,
          filterText: textAfterAt,
          startIndex: lastAtIndex,
        });
        return;
      }
    }

    setMentionState({
      isActive: false,
      filterText: '',
      startIndex: -1,
    });
  };

  const handleSelect = (agent: Agent) => {
    if (mentionState.startIndex === -1) return;

    const beforeMention = input.slice(0, mentionState.startIndex);
    const afterMention = input.slice(inputRef.current?.selectionStart ?? mentionState.startIndex);
    const mentionInsert = `@${agent.name} `;

    setInput(beforeMention + mentionInsert + afterMention);
    setMentionState({
      isActive: false,
      filterText: '',
      startIndex: -1,
    });

    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = beforeMention.length + mentionInsert.length;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      setMentionState({
        isActive: false,
        filterText: '',
        startIndex: -1,
      });
      e.preventDefault();
    }
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mentionState.isActive && inputRef.current) {
        const target = e.target as HTMLElement;
        if (!inputRef.current.contains(target) && !target.closest('.mention-dropdown')) {
          setMentionState({
            isActive: false,
            filterText: '',
            startIndex: -1,
          });
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [mentionState.isActive]);

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      if (!input.trim() || disabled) return;
      onSend(input.trim());
      setInput('');
    }} className="flex p-4 border-t bg-white">
      <div className="flex-1 relative">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "等待回复..." : "输入消息，@某人可定向发送"}
          disabled={disabled}
          className="w-full px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:border-blue-500"
        />
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              options={filteredAgents}
              onSelect={handleSelect}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={!input.trim() || disabled}
        className={`ml-3 px-6 py-3 rounded-full font-medium ${
          input.trim() && !disabled
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        发送
      </button>
    </form>
  );
}