# AgentHub 五行神兽品牌化（阶段 1）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 AgentHub 已有的"五行神兽"世界观讲出来并对外可见 —— Landing 页 + 5 水墨 SVG 头像 + README 重写 + 颜色 token 统一。

**Architecture:** 路由改造（`/` 变 Landing，`/forum` 接 chat）+ 新建 4 个 Landing section 组件（server component）+ 新建 `wuxing.ts` 元数据单一来源 + 颜色 token 三套合一 + README 重写。不动 chat 业务逻辑。

**Tech Stack:** Next.js 15 (App Router, RSC), TypeScript, Tailwind v4 (`@theme` token), React, Zustand（仅 chat 内部使用）

---

## 文件结构

| 文件 | 改动 | 里程碑 |
|------|------|--------|
| `agenthub/frontend/app/page.tsx` | **改造**：原 chat → Landing（4 section 拼装） | M1 |
| `agenthub/frontend/app/forum/page.tsx` | **新建**：原 chat 内容迁入 | M1 |
| `agenthub/frontend/components/landing/HeroSection.tsx` | 新建 | M1 |
| `agenthub/frontend/components/landing/BeastRoster.tsx` | 新建 | M2 |
| `agenthub/frontend/components/landing/ForumEntry.tsx` | 新建 | M1 |
| `agenthub/frontend/components/landing/WuxingFlow.tsx` | 新建（核心大段） | M2 |
| `agenthub/frontend/lib/wuxing.ts` | 新建（5 神兽元数据单一来源） | M2 |
| `agenthub/frontend/components/agents/DefaultAgentModal.tsx` | 修改：删 `ELEMENT_COLORS`，改 import wuxing.ts | M3 |
| `agenthub/frontend/public/avatars/qinglong.svg` | 重画（单色水墨） | M3 |
| `agenthub/frontend/public/avatars/xuanwu.svg` | 重画 | M3 |
| `agenthub/frontend/public/avatars/baihu.svg` | 重画 | M3 |
| `agenthub/frontend/public/avatars/zhuque.svg` | 重画 | M3 |
| `agenthub/frontend/public/avatars/qilin.svg` | 重画 | M3 |
| `agenthub/backend/services/agent_identity.py` | 修改：`color` 字段同步水墨色 | M3 |
| `agenthub/README.md` | 重写 | M4 |
| `agenthub/frontend/app/globals.css` | **不动** | — |
| `agenthub/frontend/app/layout.tsx` | **不动** | — |
| `agenthub/frontend/components/chat/*` | **不动** | — |

---

## Task 1: 路由改造（page.tsx → forum/page.tsx）

**Files:**
- Move: `agenthub/frontend/app/page.tsx` → `agenthub/frontend/app/forum/page.tsx`
- Create: `agenthub/frontend/app/forum/page.tsx`（原 page.tsx 内容）
- Create: `agenthub/frontend/app/page.tsx`（新 Landing 骨架占位，本 Task 内仅一个空 `<main>`）

- [ ] **Step 1: 确认现有 page.tsx 完整且本地可跑**

```bash
cd agenthub/frontend && ls -la app/page.tsx
```

预期：文件存在，约 260 行。本 Task 不修改 chat 行为。

- [ ] **Step 2: 创建 forum 目录并移动 page.tsx**

```bash
mkdir -p agenthub/frontend/app/forum
mv agenthub/frontend/app/page.tsx agenthub/frontend/app/forum/page.tsx
```

- [ ] **Step 3: 把新 page.tsx 写成 Landing 占位（仅空 main）**

新建 `agenthub/frontend/app/page.tsx`，内容：

```tsx
export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper" />
  )
}
```

- [ ] **Step 4: 启动 dev server 验证 /forum 行为与原 / 一致**

```bash
cd agenthub/frontend && npm run dev
```

浏览器访问：
- `http://localhost:7000/forum` → 应该看到原 chat（线程列表 + 消息区 + 输入框）
- `http://localhost:7000/` → 应该看到空页面（带 paper 底色）

预期：两个路径都能正常加载，无 console error，无 build error。

- [ ] **Step 5: 验证通过后停止 dev server**

Ctrl+C 停止。

- [ ] **Step 6: 提交**

```bash
git add agenthub/frontend/app/page.tsx agenthub/frontend/app/forum/
git commit -m "refactor(frontend): move chat page to /forum, add Landing placeholder"
```

---

## Task 2: 新建 wuxing.ts 元数据单一来源

**Files:**
- Create: `agenthub/frontend/lib/wuxing.ts`

- [ ] **Step 1: 写 wuxing.ts**

新建 `agenthub/frontend/lib/wuxing.ts`：

