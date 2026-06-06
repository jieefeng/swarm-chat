# AgentHub Brand Phase 2 - Form Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish AgentHub's "ink-wash" visual system: typography precision, prose / code / quote styling, hover/focus micro-interactions, and a 5-beast stagger entrance animation on the Landing page.

**Architecture:** Pure CSS additions to `globals.css` (token variables + keyframes + component classes + reduced-motion media query), one new `WUXING_FLOW_INDEX` helper in `wuxing.ts`, one new `useReducedMotion` hook (built but not consumed in this phase), and minimal className additions to 5 existing components. **Zero new npm dependencies.**

**Tech Stack:** Tailwind v4 (`@theme` + `@layer components`), CSS `@keyframes` + `prefers-reduced-motion`, vitest + @testing-library/react (for hook/component tests), Next.js 15 server/client components.

**Spec:** `docs/superpowers/specs/2026-06-07-agenthub-form-refinement-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `agenthub/frontend/lib/wuxing.ts` | Modify | Add `WUXING_FLOW_INDEX` helper exporting `pm→0, qa→1, orchestrator→2, developer→3, architect→4` |
| `agenthub/frontend/lib/hooks/useReducedMotion.ts` | Create | SSR-safe hook reading `prefers-reduced-motion`; **not consumed this phase** |
| `agenthub/frontend/app/globals.css` | Modify | Add `--type-*` tokens, `.prose-ink`, `.lift-ink`/`.focus-ink`/`.press-ink`, `inkReveal` keyframe, `.reveal-beast`, reduced-motion media query |
| `agenthub/frontend/components/landing/HeroSection.tsx` | Modify | Add `leading-tight tracking-display` to title (Hero already has it; we'll only adjust the副标题) |
| `agenthub/frontend/components/landing/WuxingFlow.tsx` | Modify | Add `className="reveal-beast"` + `style.animationDelay` to 5 nodes; add `prose-ink` to tooltip content; reduce animation impact on hover |
| `agenthub/frontend/components/landing/BeastRoster.tsx` | Modify | Replace ad-hoc hover transition with `lift-ink focus-ink`; add `reveal-beast` + `animationDelay`; add `prose-ink` to card body |
| `agenthub/frontend/components/landing/ForumEntry.tsx` | Modify | Add `press-ink focus-ink` to CTA Link |
| `agenthub/frontend/components/chat/MessageInput.tsx` | Modify | Add `focus-ink` to input + submit button (preserve existing gold border behavior) |
| `agenthub/frontend/lib/hooks/__tests__/useReducedMotion.test.ts` | Create | vitest test for the hook |
| `agenthub/frontend/lib/__tests__/wuxing-flow-index.test.ts` | Create | vitest test for `WUXING_FLOW_INDEX` |
| `agenthub/frontend/components/landing/__tests__/WuxingFlow.test.tsx` | Create | vitest + RTL test for entrance animation classes |

**Files NOT modified (despite stage-1 spec §2 listing):** `MessageBubble.tsx` — per stage-2 spec §11 decision, awaiting markdown render.

---

## Task 1: Add `WUXING_FLOW_INDEX` helper to `wuxing.ts`

**Files:**
- Modify: `agenthub/frontend/lib/wuxing.ts:115-122`
- Test: `agenthub/frontend/lib/__tests__/wuxing-flow-index.test.ts`

- [ ] **Step 1: Write the failing test**

Create `agenthub/frontend/lib/__tests__/wuxing-flow-index.test.ts`:

```ts
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
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `cd agenthub/frontend && npx vitest run lib/__tests__/wuxing-flow-index.test.ts`
Expected: FAIL with `Cannot find name 'WUXING_FLOW_INDEX'` (TS2304) or similar.

- [ ] **Step 3: Add `WUXING_FLOW_INDEX` to `wuxing.ts`**

In `agenthub/frontend/lib/wuxing.ts`, after the `WUXING_FLOW_ORDER` export (around line 122), add:

