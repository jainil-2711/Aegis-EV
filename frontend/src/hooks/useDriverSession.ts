import { useCallback, useEffect, useState } from "react";
import type { DriverPreferencesUpdate, DriverSessionResponse } from "../types/api";
import { getDriverSession, updateDriverPreferences } from "../services/driver";

export function useDriverSession() {
  const [session, setSession] = useState<DriverSessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  // CHANGE: `error` is reserved for the *initial load* only, so a failed
  // preference update can never blank out an already-loaded page (it used
  // to share this field with updatePreferences, which meant one failed
  // save could replace the whole dashboard with "Couldn't load your
  // session"). Update failures now live in their own state below.
  const [error, setError] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);

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

  // CHANGE: now returns true/false so the caller (DriverView) can tell
  // whether the save actually happened, instead of always assuming
  // success. Previously this swallowed every error and the caller had no
  // way to know the request failed.
  const updatePreferences = useCallback(async (update: DriverPreferencesUpdate): Promise<boolean> => {
    setUpdateError(null);
    try {
      setSession(await updateDriverPreferences(update));
      return true;
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : "Failed to update preferences");
      return false;
    }
  }, []);

  useEffect(() => { void fetchSession(); }, [fetchSession]);

  return { session, loading, error, updateError, refetch: fetchSession, updatePreferences };
}