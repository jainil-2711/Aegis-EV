import { useState } from "react";
import type { OperatorObjective, OptimizationRunResponse, Scenario } from "../../types/api";
import { runOptimization, applyOptimization } from "../../services/optimization";
import AegisIntelligence from "../../components/AegisIntelligence";

interface OptimizationPanelProps { onApplied: () => void; }

const MODES: { value: OperatorObjective; label: string; hint: string }[] = [
  { value: "cheapest", label: "Cheapest", hint: "Prefer lower electricity cost" },
  { value: "greenest", label: "Greenest", hint: "Prefer cleaner energy and lower carbon" },
  { value: "balanced", label: "Balanced", hint: "Trade off cost, carbon and timing" },
];

const SCENARIOS: { value: Scenario; label: string }[] = [
  { value: "normal", label: "Normal" },
  { value: "high_demand", label: "High demand" },
  { value: "high_renewable", label: "High renewable" },
  { value: "low_renewable", label: "Low renewable" },
];

function delta(before: number, after: number) {
  return after - before;
}

export default function OptimizationPanel({ onApplied }: OptimizationPanelProps) {
  const [mode, setMode] = useState<OperatorObjective>("balanced");
  const [scenario, setScenario] = useState<Scenario>("normal");
  const [candidate, setCandidate] = useState<OptimizationRunResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await runOptimization({ mode, scenario });
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
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Orchestration lens</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Optimization workspace</h2>
          <p className="mt-1 text-xs text-slate-500">The selected mode and scenario are sent together to the canonical optimizer.</p>
        </div>
        <label className="text-sm font-medium text-slate-700">
          Scenario
          <select value={scenario} onChange={(e) => setScenario(e.target.value as Scenario)} className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm">
            {SCENARIOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        {MODES.map((item) => (
          <button key={item.value} type="button" onClick={() => setMode(item.value)} className={`rounded-xl border p-3 text-left transition ${mode === item.value ? "border-cyan-500 bg-cyan-50" : "border-slate-200 bg-white hover:bg-slate-50"}`}>
            <div className="flex items-center justify-between"><span className="text-sm font-semibold text-slate-800">{item.label}</span><span className={`h-2 w-2 rounded-full ${mode === item.value ? "bg-cyan-500" : "bg-slate-300"}`} /></div>
            <p className="mt-1 text-xs text-slate-500">{item.hint}</p>
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span className="rounded-full bg-slate-100 px-2.5 py-1">Mode: <strong className="text-slate-700">{mode}</strong></span>
        <span className="rounded-full bg-slate-100 px-2.5 py-1">Scenario: <strong className="text-slate-700">{scenario}</strong></span>
      </div>

      <button type="button" onClick={handleRun} disabled={running} className="mt-4 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
        {running ? "Computing schedule…" : `Run ${mode} optimization`}
      </button>

      {error && <p className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {candidate && (
        <div className="mt-5 space-y-4">
          <div className="rounded-xl border border-cyan-100 bg-cyan-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-cyan-700">Candidate schedule</p>
                <p className="mt-1 text-sm font-medium text-slate-800">Not active until you publish it</p>
              </div>
              <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-cyan-800">{candidate.id}</span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["Peak", `${candidate.baseline.peak_kw.toFixed(1)} → ${candidate.candidate.peak_kw.toFixed(1)} kW`],
                ["Cost", `₹${candidate.baseline.cost.toFixed(0)} → ₹${candidate.candidate.cost.toFixed(0)}`],
                ["Renewable", `${candidate.baseline.renewable_share_pct.toFixed(1)}% → ${candidate.candidate.renewable_share_pct.toFixed(1)}%`],
                ["CO₂", `${candidate.baseline.co2_kg.toFixed(1)} → ${candidate.candidate.co2_kg.toFixed(1)} kg`],
              ].map(([label, value]) => <div key={label}><p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold text-slate-900">{value}</p></div>)}
            </div>
            <button type="button" onClick={handleApply} disabled={applying} className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">{applying ? "Publishing…" : "Publish as active schedule"}</button>
          </div>
          <AegisIntelligence
            title="Decision trace"
            items={[
              { label: "Operator objective", value: mode === "greenest" ? "Carbon + renewable alignment" : mode === "cheapest" ? "Cost-sensitive scheduling" : "Multi-objective trade-off", tone: "cyan" },
              { label: "Scenario", value: SCENARIOS.find((s) => s.value === scenario)?.label ?? scenario, tone: "amber" },
              { label: "Outcome", value: `${delta(candidate.baseline.cost, candidate.candidate.cost) <= 0 ? "Lower" : "Higher"} modeled cost vs baseline`, tone: "green" },
            ]}
            footer="Aegis Intelligence explains the deterministic optimizer output. It never chooses charging power or overrides physical constraints."
          />
        </div>
      )}
    </section>
  );
}
