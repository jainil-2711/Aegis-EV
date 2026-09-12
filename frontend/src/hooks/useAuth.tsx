import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AuthUser, LoginRequest } from "../types/api";
import { getStoredUser, getToken, login as loginRequest, logout as clearAuth } from "../services/auth";

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  authenticated: boolean;
  busy: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getToken());
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const handleExpired = () => {
      clearAuth();
      setToken(null);
      setUser(null);
    };
    window.addEventListener("aegis-auth-expired", handleExpired);
    return () => window.removeEventListener("aegis-auth-expired", handleExpired);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    token,
    user,
    authenticated: Boolean(token && user),
    busy,
    async login(payload) {
      setBusy(true);
      try {
        const response = await loginRequest(payload);
        setToken(response.access_token);
        setUser(response.user);
      } finally {
        setBusy(false);
      }
    },
    logout() {
      clearAuth();
      setToken(null);
      setUser(null);
    },
  }), [token, user, busy]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
