interface IntelligenceProps {
  title?: string;
  subtitle?: string;
  items: {
    label: string;
    value: string;
    tone?: "navy" | "brown" | "gray" | "soft";
  }[];
  footer?: string;
}

const toneClass = {
  navy: "border-[#CFD7E4] bg-[#EEF2F7]",
  brown: "border-[#D9CEC6] bg-[#F8F1ED]",
  gray: "border-[#E1E5EA] bg-[#F3F5F7]",
  soft: "border-[#E1E5EA] bg-white",
};

function AegisMark() {
  return (
    <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#071A3D] text-xs font-semibold text-white">
      A
    </span>
  );
}

export default function AegisIntelligence({
  title = "Decision trace",
  subtitle = "Signal fusion",
  items,
  footer,
}: IntelligenceProps) {
  return (
    <section className="rounded-2xl border border-[#DEE3E9] bg-white shadow-[0_12px_36px_rgba(15,36,68,0.055)]">
      <div className="p-6 lg:p-8">
        <div className="flex items-start justify-between gap-5">
          <div>
            <div className="flex items-center gap-3">
              <AegisMark />

              <div>
                <p className="aegis-label text-[10px] font-semibold uppercase text-[#6F2C0F]">
                  Aegis Intelligence
                </p>

                <p className="mt-1 text-xs text-[#8893A3]">
                  deterministic · auditable reasoning
                </p>
              </div>
            </div>

            <h2 className="aegis-display mt-6 text-2xl font-semibold tracking-tight text-[#071A3D]">
              {title}
            </h2>

            <p className="mt-2 text-sm text-[#66758B]">
              {subtitle}
            </p>
          </div>

          <span className="rounded-full border border-[#D8DEE8] bg-[#F7F8FA] px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#68758A]">
            No black box
          </span>
        </div>

        <div className="mt-7 grid gap-4 md:grid-cols-3">
          {items.map((item) => (
            <div
              key={item.label}
              className={`rounded-xl border p-5 ${toneClass[item.tone ?? "soft"]}`}
            >
              <p className="aegis-label text-[9px] font-semibold uppercase text-[#8A95A5]">
                {item.label}
              </p>

              <p className="mt-3 text-sm font-semibold leading-6 text-[#142B4D]">
                {item.value}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-2 text-[9px] font-semibold uppercase tracking-[0.1em] text-[#8A95A5]">
          <span className="rounded-full border border-[#D8DEE8] px-3 py-1.5">
            Grid signal
          </span>

          <span>→</span>

          <span className="rounded-full border border-[#D8DEE8] px-3 py-1.5">
            Renewable
          </span>

          <span>→</span>

          <span className="rounded-full border border-[#D8DEE8] px-3 py-1.5">
            EV flexibility
          </span>

          <span>→</span>

          <span className="rounded-full border border-[#D9CEC6] bg-[#F8F1ED] px-3 py-1.5 text-[#6F2C0F]">
            Aegis optimizer
          </span>
        </div>

        {footer && (
          <p className="mt-5 text-sm leading-6 text-[#66758B]">
            {footer}
          </p>
        )}
      </div>
    </section>
  );
}