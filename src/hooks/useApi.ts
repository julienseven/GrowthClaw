/**
 * Custom hook for API interactions with loading and error states.
 */

import { useCallback, useState } from "react";
import { apiGet, ApiResponse } from "@/lib/api";

export function useApi<T>(
  endpoint: string,
  autoFetch: boolean = false
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<T>(endpoint);
      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError(response.error || "Unknown error");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  // Auto-fetch on mount if enabled
  if (autoFetch && !data && !loading) {
    fetch();
  }

  return { data, loading, error, fetch };
}
