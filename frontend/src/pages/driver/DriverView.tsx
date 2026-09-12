import { useEffect, useState } from "react";
import { useDriverSession } from "../../hooks/useDriverSession";
import type { DriverPreference } from "../../types/api";
import { useDriverRecommendation } from "../../hooks/useDriverRecommendation";
import { useDriverSessionStatus } from "../../hooks/useDriverSessionStatus";
import PreferenceSelector from "./PreferenceSelector";
import RecommendationCard from "./RecommendationCard";
import AcceptOverrideActions from "./AcceptOverrideActions";
import SessionStatusPanel from "./SessionStatusPanel";

export default function DriverView() {
  const { session, loading: sessionLoading, error: sessionError, updatePreferences } = useDriverSession();
  const { recommendation, loading: recLoading, error: recError, accepted, overrideResult, accept, override } = useDriverRecommendation();
  const [preferenceNote, setPreferenceNote] = useState<string | null>(null);
  const sessionActive = accepted || (overrideResult?.feasible ?? false);
  const { status, loading: statusLoading, error: statusError } = useDriverSessionStatus(sessionActive);

  useEffect(() => {
    if (sessionError) setPreferenceNote(null);
  }, [sessionError]);

  if (sessionLoading) return <div className="p-8 text-sm text-slate-500">Loading your Aegis session…</div>;
  if (sessionError || !session) return <div className="p-8 text-sm text-red-700">Couldn't load your session: {sessionError ?? "unknown error"}</div>;

  async function handlePreferenceChange(preference: DriverPreference) {
    await updatePreferences({ preference });
    setPreferenceNote("Preference saved. The active schedule remains operator-controlled; a new optimization run can use this preference.");
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-600">Aegis / Driver cockpit</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Your charging session — {session.ev_id}</h1>
        <p className="mt-1 text-sm text-slate-500">{session.current_soc.toFixed(0)}% → {session.target_soc.toFixed(0)}% · Depart by {new Date(session.departure_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · {session.flexibility.replace("_", " ")} flexibility</p>
      </header>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm font-semibold text-slate-800">Your charging preference</p>
        <p className="mt-1 text-xs text-slate-500">This preference is an advisory input to the next operator optimization. It never bypasses physical constraints.</p>
        <div className="mt-4"><PreferenceSelector value={session.preference} onChange={handlePreferenceChange} /></div>
        {preferenceNote && <p className="mt-3 rounded-lg border border-cyan-100 bg-cyan-50 p-3 text-xs text-cyan-800">{preferenceNote}</p>}
      </section>

      {recError && <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">{recError.includes("No active optimization schedule") ? "No charging recommendation is published yet. The Network Operator needs to apply a schedule first." : recError}</div>}
      {!recError && recLoading && <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500 shadow-sm">Loading recommendation…</div>}
      {!recError && !recLoading && recommendation && <AcceptOverrideActions accepted={accepted} overrideResult={overrideResult} onAccept={accept} onOverride={override} />}
      {!recError && !recLoading && recommendation && <RecommendationCard recommendation={recommendation} />}

      {sessionActive && <SessionStatusPanel status={status} recommendation={recommendation} loading={statusLoading} error={statusError} />}
    </main>
  );
}
