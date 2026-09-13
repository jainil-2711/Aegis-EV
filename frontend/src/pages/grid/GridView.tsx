import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

import { useGridData } from "../../hooks/useGridData";
import type {
  GridCondition,
  RenewableAvailability,
  SignalOperator,
} from "../../types/api";

import AegisIntelligence from "../../components/AegisIntelligence";
import SourceBadge from "../../components/SourceBadge";

const conditions: GridCondition[] = [
  "normal",
  "high_demand",
  "high_renewable",
  "low_renewable",
];

const conditionLabel: Record<
  GridCondition,
  string
> = {
  normal: "Normal",
  high_demand: "High demand",
  high_renewable: "High renewable",
  low_renewable: "Low renewable",
};

const availabilityLabel: Record<
  RenewableAvailability,
  string
> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

type SourceKind =
  | "simulated"
  | "live_weather"
  | "calculated"
  | "optimized";

function MetricCard({
  label,
  value,
  note,
  source,
}: {
  label: string;
  value: string;
  note?: string;
  source?: SourceKind;
}) {
  return (
    <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_8px_24px_rgba(15,36,68,0.04)]">
      <div className="flex items-start justify-between gap-3">
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#8A95A5]">
          {label}
        </p>

        {source && <SourceBadge kind={source} />}
      </div>

      <p className="mt-4 text-3xl font-semibold tracking-[-0.035em] text-[#071A3D] lg:text-[34px]">
        {value}
      </p>

      {note && (
        <p className="mt-2 text-sm leading-5 text-[#66758B]">
          {note}
        </p>
      )}
    </div>
  );
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDateTimeLocal(value: string) {
  const date = new Date(value);

  const local = new Date(
    date.getTime() -
      date.getTimezoneOffset() * 60000,
  );

  return local.toISOString().slice(0, 16);
}

