import { useState } from "react";

import type {
  ScheduleOverrideRequest,
  ScheduleOverrideResponse,
} from "../../types/api";

interface AcceptOverrideActionsProps {
  accepted: boolean;
  overrideResult:
    | ScheduleOverrideResponse
    | null;
  onAccept: () => void;
  onOverride: (
    req: ScheduleOverrideRequest,
  ) => void;
}

export default function AcceptOverrideActions({
  accepted,
  overrideResult,
  onAccept,
  onOverride,
}: AcceptOverrideActionsProps) {
  const [
    showOverrideForm,
    setShowOverrideForm,
  ] = useState(false);

  const [
    requestedPower,
    setRequestedPower,
  ] = useState("");

  function handleOverrideSubmit() {
    onOverride({
      requested_power_kw:
        requestedPower
          ? Number(requestedPower)
          : undefined,
      reason:
        "Driver requested to charge now",
    });

    setShowOverrideForm(false);
  }

  return (
    <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
      <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
        Driver decision
      </p>

      <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
        Choose what happens next
      </h2>

      <p className="mt-2 text-sm leading-6 text-[#66758B] lg:text-base">
        Accept the network recommendation or
        request charging now.
      </p>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={onAccept}
          className="rounded-xl bg-[#071A3D] px-5 py-3.5 text-sm font-semibold text-white hover:bg-[#102A52]"
        >
          Accept recommendation
        </button>

        <button
          type="button"
          onClick={() =>
            setShowOverrideForm(
              (current) => !current,
            )
          }
          className="rounded-xl border border-[#D8DEE8] bg-white px-5 py-3.5 text-sm font-semibold text-[#253957] hover:bg-[#F7F8FA]"
        >
          {showOverrideForm
            ? "Close override"
            : "Override / Charge now"}
        </button>
      </div>

      {showOverrideForm && (
        <div className="mt-5 rounded-2xl border border-[#E1E6EC] bg-[#F7F8FA] p-5">
          <label className="block text-sm font-semibold text-[#253957]">
            Requested power (kW), optional

            <input
              type="number"
              min="0"
              step="0.1"
              value={requestedPower}
              onChange={(e) =>
                setRequestedPower(
                  e.target.value,
                )
              }
              placeholder="e.g. 22"
              className="mt-2 h-12 w-full max-w-xs rounded-xl border border-[#D8DEE8] bg-white px-3 text-sm outline-none focus:border-[#071A3D] focus:ring-4 focus:ring-[#EEF2F7]"
            />
          </label>

          <button
            type="button"
            onClick={
              handleOverrideSubmit
            }
            className="mt-4 rounded-xl bg-[#071A3D] px-4 py-3 text-sm font-semibold text-white hover:bg-[#102A52]"
          >
            Confirm override
          </button>
        </div>
      )}

      {accepted && (
        <div className="mt-5 rounded-xl border border-[#CFD7E4] bg-[#EEF2F7] px-4 py-3 text-sm font-medium text-[#071A3D]">
          Recommendation accepted.
        </div>
      )}

      {overrideResult &&
        !overrideResult.feasible && (
          <div className="mt-5 rounded-xl border border-[#D9CEC6] bg-[#F8F1ED] p-5">
            <p className="text-sm font-semibold text-[#6F2C0F]">
              That charging request isn&apos;t
              possible right now.
            </p>

            {overrideResult.explanation && (
              <p className="mt-2 text-sm leading-6 text-[#6F2C0F]">
                {
                  overrideResult.explanation
                }
              </p>
            )}

            {overrideResult.alternatives &&
              overrideResult.alternatives
                .length > 0 && (
                <ul className="mt-3 space-y-1.5 pl-5 text-sm text-[#6F2C0F]">
                  {overrideResult.alternatives.map(
                    (alternative) => (
                      <li
                        key={alternative}
                      >
                        {alternative}
                      </li>
                    ),
                  )}
                </ul>
              )}
          </div>
        )}

      {overrideResult &&
        overrideResult.feasible && (
          <div className="mt-5 rounded-xl border border-[#CFD7E4] bg-[#EEF2F7] px-4 py-3 text-sm font-medium text-[#071A3D]">
            Charging now, as requested. No
            fees or access changes apply.
          </div>
        )}
    </section>
  );
}