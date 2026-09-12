import { useState } from "react";
import type {
  OperatorObjective,
  OptimizationRunResponse,
} from "../../types/api";

/**
 * ADAPTER: this panel calls P2's optimization client
 * (frontend/src/services/optimization.ts), which is NOT owned by P4
 * and is not duplicated here (design.md SS4, DEV_WORKFLOWS.md SS2).
 * Assumed exports: runOptimization(mode) and applyOptimization(runId).
 * If P2's real function names differ, adjust only this import line.
 */
import { runOptimization, applyOptimization } from "../../services/optimization";

interface OptimizationPanelProps {
  onApplied: () => void;
}

const MODES: { value: OperatorObjective; label: string }[] = [
  { value: "cheapest", label: "Cheapest" },
  { value: "greenest", label: "Greenest" },
  { value: "balanced", label: "Balanced" },
];

export default function OptimizationPanel({ onApplied }: OptimizationPanelProps) {
  const [mode, setMode] = useState<OperatorObjective>("balanced");
  const [candidate, setCandidate] = useState<OptimizationRunResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await runOptimization({ mode });
      setCandidate(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization run failed");
    } finally {
      setRunning(false);
    }
  };

  const handleApply = async () => {
    if (!candidate) return;
    setApplying(true);
    setError(null);
    try {
      await applyOptimization({ optimization_run_id: candidate.id });
      setCandidate(null);
      onApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply schedule");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm font-medium text-slate-700">
        Optimization mode
      </p>
      <div className="flex gap-2">
        {MODES.map((m) => (
          <button
            key={m.value}
            type="button"
            onClick={() => setMode(m.value)}
            className={[
              "rounded-md border px-3 py-1.5 text-sm font-medium",
              mode === m.value
                ? "border-blue-600 bg-blue-50 text-blue-700"
                : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
            ].join(" ")}
          >
            {m.label}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={running}
        className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
      >
        {running ? "Running optimization..." : "Run optimization"}
      </button>

      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}

      {candidate && (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3">
          <p className="text-sm font-medium text-slate-700">
            Candidate schedule (not yet active)
          </p>
          <dl className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-xs text-slate-500">Peak</dt>
              <dd>
                {candidate.baseline.peak_kw.toFixed(0)} →{" "}
                {candidate.candidate.peak_kw.toFixed(0)} kW
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Cost</dt>
              <dd>
                ₹{candidate.baseline.cost.toFixed(0)} → ₹
                {candidate.candidate.cost.toFixed(0)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Renewable</dt>
              <dd>
                {candidate.baseline.renewable_share_pct.toFixed(0)}% →{" "}
                {candidate.candidate.renewable_share_pct.toFixed(0)}%
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">CO2</dt>
              <dd>
                {candidate.baseline.co2_kg.toFixed(0)} →{" "}
                {candidate.candidate.co2_kg.toFixed(0)} kg
              </dd>
            </div>
          </dl>
          <button
            type="button"
            onClick={handleApply}
            disabled={applying}
            className="mt-3 rounded-md bg-green-700 px-4 py-2 text-sm font-medium text-white hover:bg-green-800 disabled:opacity-60"
          >
            {applying ? "Applying..." : "Apply schedule"}
          </button>
        </div>
      )}
    </div>
  );
}
