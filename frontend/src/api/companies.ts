// Matches app/schemas/company.py (issue #12) — only the fields quick-add (#30) needs,
// to label the contact picker with a disambiguating company name.
import { apiFetch } from "./client";

export interface Company {
  id: number;
  name: string;
}

export function getCompanies(): Promise<Company[]> {
  return apiFetch<Company[]>("/companies");
}
