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

import type {
  EnergySlot,
  NetworkStatusResponse,
  OptimizationScheduleResponse,
} from "../../types/api";

interface NetworkChartProps {
  status: NetworkStatusResponse;
  slots: EnergySlot[];
  schedule:
    | OptimizationScheduleResponse
    | null;
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString(
    [],
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

export default function NetworkChart({
  status,
  slots,
  schedule,
}: NetworkChartProps) {
  const loadByTimestamp =
    new Map<string, number>();

  schedule?.entries.forEach((entry) => {
    loadByTimestamp.set(
      entry.timestamp,
      (loadByTimestamp.get(entry.timestamp) ??
        0) + entry.charging_power_kw,
    );
  });

  const data = slots.map((slot) => {
    const evLoad =
      loadByTimestamp.get(slot.timestamp) ??
      0;

    return {
      timestamp: slot.timestamp,
      label: formatTime(slot.timestamp),
      grid_demand:
        slot.base_load_kw + evLoad,
      grid_capacity:
        slot.grid_capacity_kw,
      renewable:
        slot.renewable_kw,
      ev_load: evLoad,
    };
  });

  if (data.length === 0) {
    data.push({
      timestamp:
        new Date().toISOString(),
      label: "Now",
      grid_demand:
        status.grid_demand_kw,
      grid_capacity:
        status.grid_capacity_kw,
      renewable:
        status.renewable_generation_kw,
      ev_load:
        status.ev_load
          .current_ev_load_kw,
    });
  }

  return (
    <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="aegis-display text-2xl font-semibold tracking-tight text-[#071A3D] lg:text-3xl">
            24-hour network energy picture
          </h2>

          <p className="mt-2 text-sm text-[#66758B] lg:text-base">
            EV load is reconstructed from the active
            schedule.
          </p>
        </div>

        <span className="rounded-full border border-[#D8DEE8] bg-[#F7F8FA] px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#68758A]">
          30-min resolution
        </span>
      </div>

      <div className="mt-8 h-[390px] w-full">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <LineChart
            data={data}
            margin={{
              top: 10,
              right: 16,
              left: 0,
              bottom: 8,
            }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#E4E7EB"
            />

            <XAxis
              dataKey="label"
              tick={{
                fontSize: 12,
                fill: "#66758B",
              }}
              minTickGap={28}
              axisLine={{
                stroke: "#CBD2DC",
              }}
            />

            <YAxis
              tick={{
                fontSize: 12,
                fill: "#66758B",
              }}
              unit=" kW"
              axisLine={{
                stroke: "#CBD2DC",
              }}
            />

            <Tooltip
              contentStyle={{
                border:
                  "1px solid #D8DEE8",
                borderRadius: 12,
                background: "#FFFFFF",
              }}
              formatter={(value) =>
                `${Number(value ?? 0).toFixed(
                  0,
                )} kW`
              }
            />

            <Legend
              wrapperStyle={{
                fontSize: 13,
                paddingTop: 10,
              }}
            />

            <Line
              type="monotone"
              dataKey="grid_capacity"
              name="Grid capacity"
              stroke="#8A95A5"
              dot={false}
              strokeWidth={2}
            />

            <Line
              type="monotone"
              dataKey="grid_demand"
              name="Grid demand"
              stroke="#071A3D"
              dot={false}
              strokeWidth={3}
            />

            <Line
              type="monotone"
              dataKey="renewable"
              name="Renewable generation"
              stroke="#6F2C0F"
              dot={false}
              strokeWidth={3}
            />

            <Line
              type="monotone"
              dataKey="ev_load"
              name="EV load"
              stroke="#102A52"
              dot={false}
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}