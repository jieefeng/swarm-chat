"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

const DiffViewerLib = dynamic(() => import("react-diff-viewer-continued"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center py-8 text-ink/30 text-sm">
      Loading diff viewer...
    </div>
  ),
});

interface DiffViewerProps {
  filePath: string;
  oldContent: string;
  newContent: string;
  onAccept?: () => void;
  onReject?: () => void;
}

export function DiffViewer({
  filePath,
  oldContent,
  newContent,
  onAccept,
  onReject,
}: DiffViewerProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="overflow-hidden rounded-lg border border-ink/[0.1]">
      {/* Header */}
      <div className="flex items-center justify-between bg-paper-dark/40 px-4 py-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-ink/30 hover:text-ink/60 transition-colors"
          >
            {expanded ? "▼" : "▶"}
          </button>
          <span className="font-mono text-sm text-ink/60">{filePath}</span>
        </div>
        <div className="flex gap-2">
          {onReject && (
            <button
              onClick={onReject}
              className="rounded-lg border border-danger/20 px-2 py-1 text-xs text-danger hover:bg-danger/10 transition-colors"
            >
              Reject
            </button>
          )}
          {onAccept && (
            <button
              onClick={onAccept}
              className="rounded-lg border border-wuxing-wood/20 px-2 py-1 text-xs text-wuxing-wood hover:bg-wuxing-wood/10 transition-colors"
            >
              Accept
            </button>
          )}
        </div>
      </div>
      {/* Diff content */}
      {expanded && (
        <div className="max-h-96 overflow-auto">
          <DiffViewerLib
            oldValue={oldContent}
            newValue={newContent}
            splitView={false}
            useDarkTheme={false}
          />
        </div>
      )}
    </div>
  );
}
