import { useCallback, useEffect, useState } from "react";
import type { EnergySlot } from "../types/api";
import { getGridForecast } from "../services/grid";

export function useNetworkForecast() {
  const [slots, setSlots] = useState<EnergySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getGridForecast();
      setSlots(data.slots);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load network forecast");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);
  return { slots, loading, error, refetch };
}
