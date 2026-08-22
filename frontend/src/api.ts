import type { Company, Contact } from "./types";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const api = {
  contacts: {
    list: () => request<Contact[]>("/contacts/"),
    create: (data: Partial<Contact>) =>
      request<Contact>("/contacts/", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<Contact>) =>
      request<Contact>(`/contacts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    delete: (id: string) =>
      request<void>(`/contacts/${id}`, { method: "DELETE" }),
  },
  companies: {
    list: () => request<Company[]>("/companies/"),
    create: (data: Partial<Company>) =>
      request<Company>("/companies/", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<Company>) =>
      request<Company>(`/companies/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    delete: (id: string) =>
      request<void>(`/companies/${id}`, { method: "DELETE" }),
  },
};
