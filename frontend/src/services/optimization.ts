import type {
  OperatorObjective,
  OptimizationApplyRequest,
  OptimizationApplyResponse,
  OptimizationRunRequest,
  OptimizationRunResponse,
  OptimizationScheduleResponse,
} from "../types/api";
import { apiFetch, readApiError } from "./http";

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
    await apiFetch("/api/optimization/run", {
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
    await apiFetch("/api/optimization/apply", {
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


export async function getActiveSchedule(): Promise<OptimizationScheduleResponse> {
  return handle(await apiFetch("/api/optimization/schedule"));
}
