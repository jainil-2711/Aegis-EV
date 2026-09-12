import type { StationsResponse, ChargersResponse } from "../../types/api";

interface StationsChargersTableProps {
  stations: StationsResponse["stations"];
  chargers: ChargersResponse["chargers"];
}

const STATUS_COLOR: Record<string, string> = {
  available: "bg-green-100 text-green-800",
  occupied: "bg-blue-100 text-blue-800",
  offline: "bg-slate-100 text-slate-600",
  maintenance: "bg-amber-100 text-amber-800",
};

export default function StationsChargersTable({
  stations,
  chargers,
}: StationsChargersTableProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm font-medium text-slate-700">
        Stations & chargers
      </p>
      <div className="space-y-4">
        {stations.map((station) => {
          const stationChargers = chargers.filter(
            (c) => c.station_id === station.id
          );
          return (
            <div key={station.id} className="border-t border-slate-100 pt-3 first:border-t-0 first:pt-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-900">{station.name}</p>
                <p className="text-xs text-slate-500">
                  {station.capacity_kw.toFixed(0)} kW capacity ·{" "}
                  {station.charger_count} chargers
                </p>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {stationChargers.map((c) => (
                  <span
                    key={c.id}
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      STATUS_COLOR[c.status] ?? "bg-slate-100 text-slate-600"
                    }`}
                    title={`${c.connector_type} · ${c.max_power_kw} kW`}
                  >
                    {c.id}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
