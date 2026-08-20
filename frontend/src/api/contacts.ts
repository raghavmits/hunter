// Matches app/schemas/contact.py (issue #13) — only the fields quick-add (#30) needs.
import { apiFetch } from "./client";

export interface Contact {
  id: number;
  company_id: number | null;
  full_name: string;
}

export function getContacts(): Promise<Contact[]> {
  return apiFetch<Contact[]>("/contacts");
}
