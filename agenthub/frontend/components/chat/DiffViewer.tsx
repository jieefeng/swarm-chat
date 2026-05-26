"use client";

import { useState } from "react";
import DiffViewerLib from "react-diff-viewer-continued";

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
    <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between bg-gray-50 px-4 py-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            {expanded ? "▼" : "▶"}
          </button>
          <span className="font-mono text-sm text-gray-700">{filePath}</span>
        </div>
        <div className="flex gap-2">
          {onReject && (
            <button
              onClick={onReject}
              className="rounded border border-red-300 px-2 py-1 text-xs text-red-600 hover:bg-red-50"
            >
              Reject
            </button>
          )}
          {onAccept && (
            <button
              onClick={onAccept}
              className="rounded border border-green-300 px-2 py-1 text-xs text-green-600 hover:bg-green-50"
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