```ts
/**
 * 五行相生流转顺序索引(用于 stagger 入场动画的 delay 序号)
 * 0..4,值与 WUXING_FLOW_ORDER 的位置严格一致。
 */
export const WUXING_FLOW_INDEX: Readonly<Record<BeastId, number>> = {
  pm: 0,
  qa: 1,
  orchestrator: 2,
  developer: 3,
  architect: 4,
};
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `cd agenthub/frontend && npx vitest run lib/__tests__/wuxing-flow-index.test.ts`
Expected: PASS — 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/lib/wuxing.ts agenthub/frontend/lib/__tests__/wuxing-flow-index.test.ts
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): add WUXING_FLOW_INDEX helper for stagger animation"
```

---

## Task 2: Create `useReducedMotion` hook (built but not consumed)

**Files:**
- Create: `agenthub/frontend/lib/hooks/useReducedMotion.ts`
- Test: `agenthub/frontend/lib/hooks/__tests__/useReducedMotion.test.ts`

- [ ] **Step 1: Write the failing test**

Create `agenthub/frontend/lib/hooks/__tests__/useReducedMotion.test.ts`:

```ts
import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useReducedMotion } from "@/lib/hooks/useReducedMotion";

describe("useReducedMotion", () => {
  const originalMatchMedia = window.matchMedia;

  function mockMatchMedia(matches: boolean) {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  }

  beforeEach(() => {
    originalMatchMedia;
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it("returns true when matchMedia reports prefers-reduced-motion: reduce", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(true);
  });

  it("returns false when matchMedia reports no reduced motion preference", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
  });

  it("uses the correct media query string", () => {
    mockMatchMedia(false);
    renderHook(() => useReducedMotion());
    expect(window.matchMedia).toHaveBeenCalledWith(
      "(prefers-reduced-motion: reduce)",
    );
  });
});
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `cd agenthub/frontend && npx vitest run lib/hooks/__tests__/useReducedMotion.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `useReducedMotion.ts`**

Create `agenthub/frontend/lib/hooks/useReducedMotion.ts`:

```ts
"use client";

import { useEffect, useState } from "react";

/**
 * 检测用户是否在系统/浏览器层启用了「减少动效」偏好。
 * SSR 安全:服务端返回 false,客户端 hydration 后再读取真实值。
 *
 * 本阶段不消费 — 留作阶段 3+ chat 内动画(消息到达 / 加载状态)。
 * Landing 入场动画的退化已通过 CSS @media (prefers-reduced-motion: reduce) 实现。
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mql.matches);

    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return reduced;
}
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `cd agenthub/frontend && npx vitest run lib/hooks/__tests__/useReducedMotion.test.ts`
Expected: PASS — 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/lib/hooks/useReducedMotion.ts agenthub/frontend/lib/hooks/__tests__/useReducedMotion.test.ts
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): add useReducedMotion hook (reserved for phase 3+ chat animations)"
```

---

## Task 3: Add typography tokens to `globals.css`

**Files:**
- Modify: `agenthub/frontend/app/globals.css:5-40` (extend `@theme` block)

- [ ] **Step 1: Verify current `@theme` block structure**

Read `agenthub/frontend/app/globals.css` lines 5-40. Confirm the `@theme { ... }` block contains `--font-display`, `--font-body`, `--font-mono`. We append after `--font-mono` declaration.

- [ ] **Step 2: Add `--type-*` variables**

After `--font-mono: "JetBrains Mono", "Fira Code", "Consolas", monospace;` (line 34), insert a blank line, then:

```css
  /* 类型尺度(行高 / 字距) */
  --type-leading-tight: 1.2;        /* 标题、卡片标题 */
  --type-leading-normal: 1.6;       /* 正文 */
  --type-leading-loose: 1.75;       /* 长文(README / 长段气泡) */
  --type-tracking-display: 0.02em;  /* display 字体微紧 */
  --type-tracking-body: 0;          /* body 默认 */
  --type-tracking-mono: -0.01em;    /* code 字符收紧 */
```

