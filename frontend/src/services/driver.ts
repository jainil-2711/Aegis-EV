import type {
  DriverPreferencesUpdate,
  DriverRecommendationResponse,
  DriverSessionResponse,
  DriverSessionStatusResponse,
  ErrorResponse,
  ScheduleAcceptRequest,
  ScheduleAcceptResponse,
  ScheduleOverrideRequest,
  ScheduleOverrideResponse,
} from "../types/api";

const BASE_URL = "/api/driver";

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

export async function getDriverSession(): Promise<DriverSessionResponse> {
  return handle(await fetch(`${BASE_URL}/session`));
}

export async function updateDriverPreferences(update: DriverPreferencesUpdate): Promise<DriverSessionResponse> {
  return handle(
    await fetch(`${BASE_URL}/preferences`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    }),
  );
}

export async function getDriverRecommendation(): Promise<DriverRecommendationResponse> {
  return handle(await fetch(`${BASE_URL}/recommendation`));
}

export async function acceptSchedule(req: ScheduleAcceptRequest): Promise<ScheduleAcceptResponse> {
  return handle(
    await fetch(`${BASE_URL}/schedule/accept`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),
  );
}

export async function overrideSchedule(req: ScheduleOverrideRequest): Promise<ScheduleOverrideResponse> {
  return handle(
    await fetch(`${BASE_URL}/schedule/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),
  );
}

export async function getDriverSessionStatus(): Promise<DriverSessionStatusResponse> {
  return handle(await fetch(`${BASE_URL}/session/status`));
}
