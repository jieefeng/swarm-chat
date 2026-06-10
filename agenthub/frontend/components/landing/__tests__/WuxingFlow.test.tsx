import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WuxingFlow } from "../WuxingFlow";

describe("WuxingFlow entrance animation", () => {
  it("renders 4 beast nodes with reveal-beast class and stagger delays in WUXING_FLOW_ORDER", () => {
    render(<WuxingFlow />);
    // 4 神兽节点的 aria-label 是 nickname（按 WUXING_FLOW_ORDER 顺序）
    const nodes = ["苍龙", "啸风", "炎翎", "瑞麟"].map((nickname) =>
      screen.getByLabelText(nickname),
    );
    expect(nodes).toHaveLength(4);
    nodes.forEach((node) => {
      // SVG <g> elements expose className as SVGAnimatedString at runtime
      // (jsdom + React). Cast through unknown to satisfy tsc's DOM lib types.
      const className = (node.className as unknown as { baseVal: string })
        .baseVal;
      expect(className).toContain("reveal-beast");
    });
    // stagger delay 0ms, 140ms, 280ms, 420ms
    expect(nodes[0]?.getAttribute("style")).toMatch(/animation-delay:\s*0ms/);
    expect(nodes[1]?.getAttribute("style")).toMatch(/animation-delay:\s*140ms/);
    expect(nodes[2]?.getAttribute("style")).toMatch(/animation-delay:\s*280ms/);
    expect(nodes[3]?.getAttribute("style")).toMatch(/animation-delay:\s*420ms/);
  });
});
