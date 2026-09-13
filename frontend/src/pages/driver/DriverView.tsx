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
  const {
    session,
    loading: sessionLoading,
    error: sessionError,
    updatePreferences,
  } = useDriverSession();

  const {
    recommendation,
    loading: recommendationLoading,
    error: recommendationError,
    accepted,
    overrideResult,
    accept,
    override,
  } = useDriverRecommendation();

  const [preferenceNote, setPreferenceNote] =
    useState<string | null>(null);

  const sessionActive =
    accepted ||
    (overrideResult?.feasible ?? false);

  const {
    status,
    loading: statusLoading,
    error: statusError,
  } = useDriverSessionStatus(
    sessionActive,
  );

  useEffect(() => {
    if (sessionError) {
      setPreferenceNote(null);
    }
  }, [sessionError]);

  if (sessionLoading) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-7 text-sm text-[#66758B]">
          Loading your Aegis session…
        </div>
      </main>
    );
  }

  if (sessionError || !session) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-2xl border border-[#D9CEC6] bg-[#F8F1ED] p-6 text-sm text-[#6F2C0F]">
          Couldn&apos;t load your session:{" "}
          {sessionError ?? "unknown error"}
        </div>
      </main>
    );
  }

  async function handlePreferenceChange(
    preference: DriverPreference,
  ) {
    const ok =
      await updatePreferences({
        preference,
      });

    if (ok) {
      setPreferenceNote(
        "Preference saved. It will influence the next network optimization.",
      );
    }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-8 px-6 py-10">
      <header>
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
          Aegis / EV driver
        </p>

        <h1 className="aegis-display mt-4 text-5xl font-semibold tracking-[-0.045em] text-[#071A3D] lg:text-6xl">
          Your charging session
        </h1>

        <p className="mt-4 text-base text-[#66758B] lg:text-lg">
          {session.ev_id} ·{" "}
          {session.current_soc.toFixed(
            0,
          )}
          % →{" "}
          {session.target_soc.toFixed(
            0,
          )}
          % · Depart by{" "}
          {new Date(
            session.departure_time,
          ).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}{" "}
          ·{" "}
          {session.flexibility.replace(
            "_",
            " ",
          )}{" "}
          flexibility
        </p>
      </header>

      <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
        <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
          Driver preference
        </p>

        <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
          How would you like to charge?
        </h2>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-[#66758B] lg:text-base">
          This is an advisory input to the next network
          optimization. It never bypasses physical
          constraints.
        </p>

        <div className="mt-8">
          <PreferenceSelector
            value={session.preference}
            onChange={
              handlePreferenceChange
            }
          />
        </div>

        {preferenceNote && (
          <div className="mt-5 rounded-xl border border-[#CFD7E4] bg-[#EEF2F7] p-4 text-sm leading-6 text-[#071A3D]">
            {preferenceNote}
          </div>
        )}
      </section>

      {recommendationError && (
        <div className="rounded-2xl border border-[#E1E6EC] bg-white p-6 text-sm leading-6 text-[#66758B] shadow-[0_8px_24px_rgba(15,36,68,0.04)]">
          {recommendationError.includes(
            "No active optimization schedule",
          )
            ? "No charging recommendation is published yet. The Network Operator needs to apply a schedule first."
            : recommendationError}
        </div>
      )}

      {!recommendationError &&
        recommendationLoading && (
          <div className="rounded-2xl border border-[#E1E6EC] bg-white p-7 text-sm text-[#66758B]">
            Loading recommendation…
          </div>
        )}

      {!recommendationError &&
        !recommendationLoading &&
        recommendation && (
          <>
            <AcceptOverrideActions
              accepted={accepted}
              overrideResult={
                overrideResult
              }
              onAccept={accept}
              onOverride={override}
            />

            <RecommendationCard
              recommendation={
                recommendation
              }
            />
          </>
        )}

      {sessionActive && (
        <SessionStatusPanel
          status={status}
          recommendation={
            recommendation
          }
          loading={statusLoading}
          error={statusError}
        />
      )}
    </main>
  );
}