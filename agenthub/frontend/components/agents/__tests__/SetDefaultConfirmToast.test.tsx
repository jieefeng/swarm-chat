import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SetDefaultConfirmToast } from "../SetDefaultConfirmToast";

describe("SetDefaultConfirmToast", () => {
  it("renders agent name in prompt", () => {
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByRole("dialog").textContent).toMatch(
      /将.*开发.*设为该.*会话的默认对话对象/,
    );
  });

  it("calls onConfirm when 确认 clicked", () => {
    const onConfirm = vi.fn();
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "确认" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when 拒绝 clicked", () => {
    const onCancel = vi.fn();
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "拒绝" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
