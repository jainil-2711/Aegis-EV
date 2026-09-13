import { FormEvent, useState } from "react";
import { useAuth } from "../hooks/useAuth";

type DemoRole = "grid_operator" | "network_operator" | "ev_driver";

const DEMOS: Record<
  DemoRole,
  {
    label: string;
    email: string;
    password: string;
    description: string;
  }
> = {
  grid_operator: {
    label: "Grid Operator",
    email: "grid@aegis.local",
    password: "AegisGrid26!",
    description: "Monitor grid & publish signals",
  },
  network_operator: {
    label: "Network Operator",
    email: "network@aegis.local",
    password: "AegisNet26!",
    description: "Optimize & manage charging",
  },
  ev_driver: {
    label: "EV Driver",
    email: "driver@aegis.local",
    password: "AegisDriver26!",
    description: "View schedule & manage charging",
  },
};

function MailIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <rect x="3" y="5" width="18" height="14" rx="2.5" />
      <path d="m4 7 8 6 8-6" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <rect x="5" y="10" width="14" height="10" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        className="h-5 w-5"
        aria-hidden="true"
      >
        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
        <circle cx="12" cy="12" r="2.5" />
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path d="m3 3 18 18" />
      <path d="M10.6 6.2A10.7 10.7 0 0 1 12 6c6 0 9.5 6 9.5 6a16.4 16.4 0 0 1-3.2 3.7" />
      <path d="M6.3 9.1C4.1 10.4 2.5 12 2.5 12s3.5 6 9.5 6a10 10 0 0 0 2.4-.3" />
    </svg>
  );
}

function LeafIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path d="M19.8 4.2C13 4.4 7.7 7 6.1 11.2c-1.3 3.5.8 6.1 3.9 6.4 4.6.5 8.2-4.4 9.8-13.4Z" />
      <path d="M5 20c2.2-4.3 5.3-7.2 10-9.7" />
    </svg>
  );
}

function GridIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <path d="m13.2 2.8-7 10h5.1l-1.3 8.4 7.8-11h-5.2l.6-7.4Z" />
    </svg>
  );
}

function NetworkIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <circle cx="6" cy="17" r="2.4" />
      <circle cx="18" cy="7" r="2.4" />
      <circle cx="18" cy="17" r="2.4" />
      <path d="m8.1 15.7 7.7-7.4M8.5 17H15.5" />
    </svg>
  );
}

function CarIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <path d="M5.2 16.5h13.6l1-4.8-2.1-4.2H6.3L4.2 11.7l1 4.8Z" />
      <path d="M7.1 7.5 8.4 4.8h7.2l1.3 2.7" />
      <circle cx="7.5" cy="17.2" r="1.5" />
      <circle cx="16.5" cy="17.2" r="1.5" />
    </svg>
  );
}

function ChargerDecoration() {
  return (
    <svg
      viewBox="0 0 340 340"
      fill="none"
      className="h-full w-full"
      aria-hidden="true"
    >
      <rect
        x="20"
        y="74"
        width="82"
        height="190"
        rx="24"
        fill="currentColor"
        opacity="0.08"
      />
      <rect
        x="34"
        y="95"
        width="54"
        height="116"
        rx="16"
        fill="currentColor"
        opacity="0.12"
      />
      <rect
        x="45"
        y="112"
        width="32"
        height="66"
        rx="12"
        fill="currentColor"
        opacity="0.14"
      />
      <path
        d="M61 122 49 148h13l-4 18 15-24H60l1-20Z"
        fill="currentColor"
        opacity="0.35"
      />
      <path
        d="M102 174c64-25 116-14 164 31"
        stroke="currentColor"
        strokeWidth="6"
        strokeLinecap="round"
        opacity="0.1"
      />
      <path
        d="M152 228c24 15 47 18 81 8"
        stroke="currentColor"
        strokeWidth="12"
        strokeLinecap="round"
        opacity="0.08"
      />
    </svg>
  );
}

function RenewableDecoration() {
  return (
    <svg
      viewBox="0 0 380 340"
      fill="none"
      className="h-full w-full"
      aria-hidden="true"
    >
      <path
        d="M182 45v188"
        stroke="currentColor"
        strokeWidth="5"
        opacity="0.14"
      />
      <path
        d="M182 45c-25 36-28 64-15 83 17-6 30-25 15-83Z"
        fill="currentColor"
        opacity="0.09"
      />
      <path
        d="M182 45c25 36 28 64 15 83-17-6-30-25-15-83Z"
        fill="currentColor"
        opacity="0.09"
      />
      <path
        d="M182 45c-36 25-48 49-40 69 19 0 37-17 40-69Z"
        fill="currentColor"
        opacity="0.09"
      />
      <circle cx="182" cy="45" r="8" fill="currentColor" opacity="0.12" />

      <path
        d="M80 265h245"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="round"
        opacity="0.1"
      />
      <path
        d="M118 255 142 225l24 30 24-35 24 35 24-30 24 30 24-26 24 31"
        stroke="currentColor"
        strokeWidth="4"
        opacity="0.12"
      />
      <path
        d="M107 268h194l-24 36H132l-25-36Z"
        fill="currentColor"
        opacity="0.06"
      />
      <path
        d="m144 277 13-9v36M181 277l13-9v36M218 277l13-9v36M255 277l13-9v36"
        stroke="currentColor"
        strokeWidth="3"
        opacity="0.08"
      />
    </svg>
  );
}

