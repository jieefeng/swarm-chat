import { WUXING_BEASTS } from "@/lib/wuxing";

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
      <p className="font-display text-base md:text-lg text-ink/60 mt-4 tracking-display">
        苍龙定策 · 玄冥筑基 · 啸风锻冶 · 炎翎试火 · 瑞麟调律
      </p>
      <p className="font-body text-sm md:text-base text-ink/50 mt-8 max-w-2xl mx-auto leading-normal">
        你只管 @ 一声，五行自转。
      </p>
      <p className="font-body text-xs md:text-sm text-ink/40 mt-3 max-w-2xl mx-auto italic leading-normal">
        不是 5 个凑数的 agent，是 5 道工序的人格式分身。
      </p>
    </section>
  );
}
