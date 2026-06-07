# AgentHub 品牌化阶段 2:形(主题精调 + 欢迎动画)设计

**日期**:2026-06-07
**状态**:设计完成,待用户 review
**阶段**:4 阶段路线图中的第 2 阶段(**形**)
**影响范围**:`agenthub/frontend/app/globals.css`、`agenthub/frontend/app/page.tsx`、`agenthub/frontend/components/landing/*`、新增 `agenthub/frontend/lib/hooks/useReducedMotion.ts`

---

## 0. 路线图调整(从阶段 1 的 4 阶段 → 当前 5 阶段)

阶段 1 设计文档(`2026-06-06-agenthub-five-elements-branding-design.md` §7)原定阶段 2 = "声与形"。本次设计前与用户共识:**TTS 声线脱离主线,本阶段不实现**。路线图调整为:

| 阶段 | 名称 | 范围 | 状态 |
|------|------|------|------|
| 1 | 立庙 | README + Landing + 路由搬迁 + 5 SVG + 颜色合一 | ✅ 已落地 |
| **2** | **形** | **水墨主题精调 + Landing 入场动画** | **本 spec** |
| 3 | 飞升 | 飞书 / 钉钉 / Telegram 跨平台网关 | 未开始 |
| 4 | 副业 | 神兽策略卡 / 共创世界 / 游戏化 | 未开始 |
| 5+ | 待定 | 神兽 TTS 声线(原阶段 2 拆出,待后续独立 spec) | 候选 |

阶段 5+ 标记为"候选",因为"声"何时做、用哪家云、能否离线,均需独立调研,**本 spec 不为它留 UI 占位**(避免半成品暗示)。

---

## 1. 背景与目标

### 1.1 问题

阶段 1 把 AgentHub 的"五行神兽"骨架立住了:5 个水墨 SVG 头像、统一颜色 token、Landing 4 section、README 重写。但**视觉上仍有未打磨的细节**:

- 标题 / 副标题 / catchphrase 缺乏显式 leading 与字距,长文(README 复刻、Agent 文本回复)读起来"散"
- `<code>` / `<pre>` / `<blockquote>` / `<table>` / `<ul>` / `<ol>` 是 Tailwind preflight 默认,没水墨调性,在水墨语境里"突然跳出来"
- 按钮、卡片、输入框缺统一的 hover / focus / active 反馈样式,各自散写
- Landing 4 section 当前是 **静态呈现**,用户首次进入没有"五行降临"的仪式感

### 1.2 目标

把"形"的颗粒度补到位:

1. 排版精度 — 标题 / 正文 / code 各自 leading 与字距,长文读起来"贴"
2. 代码与引用区样式 — `.prose-ink` 覆盖 Tailwind 默认,prose 类元素有水墨调性
3. 微交互统一 — hover / focus / active 的 lift / ring / press 反馈集中定义,组件不再散写
4. Landing 入场动画 — 5 神兽按相生顺序 stagger "墨染"出现,首次访问有"五行降临"仪式

### 1.3 非目标(Out of Scope)

明确不做:

- **TTS 神兽声线** — 移到阶段 5+ 候选,本 spec 不留 UI 占位
- **scroll-triggered 滚动入场** — 不引入 IntersectionObserver,克制
- **路径动画 / 笔画动画** — 技术债务大,克制
- **暗色模式** — 项目无此需求,token 全是 light
- **重画 5 SVG 头像** — 阶段 1 已定型
- **后端任何改动** — 本阶段纯前端
- **路由 / API 任何改动** — 无关

### 1.4 设计原则

延续阶段 1 路线:

1. **克制 > 堆砌** — 入场动画总时长 < 1.5s,微交互只做"按下/抬起/聚焦"三态
2. **Token 单一来源** — 排版变量(`--leading-*` / `--tracking-*`)与颜色 token 一样,只来自 `globals.css`
3. **无障碍优先** — `prefers-reduced-motion: reduce` 退化即时显示,不留残影
4. **零新依赖** — 纯 CSS + 已有 Tailwind v4 体系,不引 Framer Motion / GSAP
5. **可观察** — 每个目标有可观察的产物(§5 验收)

---

## 2. 文件结构与改动范围

