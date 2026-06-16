/**
 * 五行神兽元数据单一来源（前端）。
 * 后端 agent_identity.py:AGENT_IDENTITIES 是 system_prompt 源；本文件是视觉/叙事源。
 * 颜色值与 globals.css 的 --color-wuxing-* 对齐（不要单独再定义色板）。
 */

export type WuxingElement = "木" | "水" | "金" | "火" | "土";
export type WuxingDirection = "东" | "北" | "西" | "南" | "中";
export type WuxingSeason = "春" | "冬" | "秋" | "夏" | "季";
export type WuxingVerb = "谋" | "稳" | "快" | "严" | "调";

export type BeastId = "designer" | "developer" | "qa";

export interface WuxingBeast {
  id: BeastId;
  beast: string; // "青龙"
  nickname: string; // "苍龙"
  element: WuxingElement;
  direction: WuxingDirection;
  season: WuxingSeason;
  verb: WuxingVerb;
  role: string; // "创意设计师"
  /** 取自 globals.css --color-wuxing-*，写常量便于 SSR/CSR 一致 */
  color: { primary: string; secondary: string };
  svgPath: string; // "/avatars/qinglong.svg"
  personality: string;
  catchphrase: string;
  strengths: string[];
  caution: string;
}

export const WUXING_BEASTS: readonly WuxingBeast[] = [
  {
    id: "designer",
    beast: "青龙",
    nickname: "苍龙",
    element: "木",
    direction: "东",
    season: "春",
    verb: "谋",
    role: "创意设计师",
    color: { primary: "#3a7d52", secondary: "#d6e8df" },
    svgPath: "/avatars/qinglong.svg",
    personality: "深谋远虑，运筹帷幄。看似温和实则果决，关键时刻一锤定音",
    catchphrase: "且慢，先理清需求再动手",
    strengths: ["视觉设计", "用户体验", "创意方案", "产品规划"],
    caution: "不擅长技术细节，需要啸风辅助",
  },
  {
    id: "developer",
    beast: "白虎",
    nickname: "啸风",
    element: "金",
    direction: "西",
    season: "秋",
    verb: "快",
    role: "核心开发者",
    color: { primary: "#9a7b2e", secondary: "#ebe0c4" },
    svgPath: "/avatars/baihu.svg",
    personality: "雷厉风行，执行力拉满。写代码快如闪电，偶尔毛躁",
    catchphrase: "说干就干，废话少说",
    strengths: ["需求分析", "架构设计", "代码实现", "调试修复", "性能优化"],
    caution: "速度优先时容易埋 bug，需要炎翎把关",
  },
  {
    id: "qa",
    beast: "朱雀",
    nickname: "炎翎",
    element: "火",
    direction: "南",
    season: "夏",
    verb: "严",
    role: "质量守护者",
    color: { primary: "#b03a2e", secondary: "#eed4d0" },
    svgPath: "/avatars/zhuque.svg",
    personality: "火眼金睛，一丝不苟。对 bug 零容忍，但对人很温柔",
    catchphrase: "这点小把戏，还想瞒过我？",
    strengths: ["代码审查", "测试覆盖", "质量保证", "安全审计"],
    caution: "过于追求完美，有时吹毛求疵",
  },
] as const;

/** 五行相生流转顺序（3 核心 Agent） */
export const WUXING_FLOW_ORDER: readonly BeastId[] = [
  "designer", // 苍龙(谋·定策) →
  "developer", // 啸风(快·锻冶) →
  "qa", // 炎翎(严·试火) → 回到苍龙
] as const;

/**
 * 五行相生流转顺序索引（用于 stagger 入场动画的 delay 序号）
 * 0..2，值与 WUXING_FLOW_ORDER 的位置严格一致。
 */
export const WUXING_FLOW_INDEX: Readonly<Record<BeastId, number>> = {
  designer: 0,
  developer: 1,
  qa: 2,
};

export function getBeastById(id: BeastId): WuxingBeast | undefined {
  return WUXING_BEASTS.find((b) => b.id === id);
}
