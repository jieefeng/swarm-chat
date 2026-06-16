import { describe, expect, it } from "vitest";
import { WUXING_BEASTS, WUXING_FLOW_INDEX, WUXING_FLOW_ORDER } from "../wuxing";

describe("WUXING_FLOW_ORDER", () => {
  it("contains exactly 3 core agents", () => {
    expect(WUXING_FLOW_ORDER).toEqual(["designer", "developer", "qa"]);
  });

  it("no stale agent ids (pm, architect)", () => {
    expect(WUXING_FLOW_ORDER).not.toContain("pm");
    expect(WUXING_FLOW_ORDER).not.toContain("architect");
  });
});

describe("WUXING_FLOW_INDEX", () => {
  it("maps each beast to its position in FLOW_ORDER", () => {
    WUXING_FLOW_ORDER.forEach((id, i) => {
      expect(WUXING_FLOW_INDEX[id]).toBe(i);
    });
  });

  it("has no pm or architect keys", () => {
    expect(WUXING_FLOW_INDEX).not.toHaveProperty("pm");
    expect(WUXING_FLOW_INDEX).not.toHaveProperty("architect");
  });
});

describe("WUXING_BEASTS", () => {
  it("has 3 beasts (designer, developer, qa)", () => {
    expect(WUXING_BEASTS).toHaveLength(3);
    const ids = WUXING_BEASTS.map((b) => b.id);
    expect(ids).toContain("designer");
    expect(ids).toContain("developer");
    expect(ids).toContain("qa");
    expect(ids).not.toContain("pm");
    expect(ids).not.toContain("architect");
  });
});