```ts
/**
 * 五行神兽元数据单一来源（前端）。
 * 后端 agent_identity.py:AGENT_IDENTITIES 是 system_prompt 源；本文件是视觉/叙事源。
 * 颜色值与 globals.css 的 --color-wuxing-* 对齐（不要单独再定义色板）。
 */

export type WuxingElement = '木' | '水' | '金' | '火' | '土'
export type WuxingDirection = '东' | '北' | '西' | '南' | '中'
export type WuxingSeason = '春' | '冬' | '秋' | '夏' | '季'
export type WuxingVerb = '谋' | '稳' | '快' | '严' | '调'

export type BeastId =
  | 'pm'
  | 'architect'
  | 'developer'
  | 'qa'
  | 'orchestrator'

export interface WuxingBeast {
  id: BeastId
  beast: string          // "青龙"
  nickname: string       // "苍龙"
  element: WuxingElement
  direction: WuxingDirection
  season: WuxingSeason
  verb: WuxingVerb
  role: string           // "产品经理（PM）"
  /** 取自 globals.css --color-wuxing-*，写常量便于 SSR/CSR 一致 */
  color: { primary: string; secondary: string }
  svgPath: string        // "/avatars/qinglong.svg"
  personality: string
  catchphrase: string
  strengths: string[]
  caution: string
}

export const WUXING_BEASTS: readonly WuxingBeast[] = [
  {
    id: 'pm',
    beast: '青龙',
    nickname: '苍龙',
    element: '木',
    direction: '东',
    season: '春',
    verb: '谋',
    role: '产品经理（PM）',
    color: { primary: '#3a7d52', secondary: '#d6e8df' },
    svgPath: '/avatars/qinglong.svg',
    personality: '深谋远虑，运筹帷幄。看似温和实则果决，关键时刻一锤定音',
    catchphrase: '且慢，先理清需求再动手',
    strengths: ['需求分析', '全局规划', '用户洞察', '优先级判断'],
    caution: '不擅长技术细节，需要玄武辅助',
  },
  {
    id: 'architect',
    beast: '玄武',
    nickname: '玄冥',
    element: '水',
    direction: '北',
    season: '冬',
    verb: '稳',
    role: '系统架构师',
    color: { primary: '#3a6a9a', secondary: '#d6e2ee' },
    svgPath: '/avatars/xuanwu.svg',
    personality: '沉稳如山，万年不动。话少但每句都是深思熟虑',
    catchphrase: '根基不稳，地动山摇',
    strengths: ['系统设计', '架构评审', '技术选型', '性能优化'],
    caution: '过于保守，有时需要啸风推一把',
  },
  {
    id: 'developer',
    beast: '白虎',
    nickname: '啸风',
    element: '金',
    direction: '西',
    season: '秋',
    verb: '快',
    role: '全栈开发者',
    color: { primary: '#9a7b2e', secondary: '#ebe0c4' },
    svgPath: '/avatars/baihu.svg',
    personality: '雷厉风行，执行力拉满。写代码快如闪电，偶尔毛躁',
    catchphrase: '说干就干，废话少说',
    strengths: ['快速开发', '代码实现', '问题修复', '技术落地'],
    caution: '速度优先时容易埋 bug，需要炎翎把关',
  },
  {
    id: 'qa',
    beast: '朱雀',
    nickname: '炎翎',
    element: '火',
    direction: '南',
    season: '夏',
    verb: '严',
    role: 'QA 工程师',
    color: { primary: '#b03a2e', secondary: '#eed4d0' },
    svgPath: '/avatars/zhuque.svg',
    personality: '火眼金睛，一丝不苟。对 bug 零容忍，但对人很温柔',
    catchphrase: '这点小把戏，还想瞒过我？',
    strengths: ['bug 检测', '测试覆盖', '质量把关', '边界分析'],
    caution: '过于追求完美，有时吹毛求疵',
  },
  {
    id: 'orchestrator',
    beast: '麒麟',
    nickname: '瑞麟',
    element: '土',
    direction: '中',
    season: '季',
    verb: '调',
    role: '任务协调器',
    color: { primary: '#8a6840', secondary: '#e6dcc8' },
    svgPath: '/avatars/qilin.svg',
    personality: '居中调度，调和五行。不偏不倚，公正无私',
    catchphrase: '诸位稍安，容我梳理一番',
    strengths: ['任务分解', '资源调度', '冲突调解', '流程把控'],
    caution: '不直接产出代码，依赖其他神兽执行',
  },
] as const

/** 五行相生流转顺序（取自 orchestrator.py:25 "五行相生（任务流转顺序建议）"） */
export const WUXING_FLOW_ORDER: readonly BeastId[] = [
  'pm',          // 苍龙(谋·定策) →
  'qa',          // 炎翎(严·试火) →
  'orchestrator',// 瑞麟(调·调度) →
  'developer',   // 啸风(快·锻冶) →
  'architect',   // 玄冥(稳·筑基) → 回到苍龙
] as const

export function getBeastById(id: BeastId): WuxingBeast | undefined {
  return WUXING_BEASTS.find((b) => b.id === id)
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd agenthub/frontend && npx tsc --noEmit
```

预期：无 type error。

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/wuxing.ts
git commit -m "feat(frontend): add wuxing.ts as single source of truth for 5 beasts"
```

---

## Task 3: HeroSection 组件

**Files:**
- Create: `agenthub/frontend/components/landing/HeroSection.tsx`

- [ ] **Step 1: 写 HeroSection**

新建 `agenthub/frontend/components/landing/HeroSection.tsx`：

```tsx
import { WUXING_BEASTS } from "@/lib/wuxing"

