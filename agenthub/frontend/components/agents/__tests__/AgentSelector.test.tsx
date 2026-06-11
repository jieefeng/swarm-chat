import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Agent } from "@/lib/types";
import { AgentSelector } from "../AgentSelector";

const makeAgent = (id: string, nickname: string): Agent => ({
  id,
  name: id.toUpperCase(),
  role: "test",
  nickname,
  color: { primary: "#000", secondary: "#fff" },
});

const agents: Agent[] = [
  makeAgent("designer", "设计"),
  makeAgent("dev", "开发"),
  makeAgent("qa", "测试"),
];

describe("AgentSelector", () => {
  it("renders all agents", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId={null}
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    expect(screen.getByText("设计")).toBeInTheDocument();
    expect(screen.getByText("开发")).toBeInTheDocument();
    expect(screen.getByText("测试")).toBeInTheDocument();
  });

  it("shows 默认 badge on the default agent chip", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const devChip = screen.getByText("开发").closest("[role='button']");
    expect(devChip).toHaveTextContent("默认");
  });

  it("does not show 默认 badge on non-default chips", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const designerChip = screen.getByText("设计").closest("[role='button']");
    expect(designerChip).not.toHaveTextContent("默认");
  });

  it("shows 设为默认 button on non-default chips", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const designerChip = screen.getByText("设计").closest("[role='button']");
    expect(
      designerChip?.querySelector("button[aria-label='设为默认']"),
    ).toBeInTheDocument();
  });

  it("does not show 设为默认 button on the default chip", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const devChip = screen.getByText("开发").closest("[role='button']");
    expect(
      devChip?.querySelector("button[aria-label='设为默认']"),
    ).not.toBeInTheDocument();
  });

  it("calls onSetDefault with the agent id when 设为默认 clicked", () => {
    const onSetDefault = vi.fn();
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={onSetDefault}
      />,
    );
    const designerChip = screen.getByText("设计").closest("[role='button']");
    const btn = designerChip?.querySelector(
      "button[aria-label='设为默认']",
    ) as HTMLButtonElement;
    fireEvent.click(btn);
    expect(onSetDefault).toHaveBeenCalledWith("designer");
  });
});