export default function LoginScreen() {
  const { login, busy } = useAuth();

  const [selectedRole, setSelectedRole] =
    useState<DemoRole>("network_operator");
  const [email, setEmail] = useState(DEMOS.network_operator.email);
  const [password, setPassword] = useState(DEMOS.network_operator.password);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function chooseRole(role: DemoRole) {
    const demo = DEMOS[role];
    setSelectedRole(role);
    setEmail(demo.email);
    setPassword(demo.password);
    setError(null);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    try {
      await login({ email, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#eef4fb] text-slate-950">
      {/* Background wash */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_16%_28%,rgba(59,130,246,0.10),transparent_28%),radial-gradient(circle_at_84%_72%,rgba(34,197,94,0.09),transparent_28%),linear-gradient(135deg,#f8fbff_0%,#edf3fa_45%,#f7fbff_100%)]" />

      {/* Large decorative circles */}
      <div className="absolute -left-32 top-20 h-80 w-80 rounded-full bg-blue-100/40 blur-2xl" />
      <div className="absolute -right-28 bottom-4 h-96 w-96 rounded-full bg-cyan-100/35 blur-2xl" />

      {/* Left-side EV illustration */}
      <div className="pointer-events-none absolute bottom-0 left-0 hidden h-[330px] w-[350px] text-slate-500/70 xl:block">
        <ChargerDecoration />
      </div>

      {/* Right-side renewable illustration */}
      <div className="pointer-events-none absolute bottom-0 right-0 hidden h-[360px] w-[400px] text-emerald-700/60 xl:block">
        <RenewableDecoration />
      </div>

      {/* Side messaging */}
      <div className="pointer-events-none absolute left-10 top-1/2 hidden -translate-y-1/2 text-5xl font-semibold leading-[1.02] tracking-tight text-slate-400/55 xl:block">
        <span className="block">Powering</span>
        <span className="block">smarter</span>
        <span className="block">charging.</span>
      </div>

      <div className="pointer-events-none absolute right-10 top-16 hidden max-w-52 text-right text-lg font-medium leading-6 text-slate-500/75 xl:block">
        Smarter charging
        <br />
        for a cleaner tomorrow.
      </div>

      {/* Main card */}
      <div className="relative z-10 flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <section className="w-full max-w-[650px] rounded-[28px] border border-white/80 bg-white/95 p-6 shadow-[0_30px_80px_rgba(30,64,175,0.12)] backdrop-blur-xl sm:p-9 lg:p-10">
          {/* Brand */}
          <div className="text-center">
            <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[22px] bg-[#07111f] shadow-lg shadow-slate-900/10">
              <div className="text-4xl font-semibold text-cyan-300">A</div>
            </div>

            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-slate-950">
              Aegis
            </h1>

            <p className="mt-2 text-sm font-medium text-slate-500 sm:text-base">
              Renewable-aware EV charging orchestration
            </p>
          </div>

          {/* Sign-in header */}
          <div className="mt-10">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
              Sign in to your account
            </h2>
            <p className="mt-1.5 text-sm text-slate-500">
              Access your dashboard based on your role
            </p>
          </div>

          <form className="mt-7 space-y-5" onSubmit={submit}>
            {/* Email */}
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">
                Email
              </span>

              <div className="relative mt-2">
                <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                  <MailIcon />
                </span>

                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="h-14 w-full rounded-2xl border border-slate-200 bg-white pl-12 pr-4 text-sm text-slate-800 shadow-sm outline-none transition focus:border-cyan-400 focus:ring-4 focus:ring-cyan-100"
                  placeholder="e.g. driver@aegis.local"
                  autoComplete="username"
                />
              </div>
            </label>

            {/* Password */}
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">
                Password
              </span>

              <div className="relative mt-2">
                <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                  <LockIcon />
                </span>

                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type={showPassword ? "text" : "password"}
                  className="h-14 w-full rounded-2xl border border-slate-200 bg-white pl-12 pr-12 text-sm text-slate-800 shadow-sm outline-none transition focus:border-cyan-400 focus:ring-4 focus:ring-cyan-100"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-700"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>
            </label>

            {/* Error */}
            {error && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {error}
              </div>
            )}

            {/* Role selector */}
            <div>
              <div className="mb-3 text-sm font-semibold text-slate-700">
                Select your role
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <button
                  type="button"
                  onClick={() => chooseRole("grid_operator")}
                  className={[
                    "group min-h-[142px] rounded-2xl border p-4 text-left transition-all",
                    selectedRole === "grid_operator"
                      ? "border-blue-300 bg-blue-50 shadow-sm ring-1 ring-blue-200"
                      : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-blue-200 hover:bg-blue-50/40",
                  ].join(" ")}
                >
                  <div
                    className={[
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      selectedRole === "grid_operator"
                        ? "bg-blue-100 text-blue-600"
                        : "bg-blue-50 text-blue-500",
                    ].join(" ")}
                  >
                    <GridIcon />
                  </div>

                  <div className="mt-4 text-sm font-semibold text-slate-900">
                    Grid Operator
                  </div>
                  <div className="mt-1 text-xs leading-5 text-slate-500">
                    Monitor grid & publish signals
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => chooseRole("network_operator")}
                  className={[
                    "group min-h-[142px] rounded-2xl border p-4 text-left transition-all",
                    selectedRole === "network_operator"
                      ? "border-emerald-300 bg-emerald-50 shadow-sm ring-1 ring-emerald-200"
                      : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-emerald-200 hover:bg-emerald-50/40",
                  ].join(" ")}
                >
                  <div
                    className={[
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      selectedRole === "network_operator"
                        ? "bg-emerald-100 text-emerald-600"
                        : "bg-emerald-50 text-emerald-500",
                    ].join(" ")}
                  >
                    <NetworkIcon />
                  </div>

                  <div className="mt-4 text-sm font-semibold text-slate-900">
                    Network Operator
                  </div>
                  <div className="mt-1 text-xs leading-5 text-slate-500">
                    Optimize & manage charging
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => chooseRole("ev_driver")}
                  className={[
                    "group min-h-[142px] rounded-2xl border p-4 text-left transition-all",
                    selectedRole === "ev_driver"
                      ? "border-violet-300 bg-violet-50 shadow-sm ring-1 ring-violet-200"
                      : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-violet-200 hover:bg-violet-50/40",
                  ].join(" ")}
                >
                  <div
                    className={[
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      selectedRole === "ev_driver"
                        ? "bg-violet-100 text-violet-600"
                        : "bg-violet-50 text-violet-500",
                    ].join(" ")}
                  >
                    <CarIcon />
                  </div>

                  <div className="mt-4 text-sm font-semibold text-slate-900">
                    EV Driver
                  </div>
                  <div className="mt-1 text-xs leading-5 text-slate-500">
                    View schedule & manage charging
                  </div>
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={busy}
              className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-[#07111f] px-5 text-base font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-900 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            >
              {busy ? "Signing in…" : "Sign In"}
              {!busy && <span className="text-lg">→</span>}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-200" />
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                Demo accounts
              </span>
              <div className="h-px flex-1 bg-slate-200" />
            </div>

            <div className="mt-4 overflow-hidden rounded-2xl border border-slate-100 bg-slate-50/80">
              <div className="grid sm:grid-cols-3">
                {(
                  [
                    "grid_operator",
                    "network_operator",
                    "ev_driver",
                  ] as DemoRole[]
                ).map((role, index) => {
                  const demo = DEMOS[role];

                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => chooseRole(role)}
                      className={[
                        "p-4 text-left transition hover:bg-white",
                        index !== 0
                          ? "border-t border-slate-100 sm:border-l sm:border-t-0"
                          : "",
                      ].join(" ")}
                    >
                      <div className="text-sm font-semibold text-slate-800">
                        {role === "ev_driver" ? "EV Drivers" : demo.label}
                      </div>

                      <div className="mt-1 break-all text-xs text-slate-500">
                        {demo.email}
                      </div>

                      <div className="mt-1 text-xs font-medium text-slate-400">
                        {demo.password}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-7 flex items-center justify-center gap-2 text-center text-xs font-medium text-slate-400">
            <span className="text-emerald-500">
              <LeafIcon />
            </span>
            Clean energy. Smarter mobility. A brighter tomorrow.
          </div>
        </section>
      </div>

      {/* Bottom-right statement */}
      <div className="pointer-events-none absolute bottom-7 right-9 hidden text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400/70 xl:block">
        People&nbsp;&nbsp;•&nbsp;&nbsp;Planet&nbsp;&nbsp;•&nbsp;&nbsp;Progress
      </div>
    </main>
  );
}