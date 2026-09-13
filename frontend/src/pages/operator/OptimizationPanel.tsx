import { useState } from "react";
import type {
  OperatorObjective,
  OptimizationRunResponse,
  Scenario,
} from "../../types/api";

import {
  runOptimization,
  applyOptimization,
} from "../../services/optimization";

import AegisIntelligence from "../../components/AegisIntelligence";

interface OptimizationPanelProps {
  onApplied: () => void;
}

const MODES: {
  value: OperatorObjective;
  label: string;
  hint: string;
}[] = [
  {
    value: "cheapest",
    label: "Cheapest",
    hint: "Prefer lower electricity cost",
  },
  {
    value: "greenest",
    label: "Greenest",
    hint: "Prefer cleaner energy and lower carbon",
  },
  {
    value: "balanced",
    label: "Balanced",
    hint: "Trade off cost, carbon and timing",
  },
];

const SCENARIOS: {
  value: Scenario;
  label: string;
}[] = [
  {
    value: "normal",
    label: "Normal",
  },
  {
    value: "high_demand",
    label: "High demand",
  },
  {
    value: "high_renewable",
    label: "High renewable",
  },
  {
    value: "low_renewable",
    label: "Low renewable",
  },
];

export default function OptimizationPanel({
  onApplied,
}: OptimizationPanelProps) {
  const [mode, setMode] =
    useState<OperatorObjective>(
      "balanced",
    );

  const [scenario, setScenario] =
    useState<Scenario>("normal");

  const [candidate, setCandidate] =
    useState<OptimizationRunResponse | null>(
      null,
    );

  const [running, setRunning] =
    useState(false);

  const [applying, setApplying] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  async function handleRun() {
    setRunning(true);
    setError(null);

    try {
      const result =
        await runOptimization({
          mode,
          scenario,
        });

      setCandidate(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Optimization run failed",
      );
    } finally {
      setRunning(false);
    }
  }

  async function handleApply() {
    if (!candidate) {
      return;
    }

    setApplying(true);
    setError(null);

    try {
      await applyOptimization({
        optimization_run_id:
          candidate.id,
      });

      setCandidate(null);
      onApplied();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to apply schedule",
      );
    } finally {
      setApplying(false);
    }
  }

  return (
    <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
            Orchestration
          </p>

          <h2 className="aegis-display mt-3 text-3xl font-semibold tracking-tight text-[#071A3D]">
            Optimization workspace
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#66758B] lg:text-base">
            Select the operating objective and scenario
            sent to the canonical optimizer.
          </p>
        </div>

        <label className="text-sm font-semibold text-[#253957]">
          Scenario

          <select
            value={scenario}
            onChange={(e) =>
              setScenario(
                e.target.value as Scenario,
              )
            }
            className="ml-2 h-11 rounded-xl border border-[#D8DEE8] bg-white px-3 text-sm font-medium outline-none focus:border-[#071A3D] focus:ring-4 focus:ring-[#EEF2F7]"
          >
            {SCENARIOS.map((item) => (
              <option
                key={item.value}
                value={item.value}
              >
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {MODES.map((item) => {
          const active =
            mode === item.value;

          return (
            <button
              key={item.value}
              type="button"
              onClick={() =>
                setMode(item.value)
              }
              className={[
                "rounded-2xl border p-6 text-left",
                active
                  ? "border-[#BFC9D8] bg-[#EEF2F7]"
                  : "border-[#E1E6EC] bg-white hover:bg-[#F7F8FA]",
              ].join(" ")}
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold text-[#071A3D]">
                  {item.label}
                </span>

                <span
                  className={[
                    "h-3 w-3 rounded-full",
                    active
                      ? "bg-[#071A3D]"
                      : "bg-[#C8CFDA]",
                  ].join(" ")}
                />
              </div>

              <p className="mt-2 text-sm leading-5 text-[#66758B]">
                {item.hint}
              </p>
            </button>
          );
        })}
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <span className="rounded-full border border-[#D8DEE8] bg-[#F7F8FA] px-3 py-1.5 text-xs font-medium text-[#43516A]">
          Mode:{" "}
          <strong className="text-[#071A3D]">
            {mode}
          </strong>
        </span>

        <span className="rounded-full border border-[#D8DEE8] bg-[#F7F8FA] px-3 py-1.5 text-xs font-medium text-[#43516A]">
          Scenario:{" "}
          <strong className="text-[#071A3D]">
            {scenario}
          </strong>
        </span>
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={running}
        className="mt-6 rounded-xl bg-[#071A3D] px-5 py-3 text-sm font-semibold text-white hover:bg-[#102A52] disabled:opacity-60"
      >
        {running
          ? "Computing schedule…"
          : `Run ${mode} optimization`}
      </button>

      {error && (
        <div className="mt-5 rounded-xl border border-[#D9CEC6] bg-[#F8F1ED] p-4 text-sm text-[#6F2C0F]">
          {error}
        </div>
      )}

      {candidate && (
        <div className="mt-7 space-y-5">
          <div className="rounded-2xl border border-[#CFD7E4] bg-[#EEF2F7] p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
                  Candidate schedule
                </p>

                <p className="mt-2 text-sm font-medium text-[#253957]">
                  Not active until you publish it
                </p>
              </div>

              <span className="w-fit rounded-full border border-[#D0D8E4] bg-white px-3 py-1.5 text-[10px] font-semibold text-[#071A3D]">
                {candidate.id}
              </span>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-5 lg:grid-cols-4">
              <div>
                <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
                  Peak
                </p>

                <p className="mt-2 text-base font-semibold text-[#071A3D]">
                  {candidate.baseline.peak_kw.toFixed(
                    1,
                  )}{" "}
                  →{" "}
                  {candidate.candidate.peak_kw.toFixed(
                    1,
                  )}{" "}
                  kW
                </p>
              </div>

              <div>
                <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
                  Cost
                </p>

                <p className="mt-2 text-base font-semibold text-[#071A3D]">
                  ₹
                  {candidate.baseline.cost.toFixed(
                    0,
                  )}{" "}
                  → ₹
                  {candidate.candidate.cost.toFixed(
                    0,
                  )}
                </p>
              </div>

              <div>
                <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
                  Renewable
                </p>

                <p className="mt-2 text-base font-semibold text-[#071A3D]">
                  {candidate.baseline.renewable_share_pct.toFixed(
                    1,
                  )}
                  % →{" "}
                  {candidate.candidate.renewable_share_pct.toFixed(
                    1,
                  )}
                  %
                </p>
              </div>

              <div>
                <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
                  CO₂
                </p>

                <p className="mt-2 text-base font-semibold text-[#071A3D]">
                  {candidate.baseline.co2_kg.toFixed(
                    1,
                  )}{" "}
                  →{" "}
                  {candidate.candidate.co2_kg.toFixed(
                    1,
                  )}{" "}
                  kg
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleApply}
              disabled={applying}
              className="mt-6 rounded-xl bg-[#071A3D] px-5 py-3 text-sm font-semibold text-white hover:bg-[#102A52] disabled:opacity-60"
            >
              {applying
                ? "Publishing…"
                : "Publish as active schedule"}
            </button>
          </div>

          <AegisIntelligence
            title="Decision trace"
            subtitle="Optimization rationale"
            items={[
              {
                label: "Operator objective",
                value:
                  mode === "greenest"
                    ? "Carbon + renewable alignment"
                    : mode === "cheapest"
                      ? "Cost-sensitive scheduling"
                      : "Multi-objective trade-off",
                tone: "navy",
              },
              {
                label: "Scenario",
                value:
                  SCENARIOS.find(
                    (item) =>
                      item.value ===
                      scenario,
                  )?.label ?? scenario,
                tone: "brown",
              },
              {
                label: "Outcome",
                value:
                  candidate.candidate.cost <=
                  candidate.baseline.cost
                    ? "Lower modeled cost vs baseline"
                    : "Higher modeled cost vs baseline",
                tone: "gray",
              },
            ]}
            footer="Aegis Intelligence explains the deterministic optimizer output. It never violates the system's hard physical constraints."
          />
        </div>
      )}
    </section>
  );
}