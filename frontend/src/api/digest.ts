// Matches app/schemas/digest.py exactly (issue #19).
import { apiFetch } from "./client";

export type Stage = "outreach" | "replied" | "screen" | "interview" | "offer";

export interface DigestRow {
  thread_id: number;
  company_id: number;
  company_name: string;
  contact_id: number | null;
  contact_name: string | null;
  stage: Stage;
  days_overdue: number | null;
  days_in_stage: number;
}

export interface Digest {
  overdue: DigestRow[];
  due_today: DigestRow[];
  at_risk: DigestRow[];
  live_conversation_count: number;
}

export function getDigest(): Promise<Digest> {
  return apiFetch<Digest>("/digest");
}
