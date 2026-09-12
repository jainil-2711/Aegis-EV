import { useState } from "react";
import type {
  ScheduleOverrideRequest,
  ScheduleOverrideResponse,
} from "../../types/api";

interface AcceptOverrideActionsProps {
  accepted: boolean;
  overrideResult: ScheduleOverrideResponse | null;
  onAccept: () => void;
  onOverride: (req: ScheduleOverrideRequest) => void;
}

export default function AcceptOverrideActions({
  accepted,
  overrideResult,
  onAccept,
  onOverride,
}: AcceptOverrideActionsProps) {
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [requestedPower, setRequestedPower] = useState("");

  const handleOverrideSubmit = () => {
    onOverride({
      requested_power_kw: requestedPower ? Number(requestedPower) : undefined,
      reason: "Driver requested to charge now",
    });
    setShowOverrideForm(false);
  };

  return (
    <div className="mt-4 space-y-3">
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onAccept}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          Accept recommendation
        </button>
        <button
          type="button"
          onClick={() => setShowOverrideForm((s) => !s)}
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          Override / Charge now
        </button>
      </div>

      {/* Overriding is never framed as a penalty — plain, neutral copy only. */}
      {showOverrideForm && (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
          <label className="block text-sm text-slate-700">
            Requested power (kW), optional
            <input
              type="number"
              value={requestedPower}
              onChange={(e) => setRequestedPower(e.target.value)}
              className="mt-1 block w-40 rounded-md border border-slate-300 px-2 py-1 text-sm"
              placeholder="e.g. 22"
            />
          </label>
          <button
            type="button"
            onClick={handleOverrideSubmit}
            className="mt-3 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-900"
          >
            Confirm override
          </button>
        </div>
      )}

      {accepted && (
        <p className="text-sm text-green-700">Recommendation accepted.</p>
      )}

      {overrideResult && !overrideResult.feasible && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
          <p className="text-sm font-medium text-amber-800">
            That charging request isn't possible right now.
          </p>
          {overrideResult.explanation && (
            <p className="mt-1 text-sm text-amber-700">
              {overrideResult.explanation}
            </p>
          )}
          {overrideResult.alternatives && overrideResult.alternatives.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-sm text-amber-700">
              {overrideResult.alternatives.map((alt) => (
                <li key={alt}>{alt}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {overrideResult && overrideResult.feasible && (
        <p className="text-sm text-slate-700">
          Charging now, as requested. No fees or access changes apply.
        </p>
      )}
    </div>
  );
}
