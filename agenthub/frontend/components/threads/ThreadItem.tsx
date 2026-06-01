"use client";

interface ThreadItemProps {
  thread: {
    id: string;
    title: string;
    participants: string[];
  };
  isActive: boolean;
  onClick: () => void;
}

export function ThreadItem({ thread, isActive, onClick }: ThreadItemProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={`p-3 cursor-pointer border-b hover:bg-gray-50 ${
        isActive ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
      }`}
    >
      <div className="font-medium text-sm truncate">{thread.title}</div>
      <div className="text-xs text-gray-500 mt-1">
        {thread.participants.length > 0
          ? thread.participants.join(", ")
          : "无参与者"}
      </div>
    </div>
  );
}
