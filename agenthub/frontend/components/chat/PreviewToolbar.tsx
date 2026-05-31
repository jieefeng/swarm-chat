"use client";

interface PreviewToolbarProps {
  title: string;
  isCollapsed?: boolean;
  onCollapse: () => void;
  onRefresh: () => void;
  onCopy: () => void;
  onExpand?: () => void;
}

export function PreviewToolbar({
  title,
  isCollapsed = false,
  onCollapse,
  onRefresh,
  onCopy,
  onExpand,
}: PreviewToolbarProps) {
  return (
    <div className="flex items-center justify-between bg-gray-50 px-3 py-2 border-b border-gray-200">
      <div className="flex items-center gap-2">
        <span className="text-gray-400">🖥️</span>
        <span className="text-sm font-medium text-gray-700 truncate max-w-[200px]">
          {title}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={onCollapse}
          aria-label="collapse"
          className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
          title={isCollapsed ? "expand" : "collapse"}
        >
          <svg
            className={`w-4 h-4 transition-transform ${isCollapsed ? "-rotate-90" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <button
          onClick={onRefresh}
          aria-label="refresh"
          className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
          title="Refresh Preview"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button
          onClick={onCopy}
          aria-label="copy"
          className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
          title="Copy Code"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        {onExpand && (
          <button
            onClick={onExpand}
            aria-label="expand"
            className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
            title="Fullscreen Preview"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
