import { useDriverSession } from "../../hooks/useDriverSession";
import { useDriverRecommendation } from "../../hooks/useDriverRecommendation";
import { useDriverSessionStatus } from "../../hooks/useDriverSessionStatus";

import PreferenceSelector from "./PreferenceSelector";
import RecommendationCard from "./RecommendationCard";
import AcceptOverrideActions from "./AcceptOverrideActions";
import SessionStatusPanel from "./SessionStatusPanel";

export default function DriverView() {
  const {
    session,
    loading: sessionLoading,
    error: sessionError,
    updatePreferences,
  } = useDriverSession();

  const {
    recommendation,
    loading: recLoading,
    error: recError,
    accepted,
    overrideResult,
    accept,
    override,
  } = useDriverRecommendation();

  const sessionActive = accepted || (overrideResult?.feasible ?? false);

  const { status, loading: statusLoading, error: statusError } =
    useDriverSessionStatus(sessionActive);

  if (sessionLoading) {
    return <div className="p-6 text-sm text-slate-500">Loading your session...</div>;
  }

  if (sessionError || !session) {
    return (
      <div className="p-6 text-sm text-red-700">
        Couldn't load your session: {sessionError ?? "unknown error"}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">
          Your charging session — {session.ev_id}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {session.current_soc.toFixed(0)}% → {session.target_soc.toFixed(0)}%
          {" · "}
          Depart by{" "}
          {new Date(session.departure_time).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </header>

      <section>
        <p className="mb-2 text-sm font-medium text-slate-700">
          Charging preference
        </p>
        <PreferenceSelector
          value={session.preference}
          onChange={(preference) => updatePreferences({ preference })}
        />
      </section>

      {recError && (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
          {recError.includes("No active optimization schedule")
            ? "No charging recommendation is available yet. The network operator needs to apply an optimization schedule first."
            : recError}
        </div>
      )}

      {!recError && recLoading && (
        <div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-500">
          Loading recommendation...
        </div>
      )}

      {!recError && !recLoading && recommendation && (
        <div>
          <RecommendationCard recommendation={recommendation} />
          <AcceptOverrideActions
            accepted={accepted}
            overrideResult={overrideResult}
            onAccept={accept}
            onOverride={override}
          />
        </div>
      )}

      {sessionActive && (
        <SessionStatusPanel
          status={status}
          recommendation={recommendation}
          loading={statusLoading}
          error={statusError}
        />
      )}
    </div>
  );
}
