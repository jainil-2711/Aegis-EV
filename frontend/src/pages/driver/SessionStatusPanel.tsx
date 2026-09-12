import type { DriverRecommendationResponse, DriverSessionStatusResponse } from "../../types/api";

interface Props {
  status: DriverSessionStatusResponse | null;
  recommendation: DriverRecommendationResponse | null;
  loading: boolean;
  error: string | null;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "Pending",
  scheduled: "Scheduled",
  charging: "Charging now",
  completed: "Completed",
  cancelled: "Cancelled",
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusMessage(
  status: DriverSessionStatusResponse,
  recommendation: DriverRecommendationResponse | null,
): string {
  switch (status.status) {
    case "scheduled":
      return recommendation
        ? `Waiting for your charging window · starts at ${formatTime(recommendation.window_start)}`
        : "Waiting for your charging window.";
    case "charging":
      return "Your scheduled charging window is active.";
    case "completed":
      return "The scheduled charging window has completed.";
    case "cancelled":
      return "This charging session was cancelled.";
    default:
      return "Charging session is ready for the next action.";
  }
}

export default function SessionStatusPanel({
  status,
  recommendation,
  loading,
  error,
}: Props) {
  if (error) {
    return (
      <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Couldn't refresh session status: {error}
      </section>
    );
  }

  if (!status) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
        {loading ? "Loading session status..." : "No active session yet."}
      </section>
    );
  }

  const isScheduled = status.status === "scheduled";
  const hasEnergy = status.cost_so_far > 0 || status.co2_kg_so_far > 0 || status.charging_power_kw > 0;
  const renewableValue = hasEnergy ? `${status.renewable_share_pct.toFixed(0)}%` : "—";
  const gridValue = hasEnergy ? `${status.grid_share_pct.toFixed(0)}%` : "—";

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
          {STATUS_LABEL[status.status] ?? status.status}
        </span>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
          SIMULATED DATA
        </span>
      </div>

      <p className="mb-4 text-sm text-slate-600">
        {statusMessage(status, recommendation)}
      </p>

      {isScheduled && recommendation && (
        <div className="mb-4 rounded-md border border-blue-100 bg-blue-50 p-3 text-sm text-blue-800">
          Charging window: <span className="font-medium">
            {formatTime(recommendation.window_start)} – {formatTime(recommendation.window_end)}
          </span>
        </div>
      )}

      <div className="mb-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">State of charge</p>
        <div className="mt-1 h-3 w-full rounded-full bg-slate-100">
          <div
            className="h-3 rounded-full bg-blue-600 transition-all"
            style={{ width: `${Math.min(Math.max(status.current_soc, 0), 100)}%` }}
          />
        </div>
        <p className="mt-1 text-sm text-slate-700">{status.current_soc.toFixed(0)}%</p>
      </div>

      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Charging power</dt>
          <dd className="text-base font-medium text-slate-900">{status.charging_power_kw.toFixed(1)} kW</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Renewable / Grid</dt>
          <dd className="text-base font-medium text-slate-900"><span className="text-green-700">{renewableValue}</span> / {gridValue}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Cost so far</dt>
          <dd className="text-base font-medium text-slate-900">₹{status.cost_so_far.toFixed(2)}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">CO₂ so far</dt>
          <dd className="text-base font-medium text-slate-900">{status.co2_kg_so_far.toFixed(1)} kg</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Green Score</dt>
          <dd className="text-base font-medium text-slate-900">{typeof status.green_score === "number" ? status.green_score.toFixed(0) : "Not yet calculated"}</dd>
        </div>
      </dl>
    </section>
  );
}
