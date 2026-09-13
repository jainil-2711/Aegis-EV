/**
 * Aegis — Source/provenance badge (P4 Task 3)
 *
 * Every displayed number should be honest about where it came from.
 * Today the repository's renewable/base-demand numbers come from the
 * deterministic synthetic generator (no live weather feed is wired into
 * the data flow yet), so "live" is never used for those values here.
 * When a live weather-derived path is wired in (see
 * backend/app/data/external/open_meteo.py), switch that call site's
 * `kind` prop to "live_weather" — no other file needs to change.
 */

export type SourceKind = "simulated" | "live_weather" | "calculated" | "optimized";

const SOURCE_LABEL: Record<SourceKind, string> = {
  simulated: "SIMULATED DEMO FEED",
  live_weather: "LIVE WEATHER-DERIVED ESTIMATE",
  calculated: "AEGIS CALCULATED",
  optimized: "AEGIS OPTIMIZED",
};

const SOURCE_CLASS: Record<SourceKind, string> = {
  simulated: "border-amber-200 bg-amber-50 text-amber-700",
  live_weather: "border-emerald-200 bg-emerald-50 text-emerald-700",
  calculated: "border-slate-200 bg-slate-50 text-slate-600",
  optimized: "border-cyan-200 bg-cyan-50 text-cyan-700",
};

interface SourceBadgeProps {
  kind: SourceKind;
  className?: string;
}

export default function SourceBadge({ kind, className = "" }: SourceBadgeProps) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${SOURCE_CLASS[kind]} ${className}`}
    >
      {SOURCE_LABEL[kind]}
    </span>
  );
}
