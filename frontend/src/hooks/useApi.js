import { useCallback, useEffect, useState } from "react";

/**
 * Generic async data-fetching hook: runs `fetcher`, tracks
 * loading/error/data, and exposes `refetch` for manual reloads.
 *
 * `deps` should list every value the fetcher closes over (guild id,
 * filters, page, etc.) so it re-runs when they change — same rules as
 * useEffect's dependency array.
 */
export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    const cancel = load();
    return cancel;
  }, [load]);

  return { data, error, loading, refetch: load };
}
