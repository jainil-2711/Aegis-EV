import type { NetworkImpactResponse } from "../../types/api";

interface ImpactCardProps {
  impact: NetworkImpactResponse;
}

function Row({
  label,
  before,
  after,
  unit,
  lowerIsBetter = true,
}: {
  label: string;
  before: number;
  after: number;
  unit: string;
  lowerIsBetter?: boolean;
}) {
  const improved = lowerIsBetter ? after < before : after > before;
  return (
    <div className="flex items-center justify-between border-t border-slate-100 py-3 first:border-t-0">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="flex items-center gap-2 text-sm">
        <span className="text-slate-500">
          {before.toFixed(1)}
          {unit}
        </span>
        <span className="text-slate-400">→</span>
        <span
          className={`font-medium ${improved ? "text-green-700" : "text-slate-900"}`}
        >
          {after.toFixed(1)}
          {unit}
        </span>
      </span>
    </div>
  );
}

export default function ImpactCard({ impact }: ImpactCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-1 text-sm font-medium text-slate-700">
        Network impact — before vs. after
      </p>
      <div>
        <Row label="Peak load" before={impact.peak_load_kw.before} after={impact.peak_load_kw.after} unit=" kW" />
        <Row label="Cost" before={impact.cost.before} after={impact.cost.after} unit=" ₹" />
        <Row
          label="Renewable share"
          before={impact.renewable_share_pct.before}
          after={impact.renewable_share_pct.after}
          unit="%"
          lowerIsBetter={false}
        />
        <Row label="CO2" before={impact.co2_kg.before} after={impact.co2_kg.after} unit=" kg" />
      </div>

      <div className="mt-4 rounded-md bg-slate-50 p-3">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Current pricing rule
        </p>
        <p className="mt-1 text-sm text-slate-700">
          Base rate: {impact.pricing_rule.base_rate.toFixed(2)}{" "}
          {impact.pricing_rule.currency}/kWh
        </p>
        <ul className="mt-1 space-y-0.5">
          {impact.pricing_rule.tiers.map((tier) => (
            <li key={tier.condition} className="text-xs text-slate-600">
              {tier.condition.replace("_", " ")}: {tier.price_per_kwh.toFixed(2)}{" "}
              {impact.pricing_rule.currency}/kWh
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
