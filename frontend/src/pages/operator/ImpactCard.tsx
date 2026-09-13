import type { NetworkImpactResponse } from "../../types/api";
import SourceBadge from "../../components/SourceBadge";

interface ImpactCardProps { impact: NetworkImpactResponse; }

interface RowProps {
  label: string;
  before: number;
  after: number;
  unit: string;
  higherIsBetter?: boolean;
  prefix?: string;
}

function formatValue(value: number, prefix = "", unit = "") {
  return `${prefix}${value.toLocaleString("en-IN", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}${unit}`;
}

function Row({ label, before, after, unit, higherIsBetter = false, prefix = "" }: RowProps) {
  const delta = after - before;
  const improved = higherIsBetter ? delta > 0.0001 : delta < -0.0001;
  const worse = higherIsBetter ? delta < -0.0001 : delta > 0.0001;
  return (
    <div className="flex items-center justify-between gap-4 border-t border-slate-100 py-3 first:border-t-0">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="flex flex-wrap items-center justify-end gap-2 text-sm">
        <span className="text-slate-500">{formatValue(before, prefix, unit)}</span>
        <span className="text-slate-400">→</span>
        <span className={`font-semibold ${improved ? "text-emerald-700" : worse ? "text-amber-700" : "text-slate-800"}`}>{formatValue(after, prefix, unit)}</span>
        <span className="text-[10px] uppercase tracking-wide text-slate-400">{improved ? "better" : worse ? "trade-off" : "flat"}</span>
      </span>
    </div>
  );
}

export default function ImpactCard({ impact }: ImpactCardProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Measured impact</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Baseline → active schedule</h2>
          <p className="mt-1 text-xs text-slate-500">Before = deterministic baseline. After = the currently active (applied) schedule — never an unapplied candidate.</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <SourceBadge kind="optimized" />
          <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">Active run {impact.active_optimization_run_id}</span>
        </div>
      </div>
      <div className="mt-3">
        <Row label="Peak EV load" before={impact.peak_load_kw.before} after={impact.peak_load_kw.after} unit=" kW" />
        <Row label="Cost" before={impact.cost.before} after={impact.cost.after} unit="" prefix="₹" />
        <Row label="Renewable share" before={impact.renewable_share_pct.before} after={impact.renewable_share_pct.after} unit="%" higherIsBetter />
        <Row label="CO₂ impact" before={impact.co2_kg.before} after={impact.co2_kg.after} unit=" kg" />
      </div>
      <div className="mt-4 rounded-xl bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Transparent pricing guardrails</p>
        <p className="mt-1 text-sm text-slate-700">Base {impact.pricing_rule.base_rate.toFixed(2)} {impact.pricing_rule.currency}/kWh · bounded tiers, never tied to driver override.</p>
        <div className="mt-2 flex flex-wrap gap-2">{impact.pricing_rule.tiers.map((tier) => <span key={tier.condition} className="rounded-full border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600">{tier.condition.replace("_", " ")}: {tier.price_per_kwh.toFixed(2)}</span>)}</div>
      </div>
    </section>
  );
}
