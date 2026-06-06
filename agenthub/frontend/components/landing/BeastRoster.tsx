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
