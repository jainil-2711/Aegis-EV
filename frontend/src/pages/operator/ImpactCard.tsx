import type {
  NetworkImpactResponse,
} from "../../types/api";

import SourceBadge from "../../components/SourceBadge";

interface ImpactCardProps {
  impact: NetworkImpactResponse;
}

interface RowProps {
  label: string;
  before: number;
  after: number;
  unit: string;
  higherIsBetter?: boolean;
  prefix?: string;
}

function formatValue(
  value: number,
  prefix = "",
  unit = "",
) {
  return `${prefix}${value.toLocaleString(
    "en-IN",
    {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    },
  )}${unit}`;
}

function Row({
  label,
  before,
  after,
  unit,
  higherIsBetter = false,
  prefix = "",
}: RowProps) {
  const difference = after - before;

  const improved = higherIsBetter
    ? difference > 0.0001
    : difference < -0.0001;

  const worse = higherIsBetter
    ? difference < -0.0001
    : difference > 0.0001;

  return (
    <div className="grid gap-3 border-t border-[#EEF1F4] py-5 sm:grid-cols-[1fr_auto] sm:items-center">
      <span className="text-sm font-medium text-[#43516A]">
        {label}
      </span>

      <div className="flex items-center gap-2 text-sm">
        <span className="text-[#8A95A5]">
          {formatValue(
            before,
            prefix,
            unit,
          )}
        </span>

        <span className="text-[#B1B8C4]">
          →
        </span>

        <span className="font-semibold text-[#071A3D]">
          {formatValue(
            after,
            prefix,
            unit,
          )}
        </span>

        <span
          className={[
            "rounded-full px-2.5 py-1 text-[9px] font-semibold uppercase tracking-wide",
            improved
              ? "bg-[#EEF2F7] text-[#071A3D]"
              : worse
                ? "bg-[#F8F1ED] text-[#6F2C0F]"
                : "bg-[#F3F5F7] text-[#66758B]",
          ].join(" ")}
        >
          {improved
            ? "better"
            : worse
              ? "trade-off"
              : "flat"}
        </span>
      </div>
    </div>
  );
}

export default function ImpactCard({
  impact,
}: ImpactCardProps) {
  return (
    <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
            Measured impact
          </p>

          <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
            Baseline → active schedule
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#66758B]">
            Before = deterministic baseline. After = the
            currently active applied schedule.
          </p>
        </div>

        <div className="flex flex-wrap gap-2 sm:flex-col sm:items-end">
          <SourceBadge kind="optimized" />

          <span className="rounded-full border border-[#D8DEE8] bg-[#F7F8FA] px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#68758A]">
            Active run{" "}
            {impact.active_optimization_run_id}
          </span>
        </div>
      </div>

      <div className="mt-6">
        <Row
          label="Peak EV load"
          before={impact.peak_load_kw.before}
          after={impact.peak_load_kw.after}
          unit=" kW"
        />

        <Row
          label="Cost"
          before={impact.cost.before}
          after={impact.cost.after}
          unit=""
          prefix="₹"
        />

        <Row
          label="Renewable share"
          before={
            impact.renewable_share_pct.before
          }
          after={
            impact.renewable_share_pct.after
          }
          unit="%"
          higherIsBetter
        />

        <Row
          label="CO₂ impact"
          before={impact.co2_kg.before}
          after={impact.co2_kg.after}
          unit=" kg"
        />
      </div>

      <div className="mt-6 rounded-2xl border border-[#D9CEC6] bg-[#F8F1ED] p-6">
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
          Pricing guardrails
        </p>

        <p className="mt-2 text-sm leading-6 text-[#43516A]">
          Base{" "}
          {impact.pricing_rule.base_rate.toFixed(
            2,
          )}{" "}
          {impact.pricing_rule.currency}/kWh · bounded tiers.
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {impact.pricing_rule.tiers.map(
            (tier) => (
              <span
                key={tier.condition}
                className="rounded-full border border-[#D9CEC6] bg-white px-3 py-1.5 text-xs font-medium text-[#6F2C0F]"
              >
                {tier.condition.replace(
                  "_",
                  " ",
                )}{" "}
                ·{" "}
                {tier.price_per_kwh.toFixed(
                  2,
                )}
              </span>
            ),
          )}
        </div>
      </div>
    </section>
  );
}