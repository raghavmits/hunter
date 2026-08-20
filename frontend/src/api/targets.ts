// Matches app/schemas/targets.py (issue #21).
import { apiFetch } from "./client";

export interface TargetProgress {
  count: number;
  target: number;
  type: "input" | "outcome";
  deadline: string | null;
}

export interface TargetsSummary {
  new_connections_made: TargetProgress;
  warm_outreach_with_acquaintances: TargetProgress;
  cold_applications: TargetProgress;
  screens_recruiter_calls: TargetProgress;
  interviews: TargetProgress;
  offers: TargetProgress;
}

export const INPUT_TARGET_LABELS: Record<
  "new_connections_made" | "warm_outreach_with_acquaintances" | "cold_applications",
  string
> = {
  new_connections_made: "New connections made",
  warm_outreach_with_acquaintances: "Warm outreach with acquaintances",
  cold_applications: "Cold applications",
};

export const OUTCOME_TARGET_LABELS: Record<"screens_recruiter_calls" | "interviews" | "offers", string> = {
  screens_recruiter_calls: "Screens / recruiter calls",
  interviews: "Interviews",
  offers: "Offers",
};

export function getTargets(): Promise<TargetsSummary> {
  return apiFetch<TargetsSummary>("/targets");
}
