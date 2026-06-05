# AgentHub 五行神兽品牌化设计（阶段 1）

**日期**：2026-06-06
**状态**：设计完成，待用户 review
**阶段**：4 阶段路线图中的第 1 阶段（立庙）
**影响范围**：`agenthub/README.md`、`agenthub/frontend/app/page.tsx`（路由搬迁）、`agenthub/frontend/components/landing/*`（新建）、`agenthub/frontend/public/avatars/*.svg`（重画）、颜色 token 统一

---

## 1. 背景与目标

### 1.1 问题

AgentHub 已经具备完整的多 Agent 协作能力（5 神兽、SSE、SQLite、Spec 输出、HITL 澄清、任务编排、Claude Code 工具、跨模型互审的雏形），且后端已有相当完整的"东方五行神兽"世界观（`AGENT_IDENTITIES` 含性格、口头禅、羁绊、五行相生流转），**但对外完全没有讲述**：

- `README.md` 仅 30 行干巴巴的"IM 聊天式多 Agent 协作平台"
- 5 个 SVG 头像虽然存在，但实现是"彩色渐变圆 + 白色汉字"（emoji 升级版），不是水墨
- 颜色 token 三套并行：后端 `AGENT_IDENTITIES.color`、前端 `DefaultAgentModal.tsx` 的本地 `ELEMENT_COLORS`、`globals.css` 的 `--color-wuxing-*` 互不对齐
- 没有 Landing / 介绍页
- 五行叙事（软件工程五段工序的人格式分身）这个**真正独有的差异化**没有展示出来

### 1.2 目标

把"五行"作为叙事主梁，**不模仿任何具体项目**（Clowder AI 等参考项目仅作为"非我要做什么"的对位参照），把 AgentHub 自己的故事讲出来。完成：

1. README 重写：以五行流转为核心叙事
2. 新建 Landing 页（`/`）：先看故事，再进 chat
3. 路由改造：现有 chat 平移到 `/forum`（议事堂）
4. 5 个 SVG 神兽头像重画为单色水墨
5. 三套颜色 token 合一为单一来源

### 1.3 非目标（Out of Scope）

明确不做：

- **新增跨模型互审 / Signals / 游戏 / 语音 / 跨平台网关**等任何新功能 — 这些属于阶段 2-4
- **不立"CVO 首席愿景官"等神秘化角色** — 工程师用户不需要
- **不模仿"硬约束 + 软力量 / 五条第一性原理 / 铁律"等任何具体项目的章节骨架** — 借鉴其精神（克制 / 排除项 / 公开路线），不抄形式
- **不堆砌东方装饰**（印章按钮、卷轴卡片、砚台图标） — 克制，5 个水墨头像 + 五行主题色已足够
- **不拍演示视频** — Landing 直接嵌入真实 chat 入口，比视频更可信
- **不画 Landing 用的复杂插图**（手绘、矢量场景图） — 一张"五行相生"转盘图 + 5 个 SVG 头像，其余靠排版

### 1.4 设计原则

1. **五行主导**：木火土金水不只是名字，是工作流、是 UI 主题、是叙事骨架
2. **不抄形式**：参考项目是反向参考（"不要做 X"），不是模仿清单
3. **克制 > 堆砌**：水墨淡描 > 工笔重彩
4. **工程师向**：反过度营销，反温情神秘化
5. **可验证**：每个目标有可观察的产物

---

## 2. 内容叙事层

### 2.1 README 结构（重写后约 80-120 行）

```
# AgentHub — 五行神兽议事堂

> 一行 code 写不出来，五个神兽围炉议事。

[TOC]

## 1. 五行流转
[核心大段：5 神兽相生循环图 + 1 段说明 + 1 个真实示例]

## 2. 5 神兽
[全息表 + 每行 1 句口头禅 + 1 句擅长 + 1 句盲点]

## 3. Quick start
[保留现有 6 步安装命令]

## 4. 怎么调度
[3 个真实 @ 调用的对话示例]

## 5. 怎么加你的神兽
[工程师向：扩 3 个文件 5 分钟]
```

末尾附加 8 行内**短路线图**和 4-5 行**不做的清单**。

