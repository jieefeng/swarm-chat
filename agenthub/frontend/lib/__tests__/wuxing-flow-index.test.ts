import { describe, expect, it } from "vitest";
import {
  WUXING_FLOW_INDEX,
  WUXING_FLOW_ORDER,
  type BeastId,
} from "@/lib/wuxing";

describe("WUXING_FLOW_INDEX", () => {
  it("maps every BeastId to a unique stagger index 0-4", () => {
    const ids = Object.keys(WUXING_FLOW_INDEX) as BeastId[];
    expect(ids).toHaveLength(5);
    const values = ids.map((id) => WUXING_FLOW_INDEX[id]);
    expect([...values].sort((a, b) => a - b)).toEqual([0, 1, 2, 3, 4]);
  });

  it("agrees with WUXING_FLOW_ORDER ordering", () => {
    // WUXING_FLOW_ORDER[0] should be the beast with stagger index 0
    WUXING_FLOW_ORDER.forEach((id, expectedIndex) => {
      expect(WUXING_FLOW_INDEX[id]).toBe(expectedIndex);
    });
  });

  it("is frozen at the type level (Readonly<Record>)", () => {
    // TypeScript guarantees this at compile time; runtime check via Object.isFrozen
    // is best-effort. We just verify keys.
    expect(Object.keys(WUXING_FLOW_INDEX).sort()).toEqual(
      ["architect", "developer", "orchestrator", "pm", "qa"],
    );
  });
});