```
agenthub/frontend/
├── app/
│   ├── globals.css                ← 改:新增 --leading-* / --tracking-* 变量、@keyframes inkReveal、
│   │                                       .prose-ink 类、.lift-ink/.focus-ink/.press-ink、
│   │                                       @media (prefers-reduced-motion: reduce)
│   ├── page.tsx                   ← 不改(Landing 4 section 拼装,无需变)
│   └── forum/page.tsx             ← 不动
├── components/
│   ├── landing/
│   │   ├── HeroSection.tsx        ← 改:title/副标题加 leading-tight tracking-display
│   │   ├── WuxingFlow.tsx         ← 改:5 节点加 className="reveal-beast" + style.animationDelay
│   │   │                          tooltip 容器加 prose-ink
│   │   ├── BeastRoster.tsx        ← 改:5 卡片 lift-ink focus-ink,内文 prose-ink
│   │   └── ForumEntry.tsx         ← 改:CTA 按钮 press-ink focus-ink
│   └── chat/
│       └── MessageInput.tsx       ← 改:input 加 focus-ink
│       (MessageBubble.tsx 不改 — 见 §11 决策,等 markdown 渲染引入后再加 prose-ink)
├── lib/
│   ├── wuxing.ts                  ← 改:导出 WUXING_FLOW_INDEX(id → stagger 序号)helper
│   └── hooks/
│       └── useReducedMotion.ts    ← 新建:SSR-safe 读取 prefers-reduced-motion
│                                    (本阶段不消费,留作后续 chat 内动画用)
└── (其他文件均不动)
```

**总改动**:5 改 + 1 新建 + 1 后端不动。**0 新增 npm 依赖**。

---

## 3. 排版精调

### 3.1 Token 定义(`globals.css` 的 `@theme` 块)

```css
@theme {
  /* 已有 --color-* / --font-* 不动 */

  /* 类型尺度(行高 / 字距) — 必须用 Tailwind v4 识别的 --leading-* / --tracking-* 命名空间 */
  /* 才会自动生成对应 utility class(如 leading-tight, tracking-display) */
  --leading-tight: 1.2;        /* 标题、卡片标题(覆盖默认 1.25) */
  --leading-normal: 1.6;       /* 正文 */
  --leading-loose: 1.75;       /* 长文(README / 长段气泡) */
  --tracking-display: 0.02em;  /* display 字体微紧 */
  --tracking-body: 0;          /* body 默认 */
  --tracking-mono: -0.01em;    /* code 字符收紧 */
}
```

### 3.2 排版决策表

| 元素 | 当前 | 改后 |
|------|------|------|
| 标题(Hero / BeastRoster 名字) | `font-display`,无显式 leading | `font-display leading-tight tracking-display` |
| 副标题 / 口头禅 | `text-sm text-ink/70` | 加 `leading-normal` |
| 长文(README 复刻 / 长段气泡) | 默认 1.5 leading | `leading-loose` |
| Code / mono | `font-mono` | `font-mono tracking-mono` |
| Link 下划线 | 浏览器默认 | `underline decoration-ink/30 underline-offset-4 hover:decoration-ink/80` |
| 弱化文字(`text-ink/60`) | 仅 opacity | 不变 |

### 3.3 Token 单一来源

- `--leading-*` / `--tracking-*` 只在 `globals.css` 定义,组件**只引用**,不写 `leading-[1.2]` 这类魔法值
- 与阶段 1 颜色 token 规则一致(单一来源、易调)

---

## 4. 代码/引用区样式(`.prose-ink`)

### 4.1 痛点

`<code>` / `<pre>` / `<blockquote>` / `<table>` / `<ul>` / `<ol>` 当前是 Tailwind preflight 默认,在水墨语境里"突然跳出来"。

### 4.2 在 `globals.css` 的 `@layer components` 新增

