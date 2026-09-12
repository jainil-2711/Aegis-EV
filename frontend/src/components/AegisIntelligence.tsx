interface IntelligenceProps {
  title?: string;
  subtitle?: string;
  items: { label: string; value: string; tone?: "cyan" | "green" | "amber" | "slate" }[];
  footer?: string;
}

const toneClass = {
  cyan: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
  green: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  amber: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  slate: "border-white/10 bg-white/[0.04] text-slate-200",
};

export default function AegisIntelligence({ title = "Decision trace", subtitle = "Signal fusion", items, footer }: IntelligenceProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#07111f] text-white shadow-lg">
      <div className="relative p-5">
        <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-cyan-400/10 blur-3xl" />
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-cyan-300/30 bg-cyan-300/10 text-xs font-bold text-cyan-200">A</span>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cyan-300">Aegis Intelligence</p>
            </div>
            <h2 className="mt-2 text-lg font-semibold tracking-tight">{title}</h2>
            <p className="mt-1 text-xs text-slate-400">{subtitle} · deterministic, auditable reasoning</p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] uppercase tracking-wide text-slate-400">No black box</span>
        </div>

        <div className="mt-5 grid gap-2 sm:grid-cols-3">
          {items.map((item) => (
            <div key={item.label} className={`rounded-xl border p-3 ${toneClass[item.tone ?? "slate"]}`}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] opacity-60">{item.label}</p>
              <p className="mt-1.5 text-sm font-medium leading-5">{item.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wide text-slate-500">
          <span className="rounded-full border border-white/10 px-2 py-1">Grid signal</span>
          <span>→</span>
          <span className="rounded-full border border-white/10 px-2 py-1">Renewable pulse</span>
          <span>→</span>
          <span className="rounded-full border border-white/10 px-2 py-1">EV flexibility</span>
          <span>→</span>
          <span className="rounded-full border border-cyan-300/20 bg-cyan-300/5 px-2 py-1 text-cyan-200">Aegis optimizer</span>
        </div>

        {footer && <p className="mt-4 text-xs leading-5 text-slate-500">{footer}</p>}
      </div>
    </section>
  );
}
