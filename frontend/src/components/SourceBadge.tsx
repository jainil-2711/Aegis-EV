/**
 * Aegis — Source/provenance badge.
 */

export type SourceKind =
  | "simulated"
  | "live_weather"
  | "calculated"
  | "optimized";

const SOURCE_LABEL: Record<SourceKind, string> = {
  simulated: "SIMULATED DEMO FEED",
  live_weather: "LIVE WEATHER-DERIVED ESTIMATE",
  calculated: "AEGIS CALCULATED",
  optimized: "AEGIS OPTIMIZED",
};

const SOURCE_CLASS: Record<SourceKind, string> = {
  simulated:
    "border-[#D9CEC6] bg-[#F8F1ED] text-[#6F2C0F]",
  live_weather:
    "border-[#D9CEC6] bg-[#F8F1ED] text-[#6F2C0F]",
  calculated:
    "border-[#D8DEE8] bg-[#F7F8FA] text-[#43516A]",
  optimized:
    "border-[#C6CFDC] bg-[#EEF2F7] text-[#071A3D]",
};

interface SourceBadgeProps {
  kind: SourceKind;
  className?: string;
}

export default function SourceBadge({
  kind,
  className = "",
}: SourceBadgeProps) {
  return (
    <span
      className={[
        "inline-flex whitespace-nowrap rounded-full border px-2.5 py-1",
        "text-[9px] font-semibold uppercase tracking-[0.12em]",
        SOURCE_CLASS[kind],
        className,
      ].join(" ")}
    >
      {SOURCE_LABEL[kind]}
    </span>
  );
}