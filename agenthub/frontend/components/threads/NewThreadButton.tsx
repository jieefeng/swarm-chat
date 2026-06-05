"use client";

import { PlusIcon } from "@heroicons/react/24/outline";

interface NewThreadButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export function NewThreadButton({ onClick, disabled }: NewThreadButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-body text-gold-dim bg-gold/[0.08] border border-gold/15 rounded-lg hover:bg-gold/15 hover:border-gold/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
    >
      <PlusIcon className="w-4 h-4" />
      新建会话
    </button>
  );
}
