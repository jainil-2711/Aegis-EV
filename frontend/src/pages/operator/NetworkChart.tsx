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
import type { EnergySlot, NetworkStatusResponse, OptimizationScheduleResponse } from "../../types/api";

interface NetworkChartProps {
  status: NetworkStatusResponse;
  slots: EnergySlot[];
  schedule: OptimizationScheduleResponse | null;
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function NetworkChart({ status, slots, schedule }: NetworkChartProps) {
  const loadByTimestamp = new Map<string, number>();
  schedule?.entries.forEach((entry) => {
    loadByTimestamp.set(entry.timestamp, (loadByTimestamp.get(entry.timestamp) ?? 0) + entry.charging_power_kw);
  });

  const data = slots.map((slot) => {
    const evLoad = loadByTimestamp.get(slot.timestamp) ?? 0;
    return {
      timestamp: slot.timestamp,
      label: formatTime(slot.timestamp),
      grid_demand: slot.base_load_kw + evLoad,
      grid_capacity: slot.grid_capacity_kw,
      renewable: slot.renewable_kw,
      ev_load: evLoad,
    };
  });

  if (data.length === 0) {
    data.push({
      timestamp: new Date().toISOString(),
      label: "Now",
      grid_demand: status.grid_demand_kw,
      grid_capacity: status.grid_capacity_kw,
      renewable: status.renewable_generation_kw,
      ev_load: status.ev_load.current_ev_load_kw,
    });
  }

  return (
    <div className="h-80 w-full rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-800">24-hour network energy picture</p>
          <p className="mt-1 text-xs text-slate-500">The EV line is reconstructed from the active schedule, not a flat snapshot.</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">30-min resolution</span>
      </div>
      <ResponsiveContainer width="100%" height="84%">
        <LineChart data={data} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={28} />
          <YAxis tick={{ fontSize: 11 }} unit=" kW" />
          <Tooltip formatter={(value) => `${Number(value ?? 0).toFixed(0)} kW`} labelFormatter={(label) => `Time: ${label}`} />
          <Legend />
          <Line type="monotone" dataKey="grid_capacity" name="Grid capacity" stroke="#94a3b8" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="grid_demand" name="Grid demand" stroke="#3b82f6" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="renewable" name="Renewable generation" stroke="#16a34a" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="ev_load" name="EV load" stroke="#f59e0b" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
