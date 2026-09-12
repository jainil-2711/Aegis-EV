import type { DriverPreference } from "../../types/api";

interface PreferenceSelectorProps {
  value: DriverPreference;
  onChange: (preference: DriverPreference) => void;
  disabled?: boolean;
}

const OPTIONS: { value: DriverPreference; label: string }[] = [
  { value: "cheapest", label: "Cheapest" },
  { value: "greenest", label: "Greenest" },
  { value: "balanced", label: "Balanced" },
  { value: "immediate", label: "Immediate" },
];

export default function PreferenceSelector({
  value,
  onChange,
  disabled,
}: PreferenceSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Charging preference">
      {OPTIONS.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() => onChange(opt.value)}
            className={[
              "rounded-md border px-3 py-1.5 text-sm font-medium transition-colors",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
              active
                ? "border-blue-600 bg-blue-50 text-blue-700"
                : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
              disabled ? "cursor-not-allowed opacity-60" : "",
            ].join(" ")}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
