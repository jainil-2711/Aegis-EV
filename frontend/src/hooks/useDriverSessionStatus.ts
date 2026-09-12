import { useEffect, useRef, useState } from "react";
import type { DriverSessionStatusResponse } from "../types/api";
import { getDriverSessionStatus } from "../services/driver";

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
    const poll = async () => {
      setLoading(true);
      try {
        const data = await getDriverSessionStatus();
        if (!cancelled) { setStatus(data); setError(null); }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to refresh status");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void poll();
    intervalRef.current = setInterval(() => { void poll(); }, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [enabled]);

  return { status, loading, error };
}
