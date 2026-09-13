import type {
  DriverPreference,
} from "../../types/api";

interface PreferenceSelectorProps {
  value: DriverPreference;
  onChange: (
    preference: DriverPreference,
  ) => void;
  disabled?: boolean;
}

const OPTIONS: {
  value: DriverPreference;
  label: string;
  description: string;
}[] = [
  {
    value: "cheapest",
    label: "Cheapest",
    description: "Lower modeled cost",
  },
  {
    value: "greenest",
    label: "Greenest",
    description: "Cleaner energy",
  },
  {
    value: "balanced",
    label: "Balanced",
    description: "Trade off objectives",
  },
  {
    value: "immediate",
    label: "Immediate",
    description: "Charge sooner",
  },
];

export default function PreferenceSelector({
  value,
  onChange,
  disabled,
}: PreferenceSelectorProps) {
  return (
    <div
      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      role="radiogroup"
      aria-label="Charging preference"
    >
      {OPTIONS.map((option) => {
        const active =
          option.value === value;

        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() =>
              onChange(
                option.value,
              )
            }
            className={[
              "min-h-[122px] rounded-2xl border p-6 text-left",
              "focus:outline-none focus-visible:ring-4 focus-visible:ring-[#EEF2F7]",
              active
                ? "border-[#BFC9D8] bg-[#EEF2F7]"
                : "border-[#E1E6EC] bg-white hover:bg-[#F7F8FA]",
              disabled
                ? "cursor-not-allowed opacity-60"
                : "",
            ].join(" ")}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-base font-semibold text-[#071A3D]">
                {option.label}
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
              {option.description}
            </p>
          </button>
        );
      })}
    </div>
  );
}