// Placeholder — #28 replaces this with the real digest. For now it proves
// the proxy, the typed client, and the dev server are wired correctly by
// calling /api/health (issue #26).
import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "../api/health";

export function DigestPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <div>
      <h1>Digest</h1>
      <p>The real digest (#28) isn't built yet. This page proves the frontend can reach the API:</p>
      {error && <p role="alert">Could not reach the API: {error}</p>}
      {!error && !health && <p>Loading…</p>}
      {health && (
        <p>
          <code>/api/health</code> says: <strong>{health.name}</strong> v{health.version}
        </p>
      )}
    </div>
  );
}
