// Matches app/api/health.py's response shape exactly (issue #2).
import { apiFetch } from "./client";

export interface HealthResponse {
  name: string;
  version: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}
