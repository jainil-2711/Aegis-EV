import type { DriverRecommendationResponse } from "../../types/api";
import AegisIntelligence from "../../components/AegisIntelligence";

interface RecommendationCardProps { recommendation: DriverRecommendationResponse; }

function formatWindow(startIso: string, endIso: string): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const fmt = (d: Date) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return `${fmt(start)} – ${fmt(end)}`;
}

export default function RecommendationCard({ recommendation: r }: RecommendationCardProps) {
  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-600">Active network schedule</p>
            <p className="mt-1 text-xs text-slate-500">Published by Network Operator · {r.optimization_run_id}</p>
          </div>
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">Operator published</span>
        </div>
        <p className="text-sm text-slate-500">Recommended charging window</p>
        <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">{formatWindow(r.window_start, r.window_end)}</p>

        <dl className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div><dt className="text-xs uppercase tracking-wide text-slate-400">Estimated cost</dt><dd className="mt-1 text-lg font-semibold text-slate-900">₹{r.estimated_cost.toFixed(2)}</dd></div>
          <div><dt className="text-xs uppercase tracking-wide text-slate-400">Charging price</dt><dd className="mt-1 text-lg font-semibold text-slate-900">₹{r.price_per_kwh.toFixed(2)}/kWh</dd></div>
          <div><dt className="text-xs uppercase tracking-wide text-slate-400">Renewable</dt><dd className="mt-1 text-lg font-semibold text-emerald-700">{r.renewable_share_pct.toFixed(0)}%</dd></div>
          <div><dt className="text-xs uppercase tracking-wide text-slate-400">CO₂ impact</dt><dd className="mt-1 text-lg font-semibold text-slate-900">{r.co2_impact_kg.toFixed(1)} kg</dd></div>
        </dl>

        <div className="mt-5 rounded-xl bg-slate-50 p-3">
          <div className="flex items-center justify-between gap-3"><span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Green Score</span><span className="text-sm font-semibold text-slate-800">{typeof r.green_score === "number" ? `${r.green_score.toFixed(0)} / 100` : "Unavailable"}</span></div>
          <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${Math.min(Math.max(r.green_score ?? 0, 0), 100)}%` }} /></div>
          <p className="mt-2 text-xs text-slate-500">Informational only — it never changes access, priority or price.</p>
        </div>

        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-sm font-semibold text-slate-700">Why this window?</summary>
          <p className="mt-2 text-sm leading-6 text-slate-600">{r.why}</p>
        </details>
      </div>

      <AegisIntelligence
        title="Driver decision trace"
        items={[
          { label: "Source", value: `Active run ${r.optimization_run_id}`, tone: "cyan" },
          { label: "Renewable alignment", value: `${r.renewable_share_pct.toFixed(0)}% of scheduled energy`, tone: "green" },
          { label: "Preference", value: "Your saved preference is advisory to the next network optimization", tone: "amber" },
        ]}
        footer="Aegis explains a network-published recommendation. You remain free to accept it or charge now."
      />
    </section>
  );
}
