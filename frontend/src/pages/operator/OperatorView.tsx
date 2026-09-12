import { useNetworkStatus } from "../../hooks/useNetworkStatus";
import { useNetworkImpact } from "../../hooks/useNetworkImpact";
import { useNetworkForecast } from "../../hooks/useNetworkForecast";
import { useNetworkSchedule } from "../../hooks/useNetworkSchedule";
import NetworkChart from "./NetworkChart";
import OptimizationPanel from "./OptimizationPanel";
import ImpactCard from "./ImpactCard";
import StationsChargersTable from "./StationsChargersTable";
import AegisIntelligence from "../../components/AegisIntelligence";

function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-950">{value}</p>
      {detail && <p className="mt-1 text-[11px] text-slate-500">{detail}</p>}
    </div>
  );
}

export default function OperatorView() {
  const { status, stations, chargers, loading, error, refetch } = useNetworkStatus();
  const { impact, loading: impactLoading, error: impactError, refetch: refetchImpact } = useNetworkImpact();
  const { slots } = useNetworkForecast();
  const { schedule, refetch: refetchSchedule } = useNetworkSchedule();

  if (loading || !status) return <div className="p-8 text-sm text-slate-500">Loading Aegis network state…</div>;
  if (error) return <div className="p-8 text-sm text-red-700">Couldn't load network state: {error}</div>;

  const handleApplied = () => {
    void refetch();
    void refetchImpact();
    void refetchSchedule();
  };

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-600">Aegis / Network control</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Charging network command center</h1>
        <p className="mt-1 text-sm text-slate-500">One operational state: network telemetry → optimization → publish → impact.</p>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <MetricCard label="Connected EVs" value={String(status.active_evs)} />
        <MetricCard label="Chargers active" value={String(status.active_chargers)} />
        <MetricCard label="Current EV load" value={`${status.ev_load.current_ev_load_kw.toFixed(0)} kW`} />
        <MetricCard label="Peak EV load" value={`${status.ev_load.peak_ev_load_kw.toFixed(0)} kW`} />
        <MetricCard label="Renewable now" value={`${status.renewable_availability_pct.toFixed(0)}%`} detail="Share of current grid demand" />
      </div>

      <NetworkChart status={status} slots={slots} schedule={schedule} />
      <OptimizationPanel onApplied={handleApplied} />
      {schedule && (
        <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-4 text-sm text-cyan-900">
          <span className="font-semibold">Active application:</span> {schedule.optimization_run_id} · every role view consumes this published schedule.
        </div>
      )}

      <AegisIntelligence
        title="Network reading"
        items={[
          { label: "Grid headroom", value: `${Math.max(0, status.grid_capacity_kw - status.grid_demand_kw).toFixed(0)} kW available`, tone: "cyan" },
          { label: "Renewable", value: `${status.renewable_generation_kw.toFixed(0)} kW available now`, tone: "green" },
          { label: "Operating state", value: status.ev_load.scheduled_ev_load_kw > 0 ? "Published schedule in play" : "No active EV schedule", tone: "amber" },
        ]}
        footer="This trace is explanatory only. Aegis's numeric decisions remain inside the deterministic optimizer."
      />

      {!impactError && !impactLoading && impact && <ImpactCard impact={impact} />}
      {impactError && <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">{impactError.includes("No optimization run available yet") ? "Publish a schedule to see before/after network impact." : impactError}</div>}
      <StationsChargersTable stations={stations} chargers={chargers} />
    </main>
  );
}
