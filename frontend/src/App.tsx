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

function AegisLogo() {
  return (
    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#071A3D] shadow-sm">
      <span className="text-xl font-semibold text-white">A</span>
    </div>
  );
}

function AuthenticatedApp() {
  const { user, logout } = useAuth();
  const [expired, setExpired] = useState(false);

  const role = user?.role;

  useEffect(() => {
    const handleExpired = () => setExpired(true);

    window.addEventListener(
      "aegis-auth-expired",
      handleExpired,
    );

    return () => {
      window.removeEventListener(
        "aegis-auth-expired",
        handleExpired,
      );
    };
  }, []);

  useEffect(() => {
    if (user) {
      setExpired(false);
    }
  }, [user]);

  if (!user || !role) {
    return <LoginScreen />;
  }

  const page =
    role === "grid_operator" ? (
      <GridView />
    ) : role === "network_operator" ? (
      <OperatorView />
    ) : (
      <DriverView />
    );

  return (
    <div className="min-h-screen bg-[#F7F8FA]">
      <header className="sticky top-0 z-50 border-b border-[#E0E4E9] bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-4 lg:px-10">
          <div className="flex items-center gap-3">
            <AegisLogo />

            <div>
              <div className="text-lg font-semibold tracking-tight text-[#071A3D]">
                Aegis
              </div>

              <div className="text-xs text-[#66758B]">
                Renewable-aware EV charging orchestration
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-medium text-[#66758B] md:block">
              {user.display_name}
            </span>

            <span className="rounded-full border border-[#D5DAE1] bg-[#F7F8FA] px-3.5 py-2 text-xs font-semibold text-[#071A3D]">
              {ROLE_LABEL[role]}
            </span>

            <button
              type="button"
              onClick={logout}
              className="rounded-xl border border-[#D5DAE1] bg-white px-4 py-2 text-xs font-semibold text-[#3D4C64] hover:bg-[#F7F8FA]"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {expired && (
        <div className="mx-auto max-w-[1440px] px-6 pt-5 lg:px-10">
          <div className="rounded-xl border border-[#D9CEC6] bg-[#F8F1ED] px-4 py-3 text-sm text-[#6F2C0F]">
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