- [ ] **Step 3: Verify variables compile**

Run: `cd agenthub/frontend && npx tsc --noEmit`
Expected: 0 errors (these are CSS, not TS — this just confirms we didn't break the build reference).

- [ ] **Step 4: Verify variables present in file**

Run: `grep -E '\-\-type-(leading|tracking)' "D:/AAComputerCourse/AACode/muiltAgent/agenthub/frontend/app/globals.css"`
Expected: 6 lines, matching `--type-leading-tight/normal/loose` and `--type-tracking-display/body/mono`.

- [ ] **Step 5: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/app/globals.css
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): add --type-* typography tokens (leading + tracking) to globals.css"
```

---

## Task 4: Add `.prose-ink` class to `globals.css`

**Files:**
- Modify: `agenthub/frontend/app/globals.css` (append new block at end of file)

- [ ] **Step 1: Add `.prose-ink` after `inkDrop` block (around line 171)**

After the existing `.animate-ink-drop { ... }` block (end of file, line 171), append:

```css
/* ── 水墨 prose 样式(行内 code / 代码块 / 引用 / 表格) ── */
@layer components {
  .prose-ink {
    & p { @apply leading-loose my-3; }
    & code {
      @apply font-mono text-[0.9em] px-1.5 py-0.5
             bg-ink/[0.06] text-ink/85 rounded
             tracking-mono;
    }
    & pre {
      @apply font-mono text-xs leading-relaxed tracking-mono
             bg-paper-dark/80 text-ink/70
             border border-ink/[0.08]
             rounded-lg p-3 my-3
             overflow-x-auto;
    }
    & pre code { @apply bg-transparent p-0 text-inherit; }
    & blockquote {
      @apply border-l-2 border-gold/40 pl-4 my-3
             italic text-ink/65 leading-normal;
    }
    & table { @apply w-full text-sm my-3 border-collapse; }
    & th, & td { @apply border border-ink/[0.08] px-3 py-2 text-left; }
    & th { @apply bg-paper-dark/50 font-display tracking-display; }
    & ul, & ol { @apply pl-6 my-3 leading-normal; }
    & li { @apply my-1; }
    & ul { list-style: disc; }
    & ol { list-style: decimal; }
  }
}
```

- [ ] **Step 2: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -20`
Expected: Build succeeds. (The `@layer components` syntax should be processed by Tailwind v4; if build fails on `@apply` inside nested selectors, fall back to flat selector list — see "Fallback" below.)

**Fallback** if `@apply` in nested selectors fails with Tailwind v4: replace the nested `& p { ... }` with flat selectors `.prose-ink p { ... }` etc. (The v4 docs allow both, but `&` nesting can be picky.)

- [ ] **Step 3: Verify class exists**

Run: `grep -c '.prose-ink' "D:/AAComputerCourse/AACode/muiltAgent/agenthub/frontend/app/globals.css"`
Expected: 14 (one selector + 13 nested rules).

- [ ] **Step 4: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/app/globals.css
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): add .prose-ink class for ink-wash code/quote/table styling"
```

---

## Task 5: Add micro-interaction classes to `globals.css`

**Files:**
- Modify: `agenthub/frontend/app/globals.css` (append to existing `@layer components` block from Task 4)

- [ ] **Step 1: Append micro-interaction classes inside the existing `@layer components` block**

Find the closing `}` of the `.prose-ink` block (end of `@layer components` from Task 4). Right **before** that closing `}`, append (no extra blank line):

```css

  /* 卡片:hover:faint lift + cursor */
  .lift-ink {
    @apply transition-all duration-200 ease-out
           hover:-translate-y-0.5 hover:shadow-sm
           active:translate-y-0 active:shadow-none
           cursor-pointer;
  }
  /* focus ring 统一(用 ink 色而非 Tailwind 默认蓝) */
  .focus-ink {
    @apply outline-none
           focus-visible:ring-2 focus-visible:ring-ink/40
           focus-visible:ring-offset-2 focus-visible:ring-offset-paper;
  }
  /* 按钮"按下去"反馈 */
  .press-ink {
    @apply transition-transform duration-100
           active:scale-[0.97];
  }