### 2.2 README Hero（首屏文案）

```
五行神兽，共治一炉代码。
苍龙定策 · 玄冥筑基 · 啸风锻冶 · 炎翎试火 · 瑞麟调律
你只管 @ 一声，五行自转。
```

下方一行注脚：`> 不是 5 个凑数的 agent，是 5 道工序的人格式分身。`

### 2.3 5 神兽全息表（README §2 + Landing BeastRoster 共用）

| 兽 | 昵称 | 五行 | 方位 | 季节 | 性格动词 | 职能 | 口头禅 |
|----|------|------|------|------|----------|------|--------|
| 青龙 | 苍龙 | 木 | 东 | 春 | **谋** | 定策 | 且慢，先理清需求再动手 |
| 玄武 | 玄冥 | 水 | 北 | 冬 | **稳** | 筑基 | 根基不稳，地动山摇 |
| 白虎 | 啸风 | 金 | 西 | 秋 | **快** | 锻冶 | 说干就干，废话少说 |
| 朱雀 | 炎翎 | 火 | 南 | 夏 | **严** | 试火 | 这点小把戏，还想瞒过我？ |
| 麒麟 | 瑞麟 | 土 | 中 | 季 | **调** | 调律 | 诸位稍安，容我梳理一番 |

每行再附 1 句"擅长"和 1 句"盲点"，从现有 `agent_identity.py` 抽。

### 2.4 五行流转图（核心大段，README §1 + Landing WuxingFlow 共用）

流转顺序（取自 `orchestrator.py:25` "五行相生（任务流转顺序建议）"）：

```
苍龙(谋·定策) → 炎翎(严·试火) → 瑞麟(调·调度) → 啸风(快·锻冶) → 玄冥(稳·筑基) → 苍龙
```

配 1 段说明：「每一步是上一段的果，是下一段的因。」

配 1 个真实示例（README 用文字 + Landing 用对话气泡）：

```
@瑞麟 加个深色模式
  → 瑞麟拆解任务
  → @苍龙 厘清需求：「用户场景：白天/夜间、跟随系统？自定义？」
  → @啸风 实现
  → @炎翎 试火
  → @玄冥 复查架构
  → 完事
```

### 2.5 README "怎么加你的神兽"（工程师向）

扩 3 个文件即可：

1. `agenthub/backend/services/agent_identity.py` — `AGENT_IDENTITIES` 加一项
2. `agenthub/backend/services/session.py` — `AGENT_CONFIGS` 加一项
3. `agenthub/frontend/lib/wuxing.ts`（本阶段新建）— 加一项元数据

5 分钟可加一个新神兽，**不需要碰任何其他文件**（如需加新羁绊，再扩 `BOND_MAP`）。

### 2.6 README 路线图（8 行内）

```
阶段 1（现在）: 五行神兽立庙 — 真头像 + Landing + README
阶段 2:        声与形 — 神兽声线 + 水墨主题精调
阶段 3:        飞升 — 飞书/钉钉跨平台
阶段 4:        副业 — 神兽策略卡 / 共创世界
```

### 2.7 README "不做的清单"

```
- 不做 AI 陪伴和虚拟人格
- 不做演示视频
- 不立 CVO 之类的神秘化角色
- 不模仿其他项目的章节骨架
- 不堆砌东方装饰（印章/卷轴/砚台图标等）
```

---

## 3. 视觉系统

### 3.1 已就位不动的部分

确认以下现状正确，不动：

- 主题名「水墨丹青·素宣」
- Tailwind v4 `@theme` token（`--color-ink/paper/gold` + `--color-wuxing-wood/water/metal/fire/earth`）
- 字体 LXGW WenKai（霞鹜文楷，CDN 引入，display + body）
- 纸纹背景 + scrollbar 主题 + inkDrop/fadeInUp 动画
- 现有 chat 组件使用的 `font-display` / `text-ink` / `bg-paper` / `border-gold`

### 3.2 5 个 SVG 神兽头像重画

**目标风格总纲（5 个 SVG 共同遵守）**：

