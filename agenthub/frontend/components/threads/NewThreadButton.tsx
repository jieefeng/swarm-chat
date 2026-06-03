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
      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <PlusIcon className="w-4 h-4" />
      新建会话
    </button>
  );
}
