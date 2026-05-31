import { describe, it, expect } from "vitest";
import { extractHtmlFromMarkdown, processHtml, extractTitle } from "../preview";

describe("extractHtmlFromMarkdown", () => {
  it("从 html 代码块中提取", () => {
    const content = "一些文字\n```html\n<div>Hello</div>\n```\n更多文字";
    expect(extractHtmlFromMarkdown(content)).toBe("<div>Hello</div>");
  });

  it("提取完整 HTML 文档", () => {
    const content = "前文\n<!DOCTYPE html><html><body>Test</body></html>\n后文";
    expect(extractHtmlFromMarkdown(content)).toBe("<!DOCTYPE html><html><body>Test</body></html>");
  });

  it("无 HTML 时返回 null", () => {
    expect(extractHtmlFromMarkdown("普通文本")).toBeNull();
  });
});

describe("processHtml", () => {
  it("注入 viewport meta", () => {
    const html = "<html><head></head><body></body></html>";
    const result = processHtml(html);
    expect(result).toContain("viewport");
  });

  it("注入基础样式", () => {
    const html = "<html><head></head><body></body></html>";
    const result = processHtml(html);
    expect(result).toContain("box-sizing");
  });

  it("处理无 head 标签的 HTML", () => {
    const html = "<div>Hello</div>";
    const result = processHtml(html);
    expect(result).toContain("<html");
    expect(result).toContain("viewport");
  });

  it("处理有 <html> 但无 DOCTYPE 的 HTML", () => {
    const html = "<html><head></head><body>Test</body></html>";
    const result = processHtml(html);
    expect(result).toContain("<!DOCTYPE html>");
    expect(result).toContain("viewport");
  });

  it("幂等性：两次调用结果一致", () => {
    const html = "<html><head></head><body></body></html>";
    const first = processHtml(html);
    const second = processHtml(first);
    expect(second).toBe(first);
  });
});

describe("extractTitle", () => {
  it("从 markdown 标题中提取", () => {
    expect(extractTitle("# My Title\n内容")).toBe("My Title");
  });

  it("从 HTML title 中提取", () => {
    expect(extractTitle("<title>Page Title</title>")).toBe("Page Title");
  });

  it("无标题时返回默认值", () => {
    expect(extractTitle("普通文本")).toBe("预览");
  });

  it("不匹配 H2 标题", () => {
    expect(extractTitle("## Sub Title")).toBe("预览");
  });

  it("不匹配 H3 标题", () => {
    expect(extractTitle("### Sub Sub Title")).toBe("预览");
  });
});
