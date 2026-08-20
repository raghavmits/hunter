// Matches app/schemas/company.py (issue #12).
import { apiFetch } from "./client";

export type CompanyStatus = "watchlist" | "active" | "dormant" | "closed";

export interface Company {
  id: number;
  name: string;
  url: string | null;
  why_interested: string | null;
  status: CompanyStatus;
}

export function getCompanies(): Promise<Company[]> {
  return apiFetch<Company[]>("/companies");
}

export function getCompany(companyId: number): Promise<Company> {
  return apiFetch<Company>(`/companies/${companyId}`);
}
