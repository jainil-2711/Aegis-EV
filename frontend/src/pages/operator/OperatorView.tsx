import { useNetworkStatus } from "../../hooks/useNetworkStatus";
import { useNetworkImpact } from "../../hooks/useNetworkImpact";
import { useNetworkForecast } from "../../hooks/useNetworkForecast";
import { useNetworkSchedule } from "../../hooks/useNetworkSchedule";

import NetworkChart from "./NetworkChart";
import OptimizationPanel from "./OptimizationPanel";
import ImpactCard from "./ImpactCard";
import StationsChargersTable from "./StationsChargersTable";

import AegisIntelligence from "../../components/AegisIntelligence";
import SourceBadge from "../../components/SourceBadge";

function MetricCard({
  label,
  value,
  detail,
  source,
}: {
  label: string;
  value: string;
  detail?: string;
  source?:
    | "simulated"
    | "live_weather"
    | "calculated"
    | "optimized";
}) {
  return (
    <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_8px_24px_rgba(15,36,68,0.04)]">
      <div className="flex items-start justify-between gap-3">
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#8A95A5]">
          {label}
        </p>

        {source && (
          <SourceBadge kind={source} />
        )}
      </div>

      <p className="mt-4 text-3xl font-semibold tracking-[-0.035em] text-[#071A3D]">
        {value}
      </p>

      {detail && (
        <p className="mt-2 text-sm leading-5 text-[#66758B]">
          {detail}
        </p>
      )}
    </div>
  );
}

export default function OperatorView() {
  const {
    status,
    stations,
    chargers,
    loading,
    error,
    refetch,
  } = useNetworkStatus();

  const {
    impact,
    loading: impactLoading,
    error: impactError,
    refetch: refetchImpact,
  } = useNetworkImpact();

  const { slots } =
    useNetworkForecast();

  const {
    schedule,
    refetch: refetchSchedule,
  } = useNetworkSchedule();

  if (loading || !status) {
    return (
      <main className="mx-auto max-w-[1440px] px-6 py-10 lg:px-10">
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-7 text-sm text-[#66758B]">
          Loading network state…
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto max-w-[1440px] px-6 py-10 lg:px-10">
        <div className="rounded-2xl border border-[#D9CEC6] bg-[#F8F1ED] p-6 text-sm text-[#6F2C0F]">
          Couldn&apos;t load network state:{" "}
          {error}
        </div>
      </main>
    );
  }

  function handleApplied() {
    void refetch();
    void refetchImpact();
    void refetchSchedule();
  }

  return (
    <main className="mx-auto max-w-[1440px] space-y-8 px-6 py-10 lg:px-10">
      <header>
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
          Aegis / Network operator
        </p>

        <h1 className="aegis-display mt-4 text-5xl font-semibold tracking-[-0.045em] text-[#071A3D] lg:text-6xl">
          Charging network command center
        </h1>

        <p className="mt-4 max-w-3xl text-base leading-7 text-[#66758B] lg:text-lg">
          One operational state: network telemetry →
          optimization → publish → measured impact.
        </p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          label="Connected EVs"
          value={String(
            status.active_evs,
          )}
          source="calculated"
        />

        <MetricCard
          label="Chargers active"
          value={String(
            status.active_chargers,
          )}
          source="calculated"
        />

        <MetricCard
          label="Current EV load"
          value={`${status.ev_load.current_ev_load_kw.toFixed(
            0,
          )} kW`}
          source="optimized"
        />

        <MetricCard
          label="Peak EV load"
          value={`${status.ev_load.peak_ev_load_kw.toFixed(
            0,
          )} kW`}
          source="optimized"
        />

        <MetricCard
          label="Renewable coverage"
          value={`${status.renewable_availability_pct.toFixed(
            0,
          )}%`}
          detail="Renewable generation ÷ grid demand"
          source="simulated"
        />
      </section>

      <section className="grid gap-4 rounded-2xl border border-[#E1E6EC] bg-white p-4 shadow-[0_8px_24px_rgba(15,36,68,0.04)] sm:grid-cols-2">
        <div className="rounded-xl bg-[#F3F5F7] px-5 py-4">
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

        <div className="rounded-xl bg-[#F3F5F7] px-5 py-4">
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

      <NetworkChart
        status={status}
        slots={slots}
        schedule={schedule}
      />

      <OptimizationPanel
        onApplied={handleApplied}
      />

      {schedule && (
        <div className="rounded-2xl border border-[#CFD7E4] bg-[#EEF2F7] p-5 text-sm text-[#071A3D]">
          <span className="font-semibold">
            Active application:
          </span>{" "}
          {schedule.optimization_run_id} · every role view
          consumes this published schedule.
        </div>
      )}

      <AegisIntelligence
        title="Network reading"
        subtitle="Operational context"
        items={[
          {
            label: "Grid headroom",
            value: `${Math.max(
              0,
              status.grid_capacity_kw -
                status.grid_demand_kw,
            ).toFixed(0)} kW available`,
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
            label: "Operating state",
            value:
              status.ev_load
                .scheduled_ev_load_kw >
              0
                ? "Published schedule in play"
                : "No active EV schedule",
            tone: "gray",
          },
        ]}
        footer="This explanation layer is informational. Charging decisions remain inside the deterministic optimizer."
      />

      {!impactError &&
        !impactLoading &&
        impact && (
          <ImpactCard impact={impact} />
        )}

      {impactError && (
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 text-sm text-[#66758B] shadow-[0_8px_24px_rgba(15,36,68,0.04)]">
          {impactError}
        </div>
      )}

      <StationsChargersTable
        stations={stations}
        chargers={chargers}
      />
    </main>
  );
}