import { useState } from "react";
import DriverView from "./pages/driver/DriverView";
import OperatorView from "./pages/operator/OperatorView";
import GridView from "./pages/grid/GridView";

type Role = "grid" | "operator" | "driver";

export default function App() {
  const [role, setRole] = useState<Role>("operator");

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">GreenCharge</h1>
            <p className="text-xs text-slate-500">
              Renewable-aware EV charging orchestration demo
            </p>
          </div>
          <div className="flex flex-wrap justify-end gap-2" role="tablist" aria-label="Role">
            {([
              ["grid", "Grid operator"],
              ["operator", "Network operator"],
              ["driver", "Driver"],
            ] as const).map(([value, label]) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={role === value}
                onClick={() => setRole(value)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                  role === value
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {role === "grid" ? <GridView /> : role === "operator" ? <OperatorView /> : <DriverView />}
    </div>
  );
}
