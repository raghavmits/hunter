// Thread mutation endpoints used for digest row actions (issue #29).
// Matches app/schemas/thread.py, app/schemas/touch.py, app/schemas/stage_event.py.
import { apiFetch } from "./client";

export type TouchKind =
  | "cold_outreach"
  | "warm_intro_request"
  | "referral_promised"
  | "post_recruiter_call"
  | "post_interview"
  | "application_submitted"
  | "long_term_nurture";

export const TOUCH_KIND_LABELS: Record<TouchKind, string> = {
  cold_outreach: "Cold outreach",
  warm_intro_request: "Warm intro request",
  referral_promised: "Referral promised",
  post_recruiter_call: "Post recruiter call",
  post_interview: "Post interview",
  application_submitted: "Application submitted",
  long_term_nurture: "Long-term nurture",
};

export type TerminalStatus = "rejected" | "ghosted" | "withdrawn" | "closed";

export const TERMINAL_STATUS_LABELS: Record<TerminalStatus, string> = {
  rejected: "Rejected",
  ghosted: "Ghosted",
  withdrawn: "Withdrawn",
  closed: "Closed",
};

export function logTouch(threadId: number, kind: TouchKind, note: string | undefined): Promise<unknown> {
  return apiFetch(`/threads/${threadId}/touches`, {
    method: "POST",
    body: JSON.stringify({ kind, direction: "outbound", channel: "email", note: note || null }),
  });
}

export function snoozeThread(threadId: number, businessDays: number): Promise<unknown> {
  return apiFetch(`/threads/${threadId}/snooze`, {
    method: "POST",
    body: JSON.stringify({ business_days: businessDays }),
  });
}

export function changeStage(threadId: number, to: string): Promise<unknown> {
  return apiFetch(`/threads/${threadId}/stage`, {
    method: "POST",
    body: JSON.stringify({ to }),
  });
}

export type RoleFamily = "FDE" | "SWE" | "MLE" | "MTS" | "OTHER";

export const ROLE_FAMILY_LABELS: Record<RoleFamily, string> = {
  FDE: "FDE",
  SWE: "SWE",
  MLE: "MLE",
  MTS: "MTS",
  OTHER: "Other",
};

export type Motion = "cold_outreach" | "warm_outreach" | "cold_application";

export const MOTION_LABELS: Record<Motion, string> = {
  cold_outreach: "Cold outreach",
  warm_outreach: "Warm outreach",
  cold_application: "Cold application",
};

export interface ThreadCreateInput {
  company_name: string;
  role_title?: string;
  role_family?: RoleFamily;
  contact_id?: number;
  motion?: Motion;
  jd_url?: string;
}

export function createThread(input: ThreadCreateInput): Promise<unknown> {
  return apiFetch("/threads", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