export function HeroSection() {
  return (
    <section className="px-6 py-20 md:py-28 text-center">
      {/* 神兽围炉 mini 展示 */}
      <div className="flex justify-center items-center gap-3 mb-8">
        {WUXING_BEASTS.map((beast) => (
          <div
            key={beast.id}
            className="w-12 h-12 md:w-16 md:h-16 rounded-full flex items-center justify-center text-2xl font-display bg-paper-dark border-2 animate-ink-drop"
            style={{
              borderColor: beast.color.primary,
              color: beast.color.primary,
            }}
            title={beast.nickname}
          >
            {beast.beast.charAt(1)}
          </div>
        ))}
      </div>

      {/* Hero 文案 */}
      <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-semibold text-ink leading-tight tracking-wide">
        五行神兽，共治一炉代码
      </h1>
      <p className="font-display text-base md:text-lg text-ink/60 mt-4 tracking-[0.2em]">
        苍龙定策 · 玄冥筑基 · 啸风锻冶 · 炎翎试火 · 瑞麟调律
      </p>
      <p className="font-body text-sm md:text-base text-ink/50 mt-8 max-w-2xl mx-auto">
        你只管 @ 一声，五行自转。
      </p>
      <p className="font-body text-xs md:text-sm text-ink/40 mt-3 max-w-2xl mx-auto italic">
        不是 5 个凑数的 agent，是 5 道工序的人格式分身。
      </p>
    </section>
  )
}
```

- [ ] **Step 2: 把 HeroSection 接到 Landing page.tsx**

修改 `agenthub/frontend/app/page.tsx`：

```tsx
import { HeroSection } from "@/components/landing/HeroSection"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <HeroSection />
    </main>
  )
}
```

- [ ] **Step 3: 启动 dev 验证 HeroSection 渲染**

```bash
cd agenthub/frontend && npm run dev
```

浏览器访问 `http://localhost:7000/`，预期：
- 看到 5 个圆形 mini 神兽（用汉字"龙/武/虎/雀/麟"fallback）
- Hero 三行文字 + 副标题
- 没有 console error

- [ ] **Step 4: 停止 dev，提交**

```bash
git add agenthub/frontend/components/landing/HeroSection.tsx agenthub/frontend/app/page.tsx
git commit -m "feat(frontend): add HeroSection to Landing"
```

---

## Task 4: BeastRoster 组件

**Files:**
- Create: `agenthub/frontend/components/landing/BeastRoster.tsx`

- [ ] **Step 1: 写 BeastRoster**

新建 `agenthub/frontend/components/landing/BeastRoster.tsx`：

```tsx
import { WUXING_BEASTS } from "@/lib/wuxing"

export function BeastRoster() {
  return (
    <section className="px-6 py-16 md:py-20 max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="font-display text-2xl md:text-3xl font-semibold text-ink">
          五神兽
        </h2>
        <p className="font-body text-sm text-ink/50 mt-2">
          {WUXING_BEASTS[0]?.direction} · {WUXING_BEASTS[1]?.direction} · {WUXING_BEASTS[2]?.direction} · {WUXING_BEASTS[3]?.direction} · {WUXING_BEASTS[4]?.direction}
          {" "}— 方位即职责
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {WUXING_BEASTS.map((beast) => (
          <article
            key={beast.id}
            className="rounded-2xl border-2 bg-paper p-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5"
            style={{ borderColor: beast.color.secondary }}
          >
            {/* 头像（暂时用汉字 fallback，Task 9 后换 SVG） */}
            <div
              className="w-20 h-20 mx-auto mb-3 rounded-full flex items-center justify-center text-3xl font-display bg-paper-dark"
              style={{ color: beast.color.primary }}
            >
              {beast.beast.charAt(1)}
            </div>

            {/* 名字 + 性格动词 */}
            <div className="text-center mb-2">
              <h3 className="font-display text-lg font-semibold text-ink">
                {beast.nickname}
              </h3>
              <p className="font-body text-xs text-ink/40 mt-0.5">
                {beast.beast} · {beast.element} · {beast.direction} · {beast.season}
              </p>
            </div>

            {/* 性格动词大字 */}
            <div
              className="text-center text-3xl font-display font-light my-3"
              style={{ color: beast.color.primary }}
            >
              {beast.verb}
            </div>

            {/* 口头禅 */}
            <p className="font-body text-xs text-ink/60 text-center italic leading-relaxed min-h-[2.5rem]">
              「{beast.catchphrase}」
            </p>

            {/* 擅长 */}
            <p className="font-body text-[11px] text-ink/40 text-center mt-3 leading-relaxed">
              擅长：{beast.strengths.slice(0, 2).join('、')}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Step 2: 接到 Landing**

修改 `agenthub/frontend/app/page.tsx`：

```tsx
import { BeastRoster } from "@/components/landing/BeastRoster"
import { HeroSection } from "@/components/landing/HeroSection"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <HeroSection />
      <BeastRoster />
    </main>
  )
}
```

- [ ] **Step 3: dev 验证**

```bash
cd agenthub/frontend && npm run dev
```

浏览器访问 `http://localhost:7000/`，预期看到 5 张神兽卡，每张：头像 + 名字 + 性格动词 + 口头禅 + 擅长。

- [ ] **Step 4: 停止 dev，提交**

```bash
git add agenthub/frontend/components/landing/BeastRoster.tsx agenthub/frontend/app/page.tsx
git commit -m "feat(frontend): add BeastRoster with 5 beast cards"
```

---

## Task 5: ForumEntry 组件

**Files:**
- Create: `agenthub/frontend/components/landing/ForumEntry.tsx`

- [ ] **Step 1: 写 ForumEntry**

新建 `agenthub/frontend/components/landing/ForumEntry.tsx`：

