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
      /将.*开发.*设为默认/,
    );
  });

  it("calls onConfirm when 确定 clicked", () => {
    const onConfirm = vi.fn();
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "确定" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when 取消 clicked", () => {
    const onCancel = vi.fn();
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "取消" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