- viewBox `0 0 128 128`
- 圆形容器：`r=58`，`stroke=2 ink/15`，背景透明
- 内画 60×60 的"水墨意笔"神兽形
- 单一墨色 `#2c2c3a`（=`--color-ink`），**不用渐变、不用底色**
- 贝塞尔曲线 + strokeWidth 变化（3→1.5）模拟飞白
- 留白：神兽占圆形内 40-50%，周围留白（白纸感）

**5 个形的具体设计**：

- **青龙**（木·东·春·谋）—— 龙身 S 形一笔，鬃毛三两笔，头朝左上
- **玄武**（水·北·冬·稳）—— 龟壳六边形 + 蛇身缠绕
- **白虎**（金·西·秋·快）—— 虎头正视，王字 + 双眼两点
- **朱雀**（火·南·夏·严）—— 凤冠 + 长尾三羽
- **麒麟**（土·中·季·调）—— 鹿角 + 狮身 + 龙鳞一笔

**当前文件**（待重画覆盖）：

- `agenthub/frontend/public/avatars/qinglong.svg`
- `agenthub/frontend/public/avatars/xuanwu.svg`
- `agenthub/frontend/public/avatars/baihu.svg`
- `agenthub/frontend/public/avatars/zhuque.svg`
- `agenthub/frontend/public/avatars/qilin.svg`

### 3.3 颜色 token 三套合一

**现状（三套并行）**：

| 位置 | 当前色 | 备注 |
|------|--------|------|
| `backend/services/agent_identity.py` `color.primary` | `#059669` | 鲜艳绿 |
| `frontend/components/agents/DefaultAgentModal.tsx` `ELEMENT_COLORS` | `#059669` | 鲜艳绿 |
| `frontend/app/globals.css` `--color-wuxing-wood` | `#3a7d52` | 水墨绿 |

**目标（单一来源）**：

- 新建 `agenthub/frontend/lib/wuxing.ts` 作为**前端 wuxing 元数据单一来源**
- 导出 5 神兽元数据：`{ id, beast, nickname, element, color: {primary, secondary}, svgPath, personality, catchphrase, verb, ... }`
- `color.primary/secondary` 直接使用 `globals.css` 已有水墨色（`#3a7d52` 等），TS 里写常量字符串即可
- 删除 `DefaultAgentModal.tsx` 的本地 `ELEMENT_COLORS`，改 import `wuxing.ts`
- 后端 `agent_identity.py` 的 `color` 字段**保持**（API 已通过 `/api/agents` 返回给前端），但同步更新为水墨色值，与前端一致
- 不做"自动从 CSS 读"，因为后端 API 返回色值是显式契约

### 3.4 装饰克制

不新增任何"东方装饰组件"（印章按钮、卷轴卡片、砚台图标、祥云背景图等）。当前已有的水墨主题色 + 5 个水墨头像 + `font-display` 字体已足够。

---

## 4. 架构落地

### 4.1 路由改造

| 路径 | 改造前 | 改造后 |
|------|--------|--------|
| `/` | chat 主页面 | **Landing**（4 section 拼装的 server component） |
| `/forum` | 不存在 | **议事堂** — 现有 chat 整体搬迁 |
| `/agents` | 已有（Agent 配置页） | 不动 |
| 其他 (`/api/*`, SSE) | 不动 | 不动 |

**实现**：

1. 把 `agenthub/frontend/app/page.tsx`（260 行 chat 组件）**整体 move** 到 `agenthub/frontend/app/forum/page.tsx`
2. 新建 `agenthub/frontend/app/page.tsx` 作为 Landing（server component，约 30 行 JSX）
3. 全文搜索 `Link href="/"` 改为 `Link href="/forum"`，确认无遗漏
4. Landing 自身的"进议事堂"按钮：`Link href="/forum"`

**风险点**：Zustand store 跨路由切换是单例（不会丢状态），但页面 hooks 会重跑。`forum/page.tsx` 继承所有现有 chat 行为，零行为变更。

### 4.2 新增文件结构

