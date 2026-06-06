import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConfirmDialog } from "../ConfirmDialog";

describe("ConfirmDialog", () => {
  it("renders dialog when open is true", () => {
    render(
      <ConfirmDialog
        open
        title="删除会话？"
        message="此操作不可撤销"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("does not render dialog when open is false", () => {
    render(
      <ConfirmDialog
        open={false}
        title="删除会话？"
        message="此操作不可撤销"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders title and message", () => {
    render(
      <ConfirmDialog
        open
        title="删除会话？"
        message="此操作不可撤销"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByText("删除会话？")).toBeInTheDocument();
    expect(screen.getByText("此操作不可撤销")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button is clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        onCancel={vi.fn()}
        onConfirm={onConfirm}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "确定" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "取消" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("renders custom confirm and cancel text", () => {
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        confirmText="删除"
        cancelText="放弃"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "删除" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "放弃" })).toBeInTheDocument();
  });

  it("calls onCancel when Escape is pressed", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("does not call onCancel on Escape when isLoading is true", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        isLoading
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("disables both buttons when isLoading is true", () => {
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        isLoading
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "处理中…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "取消" })).toBeDisabled();
  });

  it("displays error message when error prop is set", () => {
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        error="会话不存在"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByText("会话不存在")).toBeInTheDocument();
  });
});