```

Result: the `@layer components { ... }` block now contains `.prose-ink`, `.lift-ink`, `.focus-ink`, `.press-ink`.

- [ ] **Step 2: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 3: Verify all three classes present**

Run: `grep -E '^\s*\.(lift-ink|focus-ink|press-ink)\s*\{' "D:/AAComputerCourse/AACode/muiltAgent/agenthub/frontend/app/globals.css"`
Expected: 3 lines.

- [ ] **Step 4: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/app/globals.css
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): add .lift-ink / .focus-ink / .press-ink micro-interaction classes"
```

---

## Task 6: Add `inkReveal` keyframe, `.reveal-beast`, and reduced-motion media query

**Files:**
- Modify: `agenthub/frontend/app/globals.css` (append after `@layer components` block from Tasks 4-5)

- [ ] **Step 1: Append keyframe, class, and media query at end of file**

After the `@layer components { ... }` block (closing `}` is the last character of the file as of Task 5), append:

```css

/* ── Landing 入场动画(5 神兽墨染) ── */
@keyframes inkReveal {
  0% {
    opacity: 0;
    transform: scale(0.85) translateY(8px);
    filter: blur(4px);
  }
  60% { filter: blur(0); }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
    filter: blur(0);
  }
}

.reveal-beast {
  opacity: 0;                          /* 默认隐藏,避免动画前闪烁 */
  animation: inkReveal 700ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

/* ── 无障碍:减少动效偏好 → 退化即时显示 ── */
@media (prefers-reduced-motion: reduce) {
  .reveal-beast {
    animation: none;
    opacity: 1;
    transform: none;
    filter: none;
  }
  .lift-ink,
  .press-ink {
    transition: none;
  }
  .lift-ink:hover { transform: none; }
  .press-ink:active { transform: none; }
}
```

- [ ] **Step 2: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 3: Verify keyframe + class + media query all present**

Run:
```bash
grep -c '@keyframes inkReveal' "D:/AAComputerCourse/AACode/muiltAgent/agenthub/frontend/app/globals.css"
grep -c '\.reveal-beast' "D:/AAComputerCourse/AACode/muiltAgent/agenthub/frontend/app/globals.css"
grep -c 'prefers-reduced-motion' "D:/AAComputerCourse/AACode/muiltAgent/agenthub/frontend/app/globals.css"
```
Expected: 1, 4 (selector + 3 media-query overrides + 1 base), 1.

- [ ] **Step 4: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/app/globals.css
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): add inkReveal keyframe, .reveal-beast, and reduced-motion media query"
```

---

## Task 7: Wire entrance animation + lift classes in `BeastRoster.tsx`

**Files:**
- Modify: `agenthub/frontend/components/landing/BeastRoster.tsx:17-62`

- [ ] **Step 1: Add `WUXING_FLOW_INDEX` to imports**

At top of `BeastRoster.tsx`, change the import to:

```ts
import { WUXING_BEASTS, WUXING_FLOW_INDEX } from "@/lib/wuxing";
```

- [ ] **Step 2: Update the `<article>` element to add `reveal-beast` + `lift-ink focus-ink`**

Replace the article element (line 19-23) with:

```tsx
        <article
          key={beast.id}
          data-testid="beast-card"
          className="reveal-beast lift-ink focus-ink rounded-2xl border-2 bg-paper p-5"
          style={{
            borderColor: beast.color.secondary,
            animationDelay: `${WUXING_FLOW_INDEX[beast.id] * 140}ms`,
          }}
        >