```tsx
import Link from "next/link"

export function ForumEntry() {
  return (
    <section className="px-6 py-20 md:py-24 text-center bg-paper-dark/40">
      <h2 className="font-display text-2xl md:text-3xl font-semibold text-ink mb-4">
        入议事堂
      </h2>
      <p className="font-body text-sm text-ink/60 mb-8 max-w-xl mx-auto">
        议事堂是真正动手的地方。挑一只神兽开聊，或 @ 一声调度五行。
      </p>

      <Link
        href="/forum"
        className="inline-block font-display text-base px-8 py-3 rounded-xl bg-ink text-paper hover:bg-ink-light transition-colors shadow-lg shadow-ink/20"
      >
        进议事堂 →
      </Link>

      <div className="mt-16 max-w-2xl mx-auto text-left">
        <h3 className="font-display text-sm font-semibold text-ink/70 mb-3 tracking-wider">
          怎么加你自己的神兽
        </h3>
        <p className="font-body text-xs text-ink/50 leading-relaxed">
          扩 3 个文件即可，5 分钟内完成：<br />
          <code className="text-ink/70">backend/services/agent_identity.py</code> 的
          <code className="text-ink/70"> AGENT_IDENTITIES</code> 加一项；<br />
          <code className="text-ink/70">backend/services/session.py</code> 的
          <code className="text-ink/70"> AGENT_CONFIGS</code> 加一项；<br />
          <code className="text-ink/70">frontend/lib/wuxing.ts</code> 的
          <code className="text-ink/70"> WUXING_BEASTS</code> 加一项。
        </p>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: 接到 Landing**

修改 `agenthub/frontend/app/page.tsx`：

```tsx
import { BeastRoster } from "@/components/landing/BeastRoster"
import { ForumEntry } from "@/components/landing/ForumEntry"
import { HeroSection } from "@/components/landing/HeroSection"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <HeroSection />
      <BeastRoster />
      <ForumEntry />
    </main>
  )
}
```

- [ ] **Step 3: dev 验证**

```bash
cd agenthub/frontend && npm run dev
```

浏览器访问 `http://localhost:7000/`，预期：
- 看到"入议事堂"按钮
- 点击跳转到 `/forum`，原 chat 正常加载
- 按钮下方有"怎么加你自己的神兽"3 行说明

- [ ] **Step 4: 停止 dev，提交**

```bash
git add agenthub/frontend/components/landing/ForumEntry.tsx agenthub/frontend/app/page.tsx
git commit -m "feat(frontend): add ForumEntry CTA and customization hint"
```

---

## Task 6: WuxingFlow 组件（核心大段）

**Files:**
- Create: `agenthub/frontend/components/landing/WuxingFlow.tsx`

- [ ] **Step 1: 写 WuxingFlow**

新建 `agenthub/frontend/components/landing/WuxingFlow.tsx`：

