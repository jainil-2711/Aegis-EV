import { getToken, logout } from "./auth";

/**
 * An API error that preserves the HTTP status code so callers (especially
 * polling hooks) can distinguish a permanent auth/authorization failure
 * (401/403 — retrying will never succeed) from a transient one worth
 * retrying.
 */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function isAuthOrPermissionError(err: unknown): boolean {
  return err instanceof ApiError && (err.status === 401 || err.status === 403);
}

export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", token);

  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) {
    logout();
    window.dispatchEvent(new Event("aegis-auth-expired"));
  }
  return response;
}

export async function readApiError(res: Response): Promise<string> {
  let message = `Request failed (${res.status})`;
  try {
    const body = (await res.json()) as { detail?: unknown; error?: { message?: string } };
    if (typeof body.detail === "string") return body.detail;
    if (body.detail && typeof body.detail === "object" && "error" in body.detail) {
      const detail = body.detail as { error?: { message?: string } };
      if (detail.error?.message) return detail.error.message;
    }
    if (body.error?.message) message = body.error.message;
  } catch {
    // Keep generic message.
  }
  return message;
}