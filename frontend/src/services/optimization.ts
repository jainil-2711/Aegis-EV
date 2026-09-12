import type {
  OperatorObjective,
  OptimizationApplyRequest,
  OptimizationApplyResponse,
  OptimizationRunRequest,
  OptimizationRunResponse,
} from "../types/api";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: string | { message?: string } };
      if (typeof body.detail === "string") message = body.detail;
      else if (body.detail?.message) message = body.detail.message;
    } catch {
      // Keep generic message.
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function runOptimization(
  request: OptimizationRunRequest,
): Promise<OptimizationRunResponse> {
  return handle(
    await fetch("/api/optimization/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }),
  );
}

export async function applyOptimization(
  request: OptimizationApplyRequest,
): Promise<OptimizationApplyResponse> {
  return handle(
    await fetch("/api/optimization/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }),
  );
}

export const operatorObjectives: OperatorObjective[] = [
  "cheapest",
  "greenest",
  "balanced",
];