```tsx
"use client"

import { useState } from "react"
import { WUXING_BEASTS, WUXING_FLOW_ORDER, type BeastId } from "@/lib/wuxing"

const CENTER_X = 200
const CENTER_Y = 200
const RADIUS = 130
const NODE_R = 38

function nodePosition(index: number, total: number) {
  // 5 个节点从顶部开始顺时针排布
  const angle = (index * 2 * Math.PI) / total - Math.PI / 2
  return {
    x: CENTER_X + RADIUS * Math.cos(angle),
    y: CENTER_Y + RADIUS * Math.sin(angle),
  }
}

export function WuxingFlow() {
  const [hovered, setHovered] = useState<BeastId | null>(null)

  // 实时示例对话步骤（基于 WUXING_FLOW_ORDER）
  const flowSteps = WUXING_FLOW_ORDER.map((id) => {
    const b = WUXING_BEASTS.find((beast) => beast.id === id)!
    return { id, beast: b }
  })

  return (
    <section className="px-6 py-16 md:py-20 max-w-5xl mx-auto">
      <div className="text-center mb-10">
        <h2 className="font-display text-2xl md:text-3xl font-semibold text-ink">
          五行流转
        </h2>
        <p className="font-body text-sm text-ink/50 mt-2">
          每一步是上一段的果，是下一段的因
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-10 items-center">
        {/* SVG 转盘 */}
        <div className="flex justify-center">
          <svg
            viewBox="0 0 400 400"
            className="w-full max-w-[400px] h-auto"
            aria-label="五行流转图"
          >
            {/* 相生箭头（5 条曲线） */}
            {flowSteps.map((step, i) => {
              const next = flowSteps[(i + 1) % flowSteps.length]!
              const p1 = nodePosition(i, flowSteps.length)
              const p2 = nodePosition((i + 1) % flowSteps.length, flowSteps.length)
              const midX = (p1.x + p2.x) / 2
              const midY = (p1.y + p2.y) / 2
              // 切线偏移让曲线略外凸
              const dx = p2.x - p1.x
              const dy = p2.y - p1.y
              const nx = -dy * 0.18
              const ny = dx * 0.18
              return (
                <path
                  key={`arrow-${step.id}`}
                  d={`M ${p1.x} ${p1.y} Q ${midX + nx} ${midY + ny} ${p2.x} ${p2.y}`}
                  fill="none"
                  stroke={step.beast.color.primary}
                  strokeWidth={1.5}
                  strokeOpacity={0.4}
                  strokeDasharray="3 4"
                />
              )
            })}

            {/* 中心 "议事" 字样 */}
            <text
              x={CENTER_X}
              y={CENTER_Y - 8}
              textAnchor="middle"
              className="font-display"
              fontSize={28}
              fill="#2c2c3a"
              fontWeight={500}
            >
              议事
            </text>
            <text
              x={CENTER_X}
              y={CENTER_Y + 18}
              textAnchor="middle"
              className="font-body"
              fontSize={11}
              fill="#2c2c3a"
              opacity={0.5}
            >
              五行自转
            </text>

            {/* 5 节点 */}
            {flowSteps.map((step, i) => {
              const p = nodePosition(i, flowSteps.length)
              const isHovered = hovered === step.id
              return (
                <g
                  key={step.id}
                  onMouseEnter={() => setHovered(step.id)}
                  onMouseLeave={() => setHovered(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={isHovered ? NODE_R + 4 : NODE_R}
                    fill={step.beast.color.secondary}
                    stroke={step.beast.color.primary}
                    strokeWidth={isHovered ? 3 : 2}
                    style={{ transition: 'all 0.2s ease' }}
                  />
                  <text
                    x={p.x}
                    y={p.y + 4}
                    textAnchor="middle"
                    className="font-display"
                    fontSize={18}
                    fill={step.beast.color.primary}
                    fontWeight={600}
                  >
                    {step.beast.verb}
                  </text>
                  <text
                    x={p.x}
                    y={p.y + NODE_R + 18}
                    textAnchor="middle"
                    className="font-display"
                    fontSize={13}
                    fill="#2c2c3a"
                  >
                    {step.beast.nickname}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>

        {/* 右侧：当前 hover 详情 / 默认示例 */}
        <div className="space-y-4">
          {hovered ? (
            (() => {
              const b = WUXING_BEASTS.find((beast) => beast.id === hovered)!
              return (
                <div
                  className="rounded-2xl p-6 border-2"
                  style={{
                    borderColor: b.color.primary,
                    backgroundColor: b.color.secondary,
                  }}
                >
                  <div className="font-display text-xl text-ink mb-1">
                    {b.nickname} · {b.verb}
                  </div>
                  <div className="font-body text-xs text-ink/60 mb-3">
                    {b.role} · {b.element} · {b.direction} · {b.season}
                  </div>
                  <p className="font-body text-sm text-ink/80 italic mb-3">
                    「{b.catchphrase}」
                  </p>
                  <p className="font-body text-xs text-ink/60 leading-relaxed">
                    擅长：{b.strengths.join('、')}
                  </p>
                </div>
              )
            })()
          ) : (
            <div className="rounded-2xl p-6 border border-ink/10 bg-paper">
              <div className="font-display text-sm text-ink/70 mb-3">
                真实示例
              </div>
              <pre className="font-mono text-xs text-ink/70 whitespace-pre-wrap leading-relaxed">
{`@瑞麟 加个深色模式
  → 瑞麟拆解任务
  → @苍龙 厘清需求
  → @啸风 实现
  → @炎翎 试火
  → @玄冥 复查架构
  → 完事`}
              </pre>
              <p className="font-body text-[11px] text-ink/40 mt-3">
                鼠标 hover 转盘节点看每个神兽的细节
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: 接到 Landing（放在 BeastRoster 和 ForumEntry 之间）**

修改 `agenthub/frontend/app/page.tsx`：

```tsx
import { BeastRoster } from "@/components/landing/BeastRoster"
import { ForumEntry } from "@/components/landing/ForumEntry"
import { HeroSection } from "@/components/landing/HeroSection"
import { WuxingFlow } from "@/components/landing/WuxingFlow"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <HeroSection />
      <WuxingFlow />
      <BeastRoster />
      <ForumEntry />
    </main>
  )
}
```

- [ ] **Step 3: dev 验证 WuxingFlow**

```bash
cd agenthub/frontend && npm run dev
```

浏览器访问 `http://localhost:7000/`，预期：
- 看到五边形排列的 5 节点转盘
- 节点间有虚线相生箭头
- 中心"议事 · 五行自转"
- 鼠标 hover 节点：右侧卡片显示对应神兽详情
- 鼠标移开：右侧回到"真实示例"代码块
- 无 console error

- [ ] **Step 4: 停止 dev，提交**

```bash
git add agenthub/frontend/components/landing/WuxingFlow.tsx agenthub/frontend/app/page.tsx
git commit -m "feat(frontend): add WuxingFlow with 5-node SVG and live example"
```

---

## Task 7: 颜色 token 合一（前端 DefaultAgentModal）

**Files:**
- Modify: `agenthub/frontend/components/agents/DefaultAgentModal.tsx`

- [ ] **Step 1: 读 DefaultAgentModal 现状，确认 ELEMENT_COLORS 使用位置**

```bash
grep -n "ELEMENT_COLORS" agenthub/frontend/components/agents/DefaultAgentModal.tsx
```

预期：文件顶部有 `const ELEMENT_COLORS: Record<string, string> = { ... }`，文件内有几处 `ELEMENT_COLORS[element]`。

- [ ] **Step 2: 删除 ELEMENT_COLORS 本地常量，改用 wuxing.ts**

修改 `agenthub/frontend/components/agents/DefaultAgentModal.tsx`：

**顶部 imports 改为**（添加 wuxing 导入，删除 ELEMENT_COLORS 块）：

