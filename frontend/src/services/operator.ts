/**
 * Aegis — Operator API Client (P4)
 *
 * Thin typed wrapper over /api/stations, /api/chargers, /api/network/*.
 * Uses shared types from frontend/src/types/api.ts only (rules.md SS12).
 *
 * Does NOT wrap /api/optimization/run or /api/optimization/apply — those
 * are P2-owned (frontend/src/services/optimization.ts). The operator
 * pages import that client directly rather than re-wrapping it here,
 * so there is exactly one client per shared endpoint.
 */

import type {
  StationsResponse,
  ChargersResponse,
  NetworkStatusResponse,
  NetworkImpactResponse,
  ErrorResponse,
} from "../types/api";
import { apiFetch, readApiError } from "./http";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as ErrorResponse & {
        detail?: string | { error?: ErrorResponse["error"] };
      };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (body.detail?.error?.message) {
        message = body.detail.error.message;
      } else if (body.error?.message) {
        message = body.error.message;
      }
    } catch {
      // Keep the generic HTTP error.
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function getStations(): Promise<StationsResponse> {
  const res = await apiFetch("/api/stations");
  return handle<StationsResponse>(res);
}

export async function getChargers(stationId?: string): Promise<ChargersResponse> {
  const url = stationId
    ? `/api/chargers?station_id=${encodeURIComponent(stationId)}`
    : "/api/chargers";
  const res = await apiFetch(url);
  return handle<ChargersResponse>(res);
}

export async function getNetworkStatus(): Promise<NetworkStatusResponse> {
  const res = await apiFetch("/api/network/status");
  return handle<NetworkStatusResponse>(res);
}

export async function getNetworkImpact(): Promise<NetworkImpactResponse> {
  const res = await apiFetch("/api/network/impact");
  return handle<NetworkImpactResponse>(res);
}
