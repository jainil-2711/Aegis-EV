import type {
  StationsResponse,
  ChargersResponse,
} from "../../types/api";

interface StationsChargersTableProps {
  stations: StationsResponse["stations"];
  chargers: ChargersResponse["chargers"];
}

const STATUS_CLASS: Record<
  string,
  string
> = {
  available:
    "border-[#CCD7E5] bg-[#EEF2F7] text-[#071A3D]",
  occupied:
    "border-[#D9CEC6] bg-[#F8F1ED] text-[#6F2C0F]",
  offline:
    "border-[#E1E6EC] bg-[#F3F5F7] text-[#66758B]",
  maintenance:
    "border-[#D8DEE8] bg-white text-[#43516A]",
};

export default function StationsChargersTable({
  stations,
  chargers,
}: StationsChargersTableProps) {
  return (
    <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
      <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
        Infrastructure
      </p>

      <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
        Stations & chargers
      </h2>

      <p className="mt-2 text-sm leading-6 text-[#66758B]">
        Current charging infrastructure status.
      </p>

      <div className="mt-8 space-y-5">
        {stations.map((station) => {
          const stationChargers =
            chargers.filter(
              (charger) =>
                charger.station_id ===
                station.id,
            );

          return (
            <div
              key={station.id}
              className="rounded-2xl border border-[#E1E6EC] bg-[#F7F8FA] p-6"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-base font-semibold text-[#071A3D]">
                    {station.name}
                  </p>

                  <p className="mt-1 text-xs text-[#8A95A5]">
                    {station.id}
                  </p>
                </div>

                <p className="text-sm text-[#66758B]">
                  {station.capacity_kw.toFixed(
                    0,
                  )}{" "}
                  kW ·{" "}
                  {station.charger_count}{" "}
                  chargers
                </p>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {stationChargers.map(
                  (charger) => (
                    <span
                      key={charger.id}
                      title={`${charger.connector_type} · ${charger.max_power_kw} kW`}
                      className={[
                        "rounded-full border px-3 py-1.5 text-xs font-medium",
                        STATUS_CLASS[
                          charger.status
                        ] ??
                          "border-[#D8DEE8] bg-white text-[#43516A]",
                      ].join(" ")}
                    >
                      {charger.id}
                    </span>
                  ),
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}