```
agenthub/frontend/
├── app/
│   ├── page.tsx              ← 改造：Landing（替换原 chat）
│   ├── forum/
│   │   └── page.tsx          ← 新建：现有 chat（原 page.tsx 迁入）
│   ├── agents/...            ← 不动
│   ├── layout.tsx            ← 不动
│   └── globals.css           ← 不动
├── components/
│   ├── landing/              ← 新建目录
│   │   ├── HeroSection.tsx
│   │   ├── WuxingFlow.tsx
│   │   ├── BeastRoster.tsx
│   │   └── ForumEntry.tsx
│   ├── chat/                 ← 不动
│   ├── agents/               ← 不动
│   └── threads/              ← 不动
├── public/avatars/           ← 5 SVG 重画覆盖
└── lib/
    └── wuxing.ts             ← 新建：5 神兽元数据单一来源

agenthub/
└── README.md                 ← 重写
```

### 4.3 Landing 组件树

```tsx
// app/page.tsx (server component, 无 'use client')
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

- 全部是 server component（SEO 友好，bundle 小）
- 4 个 section 之间用 `<section>` 包裹，配 `@theme` 已有 token
- 动画统一用 `animate-fade-in-up` / `animate-ink-drop`（已在 `globals.css` 定义）
- 5 神兽数据从 `lib/wuxing.ts` 导入，**不在组件内 hardcode**

### 4.4 WuxingFlow 组件（核心大段）

**展示形式**：水墨风"五行相生"转盘图

**视觉要求**：

- 五边形排列（或环形），5 个神兽头像（40-48px）均匀分布
- 节点之间用**相生箭头**连接（顺时针）
- 中心是"议事堂"或留空
- 鼠标 hover 节点：高亮 + 显示该神兽的"擅长"（tooltip）
- 用 `animate-ink-drop` 入场

**实现选择**：

- 纯 SVG 绘制（控制力最强，动画可自定义）
- 或 HTML + Tailwind grid（响应式友好）

**推荐**：纯 SVG（约 80-150 行），用 `<g transform="rotate()">` 排布 5 个节点。

### 4.5 wuxing.ts 元数据

```ts
// agenthub/frontend/lib/wuxing.ts
export interface WuxingBeast {
  id: 'pm' | 'architect' | 'developer' | 'qa' | 'orchestrator'
  beast: string              // "青龙"
  nickname: string           // "苍龙"
  element: '木' | '水' | '金' | '火' | '土'
  direction: '东' | '北' | '西' | '南' | '中'
  season: '春' | '冬' | '秋' | '夏' | '季'
  verb: '谋' | '稳' | '快' | '严' | '调'
  role: string               // "产品经理（PM）"
  color: { primary: string; secondary: string }
  svgPath: string            // "/avatars/qinglong.svg"
  personality: string
  catchphrase: string
  strengths: string[]
  caution: string
}

export const WUXING_BEASTS: readonly WuxingBeast[] = [...] as const

// 五行相生流转顺序（取自 orchestrator.py:25）
export const WUXING_FLOW_ORDER = ['pm', 'qa', 'orchestrator', 'developer', 'architect'] as const
```

**与后端关系**：

- 后端 `agent_identity.py:AGENT_IDENTITIES` 保留（作为 system_prompt source），但**颜色字段同步**为水墨色
- 前端 `wuxing.ts` 是**视觉元数据**的单一来源
- 后端 `/api/agents` 仍返回完整 agent 元数据（前端用于 chat 内的实时展示），但颜色值与 wuxing.ts 对齐

---

## 5. 验收标准

### 5.1 README

- [ ] 5 节齐全：五行流转 / 5 神兽 / Quick start / 怎么调度 / 怎么加你的神兽
- [ ] 含五行流转核心图（文字版 + Landing SVG 版）
- [ ] 含 5 神兽全息表
- [ ] 含 3 个真实 @ 调度示例
- [ ] 含 8 行内路线图
- [ ] 含 4-5 行"不做的清单"
- [ ] 总行数 80-120 行
- [ ] 不出现 "CVO" / "铁律" / "硬约束" / "陪伴" / "家" 等字眼（除非必要的元数据）

### 5.2 Landing

- [ ] `npm run dev` 打开 `http://localhost:7000` 先看到 Landing（不是 chat）
- [ ] 4 section 全部渲染：Hero / WuxingFlow / BeastRoster / ForumEntry
- [ ] WuxingFlow 展示 5 神兽按相生顺序循环
- [ ] BeastRoster 5 张卡：头像 + 名字 + 性格动词 + 口头禅 + 1 句擅长
- [ ] "进议事堂"按钮跳转到 `/forum`
- [ ] `/forum` 行为与原 `/` 完全一致（无功能变更）

