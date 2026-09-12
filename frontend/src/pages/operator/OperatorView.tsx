import { useNetworkStatus } from "../../hooks/useNetworkStatus";
import { useNetworkImpact } from "../../hooks/useNetworkImpact";

import NetworkChart from "./NetworkChart";
import OptimizationPanel from "./OptimizationPanel";
import ImpactCard from "./ImpactCard";
import StationsChargersTable from "./StationsChargersTable";

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function OperatorView() {
  const { status, stations, chargers, loading, error, refetch } =
    useNetworkStatus();
  const { impact, loading: impactLoading, error: impactError, refetch: refetchImpact } =
    useNetworkImpact();

  if (loading) {
    return <div className="p-6 text-sm text-slate-500">Loading network state...</div>;
  }

  if (error || !status) {
    return (
      <div className="p-6 text-sm text-red-700">
        Couldn't load network status: {error ?? "unknown error"}
      </div>
    );
  }

  const handleApplied = () => {
    refetch();
    refetchImpact();
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">
          Charging network overview
        </h1>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <MetricCard label="Active EVs" value={String(status.active_evs)} />
        <MetricCard label="Active chargers" value={String(status.active_chargers)} />
        <MetricCard
          label="Current EV load"
          value={`${status.ev_load.current_ev_load_kw.toFixed(0)} kW`}
        />
        <MetricCard
          label="Peak EV load"
          value={`${status.ev_load.peak_ev_load_kw.toFixed(0)} kW`}
        />
        <MetricCard
          label="Renewable availability"
          value={`${status.renewable_availability_pct.toFixed(0)}%`}
        />
      </div>

      <NetworkChart status={status} />

      <OptimizationPanel onApplied={handleApplied} />

      {!impactError && !impactLoading && impact && <ImpactCard impact={impact} />}
      {impactError && (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
          {impactError.includes("No optimization run available yet")
            ? "Apply an optimization schedule to see network impact."
            : impactError}
        </div>
      )}

      <StationsChargersTable stations={stations} chargers={chargers} />
    </div>
  );
}
