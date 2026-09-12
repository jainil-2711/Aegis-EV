import { FormEvent, useState } from "react";
import { useAuth } from "../hooks/useAuth";

const DEMOS = [
  { label: "Grid Operator", email: "grid@aegis.local", password: "AegisGrid26!" },
  { label: "Network Operator", email: "network@aegis.local", password: "AegisNet26!" },
  { label: "EV Driver", email: "driver@aegis.local", password: "AegisDriver26!" },
];

export default function LoginScreen() {
  const { login, busy } = useAuth();
  const [email, setEmail] = useState(DEMOS[1].email);
  const [password, setPassword] = useState(DEMOS[1].password);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await login({ email, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    }
  }

  function choose(emailValue: string, passwordValue: string) {
    setEmail(emailValue);
    setPassword(passwordValue);
    setError(null);
  }

  return (
    <main className="min-h-screen bg-[#07111f] px-6 py-10 text-white">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <section>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-200">
            AEGIS / ENERGY ORCHESTRATION
          </div>
          <h1 className="max-w-2xl text-5xl font-semibold tracking-tight">
            Protect the grid. Shift the load. Keep the driver in control.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">
            Aegis coordinates grid signals, renewable availability and EV flexibility into one auditable charging plan.
          </p>
          <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
            {["Grid-aware", "Renewable-first", "Driver-controlled"].map((item) => (
              <div key={item} className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white p-6 text-slate-900 shadow-2xl">
          <p className="text-sm font-medium text-slate-500">Secure demo access</p>
          <h2 className="mt-1 text-2xl font-semibold">Sign in to Aegis</h2>
          <p className="mt-2 text-sm text-slate-500">Your role determines which actions and data you can access.</p>
          <form className="mt-6 space-y-4" onSubmit={submit}>
            <label className="block text-sm font-medium text-slate-700">
              Email
              <input value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-cyan-500" autoComplete="username" />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Password
              <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-cyan-500" autoComplete="current-password" />
            </label>
            {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
            <button disabled={busy} className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
              {busy ? "Signing in…" : "Enter Aegis"}
            </button>
          </form>
          <div className="mt-6 border-t border-slate-100 pt-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Demo identities</p>
            <div className="mt-3 grid gap-2">
              {DEMOS.map((demo) => (
                <button key={demo.email} type="button" onClick={() => choose(demo.email, demo.password)} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-left text-sm hover:bg-slate-50">
                  <span className="font-medium text-slate-700">{demo.label}</span>
                  <span className="text-xs text-slate-400">Use demo account</span>
                </button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