### 5.3 SVG 头像

- [ ] 5 个 SVG 都是单色墨色 `#2c2c3a`
- [ ] viewBox 一致（128×128）
- [ ] 圆形容器 + 飞白笔触感
- [ ] 5 个形可辨：龙 / 龟蛇 / 虎 / 凤 / 麒麟
- [ ] 视觉风格一致（同一设计师同日产出，或同一 spec 给 AI 工具）

### 5.4 颜色 token

- [ ] `DefaultAgentModal.tsx` 不再有本地 `ELEMENT_COLORS`
- [ ] 改用 `wuxing.ts` import
- [ ] 后端 `AGENT_IDENTITIES[*].color` 与前端 `wuxing.ts` 颜色值一致
- [ ] 不引入新的 CSS 颜色变量

### 5.5 质量门禁

- [ ] `npm run check` 通过（Biome + TypeScript）
- [ ] `npm run build` 通过
- [ ] `pytest` 通过
- [ ] 浏览器实测：Landing → /forum → 收发消息 → 切回 Landing 无残留

---

## 6. 工作量与里程碑

| 任务 | 估时 | 风险 |
|------|------|------|
| 路由改造（page.tsx → forum） | 0.5 小时 | 低 |
| Landing 4 组件（Hero/Roster/Entry + 简单） | 4-6 小时 | 低 |
| WuxingFlow 组件（核心大段） | 2-3 小时 | 中（构图 + 动画） |
| 5 SVG 神兽头像重画 | 1 天 | 中（一致性） |
| wuxing.ts 单一来源 + 3 处对齐 | 2 小时 | 低 |
| README 重写 | 1-2 小时 | 低 |
| 验证（check/build/启动看效果） | 1 小时 | 低 |

**总估时**：3-5 个工作日（单人）。

**里程碑**：

- M1（半天）：路由改造 + Landing 4 组件骨架 + README 初稿
- M2（1 天）：WuxingFlow 完整版 + BeastRoster 数据接通
- M3（1-2 天）：5 SVG 头像重画 + 颜色 token 合一
- M4（半天）：验证 + 修细节

---

## 7. 后续阶段（Out of Scope，本 spec 不涉及）

- **阶段 2：声与形** — 神兽声线（独立 TTS 音色）+ 水墨主题精调 + 欢迎动画
- **阶段 3：飞升** — 飞书 / 钉钉 / Telegram 跨平台网关
- **阶段 4：副业** — 神兽策略卡 / 共创世界 / 游戏化

每个阶段独立 spec → plan → implementation。

---

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| WuxingFlow 视觉不到位（核心大段） | 先 ASCII mock 草图 + 评审，再交实现 |
| 5 SVG 风格不一致 | 同一设计师 / 同一 spec 给 AI 工具；设计稿先评审再量产 |
| 路由改造破坏 Zustand 状态 | zustand store 是模块单例，路由切换不丢；hooks 重跑是预期行为 |
| 用户从 `/forum` 刷新跳到 `/`（Landing） | 明确这是设计意图："先看故事，再进 chat"；如不要该行为可加 `<Link replace>` |
| README 文案调性跑偏 | §2.7 列出"不做的清单"作为自我审查清单 |

---

## 9. 自我审查（Spec Self-Review）

- [x] 无 "TBD" / "TODO" / 占位段落
- [x] 内部一致：所有"五行色"指向同一份；所有"5 神兽"指向同一份
- [x] 范围聚焦：只做阶段 1，阶段 2-4 在 §7 明确 out of scope
- [x] 无歧义：每节有可观察的产物和验收标准
- [x] 不重复造轮子：明确"已就位不动"的部分（globals.css、字体、tailwind token）