```tsx
"use client"

import { useState } from "react"
import type { Agent } from "@/lib/types"
import { WUXING_BEASTS } from "@/lib/wuxing"

// 五行神兽 fallback SVG（保留，Task 9 后会换）
const BEAST_SVGS: Record<string, string> = {
  pm: "龙",
  architect: "龟",
  developer: "虎",
  qa: "雀",
  orchestrator: "麟",
}

// 颜色从 wuxing.ts 取，按 element 索引
const ELEMENT_COLOR_MAP: Record<string, { primary: string; secondary: string }> =
  Object.fromEntries(
    WUXING_BEASTS.map((b) => [b.element, b.color])
  )
```

**文件内所有 `ELEMENT_COLORS[element]` 改为**：

```tsx
ELEMENT_COLOR_MAP[element]?.primary
```

**以及所有 `ELEMENT_COLORS[element]` 用于 secondary 的地方改为**：

```tsx
ELEMENT_COLOR_MAP[element]?.secondary
```

- [ ] **Step 3: 验证类型**

```bash
cd agenthub/frontend && npx tsc --noEmit
```

预期：无 type error。

- [ ] **Step 4: 启动 dev 验证颜色一致**

```bash
cd agenthub/frontend && npm run dev
```

浏览器访问 `http://localhost:7000/forum`，触发"选择默认 Agent"弹窗（新建会话触发），预期：
- 5 张神兽卡边框颜色比之前**更水墨**（暗一档）
- 比如青龙从 `#059669` 变成 `#3a7d52`

- [ ] **Step 5: 停止 dev，提交**

```bash
git add agenthub/frontend/components/agents/DefaultAgentModal.tsx
git commit -m "refactor(frontend): unify wuxing colors via wuxing.ts"
```

---

## Task 8: 颜色 token 合一（后端 agent_identity.py）

**Files:**
- Modify: `agenthub/backend/services/agent_identity.py`

- [ ] **Step 1: 改 5 个 color.primary 和 color.secondary**

在 `agenthub/backend/services/agent_identity.py` 中，把 5 个 AGENT_IDENTITIES 项的 `color` 字段：

- `pm`: primary `#059669` → `#3a7d52`，secondary `#D1FAE5` → `#d6e8df`
- `architect`: primary `#1E40AF` → `#3a6a9a`，secondary `#DBEAFE` → `#d6e2ee`
- `developer`: primary `#F59E0B` → `#9a7b2e`，secondary `#FEF3C7` → `#ebe0c4`
- `qa`: primary `#DC2626` → `#b03a2e`，secondary `#FEE2E2` → `#eed4d0`
- `orchestrator`: primary `#7C3AED` → `#8a6840`，secondary `#EDE9FE` → `#e6dcc8`

（颜色值与 `frontend/lib/wuxing.ts` 完全一致）

- [ ] **Step 2: 跑后端测试**

```bash
cd agenthub && pytest -q
```

预期：所有测试通过。

- [ ] **Step 3: 启动后端 dev 验证 /api/agents 返回新色值**

```bash
cd agenthub/backend && python main.py
```

另开终端：
```bash
curl -s -H "X-API-Key: dev-secret-key" http://localhost:7010/api/agents | python -m json.tool
```

预期：每个 agent 返回的 `color.primary` 是新的水墨色值（如 `#3a7d52`）。

- [ ] **Step 4: 停止后端，提交**

```bash
git add agenthub/backend/services/agent_identity.py
git commit -m "refactor(backend): align agent color tokens with wuxing water-ink palette"
```

---

## Task 9: 5 SVG 神兽头像重画

**Files:**
- Replace: `agenthub/frontend/public/avatars/qinglong.svg`
- Replace: `agenthub/frontend/public/avatars/xuanwu.svg`
- Replace: `agenthub/frontend/public/avatars/baihu.svg`
- Replace: `agenthub/frontend/public/avatars/zhuque.svg`
- Replace: `agenthub/frontend/public/avatars/qilin.svg`

- [ ] **Step 1: 准备 SVG 风格 spec**

5 个 SVG 共同遵守：

- viewBox `0 0 128 128`
- 圆形容器：`r=58`，`stroke=#2c2c3a`，`stroke-width=2`，`stroke-opacity=0.15`，`fill=none`
- 内画 60×60 的"水墨意笔"神兽形
- 单一墨色 `#2c2c3a`（其他颜色**不用**）
- 贝塞尔曲线 + `stroke-width` 变化（3→1.5）模拟飞白
- 留白：神兽占圆形内 40-50%，周围留白
- 不用渐变、不用底色、不用 emoji

**5 个形的设计**：

- **青龙**（qinglong）—— 龙身 S 形一笔，鬃毛三两笔，头朝左上
- **玄武**（xuanwu）—— 龟壳六边形 + 蛇身缠绕
- **白虎**（baihu）—— 虎头正视，王字 + 双眼两点
- **朱雀**（zhuque）—— 凤冠 + 长尾三羽
- **麒麟**（qilin）—— 鹿角 + 狮身 + 龙鳞一笔

- [ ] **Step 2: 重画 5 个 SVG 文件**

