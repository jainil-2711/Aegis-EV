import { useEffect, useRef, useState } from "react";
import type { DriverSessionStatusResponse } from "../types/api";
import { getDriverSessionStatus } from "../services/driver";
import { isAuthOrPermissionError } from "../services/http";

const POLL_INTERVAL_MS = 5000;

export function useDriverSessionStatus(enabled: boolean) {
  const [status, setStatus] = useState<DriverSessionStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
      return;
    }

    let cancelled = false;
    const stopPolling = () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };

    const poll = async () => {
      setLoading(true);
      try {
        const data = await getDriverSessionStatus();
        if (!cancelled) { setStatus(data); setError(null); }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to refresh status");
        }
        // A 401/403 here means this session no longer has permission to
        // read this driver's status (token expired, or the signed-in role
        // changed in this browser). Retrying every 5s would never succeed
        // and only spams the backend — stop instead of looping forever.
        if (isAuthOrPermissionError(err)) {
          stopPolling();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void poll();
    intervalRef.current = setInterval(() => { void poll(); }, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [enabled]);

  return { status, loading, error };
}