import type { AuthUser, LoginRequest, LoginResponse } from "../types/api";

const TOKEN_KEY = "aegis_access_token";
const USER_KEY = "aegis_user";

function parseErrorBody(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  const value = body as { detail?: unknown; error?: { message?: string } };
  if (typeof value.detail === "string") return value.detail;
  if (typeof value.detail === "object" && value.detail && "error" in value.detail) {
    const detail = value.detail as { error?: { message?: string } };
    return detail.error?.message ?? null;
  }
  return value.error?.message ?? null;
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = (await res.json().catch(() => null)) as LoginResponse & { detail?: unknown };
  if (!res.ok) {
    throw new Error(parseErrorBody(body) ?? `Sign in failed (${res.status})`);
  }
  localStorage.setItem(TOKEN_KEY, body.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(body.user));
  return body;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
