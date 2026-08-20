// Matches app/schemas/quota.py exactly (issue #20).
import { apiFetch } from "./client";

export interface QuotaProgress {
  count: number;
  target: number;
  remaining: number;
}

export interface QuotaSummary {
  cold_outreach_sent: QuotaProgress;
  warm_intro_requests_sent: QuotaProgress;
  cold_applications_submitted: QuotaProgress;
  referral_asks_made: QuotaProgress;
}

export function getQuotaProgress(): Promise<QuotaSummary> {
  return apiFetch<QuotaSummary>("/quotas");
}
