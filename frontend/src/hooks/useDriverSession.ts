import { useCallback, useEffect, useState } from "react";
import type { DriverPreferencesUpdate, DriverSessionResponse } from "../types/api";
import { getDriverSession, updateDriverPreferences } from "../services/driver";

export function useDriverSession() {
  const [session, setSession] = useState<DriverSessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSession(await getDriverSession());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load session");
    } finally {
      setLoading(false);
    }
  }, []);

  const updatePreferences = useCallback(async (update: DriverPreferencesUpdate) => {
    setError(null);
    try {
      setSession(await updateDriverPreferences(update));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update preferences");
    }
  }, []);

  useEffect(() => { void fetchSession(); }, [fetchSession]);

  return { session, loading, error, refetch: fetchSession, updatePreferences };
}
