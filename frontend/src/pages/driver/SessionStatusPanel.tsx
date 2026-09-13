import type {
  DriverRecommendationResponse,
  DriverSessionStatusResponse,
} from "../../types/api";

interface Props {
  status:
    | DriverSessionStatusResponse
    | null;
  recommendation:
    | DriverRecommendationResponse
    | null;
  loading: boolean;
  error: string | null;
}

const STATUS_LABEL: Record<
  string,
  string
> = {
  pending: "Pending",
  scheduled: "Scheduled",
  charging: "Charging now",
  completed: "Completed",
  cancelled: "Cancelled",
};

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString(
    [],
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function statusMessage(
  status: DriverSessionStatusResponse,
  recommendation:
    | DriverRecommendationResponse
    | null,
) {
  switch (status.status) {
    case "scheduled":
      return recommendation
        ? `Waiting for your charging window · starts at ${formatTime(
            recommendation.window_start,
          )}`
        : "Waiting for your charging window.";

    case "charging":
      return "Your scheduled charging window is active.";

    case "completed":
      return "The scheduled charging window has completed.";

    case "cancelled":
      return "This charging session was cancelled.";

    default:
      return "Charging session is ready for the next action.";
  }
}

export default function SessionStatusPanel({
  status,
  recommendation,
  loading,
  error,
}: Props) {
  if (error) {
    return (
      <section className="rounded-2xl border border-[#D9CEC6] bg-[#F8F1ED] p-5 text-sm leading-6 text-[#6F2C0F]">
        Couldn&apos;t refresh session status:{" "}
        {error}
      </section>
    );
  }

  if (!status) {
    return (
      <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 text-sm text-[#66758B] shadow-[0_8px_24px_rgba(15,36,68,0.04)]">
        {loading
          ? "Loading session status…"
          : "No active session yet."}
      </section>
    );
  }

  const isScheduled =
    status.status === "scheduled";

  const isCharging =
    status.status === "charging";

  const hasTelemetry =
    isCharging ||
    status.cost_so_far > 0 ||
    status.co2_kg_so_far > 0 ||
    status.charging_power_kw > 0;

  const renewableValue = hasTelemetry
    ? `${status.renewable_share_pct.toFixed(
        0,
      )}%`
    : "—";

  const gridValue = hasTelemetry
    ? `${status.grid_share_pct.toFixed(
        0,
      )}%`
    : "—";

  return (
    <section className="rounded-2xl border border-[#E1E6EC] bg-white p-6 shadow-[0_10px_28px_rgba(15,36,68,0.045)] lg:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span
          className={[
            "rounded-full border px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.12em]",
            isCharging
              ? "border-[#BFC9D8] bg-[#EEF2F7] text-[#071A3D]"
              : "border-[#D8DEE8] bg-[#F7F8FA] text-[#66758B]",
          ].join(" ")}
        >
          {STATUS_LABEL[
            status.status
          ] ?? status.status}
        </span>

        <span className="rounded-full border border-[#D9CEC6] bg-[#F8F1ED] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F2C0F]">
          Simulated data
        </span>
      </div>

      <p className="mt-5 text-base leading-7 text-[#43516A]">
        {statusMessage(
          status,
          recommendation,
        )}
      </p>

      {isScheduled &&
        recommendation && (
          <div className="mt-5 rounded-xl border border-[#CFD7E4] bg-[#EEF2F7] p-4 text-sm text-[#071A3D]">
            Charging window:{" "}
            <span className="font-semibold">
              {formatTime(
                recommendation.window_start,
              )}{" "}
              –{" "}
              {formatTime(
                recommendation.window_end,
              )}
            </span>
          </div>
        )}

      <div className="mt-8">
        <div className="flex items-center justify-between">
          <span className="aegis-label text-[10px] font-semibold uppercase text-[#8A95A5]">
            State of charge
          </span>

          <span className="text-base font-semibold text-[#071A3D]">
            {status.current_soc.toFixed(
              0,
            )}
            %
          </span>
        </div>

        <div className="mt-3 h-3 overflow-hidden rounded-full bg-[#E4E8EE]">
          <div
            className="h-full rounded-full bg-[#071A3D] transition-all"
            style={{
              width: `${Math.min(
                Math.max(
                  status.current_soc,
                  0,
                ),
                100,
              )}%`,
            }}
          />
        </div>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div className="rounded-xl bg-[#F3F5F7] p-5">
          <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
            Charging power
          </p>

          <p className="mt-2 text-lg font-semibold text-[#071A3D]">
            {status.charging_power_kw.toFixed(
              1,
            )}{" "}
            kW
          </p>
        </div>

        <div className="rounded-xl bg-[#F3F5F7] p-5">
          <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
            Renewable / Grid
          </p>

          <p className="mt-2 text-lg font-semibold text-[#071A3D]">
            {renewableValue}{" "}
            <span className="text-[#8A95A5]">
              /
            </span>{" "}
            {gridValue}
          </p>
        </div>

        <div className="rounded-xl bg-[#F3F5F7] p-5">
          <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
            Cost so far
          </p>

          <p className="mt-2 text-lg font-semibold text-[#071A3D]">
            ₹
            {status.cost_so_far.toFixed(
              2,
            )}
          </p>
        </div>

        <div className="rounded-xl bg-[#F3F5F7] p-5">
          <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
            CO₂ so far
          </p>

          <p className="mt-2 text-lg font-semibold text-[#071A3D]">
            {status.co2_kg_so_far.toFixed(
              1,
            )}{" "}
            kg
          </p>
        </div>

        <div className="rounded-xl border border-[#D9CEC6] bg-[#F8F1ED] p-5">
          <p className="aegis-label text-[9px] font-semibold uppercase text-[#6F2C0F]">
            Green score
          </p>

          <p className="mt-2 text-lg font-semibold text-[#6F2C0F]">
            {typeof status.green_score ===
            "number"
              ? status.green_score.toFixed(
                  0,
                )
              : "Not yet calculated"}
          </p>
        </div>
      </div>
    </section>
  );
}