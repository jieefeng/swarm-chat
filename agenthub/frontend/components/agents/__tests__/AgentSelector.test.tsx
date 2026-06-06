import { render, screen } from "@testing-library/react";
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
  makeAgent("pm", "产品"),
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
    expect(screen.getByText("产品")).toBeInTheDocument();
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
    const pmChip = screen.getByText("产品").closest("[role='button']");
    expect(pmChip).not.toHaveTextContent("默认");
  });
});
