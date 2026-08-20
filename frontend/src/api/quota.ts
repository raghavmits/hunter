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

export const QUOTA_LABELS: Record<keyof QuotaSummary, string> = {
  cold_outreach_sent: "Cold outreach sent",
  warm_intro_requests_sent: "Warm intro requests sent",
  cold_applications_submitted: "Cold applications submitted",
  referral_asks_made: "Referral asks made",
};

export function getQuotaProgress(): Promise<QuotaSummary> {
  return apiFetch<QuotaSummary>("/quotas");
}
