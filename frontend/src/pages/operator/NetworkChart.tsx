import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import type { NetworkStatusResponse } from "../../types/api";

interface NetworkChartProps {
  status: NetworkStatusResponse;
}

/**
 * design.md SS7/SS9: grid demand vs capacity vs renewable generation
 * vs EV load, in one chart. Uses semantic colors — green for
 * renewable, blue/neutral for informational series (design.md SS3).
 */
export default function NetworkChart({ status }: NetworkChartProps) {
  const data = [
    {
      label: "Current",
      grid_demand: status.grid_demand_kw,
      grid_capacity: status.grid_capacity_kw,
      renewable: status.renewable_generation_kw,
      ev_load: status.ev_load.current_ev_load_kw,
    },
  ];

  return (
    <div className="h-64 w-full rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-2 text-sm font-medium text-slate-700">
        Grid demand vs. capacity vs. renewable vs. EV load
      </p>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" unit=" kW" />
          <YAxis type="category" dataKey="label" hide />
          <Tooltip
            formatter={(value) => {
              const numeric = typeof value === "number" ? value : Number(value ?? 0);
              return `${numeric.toFixed(0)} kW`;
            }}
          />
          <Legend />
          <Bar dataKey="grid_capacity" name="Grid capacity" fill="#94a3b8" />
          <Bar dataKey="grid_demand" name="Grid demand" fill="#3b82f6" />
          <Bar dataKey="renewable" name="Renewable generation" fill="#16a34a" />
          <Bar dataKey="ev_load" name="EV load" fill="#f59e0b" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
