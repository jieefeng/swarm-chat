import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PreviewCard } from "../PreviewCard";


afterEach(() => {
  vi.restoreAllMocks();
});
describe("PreviewCard", () => {
  const mockHtml = "<html><body><div>Hello World</div></body></html>";

  it("renders preview card", () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    expect(screen.getByText("预览")).toBeInTheDocument();
    expect(screen.getByTitle("网页预览")).toBeInTheDocument();
  });

  it("shows custom title", () => {
    render(<PreviewCard htmlCode={mockHtml} title="登录页面" />);
    expect(screen.getByText("登录页面")).toBeInTheDocument();
  });

  it("supports collapse", () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    expect(screen.getByTitle("网页预览")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("collapse"));
    expect(screen.queryByTitle("网页预览")).not.toBeInTheDocument();
  });

  it("supports expand after collapse", () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    fireEvent.click(screen.getByLabelText("collapse"));
    expect(screen.queryByTitle("网页预览")).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("collapse"));
    expect(screen.getByTitle("网页预览")).toBeInTheDocument();
  });

  it("supports refresh", () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    const refreshBtn = screen.getByLabelText("refresh");
    expect(refreshBtn).toBeInTheDocument();
    fireEvent.click(refreshBtn);
    expect(screen.getByTitle("网页预览")).toBeInTheDocument();
  });

  it("supports copy", () => {
    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText: writeTextSpy } });

    render(<PreviewCard htmlCode={mockHtml} />);
    fireEvent.click(screen.getByLabelText("copy"));
    expect(writeTextSpy).toHaveBeenCalledWith(mockHtml);
  });

  it("shows expand button when onExpand is provided", () => {
    render(<PreviewCard htmlCode={mockHtml} onExpand={vi.fn()} />);
    expect(screen.getByLabelText("expand")).toBeInTheDocument();
  });

  it("hides expand button when onExpand is not provided", () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    expect(screen.queryByLabelText("expand")).not.toBeInTheDocument();
  });

  it("calls onExpand callback", () => {
    const onExpand = vi.fn();
    render(<PreviewCard htmlCode={mockHtml} onExpand={onExpand} />);
    fireEvent.click(screen.getByLabelText("expand"));
    expect(onExpand).toHaveBeenCalled();
  });
});
