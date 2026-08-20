// Matches app/schemas/contact.py (issue #13).
import { apiFetch } from "./client";

export interface Contact {
  id: number;
  company_id: number | null;
  full_name: string;
  title: string | null;
}

export function getContacts(companyId?: number): Promise<Contact[]> {
  const query = companyId !== undefined ? `?company_id=${companyId}` : "";
  return apiFetch<Contact[]>(`/contacts${query}`);
}
