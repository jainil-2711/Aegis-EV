import { useCallback, useEffect, useState } from "react";
import { createGridSignal, getGridForecast, getGridSignals, getGridStatus } from "../services/grid";
import type { GridForecastResponse, GridSignal, GridSignalCreate, GridStatusResponse } from "../types/api";

export function useGridData() {
  const [status, setStatus] = useState<GridStatusResponse | null>(null);
  const [forecast, setForecast] = useState<GridForecastResponse | null>(null);
  const [signals, setSignals] = useState<GridSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextStatus, nextForecast, nextSignals] = await Promise.all([
        getGridStatus(),
        getGridForecast(),
        getGridSignals(),
      ]);
      setStatus(nextStatus);
      setForecast(nextForecast);
      setSignals(nextSignals.signals);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't load grid data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  const publishSignal = useCallback(async (payload: GridSignalCreate) => {
    const created = await createGridSignal(payload);
    setSignals((current) => [created, ...current]);
    return created;
  }, []);

  return { status, forecast, signals, loading, error, refetch, publishSignal };
}
