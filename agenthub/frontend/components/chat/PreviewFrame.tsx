"use client";

import { useMemo } from "react";
import { processHtml } from "@/lib/preview";

interface PreviewFrameProps {
  htmlCode: string;
  height?: number;
}

export function PreviewFrame({ htmlCode, height = 400 }: PreviewFrameProps) {
  const processedHtml = useMemo(() => processHtml(htmlCode), [htmlCode]);

  return (
    <div className="relative bg-white" style={{ height }}>
      <iframe
        srcDoc={processedHtml}
        sandbox="allow-scripts allow-forms allow-modals"
        className="w-full h-full border-0"
        title="网页预览"
      />
    </div>
  );
}
