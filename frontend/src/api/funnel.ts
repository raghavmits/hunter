// Matches app/schemas/funnel.py (issue #22).
import type { Stage } from "./digest";
import { apiFetch } from "./client";
import type { Motion, RoleFamily } from "./threads";

export type Window = "today" | "7d" | "30d" | "all";

export interface FunnelStage {
  stage: Stage;
  count: number;
  conversion_from_previous: number | null;
}

export interface Funnel {
  stages: FunnelStage[];
}

export interface FunnelFilters {
  motion?: Motion;
  role_family?: RoleFamily;
  window?: Window;
}

export function getFunnel(filters: FunnelFilters = {}): Promise<Funnel> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined) params.set(key, String(value));
  }
  const query = params.toString();
  return apiFetch<Funnel>(`/funnel${query ? `?${query}` : ""}`);
}