```

- [ ] **Step 3: Wrap inner text block in `prose-ink`**

After the avatar div (line 30, `</div>`), wrap the remaining text content (lines 32-59) in a `<div className="prose-ink">...</div>`. Specifically, change the structure to:

```tsx
        <article ...>
          {/* 头像 */}
          <div className="w-20 h-20 mx-auto mb-3 rounded-full flex items-center justify-center text-3xl font-display bg-paper-dark" style={{ color: beast.color.primary }}>
            {beast.beast.charAt(1)}
          </div>

          <div className="prose-ink">
            {/* 名字 + 性格动词 */}
            <div className="text-center mb-2">
              <h3 className="font-display text-lg font-semibold text-ink leading-tight tracking-display">
                {beast.nickname}
              </h3>
              <p className="font-body text-xs text-ink/40 mt-0.5">
                {beast.beast} · {beast.element} · {beast.direction} · {beast.season}
              </p>
            </div>

            {/* 性格动词大字 */}
            <div className="text-center text-3xl font-display font-light my-3" style={{ color: beast.color.primary }}>
              {beast.verb}
            </div>

            {/* 口头禅 */}
            <p className="font-body text-xs text-ink/60 text-center italic leading-normal min-h-[2.5rem]">
              「{beast.catchphrase}」
            </p>

            {/* 擅长 */}
            <p className="font-body text-[11px] text-ink/40 text-center mt-3 leading-normal">
              擅长：{beast.strengths.slice(0, 2).join("、")}
            </p>
          </div>
        </article>
```

Note: the existing `transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5` class on the article is **removed** because `.lift-ink` (added via className) replaces it. We also drop the bigger `hover:shadow-lg` in favor of `.lift-ink`'s gentler `hover:shadow-sm` (the spec's "克制" principle).

- [ ] **Step 4: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/components/landing/BeastRoster.tsx
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): BeastRoster - reveal-beast stagger + lift-ink + prose-ink"
```

---

## Task 8: Wire entrance animation + tooltip `prose-ink` in `WuxingFlow.tsx`

**Files:**
- Modify: `agenthub/frontend/components/landing/WuxingFlow.tsx:101-148` (5 nodes), `:154-179` (tooltip)
- Test: `agenthub/frontend/components/landing/__tests__/WuxingFlow.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `agenthub/frontend/components/landing/__tests__/WuxingFlow.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WuxingFlow } from "@/components/landing/WuxingFlow";

describe("WuxingFlow entrance animation", () => {
  it("renders 5 beast nodes with reveal-beast class and stagger delays in WUXING_FLOW_ORDER", () => {
    render(<WuxingFlow />);
    // 5 神兽节点的 aria-label 是 nickname
    const nodes = ["苍龙", "炎翎", "瑞麟", "啸风", "玄冥"].map((nickname) =>
      screen.getByLabelText(nickname),
    );
    expect(nodes).toHaveLength(5);
    nodes.forEach((node) => {
      expect(node.className.baseVal).toContain("reveal-beast");
    });
    // stagger delay 0ms, 140ms, 280ms, 420ms, 560ms
    expect(nodes[0]!.getAttribute("style")).toMatch(/animation-delay:\s*0ms/);
    expect(nodes[1]!.getAttribute("style")).toMatch(/animation-delay:\s*140ms/);
    expect(nodes[2]!.getAttribute("style")).toMatch(/animation-delay:\s*280ms/);
    expect(nodes[3]!.getAttribute("style")).toMatch(/animation-delay:\s*420ms/);
    expect(nodes[4]!.getAttribute("style")).toMatch(/animation-delay:\s*560ms/);
  });
});
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `cd agenthub/frontend && npx vitest run components/landing/__tests__/WuxingFlow.test.tsx`
Expected: FAIL — `reveal-beast` not in className.

- [ ] **Step 3: Add `WUXING_FLOW_INDEX` to imports**

Change `import { type BeastId, WUXING_BEASTS, WUXING_FLOW_ORDER } from "@/lib/wuxing";` to:

```ts
import {
  type BeastId,
  WUXING_BEASTS,
  WUXING_FLOW_INDEX,
  WUXING_FLOW_ORDER,
} from "@/lib/wuxing";
```

