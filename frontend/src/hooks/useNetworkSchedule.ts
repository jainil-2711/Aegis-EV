import { useCallback, useEffect, useState } from "react";
import type { OptimizationScheduleResponse } from "../types/api";
import { getActiveSchedule } from "../services/optimization";

export function useNetworkSchedule() {
  const [schedule, setSchedule] = useState<OptimizationScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      setSchedule(await getActiveSchedule());
    } catch {
      setSchedule(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { schedule, loading, refetch };
}
