import type {
  DriverRecommendationResponse,
} from "../../types/api";

import AegisIntelligence from "../../components/AegisIntelligence";

interface RecommendationCardProps {
  recommendation: DriverRecommendationResponse;
}

function formatWindow(
  startIso: string,
  endIso: string,
) {
  const start = new Date(startIso);
  const end = new Date(endIso);

  const format = (date: Date) =>
    date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  return `${format(start)} – ${format(end)}`;
}

export default function RecommendationCard({
  recommendation: r,
}: RecommendationCardProps) {
  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
              Active network schedule
            </p>

            <p className="mt-2 text-sm text-[#66758B]">
              Published by Network Operator ·{" "}
              {r.optimization_run_id}
            </p>
          </div>

          <span className="w-fit rounded-full border border-[#BFC9D8] bg-[#EEF2F7] px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#071A3D]">
            Operator published
          </span>
        </div>

        <p className="aegis-label mt-9 text-[10px] font-semibold uppercase text-[#8A95A5]">
          Recommended charging window
        </p>

        <p className="aegis-display mt-3 text-5xl font-semibold tracking-[-0.05em] text-[#071A3D] lg:text-6xl">
          {formatWindow(
            r.window_start,
            r.window_end,
          )}
        </p>

        <div className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div className="rounded-xl bg-[#F3F5F7] p-5">
            <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
              Estimated cost
            </p>

            <p className="mt-2 text-xl font-semibold text-[#071A3D]">
              ₹{r.estimated_cost.toFixed(
                2,
              )}
            </p>
          </div>

          <div className="rounded-xl bg-[#F3F5F7] p-5">
            <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
              Charging price
            </p>

            <p className="mt-2 text-xl font-semibold text-[#071A3D]">
              ₹{r.price_per_kwh.toFixed(
                2,
              )}
              /kWh
            </p>
          </div>

          <div className="rounded-xl border border-[#D9CEC6] bg-[#F8F1ED] p-5">
            <p className="aegis-label text-[9px] font-semibold uppercase text-[#6F2C0F]">
              Renewable
            </p>

            <p className="mt-2 text-xl font-semibold text-[#6F2C0F]">
              {r.renewable_share_pct.toFixed(
                0,
              )}
              %
            </p>
          </div>

          <div className="rounded-xl bg-[#F3F5F7] p-5">
            <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
              CO₂ impact
            </p>

            <p className="mt-2 text-xl font-semibold text-[#071A3D]">
              {r.co2_impact_kg.toFixed(
                1,
              )}{" "}
              kg
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-[#E1E6EC] bg-[#F7F8FA] p-5">
          <div className="flex items-center justify-between gap-3">
            <span className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
              Green Score
            </span>

            <span className="text-sm font-semibold text-[#071A3D]">
              {typeof r.green_score ===
              "number"
                ? `${r.green_score.toFixed(
                    0,
                  )} / 100`
                : "Unavailable"}
            </span>
          </div>

          <div className="mt-3 h-3 overflow-hidden rounded-full bg-[#DDE2E9]">
            <div
              className="h-full rounded-full bg-[#071A3D]"
              style={{
                width: `${Math.min(
                  Math.max(
                    r.green_score ?? 0,
                    0,
                  ),
                  100,
                )}%`,
              }}
            />
          </div>

          <p className="mt-3 text-xs leading-5 text-[#66758B]">
            Informational only — it never
            changes access, priority, or
            price.
          </p>
        </div>

        <details className="mt-5 rounded-xl border border-[#E1E6EC] bg-white p-5">
          <summary className="cursor-pointer text-sm font-semibold text-[#071A3D]">
            Why this window?
          </summary>

          <p className="mt-3 text-sm leading-6 text-[#66758B]">
            {r.why}
          </p>
        </details>
      </div>

      <AegisIntelligence
        title="Driver decision trace"
        subtitle="How the published recommendation reaches you"
        items={[
          {
            label: "Source",
            value: `Active run ${r.optimization_run_id}`,
            tone: "navy",
          },
          {
            label: "Renewable alignment",
            value: `${r.renewable_share_pct.toFixed(
              0,
            )}% of scheduled energy`,
            tone: "brown",
          },
          {
            label: "Preference",
            value:
              "Your saved preference is advisory to the next network optimization",
            tone: "gray",
          },
        ]}
        footer="Aegis explains a network-published recommendation. You remain free to accept it or charge now."
      />
    </section>
  );
}