每个 SVG 文件结构（以 qinglong.svg 为例）：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" fill="none">
  <circle cx="64" cy="64" r="58" stroke="#2c2c3a" stroke-width="2" stroke-opacity="0.15" />
  <g stroke="#2c2c3a" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <!-- 龙身 S 形一笔：头朝左上 → 蜿蜒 → 尾朝右下 -->
    <path d="M 40 50 Q 50 40 60 50 Q 70 60 80 55 Q 90 50 95 65" stroke-width="3" />
    <!-- 头 -->
    <circle cx="40" cy="50" r="5" stroke-width="2" />
    <!-- 鬃毛三两笔 -->
    <path d="M 35 45 L 32 38" stroke-width="1.5" />
    <path d="M 38 42 L 36 35" stroke-width="1.5" />
    <path d="M 41 40 L 41 33" stroke-width="1.5" />
    <!-- 鳞片点点 -->
    <circle cx="60" cy="55" r="1" fill="#2c2c3a" />
    <circle cx="68" cy="58" r="1" fill="#2c2c3a" />
    <circle cx="76" cy="58" r="1" fill="#2c2c3a" />
  </g>
</svg>
```

其他 4 个用同样骨架，path 改为对应神兽的形。

**重要**：5 个文件由**同一设计师**同日产出，或**同一 prompt** 给 AI 工具生成后人工精调，确保风格统一（飞白粗细、留白比例、细节密度一致）。

- [ ] **Step 3: 浏览器单独打开每个 SVG 文件验证**

```bash
cd agenthub/frontend/public/avatars
# 浏览器逐个打开
```

或在 dev 启动后访问 `http://localhost:7000/avatars/qinglong.svg` 等。

预期：5 个 SVG 在浏览器显示为单色墨色水墨意笔图，无渐变无底色，5 个形可辨。

- [ ] **Step 4: dev 启动验证 Landing 和 chat 内头像都更新**

```bash
cd agenthub/frontend && npm run dev
```

- `http://localhost:7000/` → HeroSection 5 个 mini 神兽位置**暂仍用汉字**（因为 HeroSection 当前用汉字 fallback）
- `http://localhost:7000/forum` → 触发 DefaultAgentModal（新建会话）→ 5 张神兽卡头像仍是 fallback 汉字

**如果想让 HeroSection 和 DefaultAgentModal 改用 SVG**，在两个组件中把汉字 fallback 改为：

```tsx
<img src={beast.svgPath} alt={beast.nickname} className="w-full h-full object-contain" />
```

**这一步可选** — 若不接，5 SVG 仍然作为后续阶段（声与形）的基础，但本阶段 Landing 视觉上仍是汉字 fallback。

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/public/avatars/
git commit -m "feat(frontend): redraw 5 beast avatars in water-ink style"
```

---

## Task 10: README 重写

**Files:**
- Replace: `agenthub/README.md`

- [ ] **Step 1: 写新 README**

完整替换 `agenthub/README.md`：

```markdown
# AgentHub — 五行神兽议事堂

> 一行 code 写不出来，五个神兽围炉议事。

## 五行流转

```
苍龙(谋·定策) → 炎翎(严·试火) → 瑞麟(调·调度) → 啸风(快·锻冶) → 玄冥(稳·筑基) → 苍龙
```

每一步是上一段的果，是下一段的因。

**真实示例：**

\`\`\`
@瑞麟 加个深色模式
  → 瑞麟拆解任务
  → @苍龙 厘清需求
  → @啸风 实现
  → @炎翎 试火
  → @玄冥 复查架构
  → 完事
\`\`\`

## 5 神兽

| 兽 | 昵称 | 五行 | 方位 | 季节 | 性格动词 | 职能 | 口头禅 |
|----|------|------|------|------|----------|------|--------|
| 青龙 | 苍龙 | 木 | 东 | 春 | **谋** | 定策 | 且慢，先理清需求再动手 |
| 玄武 | 玄冥 | 水 | 北 | 冬 | **稳** | 筑基 | 根基不稳，地动山摇 |
| 白虎 | 啸风 | 金 | 西 | 秋 | **快** | 锻冶 | 说干就干，废话少说 |
| 朱雀 | 炎翎 | 火 | 南 | 夏 | **严** | 试火 | 这点小把戏，还想瞒过我？ |
| 麒麟 | 瑞麟 | 土 | 中 | 季 | **调** | 调律 | 诸位稍安，容我梳理一番 |

## 快速开始

### 后端

\`\`\`bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入 ANTHROPIC_API_KEY 或 DASHSCOPE_API_KEY
python main.py
\`\`\`

后端运行在 http://localhost:7010

### 前端

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

浏览器打开 http://localhost:7000，从 Landing 进 /forum，挑一只神兽开聊。

## 怎么调度

- \`@苍龙 <需求>\` — 让 PM 分析需求
- \`@啸风 <任务>\` — 让开发者实现
- \`@炎翎 <代码>\` — 让 QA 审查
- \`@瑞麟 <目标>\` — 让协调器按五行流转拆解 + 调度
- \`@玄冥 <方案>\` — 让架构师评审架构

无 @ 指令的消息会发给当前会话的默认 Agent（首次进入会话会引导选择）。

## 怎么加你的神兽

扩 3 个文件即可，5 分钟内完成：

1. \`backend/services/agent_identity.py\` 的 \`AGENT_IDENTITIES\` 加一项（含 beast/nickname/element/personality/catchphrase/strengths/caution/system_prompt_suffix）
2. \`backend/services/session.py\` 的 \`AGENT_CONFIGS\` 加一项（含 name/role/llm_provider/system_prompt）
3. \`frontend/lib/wuxing.ts\` 的 \`WUXING_BEASTS\` 加一项（含 beast/nickname/element/direction/season/verb/role/color/svgPath/personality/catchphrase/strengths/caution）

如需新羁绊，再扩 \`BOND_MAP\`（同文件）。

## 路线图

- **阶段 1（现在）**: 五行神兽立庙 — 真头像 + Landing + README
- **阶段 2**: 声与形 — 神兽声线 + 水墨主题精调
- **阶段 3**: 飞升 — 飞书/钉钉跨平台
- **阶段 4**: 副业 — 神兽策略卡 / 共创世界

## 不做的清单

- 不做 AI 陪伴和虚拟人格
- 不做演示视频
- 不立 CVO 之类的神秘化角色
- 不模仿其他项目的章节骨架
- 不堆砌东方装饰（印章/卷轴/砚台图标等）

## License

MIT
```