- [ ] **Step 4: Add `reveal-beast` + `animationDelay` to the 5 `<g>` elements**

In the `{flowSteps.map((step, i) => { ... return ( <g ... /> ); })}` block (around lines 101-148), update the `<g>` opening tag to add `className="reveal-beast"` and `style={{ animationDelay: ... }}`:

```tsx
                <g
                  key={step.id}
                  role="button"
                  tabIndex={0}
                  aria-label={step.beast.nickname}
                  className="reveal-beast"
                  style={{
                    cursor: "pointer",
                    animationDelay: `${WUXING_FLOW_INDEX[step.id] * 140}ms`,
                  }}
                  onMouseEnter={() => setHovered(step.id)}
                  onMouseLeave={() => setHovered(null)}
                  onFocus={() => setHovered(step.id)}
                  onBlur={() => setHovered(null)}
                >
```

- [ ] **Step 5: Wrap the tooltip block in `prose-ink`**

The tooltip div (lines 159-178) currently uses inline styles. Replace its outermost container to add `prose-ink` while keeping the inline color styling for border/background:

```tsx
                <div
                  className="prose-ink rounded-2xl p-6 border-2"
                  style={{
                    borderColor: b.color.primary,
                    backgroundColor: b.color.secondary,
                  }}
                >
                  <div className="font-display text-xl text-ink mb-1 leading-tight tracking-display">
                    {b.nickname} · {b.verb}
                  </div>
                  <div className="font-body text-xs text-ink/60 mb-3">
                    {b.role} · {b.element} · {b.direction} · {b.season}
                  </div>
                  <p className="font-body text-sm text-ink/80 italic mb-3 leading-normal">
                    「{b.catchphrase}」
                  </p>
                  <p className="font-body text-xs text-ink/60 leading-normal">
                    擅长：{b.strengths.join("、")}
                  </p>
                </div>
```

- [ ] **Step 6: Run the test, verify it passes**

Run: `cd agenthub/frontend && npx vitest run components/landing/__tests__/WuxingFlow.test.tsx`
Expected: PASS — 1 test passes.

- [ ] **Step 7: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 8: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/components/landing/WuxingFlow.tsx agenthub/frontend/components/landing/__tests__/WuxingFlow.test.tsx
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): WuxingFlow - reveal-beast stagger on 5 nodes + prose-ink tooltip"
```

---

## Task 9: Add `press-ink focus-ink` to `ForumEntry.tsx` CTA

**Files:**
- Modify: `agenthub/frontend/components/landing/ForumEntry.tsx:13-18`

- [ ] **Step 1: Update the `<Link>` className**

Change the Link's className from:

```tsx
        className="inline-block font-display text-base px-8 py-3 rounded-xl bg-ink text-paper hover:bg-ink-light transition-colors shadow-lg shadow-ink/20"
```

to:

```tsx
        className="press-ink focus-ink inline-block font-display text-base px-8 py-3 rounded-xl bg-ink text-paper hover:bg-ink-light transition-colors shadow-lg shadow-ink/20"
```

- [ ] **Step 2: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/components/landing/ForumEntry.tsx
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): ForumEntry CTA - press-ink + focus-ink micro-interactions"
```

---

## Task 10: Add `focus-ink` to `MessageInput.tsx`

**Files:**
- Modify: `agenthub/frontend/components/chat/MessageInput.tsx:163`, `:182-186`

- [ ] **Step 1: Add `focus-ink` to the `<input>` className (line 163)**

Change:

```tsx
            className="w-full px-5 py-3 bg-white border border-ink/[0.1] rounded-xl text-ink placeholder:text-ink/30 focus:outline-none focus:border-gold/40 focus:bg-white transition-all duration-200 font-body text-sm"
```

to:

```tsx
            className="focus-ink w-full px-5 py-3 bg-white border border-ink/[0.1] rounded-xl text-ink placeholder:text-ink/30 focus:border-gold/40 focus:bg-white transition-all duration-200 font-body text-sm"
```