```css
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

### 4.3 适用与不适用

**适用**(加 `className="prose-ink"`):
- `WuxingFlow.tsx` tooltip 内容(兽擅长/盲点)
- `BeastRoster.tsx` 卡片内 catchphrase / strengths
- `MessageBubble.tsx` Agent 文本回复容器(等 markdown 渲染)
- 未来 Landing 介绍 README 复刻的 section

**不适用**:
- Landing Hero 标题、ForumEntry CTA(装饰,非阅读)
- 按钮 / 导航 / input(走 Tailwind utility)

### 4.4 Token 复用

全部用阶段 1 已定义的 `--color-ink/paper/gold/wuxing-*`,**不引入新颜色变量**(与阶段 1 §3.3 颜色三套合一规则一致)。

---

## 5. 微交互(`hover` / `focus` / `active`)

### 5.1 在 `globals.css` 的 `@layer components` 块新增

```css
@layer components {
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
}
```

### 5.2 应用位置

- `BeastRoster.tsx` 5 卡片:`lift-ink focus-ink`
- `ForumEntry.tsx` 按钮:`press-ink focus-ink`
- `AgentSelector.tsx` 选中态:`focus-ink`(与现有交互共存)
- `MessageInput.tsx` 输入框:`focus-ink`(覆盖浏览器默认 outline)
- `MessageBubble.tsx` 文本容器:`focus-ink`(键盘 tab 时可见)

---

## 6. Landing 入场动画

### 6.1 keyframe 定义

**在 `globals.css` 的非 `@theme` 块新增:**

```css
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
  opacity: 0;                       /* 默认隐藏,避免动画前闪烁 */
  animation: inkReveal 700ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