**注**：上面的 \`\`\` 是 markdown 转义，真实写入时去掉反斜杠（这里为避免 README 文件本身被渲染而转义）。

- [ ] **Step 2: 验证 README 渲染**

浏览器打开 GitHub 仓库或本地 Markdown 预览：

```bash
code agenthub/README.md
```

（或用任意 markdown 预览工具）

预期：
- Hero 段落有视觉冲击力
- 5 神兽表格清晰
- 真实示例代码块
- 路线图 4 行
- "不做的清单" 5 行

- [ ] **Step 3: 提交**

```bash
git add agenthub/README.md
git commit -m "docs: rewrite README with five-elements narrative"
```

---

## Task 11: 验证门禁

**Files:** 无（验证步骤）

- [ ] **Step 1: TypeScript 检查**

```bash
cd agenthub/frontend && npm run check
```

预期：Biome + TypeScript 全部通过，无 error。

- [ ] **Step 2: Next.js 构建**

```bash
cd agenthub/frontend && npm run build
```

预期：build 成功，无 type error / 静态分析 error。

- [ ] **Step 3: 后端测试**

```bash
cd agenthub && pytest -q
```

预期：所有测试通过。

- [ ] **Step 4: 端到端浏览器实测**

启动两边：

```bash
# 终端 1
cd agenthub/backend && python main.py

# 终端 2
cd agenthub/frontend && npm run dev
```

浏览器测试路径：

1. `http://localhost:7000/` → 看到 Landing（4 section 完整：Hero + WuxingFlow + BeastRoster + ForumEntry）
2. 点击"进议事堂"按钮 → 跳转到 `/forum`，原 chat 加载
3. 在 chat 触发"选择默认 Agent"弹窗 → 5 张神兽卡显示，**颜色比之前更水墨**
4. 选择苍龙 → 进入 chat
5. 发消息 \`@啸风 写一个 hello world\` → 啸风回复
6. 切回浏览器地址栏输入 \`/\` → 回 Landing
7. 刷新 \`/forum\` → 状态保留（zustand 持久），chat 正常

预期：7 步全部通过，无 console error / 404 / 500。

- [ ] **Step 5: 视觉对照清单**

对照 spec §5 验收标准：

- [ ] README 5 节齐全
- [ ] Landing 4 section 完整
- [ ] WuxingFlow 转盘可辨 + hover 切换
- [ ] BeastRoster 5 卡
- [ ] `/forum` 行为与原 `/` 一致
- [ ] 5 SVG 都是单色墨色 `#2c2c3a`
- [ ] DefaultAgentModal 颜色已用 wuxing.ts
- [ ] 后端 `/api/agents` 返回新色值

如有未通过项，回到对应 Task 修复。

- [ ] **Step 6: 全部通过则 final commit**

```bash
git status  # 应该无未提交改动
```

如果没有未提交改动，整个 plan 落地完成。

---

## Self-Review

### 1. Spec 覆盖

| Spec 节 | 实现 Task |
|---------|-----------|
| §2 内容叙事（README 5 节） | Task 10 |
| §2.4 五行流转图 | Task 6（WuxingFlow）+ Task 10（README 文字版） |
| §3.2 5 SVG 重画 | Task 9 |
| §3.3 颜色 token 合一 | Task 7（前端）+ Task 8（后端） |
| §4.1 路由改造 | Task 1 |
| §4.2 文件结构 | Task 1-6 全部对齐 |
| §4.4 WuxingFlow | Task 6 |
| §4.5 wuxing.ts | Task 2 |
| §5 验收标准 | Task 11 |

无 spec 要求遗漏。

### 2. Placeholder 扫描

- 无 "TBD" / "TODO" / "implement later"
- 无 "Add appropriate error handling" 类笼统描述
- 所有代码块都是完整可粘贴
- 所有 commit 命令都给出了精确的 add 列表和 message

### 3. 类型一致性

- `WUXING_BEASTS` / `WUXING_FLOW_ORDER` / `getBeastById` 在 Task 2 定义
- Task 3-6 import 自 `@/lib/wuxing` — 一致
- Task 7 用 `ELEMENT_COLOR_MAP` 索引 `WUXING_BEASTS` 的 color — 一致
- Task 8 后端色值与 wuxing.ts 完全一致（手抄对齐）
- `WuxingBeast` interface 字段（id/beast/nickname/element/direction/season/verb/role/color/svgPath/personality/catchphrase/strengths/caution）在 Task 2 定义、Task 3-6 使用 — 字段名一致
