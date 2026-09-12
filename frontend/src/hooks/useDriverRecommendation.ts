import { useCallback, useEffect, useState } from "react";
import type { DriverRecommendationResponse, ScheduleOverrideRequest, ScheduleOverrideResponse } from "../types/api";
import { acceptSchedule, getDriverRecommendation, overrideSchedule } from "../services/driver";

export function useDriverRecommendation() {
  const [recommendation, setRecommendation] = useState<DriverRecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [overrideResult, setOverrideResult] = useState<ScheduleOverrideResponse | null>(null);

  const fetchRecommendation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRecommendation(await getDriverRecommendation());
    } catch (err) {
      setError(err instanceof Error ? err.message : "No recommendation available yet");
    } finally {
      setLoading(false);
    }
  }, []);

  const accept = useCallback(async () => {
    if (!recommendation) return;
    setError(null);
    try {
      await acceptSchedule({ optimization_run_id: recommendation.optimization_run_id });
      setAccepted(true);
      setOverrideResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to accept");
    }
  }, [recommendation]);

  const override = useCallback(async (req: ScheduleOverrideRequest) => {
    setError(null);
    try {
      const result = await overrideSchedule(req);
      setOverrideResult(result);
      setAccepted(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to override");
    }
  }, []);

  useEffect(() => { void fetchRecommendation(); }, [fetchRecommendation]);

  return { recommendation, loading, error, accepted, overrideResult, refetch: fetchRecommendation, accept, override };
}
