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
