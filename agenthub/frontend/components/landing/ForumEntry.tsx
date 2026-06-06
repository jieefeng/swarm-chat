import Link from "next/link";

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
          扩 3 个文件即可，5 分钟内完成：
          <br />
          <code className="text-ink/70">
            backend/services/agent_identity.py
          </code>{" "}
          的<code className="text-ink/70"> AGENT_IDENTITIES</code> 加一项；
          <br />
          <code className="text-ink/70">backend/services/session.py</code> 的
          <code className="text-ink/70"> AGENT_CONFIGS</code> 加一项；
          <br />
          <code className="text-ink/70">frontend/lib/wuxing.ts</code> 的
          <code className="text-ink/70"> WUXING_BEASTS</code> 加一项。
        </p>
      </div>
    </section>
  );
}
