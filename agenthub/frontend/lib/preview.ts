/**
 * 从 markdown 内容中提取 HTML 代码
 */
export function extractHtmlFromMarkdown(content: string): string | null {
  const htmlMatch = content.match(/```html\n([\s\S]*?)\n```/);
  if (htmlMatch) { return htmlMatch[1]!.trim(); }

  const fullHtmlMatch = content.match(/(<!DOCTYPE html>[\s\S]*<\/html>)/i);
  if (fullHtmlMatch) { return fullHtmlMatch[1]!; }

  const basicHtmlMatch = content.match(/(<html[\s\S]*<\/html>)/i);
  if (basicHtmlMatch) { return basicHtmlMatch[1]!; }

  return null;
}

/**
 * 处理 HTML：注入 viewport、基础样式
 */
export function processHtml(htmlCode: string): string {
  let html = htmlCode;

  if (!html.includes("<html")) {
    html = `<!DOCTYPE html><html><head><\/head><body>${html}<\/body><\/html>`;
  }

  if (!html.includes("<!DOCTYPE")) {
    html = "<!DOCTYPE html>" + html;
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
  <\/style>`;

  if (!html.includes("box-sizing")) {
    html = html.replace(/<\/head>/i, `${baseStyles}<\/head>`);
  }

  return html;
}

/**
 * 从内容中提取标题
 */
export function extractTitle(content: string): string {
  const titleMatch = content.match(/^#\s+(.+)$/m);
  if (titleMatch) { return titleMatch[1]!; }

  const htmlTitleMatch = content.match(/<title>(.+?)<\/title>/i);
  if (htmlTitleMatch) { return htmlTitleMatch[1]!; }

  return "预览";
}
