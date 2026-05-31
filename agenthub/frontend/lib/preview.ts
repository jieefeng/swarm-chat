/**
 * 从 markdown 内容中提取 HTML 代码
 */
export function extractHtmlFromMarkdown(content: string): string | null {
  const htmlMatch = content.match(/```html\n([\s\S]*?)\n```/);
  if (htmlMatch?.[1]) { return htmlMatch[1].trim(); }

  const fullHtmlMatch = content.match(/(<!DOCTYPE html>[\s\S]*<\/html>)/i);
  if (fullHtmlMatch?.[1]) { return fullHtmlMatch[1]; }

  const basicHtmlMatch = content.match(/(<html[\s\S]*<\/html>)/i);
  if (basicHtmlMatch?.[1]) { return basicHtmlMatch[1]; }

  return null;
}

/**
 * 处理 HTML：注入 CSP、viewport、基础样式
 *
 * 顺序依赖说明：
 * 1. 先检查 <html> 是否存在，不存在则包裹完整骨架（含 <head> 和 <body>）
 * 2. 再检查 DOCTYPE，不存在则前缀添加
 * 3. 最后注入 CSP、viewport 和样式——此时 <head> 和 </head> 一定存在
 * 如果调换步骤 1 和 3，当输入为裸片段时 <head> 不存在，replace 会静默失败
 */
export function processHtml(htmlCode: string): string {
  let html = htmlCode;

  if (!html.includes("<html")) {
    html = `<!DOCTYPE html><html><head></head><body>${html}</body></html>`;
  }

  if (!html.includes("<!DOCTYPE")) {
    html = "<!DOCTYPE html>" + html;
  }

  if (!html.includes("Content-Security-Policy")) {
    html = html.replace(/<head>/i,
      `<head><meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' 'unsafe-eval' https:">`
    );
  }

  if (!html.includes("viewport")) {
    html = html.replace(/<head>/i,
      "<head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
    );
  }

  const baseStyles = `<style>
    * { box-sizing: border-box; }
    body { margin: 0; padding: 16px; font-family: system-ui, -apple-system, sans-serif; }
    img { max-width: 100%; height: auto; }
    pre { overflow-x: auto; }
  </style>`;

  if (!html.includes("box-sizing")) {
    html = html.replace(/<\/head>/i, `${baseStyles}</head>`);
  }

  return html;
}

/**
 * 从内容中提取标题
 */
export function extractTitle(content: string): string {
  const titleMatch = content.match(/^#\s+(.+)$/m);
  if (titleMatch?.[1]) { return titleMatch[1]; }

  const htmlTitleMatch = content.match(/<title>(.+?)<\/title>/i);
  if (htmlTitleMatch?.[1]) { return htmlTitleMatch[1]; }

  return "预览";
}
