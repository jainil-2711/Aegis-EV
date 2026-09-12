import type { DriverRecommendationResponse } from "../../types/api";

interface RecommendationCardProps {
  recommendation: DriverRecommendationResponse;
}

function formatWindow(startIso: string, endIso: string): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const fmt = (d: Date) =>
    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return `${fmt(start)} – ${fmt(end)}`;
}

export default function RecommendationCard({
  recommendation,
}: RecommendationCardProps) {
  const r = recommendation;

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
            Active network schedule
          </span>
          <span className="text-xs text-slate-500">
            Published by network operator · {r.optimization_run_id}
          </span>
        </div>
        <p className="text-sm text-slate-500">Recommended charging</p>
        <p className="text-2xl font-semibold text-slate-900">
          {formatWindow(r.window_start, r.window_end)}
        </p>
      </div>

      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            Estimated cost
          </dt>
          <dd className="text-lg font-medium text-slate-900">
            ₹{r.estimated_cost.toFixed(2)}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            Charging price
          </dt>
          <dd className="text-lg font-medium text-slate-900">
            ₹{r.price_per_kwh.toFixed(2)}/kWh
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            Renewable share
          </dt>
          <dd className="text-lg font-medium text-green-700">
            {r.renewable_share_pct.toFixed(0)}%
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            CO2 impact
          </dt>
          <dd className="text-lg font-medium text-slate-900">
            {r.co2_impact_kg.toFixed(1)} kg
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-slate-500">
          Green Score
        </span>
        <div className="h-2 flex-1 rounded-full bg-slate-100">
          {typeof r.green_score === "number" && (
            <div
              className="h-2 rounded-full bg-green-600"
              style={{ width: `${Math.min(Math.max(r.green_score, 0), 100)}%` }}
            />
          )}
        </div>
        <span className="text-sm font-medium text-slate-900">
          {typeof r.green_score === "number" ? r.green_score.toFixed(0) : "—"}
        </span>
      </div>

      <details className="mt-4 rounded-md bg-slate-50 p-3">
        <summary className="cursor-pointer text-sm font-medium text-slate-700">
          Why?
        </summary>
        <p className="mt-2 text-sm text-slate-600">{r.why}</p>
      </details>
    </section>
  );
}
