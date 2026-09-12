import { useCallback, useEffect, useState } from "react";
import type { NetworkImpactResponse } from "../types/api";
import { getNetworkImpact } from "../services/operator";

interface UseNetworkImpactResult {
  impact: NetworkImpactResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useNetworkImpact(): UseNetworkImpactResult {
  const [impact, setImpact] = useState<NetworkImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchImpact = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getNetworkImpact();
      setImpact(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No network impact available yet"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchImpact();
  }, [fetchImpact]);

  return { impact, loading, error, refetch: fetchImpact };
}