```

### 6.2 Stagger 顺序

**固定为相生顺序**,从 `WUXING_FLOW_INDEX` helper 取:

| 序号 | id | 兽 | 元素 |
|------|------|------|------|
| 0 | `pm` | 苍龙 | 木 |
| 1 | `qa` | 炎翎 | 火 |
| 2 | `orchestrator` | 瑞麟 | 土 |
| 3 | `developer` | 啸风 | 金 |
| 4 | `architect` | 玄冥 | 水 |

**为什么不用随机**:与 README 叙事"五行流转"对齐,首次访问者一眼看到"流转"秩序感;随机会让 5 节点每次出现顺序不同,削弱"五行"概念。

**总入场时长**:700ms(单头像) + 4 × 140ms(stagger 间隔)= **1.26s**,与"克制"原则对齐(< 1.5s)。

### 6.3 实现位置

**`WuxingFlow.tsx`**:5 节点 `className="reveal-beast"` + `style={{ animationDelay: '${i * 140}ms' }}`,其中 `i` 来自 `WUXING_FLOW_INDEX[id]`。

**`BeastRoster.tsx`**:5 卡片错开入场(沿用同一组 stagger 序号),让 Roster 也"流动出现"。

### 6.4 `WUXING_FLOW_INDEX` helper(在 `wuxing.ts` 新增)

```ts
export const WUXING_FLOW_INDEX: Readonly<Record<BeastId, number>> = {
  pm: 0,
  qa: 1,
  orchestrator: 2,
  developer: 3,
  architect: 4,
};
```

---

## 7. 无障碍(`prefers-reduced-motion`)

### 7.1 CSS 媒体查询(用于 Landing 入场)

**在 `globals.css` 末尾新增:**

```css
@media (prefers-reduced-motion: reduce) {
  .reveal-beast {
    animation: none;
    opacity: 1;
    transform: none;
    filter: none;
  }
  .lift-ink, .press-ink {
    transition: none;
  }
  .lift-ink:hover { transform: none; }
  .press-ink:active { transform: none; }
}
```

### 7.2 为什么要 CSS media query,不用 JS hook

- 零 JS 开销
- SSR 友好(无 hydration mismatch)
- 与阶段 1 `inkDrop` / `fadeInUp` 已有的媒体查询惯例一致

### 7.3 `useReducedMotion` hook(本阶段不消费)

新建 `lib/hooks/useReducedMotion.ts`,SSR-safe 读取 `window.matchMedia('(prefers-reduced-motion: reduce)').matches`,但**本阶段不消费**。留给后续需要运行时决策的场景(例:chat 内"消息到达"动画,可能阶段 3+)。

---

## 8. 验收标准

### 8.1 排版精度

- [ ] `globals.css` 含 `--leading-tight/normal/loose` 与 `--tracking-display/body/mono` 共 6 个变量
- [ ] Hero / BeastRoster 标题带 `leading-tight tracking-display`
- [ ] 长文段落带 `leading-loose`
- [ ] Code 元素带 `tracking-mono`
- [ ] 组件中**无魔法数字**(`leading-[1.2]` 之类不出现)
- [ ] grep 确认 `--leading-` / `--tracking-` 在 `globals.css` 唯一定义,在组件中只引用

### 8.2 代码/引用区

- [ ] `.prose-ink` 类存在于 `globals.css` 的 `@layer components` 块
- [ ] `WuxingFlow.tsx` tooltip、`BeastRoster.tsx` 卡片内文、`MessageBubble.tsx` 文本容器加 `prose-ink`
- [ ] `<code>` 视觉:`bg-ink/[0.06]` + 圆角 + 小字
- [ ] `<pre>` 视觉:`bg-paper-dark/80` + 边框 + 滚动
- [ ] `<blockquote>` 视觉:`border-l-2 border-gold/40` + 斜体
- [ ] `<table>` 视觉:水墨淡边、th 浅底
- [ ] 不引入新 CSS 颜色变量

### 8.3 微交互

- [ ] `.lift-ink` / `.focus-ink` / `.press-ink` 三类存在于 `globals.css`
- [ ] `BeastRoster` 5 卡片 hover 浮起 + cursor pointer
- [ ] `ForumEntry` 按钮 active scale 反馈
- [ ] `MessageInput` 输入框聚焦时 ring 出现(ink 色,非 Tailwind 默认蓝)
- [ ] Tab 键可遍历所有可聚焦元素,focus ring 可见

### 8.4 入场动画

- [ ] 5 神兽在 Landing 上以相生顺序 stagger 出现
- [ ] 总入场时长 ≤ 1.5s
- [ ] 动画曲线 `cubic-bezier(0.22, 1, 0.36, 1)`(ease-out,墨感)
- [ ] 首屏前 5 节点隐藏(opacity:0),动画结束后保留终态
- [ ] 刷新页面动画每次都播(无 localStorage 记忆)

### 8.5 无障碍

- [ ] OS / 浏览器开启"减少动效"后,5 神兽即时显示,无残影
- [ ] `lift-ink` / `press-ink` 在 reduced-motion 下无 transition
- [ ] `useReducedMotion` hook 存在但不消费(留作未来)

### 8.6 质量门禁

- [ ] `npm run check` 通过(Biome + TypeScript)
- [ ] `npm run build` 通过
- [ ] 浏览器实测:Landing 入场动画流畅、`/forum` 行为不变、切换回 Landing 动画重播

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| `inkReveal` 动画在某些设备掉帧 | 时长 700ms 不算长;`filter: blur` 已知开销,只用在 0%–60% 关键帧 |
| `prefers-reduced-motion` 在 SSR 阶段无法读取 | 用 CSS media query,不依赖 JS,SSR 友好 |
| `.prose-ink` 与现有 Tailwind preflight 冲突 | 用 `@layer components` 提升优先级;组件不直接用 Tailwind preflight 的 prose |
| `lift-ink` 与现有 `transition-colors` 冲突 | `lift-ink` 用 `transition-all` 覆盖,组件验证无残留 |
| `useReducedMotion` hook 未消费被质疑"无用" | 注释中明确"为阶段 3+ 预留";review 时解释 |

---

## 10. 自我审查(Spec Self-Review)

- [x] 无 "TBD" / "TODO" / 占位段落(已修:不再为 TTS 留 UI 占位)
- [x] 内部一致:`--leading-*` / `--tracking-*` 只在 `globals.css` 定义,`.prose-ink` 只在 `@layer components`,`.reveal-beast` 只在非 `@theme` 块
- [x] 范围聚焦:阶段 2 = 形(精调 + 动画),声延后到阶段 5+ 候选
- [x] 无歧义:每节有可观察的产物和验收标准
- [x] 不重复造轮子:沿用阶段 1 颜色 token 与 `inkDrop` / `fadeInUp` 体系
- [x] 与 CLAUDE.md 规则一致:0 新依赖、Token 单一来源、Zustand 状态不变

---

## 11. 已决策的开放项(本 spec 期间已闭环)

| 项 | 决策 |
|----|------|
| `useReducedMotion` hook 是否同期创建 | **创建但不消费**,留作阶段 3+ chat 动画用 |
| `WuxingFlow.tsx` 5 节点 hover tooltip 与 stagger 动画的优先级 | tooltip 用 `:hover` CSS 实现,与 `.reveal-beast` 不冲突(tooltip 在 animation 完成后可点) |
| `MessageBubble.tsx` 文本容器加 `prose-ink` 是否现在加 | **当前不加**(未引入 markdown 渲染),留作未来 |
