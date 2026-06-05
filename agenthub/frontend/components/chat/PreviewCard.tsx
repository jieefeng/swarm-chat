"use client";

import { useCallback, useState } from "react";
import { PreviewFrame } from "./PreviewFrame";
import { PreviewToolbar } from "./PreviewToolbar";

interface PreviewCardProps {
  htmlCode: string;
  title?: string;
  height?: number;
  onExpand?: () => void;
}

export function PreviewCard({
  htmlCode,
  title = "预览",
  height = 400,
  onExpand,
}: PreviewCardProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  const handleCollapse = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, []);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(htmlCode).catch(() => {
      try {
        const textarea = document.createElement("textarea");
        textarea.value = htmlCode;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      } catch {
        window.alert("复制失败，请手动选择内容复制");
      }
    });
  }, [htmlCode]);

  return (
    <div className="rounded-lg border border-ink/[0.1] overflow-hidden">
      <PreviewToolbar
        title={title}
        isCollapsed={isCollapsed}
        onCollapse={handleCollapse}
        onRefresh={handleRefresh}
        onCopy={handleCopy}
        onExpand={onExpand}
      />
      {!isCollapsed && (
        <PreviewFrame key={refreshKey} htmlCode={htmlCode} height={height} />
      )}
    </div>
  );
}
