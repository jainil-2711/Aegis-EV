import type {
  GridForecastResponse,
  GridSignal,
  GridSignalCreate,
  GridSignalsResponse,
  GridStatusResponse,
} from "../types/api";
import { apiFetch, readApiError } from "./http";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Keep generic HTTP error.
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function getGridStatus(): Promise<GridStatusResponse> {
  return handle(await apiFetch("/api/grid/status"));
}

export async function getGridForecast(): Promise<GridForecastResponse> {
  return handle(await apiFetch("/api/grid/forecast"));
}

export async function getGridSignals(): Promise<GridSignalsResponse> {
  return handle(await apiFetch("/api/grid/signals"));
}

export async function createGridSignal(payload: GridSignalCreate): Promise<GridSignal> {
  return handle(
    await apiFetch("/api/grid/signals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}