export default function GridView() {
  const {
    status,
    forecast,
    signals,
    loading,
    error,
    publishSignal,
  } = useGridData();

  const [condition, setCondition] =
    useState<GridCondition>("high_demand");

  const [recommendedLoad, setRecommendedLoad] =
    useState("250");

  const [operator, setOperator] =
    useState<SignalOperator>("lte");

  const [renewable, setRenewable] =
    useState<RenewableAvailability>("medium");

  const [startTime, setStartTime] =
    useState("");

  const [endTime, setEndTime] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const [message, setMessage] =
    useState<string | null>(null);

  const chartData = useMemo(
    () =>
      (forecast?.slots ?? []).map((slot) => ({
        time: formatTime(slot.timestamp),
        demand: slot.base_load_kw,
        renewable: slot.renewable_kw,
        capacity: slot.grid_capacity_kw,
      })),
    [forecast],
  );

  useEffect(() => {
    const first = forecast?.slots?.[0];
    const fifth = forecast?.slots?.[4];

    if (first) {
      setStartTime(
        (current) =>
          current ||
          formatDateTimeLocal(first.timestamp),
      );
    }

    if (fifth) {
      setEndTime(
        (current) =>
          current ||
          formatDateTimeLocal(fifth.timestamp),
      );
    }
  }, [forecast]);

  if (loading) {
    return (
      <main className="mx-auto max-w-[1440px] px-6 py-10 lg:px-10">
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-7 text-sm text-[#66758B]">
          Loading grid state…
        </div>
      </main>
    );
  }

  if (error || !status || !forecast) {
    return (
      <main className="mx-auto max-w-[1440px] px-6 py-10 lg:px-10">
        <div className="rounded-2xl border border-[#D9CEC6] bg-[#F8F1ED] p-6 text-sm text-[#6F2C0F]">
          Couldn&apos;t load grid data:{" "}
          {error ?? "unknown error"}
        </div>
      </main>
    );
  }

  async function handleSubmit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setSubmitting(true);
    setMessage(null);

    try {
      await publishSignal({
        start_time: startTime,
        end_time: endTime,
        condition,
        recommended_ev_load_kw:
          Number(recommendedLoad),
        signal_operator: operator,
        renewable_availability:
          renewable,
      });

      setMessage(
        "Grid signal published successfully.",
      );
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Couldn’t publish signal",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-[1440px] space-y-9 px-6 py-10 lg:px-10 lg:py-12">
      {/* PAGE HEADER */}
      <header>
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
          Aegis / Grid operator
        </p>

        <h1 className="aegis-display mt-4 text-5xl font-semibold tracking-[-0.045em] text-[#071A3D] lg:text-[62px] lg:leading-[1.02]">
          Grid at a glance
        </h1>

        <p className="mt-4 max-w-3xl text-base leading-7 text-[#66758B] lg:text-[18px]">
          Monitor grid conditions and publish advisory
          signals for charging-network optimization.
        </p>
      </header>

      {/* METRICS */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          label="Grid demand"
          value={`${status.grid_demand_kw.toFixed(
            0,
          )} kW`}
          note={`${Math.max(
            0,
            status.grid_demand_kw -
              status.ev_load
                .current_ev_load_kw,
          ).toFixed(0)} base + ${status.ev_load.current_ev_load_kw.toFixed(
            0,
          )} EV`}
          source="calculated"
        />

        <MetricCard
          label="Grid capacity"
          value={`${status.grid_capacity_kw.toFixed(
            0,
          )} kW`}
          source="calculated"
        />

        <MetricCard
          label="Headroom"
          value={`${status.headroom_kw.toFixed(
            0,
          )} kW`}
          note="Available before grid capacity"
          source="calculated"
        />

        <MetricCard
          label="Renewable generation"
          value={`${status.renewable_generation_kw.toFixed(
            0,
          )} kW`}
          source="simulated"
        />

        <MetricCard
          label="Aggregate EV load"
          value={`${status.ev_load.current_ev_load_kw.toFixed(
            0,
          )} kW`}
          note={`Peak ${status.ev_load.peak_ev_load_kw.toFixed(
            0,
          )} kW`}
          source="optimized"
        />
      </section>

      {/* GRID SUMMARY */}
      <section className="grid gap-4 rounded-2xl border border-[#E1E6EC] bg-white p-4 shadow-[0_8px_24px_rgba(15,36,68,0.04)] sm:grid-cols-2 lg:p-5">
        <div className="rounded-xl bg-[#F3F5F7] px-5 py-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-sm font-semibold text-[#253957]">
              Grid demand
            </span>

            <span className="font-mono text-xs text-[#66758B]">
              {Math.max(
                0,
                status.grid_demand_kw -
                  status.ev_load
                    .current_ev_load_kw,
              ).toFixed(0)}{" "}
              base +{" "}
              {status.ev_load.current_ev_load_kw.toFixed(
                0,
              )}{" "}
              EV ={" "}
              {status.grid_demand_kw.toFixed(
                0,
              )}{" "}
              kW
            </span>
          </div>
        </div>

        <div className="rounded-xl bg-[#F3F5F7] px-5 py-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-sm font-semibold text-[#253957]">
              Headroom
            </span>

            <span className="font-mono text-xs text-[#66758B]">
              {status.grid_capacity_kw.toFixed(
                0,
              )}{" "}
              −{" "}
              {status.grid_demand_kw.toFixed(
                0,
              )}{" "}
              ={" "}
              {Math.max(
                0,
                status.grid_capacity_kw -
                  status.grid_demand_kw,
              ).toFixed(0)}{" "}
              kW
            </span>
          </div>
        </div>
      </section>

      {/* 24-HOUR GRAPH */}
      <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
              Network outlook
            </p>

            <h2 className="aegis-display mt-3 text-2xl font-semibold tracking-tight text-[#071A3D] lg:text-3xl">
              24-hour grid outlook
            </h2>

            <p className="mt-2 text-sm text-[#66758B] lg:text-base">
              Forecasted demand, renewable generation,
              and available capacity.
            </p>
          </div>

          <span className="w-fit rounded-full border border-[#D8DEE8] bg-[#F7F8FA] px-3.5 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#68758A]">
            30-minute resolution
          </span>
        </div>

        <div className="mt-8 h-[390px] w-full">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <LineChart
              data={chartData}
              margin={{
                top: 12,
                right: 20,
                left: 4,
                bottom: 14,
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#DDE2E8"
              />

              <XAxis
                dataKey="time"
                interval={3}
                tick={{
                  fontSize: 12,
                  fill: "#66758B",
                }}
                tickLine={{
                  stroke: "#CBD2DC",
                }}
                axisLine={{
                  stroke: "#CBD2DC",
                }}
              />

              <YAxis
                unit=" kW"
                tick={{
                  fontSize: 12,
                  fill: "#66758B",
                }}
                tickLine={{
                  stroke: "#CBD2DC",
                }}
                axisLine={{
                  stroke: "#CBD2DC",
                }}
              />

              <Tooltip
                cursor={{
                  stroke: "#C7CDD6",
                  strokeDasharray: "4 4",
                }}
                contentStyle={{
                  border:
                    "1px solid #D8DEE8",
                  borderRadius: 12,
                  background: "#FFFFFF",
                  boxShadow:
                    "0 10px 25px rgba(15,36,68,0.08)",
                  color: "#071A3D",
                  fontSize: 13,
                }}
                labelStyle={{
                  color: "#071A3D",
                  fontWeight: 600,
                  marginBottom: 6,
                }}
                formatter={(value) =>
                  `${Number(value ?? 0).toFixed(
                    0,
                  )} kW`
                }
              />

              <Legend
                verticalAlign="bottom"
                height={36}
                wrapperStyle={{
                  fontSize: 13,
                  paddingTop: 12,
                }}
              />

              <Line
                type="monotone"
                dataKey="capacity"
                name="Grid capacity"
                stroke="#8A95A5"
                dot={false}
                strokeWidth={2.2}
              />

              <Line
                type="monotone"
                dataKey="demand"
                name="Grid demand"
                stroke="#071A3D"
                dot={false}
                strokeWidth={3.2}
                activeDot={{
                  r: 5,
                  fill: "#071A3D",
                  stroke: "#FFFFFF",
                  strokeWidth: 2,
                }}
              />

              <Line
                type="monotone"
                dataKey="renewable"
                name="Renewable generation"
                stroke="#6F2C0F"
                dot={false}
                strokeWidth={3.2}
                activeDot={{
                  r: 5,
                  fill: "#6F2C0F",
                  stroke: "#FFFFFF",
                  strokeWidth: 2,
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* SIGNAL WORKSPACE */}
      <section className="grid gap-6 xl:grid-cols-[1.12fr_0.88fr]">
        {/* PUBLISH */}
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
          <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
            Grid signal
          </p>

          <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
            Publish advisory signal
          </h2>

          <p className="mt-3 text-sm leading-6 text-[#66758B] lg:text-base">
            Provide quantitative guidance to the network
            optimizer.
          </p>

          <form
            onSubmit={handleSubmit}
            className="mt-8 grid gap-5 sm:grid-cols-2"
          >
            <label className="text-sm font-semibold text-[#253957]">
              Condition

              <select
                value={condition}
                onChange={(e) =>
                  setCondition(
                    e.target
                      .value as GridCondition,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-[#D8DEE8] bg-white px-3.5 text-sm font-medium text-[#253957] outline-none transition focus:border-[#071A3D] focus:ring-4 focus:ring-[#E8EBF0]"
              >
                {conditions.map((value) => (
                  <option
                    key={value}
                    value={value}
                  >
                    {conditionLabel[value]}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm font-semibold text-[#253957]">
              Recommended EV load (kW)

              <input
                type="number"
                min="0"
                step="1"
                value={recommendedLoad}
                onChange={(e) =>
                  setRecommendedLoad(
                    e.target.value,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-[#D8DEE8] bg-white px-3.5 text-sm font-medium text-[#253957] outline-none transition focus:border-[#071A3D] focus:ring-4 focus:ring-[#E8EBF0]"
              />
            </label>

            <label className="text-sm font-semibold text-[#253957]">
              Signal operator

              <select
                value={operator}
                onChange={(e) =>
                  setOperator(
                    e.target
                      .value as SignalOperator,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-[#D8DEE8] bg-white px-3.5 text-sm font-medium text-[#253957] outline-none transition focus:border-[#071A3D] focus:ring-4 focus:ring-[#E8EBF0]"
              >
                <option value="lte">
                  At or below (≤)
                </option>

                <option value="gte">
                  At or above (≥)
                </option>
              </select>
            </label>

            <label className="text-sm font-semibold text-[#253957]">
              Renewable availability

              <select
                value={renewable}
                onChange={(e) =>
                  setRenewable(
                    e.target
                      .value as RenewableAvailability,
                  )
                }
                className="mt-2 h-12 w-full rounded-xl border border-[#D8DEE8] bg-white px-3.5 text-sm font-medium text-[#253957] outline-none transition focus:border-[#071A3D] focus:ring-4 focus:ring-[#E8EBF0]"
              >
                {Object.entries(
                  availabilityLabel,
                ).map(([value, label]) => (
                  <option
                    key={value}
                    value={value}
                  >
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm font-semibold text-[#253957]">
              Start

              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) =>
                  setStartTime(
                    e.target.value,
                  )
                }
                required
                className="mt-2 h-12 w-full rounded-xl border border-[#D8DEE8] bg-white px-3.5 text-sm font-medium text-[#253957] outline-none transition focus:border-[#071A3D] focus:ring-4 focus:ring-[#E8EBF0]"
              />
            </label>

            <label className="text-sm font-semibold text-[#253957]">
              End

              <input
                type="datetime-local"
                value={endTime}
                onChange={(e) =>
                  setEndTime(
                    e.target.value,
                  )
                }
                required
                className="mt-2 h-12 w-full rounded-xl border border-[#D8DEE8] bg-white px-3.5 text-sm font-medium text-[#253957] outline-none transition focus:border-[#071A3D] focus:ring-4 focus:ring-[#E8EBF0]"
              />
            </label>

            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={
                  submitting ||
                  !startTime ||
                  !endTime
                }
                className="rounded-xl bg-[#071A3D] px-6 py-3.5 text-sm font-semibold text-white shadow-sm hover:bg-[#102A52] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting
                  ? "Publishing…"
                  : "Publish signal"}
              </button>

              {message && (
                <p className="mt-3 text-sm text-[#66758B]">
                  {message}
                </p>
              )}
            </div>
          </form>
        </div>

        {/* SIGNAL HISTORY */}
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
          <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
            Published signals
          </p>

          <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
            Latest grid instructions
          </h2>

          <p className="mt-3 text-sm leading-6 text-[#66758B]">
            Advisory signals currently available to
            network optimization.
          </p>

          {signals.length === 0 ? (
            <div className="mt-8 rounded-xl border border-dashed border-[#D8DEE8] bg-[#F7F8FA] p-6 text-sm text-[#66758B]">
              No signals published yet.
            </div>
          ) : (
            <div className="mt-8 space-y-3">
              {signals
                .slice(0, 5)
                .map((signal) => (
                  <div
                    key={signal.id}
                    className="rounded-xl border border-[#E1E6EC] p-5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-[#071A3D]">
                        {
                          conditionLabel[
                            signal.condition
                          ]
                        }
                      </span>

                      <span className="text-xs font-semibold text-[#6F2C0F]">
                        {signal.signal_operator ===
                        "lte"
                          ? "≤"
                          : "≥"}{" "}
                        {signal.recommended_ev_load_kw.toFixed(
                          0,
                        )}{" "}
                        kW
                      </span>
                    </div>

                    <p className="mt-2 text-xs leading-5 text-[#66758B]">
                      {formatTime(
                        signal.start_time,
                      )}{" "}
                      –{" "}
                      {formatTime(
                        signal.end_time,
                      )}{" "}
                      · Renewable{" "}
                      {
                        availabilityLabel[
                          signal
                            .renewable_availability
                        ]
                      }
                    </p>
                  </div>
                ))}
            </div>
          )}
        </div>
      </section>

      {/* INTELLIGENCE */}
      <AegisIntelligence
        title="Grid signal trace"
        subtitle="System context"
        items={[
          {
            label: "Demand",
            value: `${status.grid_demand_kw.toFixed(
              0,
            )} kW of ${status.grid_capacity_kw.toFixed(
              0,
            )} kW capacity`,
            tone: "navy",
          },
          {
            label: "Renewable",
            value: `${status.renewable_generation_kw.toFixed(
              0,
            )} kW available now`,
            tone: "brown",
          },
          {
            label: "Headroom",
            value: `${status.headroom_kw.toFixed(
              0,
            )} kW remaining`,
            tone: "gray",
          },
        ]}
        footer="Aegis translates grid conditions into optimizer inputs. Publishing a signal does not directly control an individual vehicle."
      />

      {/* ENERGY SLOTS */}
      <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
              Grid forecast
            </p>

            <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
              Upcoming energy slots
            </h2>
          </div>

          <SourceBadge kind="simulated" />
        </div>

        <div className="mt-7 overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-[#E3E7EC] text-left">
                {[
                  "Time",
                  "Base demand",
                  "Renewable",
                  "Capacity",
                  "Price",
                  "Carbon",
                ].map((heading) => (
                  <th
                    key={heading}
                    className="px-3 py-4 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#8A95A5]"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {forecast.slots
                .slice(0, 12)
                .map((slot) => (
                  <tr
                    key={slot.timestamp}
                    className="border-b border-[#F0F2F5] last:border-0"
                  >
                    <td className="px-3 py-4 text-sm font-semibold text-[#253957]">
                      {formatTime(
                        slot.timestamp,
                      )}
                    </td>

                    <td className="px-3 py-4 text-sm text-[#66758B]">
                      {slot.base_load_kw.toFixed(
                        0,
                      )}{" "}
                      kW
                    </td>

                    <td className="px-3 py-4 text-sm font-semibold text-[#6F2C0F]">
                      {slot.renewable_kw.toFixed(
                        0,
                      )}{" "}
                      kW
                    </td>

                    <td className="px-3 py-4 text-sm text-[#66758B]">
                      {slot.grid_capacity_kw.toFixed(
                        0,
                      )}{" "}
                      kW
                    </td>

                    <td className="px-3 py-4 text-sm text-[#66758B]">
                      ₹
                      {slot.electricity_price.toFixed(
                        2,
                      )}
                    </td>

                    <td className="px-3 py-4 text-sm text-[#66758B]">
                      {slot.carbon_intensity.toFixed(
                        3,
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}