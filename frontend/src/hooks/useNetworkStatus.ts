import { useCallback, useEffect, useState } from "react";
import type {
  NetworkStatusResponse,
  StationsResponse,
  ChargersResponse,
} from "../types/api";
import { getNetworkStatus, getStations, getChargers } from "../services/operator";

interface UseNetworkStatusResult {
  status: NetworkStatusResponse | null;
  stations: StationsResponse["stations"];
  chargers: ChargersResponse["chargers"];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useNetworkStatus(): UseNetworkStatusResult {
  const [status, setStatus] = useState<NetworkStatusResponse | null>(null);
  const [stations, setStations] = useState<StationsResponse["stations"]>([]);
  const [chargers, setChargers] = useState<ChargersResponse["chargers"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, stationsRes, chargersRes] = await Promise.all([
        getNetworkStatus(),
        getStations(),
        getChargers(),
      ]);
      setStatus(statusRes);
      setStations(stationsRes.stations);
      setChargers(chargersRes.chargers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load network status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return { status, stations, chargers, loading, error, refetch: fetchAll };
}
