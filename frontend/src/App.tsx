import { useEffect, useState } from "react";
import DriverView from "./pages/driver/DriverView";
import OperatorView from "./pages/operator/OperatorView";
import GridView from "./pages/grid/GridView";
import LoginScreen from "./pages/LoginScreen";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import type { AuthRole } from "./types/api";

const ROLE_LABEL: Record<AuthRole, string> = {
  grid_operator: "Grid Operator",
  network_operator: "Network Operator",
  ev_driver: "EV Driver",
};

function AuthenticatedApp() {
  const { user, logout } = useAuth();
  const [expired, setExpired] = useState(false);
  const role = user?.role;

  useEffect(() => {
    const onExpired = () => setExpired(true);
    window.addEventListener("aegis-auth-expired", onExpired);
    return () => window.removeEventListener("aegis-auth-expired", onExpired);
  }, []);

  useEffect(() => {
    if (user) setExpired(false);
  }, [user]);

  if (!user || !role) return <LoginScreen />;

  const page = role === "grid_operator" ? <GridView /> : role === "network_operator" ? <OperatorView /> : <DriverView />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-6 py-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-cyan-300">A</div>
              <div>
                <h1 className="text-lg font-semibold tracking-tight text-slate-950">Aegis</h1>
                <p className="text-xs text-slate-500">Renewable-aware EV charging orchestration</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full border border-cyan-100 bg-cyan-50 px-3 py-1 text-xs font-medium text-cyan-800">{ROLE_LABEL[role]}</span>
            <button type="button" onClick={logout} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">Sign out</button>
          </div>
        </div>
      </header>
      {expired && (
        <div className="mx-auto max-w-7xl px-6 pt-4">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            Your session expired. Please sign in again.
          </div>
        </div>
      )}
      {page}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}
