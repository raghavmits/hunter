// Thread endpoints for digest row actions (#29), quick-add (#30), and the
// thread detail page (#31). Matches app/schemas/thread.py, touch.py, stage_event.py.
import type { Stage } from "./digest";
import { apiFetch } from "./client";

export const STAGE_ORDER: Stage[] = ["outreach", "replied", "screen", "interview", "offer"];

export function nextStage(stage: Stage): Stage | null {
  const index = STAGE_ORDER.indexOf(stage);
  return index >= 0 && index < STAGE_ORDER.length - 1 ? STAGE_ORDER[index + 1] : null;
}

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

export type TouchDirection = "outbound" | "inbound";

export const TOUCH_DIRECTION_LABELS: Record<TouchDirection, string> = {
  outbound: "Outbound",
  inbound: "Inbound",
};

export type TouchChannel = "email" | "linkedin" | "referral" | "phone" | "in_person" | "portal" | "other";

export const TOUCH_CHANNEL_LABELS: Record<TouchChannel, string> = {
  email: "Email",
  linkedin: "LinkedIn",
  referral: "Referral",
  phone: "Phone",
  in_person: "In person",
  portal: "Portal",
  other: "Other",
};

export type TerminalStatus = "rejected" | "ghosted" | "withdrawn" | "closed";

export const TERMINAL_STATUS_LABELS: Record<TerminalStatus, string> = {
  rejected: "Rejected",
  ghosted: "Ghosted",
  withdrawn: "Withdrawn",
  closed: "Closed",
};

export interface TouchRead {
  id: number;
  thread_id: number;
  kind: TouchKind;
  direction: TouchDirection;
  channel: TouchChannel;
  occurred_at: string;
  note: string | null;
  created_at: string;
}

export interface StageEventRead {
  id: number;
  thread_id: number;
  from_stage: Stage | TerminalStatus | null;
  to_stage: Stage | TerminalStatus;
  occurred_at: string;
  note: string | null;
}

export type ThreadStatus = "open" | TerminalStatus;

export interface ThreadDetail {
  id: number;
  company_id: number;
  company_name: string;
  contact_id: number | null;
  contact_name: string | null;
  role_title: string | null;
  role_family: RoleFamily | null;
  motion: Motion | null;
  stage: Stage;
  status: ThreadStatus;
  stage_entered_at: string;
  next_follow_up_date: string | null;
  nudge_number: number;
  follow_up_pinned: boolean;
  jd_url: string | null;
  notes: string | null;
  created_at: string;
  closed_at: string | null;
  is_ghost_suggested: boolean;
  days_in_stage: number;
  company: { id: number; name: string };
  contact: { id: number; full_name: string } | null;
  touches: TouchRead[];
  stage_events: StageEventRead[];
}

export function getThread(threadId: number): Promise<ThreadDetail> {
  return apiFetch<ThreadDetail>(`/threads/${threadId}`);
}

export interface ThreadListItem {
  id: number;
  company_id: number;
  company_name: string;
  contact_id: number | null;
  contact_name: string | null;
  role_title: string | null;
  role_family: RoleFamily | null;
  motion: Motion | null;
  stage: Stage;
  status: ThreadStatus;
  next_follow_up_date: string | null;
  nudge_number: number;
  is_ghost_suggested: boolean;
}

export interface ThreadListFilters {
  status?: ThreadStatus;
  stage?: Stage;
  motion?: Motion;
  role_family?: RoleFamily;
  company_id?: number;
}

export function listThreads(filters: ThreadListFilters = {}): Promise<ThreadListItem[]> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined) params.set(key, String(value));
  }
  const query = params.toString();
  return apiFetch<ThreadListItem[]>(`/threads${query ? `?${query}` : ""}`);
}

export interface TouchCreateInput {
  kind: TouchKind;
  direction: TouchDirection;
  channel: TouchChannel;
  occurred_at?: string;
  note?: string;
}

export function createTouch(threadId: number, input: TouchCreateInput): Promise<unknown> {
  return apiFetch(`/threads/${threadId}/touches`, {
    method: "POST",
    body: JSON.stringify({ ...input, note: input.note || null }),
  });
}

export function logTouch(threadId: number, kind: TouchKind, note: string | undefined): Promise<unknown> {
  return createTouch(threadId, { kind, direction: "outbound", channel: "email", note });
}

export function setFollowUp(threadId: number, nextFollowUpDate: string): Promise<unknown> {
  return apiFetch(`/threads/${threadId}/follow-up`, {
    method: "PATCH",
    body: JSON.stringify({ next_follow_up_date: nextFollowUpDate }),
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

export interface BulkOutreachRow {
  company_name: string;
  contact_id?: number;
  role_title?: string;
}

export interface BulkOutreachRequest {
  kind: TouchKind;
  channel: TouchChannel;
  occurred_at?: string;
  rows: BulkOutreachRow[];
}

export interface BulkOutreachRowResult {
  row_index: number;
  success: boolean;
  error: string | null;
  thread_id: number | null;
}

export interface BulkOutreachResult {
  results: BulkOutreachRowResult[];
}

export function bulkOutreach(request: BulkOutreachRequest): Promise<BulkOutreachResult> {
  return apiFetch<BulkOutreachResult>("/threads/bulk-outreach", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
