'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { type SendMessageInput, sendMessageSchema } from '@/lib/schemas/message'
import type { MentionCandidate } from '@/lib/types'
import { MentionDropdown } from './MentionDropdown'

interface MessageInputProps {
  onSubmit: (content: string) => void
  disabled: boolean
  mentionCandidates: MentionCandidate[]
}

interface MentionState {
  isActive: boolean
  filterText: string
  startIndex: number
  cursorPos: number
}

export function MessageInput({
  onSubmit,
  disabled,
  mentionCandidates,
}: MessageInputProps) {
  const [input, setInput] = useState('')
  const [mentionState, setMentionState] = useState<MentionState>({
    isActive: false,
    filterText: '',
    startIndex: -1,
    cursorPos: 0,
  })
  const inputRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<SendMessageInput>({
    resolver: zodResolver(sendMessageSchema),
  })

  const filteredAgents = mentionState.isActive
    ? mentionCandidates.filter((agent) =>
        agent.label
          .toLowerCase()
          .includes(mentionState.filterText.toLowerCase()),
      )
    : []

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const cursorPos = e.target.selectionStart ?? 0

    setInput(value)

    const textBeforeCursor = value.slice(0, cursorPos)
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')

    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1)
      if (!textAfterAt.includes(' ')) {
        setMentionState({
          isActive: true,
          filterText: textAfterAt,
          startIndex: lastAtIndex,
          cursorPos: cursorPos,
        })
        return
      }
    }

    setMentionState({
      isActive: false,
      filterText: '',
      startIndex: -1,
      cursorPos: 0,
    })
  }

  const handleSelect = (candidate: MentionCandidate) => {
    if (mentionState.startIndex === -1) return

    const beforeMention = input.slice(0, mentionState.startIndex)
    const afterMention = input.slice(mentionState.cursorPos)
    const mentionInsert = `@${candidate.label} `

    setInput(beforeMention + mentionInsert + afterMention)
    setMentionState({
      isActive: false,
      filterText: '',
      startIndex: -1,
      cursorPos: 0,
    })

    setTimeout(() => {
      inputRef.current?.focus()
      const newCursorPos = beforeMention.length + mentionInsert.length
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  const onFormSubmit = (data: SendMessageInput) => {
    onSubmit(data.content)
    reset()
  }

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mentionState.isActive && inputRef.current) {
        const target = e.target as HTMLElement
        if (
          !inputRef.current.contains(target) &&
          !target.closest('.mention-dropdown')
        ) {
          setMentionState({
            isActive: false,
            filterText: '',
            startIndex: -1,
            cursorPos: 0,
          })
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [mentionState.isActive])

  return (
    <form
      onSubmit={handleSubmit(onFormSubmit)}
      className="flex p-4 border-t bg-white"
    >
      <div className="flex-1 relative">
        <input
          {...register('content')}
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          placeholder={disabled ? '等待回复...' : '输入消息，@某人可定向发送'}
          disabled={disabled}
          className="w-full px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:border-blue-500"
        />
        {errors.content && (
          <p className="text-red-500 text-sm mt-1">{errors.content.message}</p>
        )}
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              candidates={filteredAgents}
              query={mentionState.filterText}
              onSelect={handleSelect}
              onClose={() =>
                setMentionState((s) => ({ ...s, isActive: false }))
              }
              anchorRect={null}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className={`ml-3 px-6 py-3 rounded-full font-medium ${
          input.trim() && !disabled
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        发送
      </button>
    </form>
  )
}
