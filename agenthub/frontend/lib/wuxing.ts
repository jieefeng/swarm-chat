/**
 * 五行神兽元数据单一来源（前端）。
 * 后端 agent_identity.py:AGENT_IDENTITIES 是 system_prompt 源；本文件是视觉/叙事源。
 * 颜色值与 globals.css 的 --color-wuxing-* 对齐（不要单独再定义色板）。
 */

export type WuxingElement = "木" | "水" | "金" | "火" | "土";
export type WuxingDirection = "东" | "北" | "西" | "南" | "中";
export type WuxingSeason = "春" | "冬" | "秋" | "夏" | "季";
export type WuxingVerb = "谋" | "稳" | "快" | "严" | "调";

export type BeastId = "pm" | "architect" | "developer" | "qa" | "orchestrator";

export interface WuxingBeast {
  id: BeastId;
  beast: string; // "青龙"
  nickname: string; // "苍龙"
  element: WuxingElement;
  direction: WuxingDirection;
  season: WuxingSeason;
  verb: WuxingVerb;
  role: string; // "产品经理（PM）"
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
    id: "pm",
    beast: "青龙",
    nickname: "苍龙",
    element: "木",
    direction: "东",
    season: "春",
    verb: "谋",
    role: "产品经理（PM）",
    color: { primary: "#3a7d52", secondary: "#d6e8df" },
    svgPath: "/avatars/qinglong.svg",
    personality: "深谋远虑，运筹帷幄。看似温和实则果决，关键时刻一锤定音",
    catchphrase: "且慢，先理清需求再动手",
    strengths: ["需求分析", "全局规划", "用户洞察", "优先级判断"],
    caution: "不擅长技术细节，需要玄武辅助",
  },
  {
    id: "architect",
    beast: "玄武",
    nickname: "玄冥",
    element: "水",
    direction: "北",
    season: "冬",
    verb: "稳",
    role: "系统架构师",
    color: { primary: "#3a6a9a", secondary: "#d6e2ee" },
    svgPath: "/avatars/xuanwu.svg",
    personality: "沉稳如山，万年不动。话少但每句都是深思熟虑",
    catchphrase: "根基不稳，地动山摇",
    strengths: ["系统设计", "架构评审", "技术选型", "性能优化"],
    caution: "过于保守，有时需要啸风推一把",
  },
  {
    id: "developer",
    beast: "白虎",
    nickname: "啸风",
    element: "金",
    direction: "西",
    season: "秋",
    verb: "快",
    role: "全栈开发者",
    color: { primary: "#9a7b2e", secondary: "#ebe0c4" },
    svgPath: "/avatars/baihu.svg",
    personality: "雷厉风行，执行力拉满。写代码快如闪电，偶尔毛躁",
    catchphrase: "说干就干，废话少说",
    strengths: ["快速开发", "代码实现", "问题修复", "技术落地"],
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
    role: "QA 工程师",
    color: { primary: "#b03a2e", secondary: "#eed4d0" },
    svgPath: "/avatars/zhuque.svg",
    personality: "火眼金睛，一丝不苟。对 bug 零容忍，但对人很温柔",
    catchphrase: "这点小把戏，还想瞒过我？",
    strengths: ["bug 检测", "测试覆盖", "质量把关", "边界分析"],
    caution: "过于追求完美，有时吹毛求疵",
  },
  {
    id: "orchestrator",
    beast: "麒麟",
    nickname: "瑞麟",
    element: "土",
    direction: "中",
    season: "季",
    verb: "调",
    role: "任务协调器",
    color: { primary: "#8a6840", secondary: "#e6dcc8" },
    svgPath: "/avatars/qilin.svg",
    personality: "居中调度，调和五行。不偏不倚，公正无私",
    catchphrase: "诸位稍安，容我梳理一番",
    strengths: ["任务分解", "资源调度", "冲突调解", "流程把控"],
    caution: "不直接产出代码，依赖其他神兽执行",
  },
] as const;

/** 五行相生流转顺序（取自 orchestrator.py:25 "五行相生（任务流转顺序建议）"） */
export const WUXING_FLOW_ORDER: readonly BeastId[] = [
  "pm", // 苍龙(谋·定策) →
  "qa", // 炎翎(严·试火) →
  "orchestrator", // 瑞麟(调·调度) →
  "developer", // 啸风(快·锻冶) →
  "architect", // 玄冥(稳·筑基) → 回到苍龙
] as const;

export function getBeastById(id: BeastId): WuxingBeast | undefined {
  return WUXING_BEASTS.find((b) => b.id === id);
}