Note: the existing `focus:outline-none` is removed because `.focus-ink` already includes `outline-none` (using `focus-visible:ring` for keyboard accessibility only). The existing `focus:border-gold/40` is preserved.

- [ ] **Step 2: Add `focus-ink` to the submit `<button>` className (line 182-186)**

Change the button's className template from:

```tsx
        className={`ml-3 px-6 py-3 rounded-xl font-display font-medium text-sm transition-all duration-200 ${
```

to:

```tsx
        className={`focus-ink ml-3 px-6 py-3 rounded-xl font-display font-medium text-sm transition-all duration-200 ${
```

- [ ] **Step 3: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/components/chat/MessageInput.tsx
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): MessageInput - focus-ink on input + submit button"
```

---

## Task 11: Add typography precision to `HeroSection.tsx`

**Files:**
- Modify: `agenthub/frontend/components/landing/HeroSection.tsx:24, 27, 30, 33`

- [ ] **Step 1: Tighten title's leading (already has `leading-tight`)**

Line 24 already has `leading-tight tracking-wide`. **No change needed for the h1** — it was already correct. We only adjust the副标题 tracking (line 27) and the long body (lines 30, 33).

- [ ] **Step 2: Replace `tracking-[0.2em]` with `tracking-display` on the p tag (line 27)**

Change:

```tsx
      <p className="font-display text-base md:text-lg text-ink/60 mt-4 tracking-[0.2em]">
        苍龙定策 · 玄冥筑基 · 啸风锻冶 · 炎翎试火 · 瑞麟调律
      </p>
```

to:

```tsx
      <p className="font-display text-base md:text-lg text-ink/60 mt-4 tracking-display">
        苍龙定策 · 玄冥筑基 · 啸风锻冶 · 炎翎试火 · 瑞麟调律
      </p>
```

(Note: `tracking-display` is `0.02em`, much smaller than the previous `tracking-[0.2em]` which was a typo / too-loose. The new value aligns with the spec's "微紧" intent for display font.)

- [ ] **Step 3: Add `leading-normal` to the small body lines (lines 30, 33)**

Change line 30 from:

```tsx
      <p className="font-body text-sm md:text-base text-ink/50 mt-8 max-w-2xl mx-auto">
        你只管 @ 一声，五行自转。
      </p>
```

to:

```tsx
      <p className="font-body text-sm md:text-base text-ink/50 mt-8 max-w-2xl mx-auto leading-normal">
        你只管 @ 一声，五行自转。
      </p>
```

Change line 33 from:

```tsx
      <p className="font-body text-xs md:text-sm text-ink/40 mt-3 max-w-2xl mx-auto italic">
        不是 5 个凑数的 agent，是 5 道工序的人格式分身。
      </p>
```

to:

```tsx
      <p className="font-body text-xs md:text-sm text-ink/40 mt-3 max-w-2xl mx-auto italic leading-normal">
        不是 5 个凑数的 agent，是 5 道工序的人格式分身。
      </p>
```

- [ ] **Step 4: Verify build**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add agenthub/frontend/components/landing/HeroSection.tsx
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "feat(frontend): HeroSection - typography precision (tracking-display + leading-normal)"
```

---

## Task 12: Integration verification (all quality gates)

**Files:** None modified. Pure verification.

- [ ] **Step 1: Type check passes**

Run: `cd agenthub/frontend && npm run check 2>&1 | tail -20`
Expected: 0 TypeScript errors. (Biome + tsc.)

- [ ] **Step 2: Full test suite passes**

Run: `cd agenthub/frontend && npx vitest run 2>&1 | tail -30`
Expected: All tests pass (existing tests + 3 new tests from Tasks 1, 2, 8). Test count should grow from current N to N+8 (1+3+1+3 = 8 new test cases, distributed across 4 files).

- [ ] **Step 3: Production build succeeds**

Run: `cd agenthub/frontend && npm run build 2>&1 | tail -10`
Expected: Build succeeds, no errors.

- [ ] **Step 4: Manual browser verification (the only step that requires a human eye)**

Start dev server: `cd agenthub/frontend && npm run dev`

Then in a browser, navigate to `http://localhost:7000`:

1. **Landing entrance animation** — Refresh page. 5 beast nodes (in `WuxingFlow`) and 5 roster cards should appear sequentially in this order: 苍龙 → 炎翎 → 瑞麟 → 啸风 → 玄冥. Total animation duration should be ~1.26s. No flash of unstyled content before animation starts.
2. **Hover lift on cards** — Hover any of the 5 BeastRoster cards. Should lift up by 0.5 with cursor pointer and slight shadow. Click on a card (just focus it via Tab) should show a focus ring in ink color (not Tailwind default blue).
3. **ForumEntry button** — Click "进议事堂 →" button. Should compress (active:scale-[0.97]) on mousedown. Tab to it — focus ring visible.
4. **MessageInput focus** — Navigate to `/forum`, tab to the message input. Border should turn gold AND a focus ring should appear.
5. **Reduced motion** — In browser dev tools, toggle "Emulate CSS media feature prefers-reduced-motion: reduce". Refresh Landing. 5 nodes should appear instantly with no animation.

If any check fails, fix and re-run from Step 1.

- [ ] **Step 5: No regression on existing tests / build**

Re-run: `cd agenthub/frontend && npx vitest run 2>&1 | tail -10 && npm run check 2>&1 | tail -10`
Expected: 0 failures, 0 type errors.

- [ ] **Step 6: Final commit (only if any verification-time fix-ups were made)**

If Steps 1-5 needed no fixes, skip this commit. Otherwise:

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" add -A
git -C "D:/AAComputerCourse/AACode/muiltAgent" commit -m "chore(frontend): integration verification fixes"
```

- [ ] **Step 7: Tag this milestone**

```bash
git -C "D:/AAComputerCourse/AACode/muiltAgent" tag -a phase-2-form-complete -m "Phase 2: form refinement + landing entrance animation complete"
```

---

## Self-Review (post-write)

**1. Spec coverage:**

| Spec § | Requirement | Task |
|--------|-------------|------|
| §0 | Route map updated (TTS moved to phase 5+ candidate) | spec-only (already done) |
| §2 | File structure map | Tasks 1-11 (all files covered) |
| §3.1 | `--type-*` token definitions | Task 3 |
| §3.2 | Typography precision in components | Task 11 (HeroSection) — also covered by Task 7 (BeastRoster) and Task 8 (WuxingFlow tooltip) |
| §4.2 | `.prose-ink` definition | Task 4 |
| §4.3 | Apply to WuxingFlow / BeastRoster | Tasks 7, 8 |
| §5.1 | `.lift-ink`/`.focus-ink`/`.press-ink` definitions | Task 5 |
| §5.2 | Apply to BeastRoster / ForumEntry / MessageInput | Tasks 7, 9, 10 |
| §6.1 | `inkReveal` keyframe + `.reveal-beast` | Task 6 |
| §6.2 | `WUXING_FLOW_INDEX` helper | Task 1 |
| §6.3 | Apply stagger to WuxingFlow / BeastRoster | Tasks 7, 8 |
| §7.1 | `prefers-reduced-motion` media query | Task 6 |
| §7.3 | `useReducedMotion` hook (created, not consumed) | Task 2 |
| §8 | Acceptance criteria (typography/prose/micro/animation/a11y/quality) | Task 12 |

All spec items covered. No gaps.

**2. Placeholder scan:**

No "TBD", "TODO", "implement later", "add appropriate error handling" found. Each step contains concrete code or a concrete verification command.

**3. Type consistency:**

- `WUXING_FLOW_INDEX` typed as `Readonly<Record<BeastId, number>>` in Task 1.
- All imports use consistent paths (`@/lib/wuxing`, `@/components/landing/WuxingFlow`).
- `data-testid="beast-card"` is a new attribute (no collision).

No type drift detected.
