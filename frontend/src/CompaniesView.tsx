import { useCallback, useEffect, useRef } from "react";
import { api } from "./api";
import type { Company } from "./types";
import { COMPANY_STAGES, INDUSTRIES, INTEREST_LEVELS } from "./types";

interface Props {
  companies: Company[];
  onReload: () => void;
  highlightId: string | null;
  onHighlightDone: () => void;
}

export function CompaniesView({ companies, onReload, highlightId, onHighlightDone }: Props) {
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const rowRefs = useRef<Record<string, HTMLTableRowElement | null>>({});

  const save = useCallback(
    (id: string, patch: Partial<Company>) => {
      clearTimeout(timers.current[id]);
      timers.current[id] = setTimeout(() => api.companies.update(id, patch).then(onReload), 500);
    },
    [onReload],
  );

  useEffect(() => {
    if (!highlightId) return;
    const row = rowRefs.current[highlightId];
    if (!row) return;
    row.scrollIntoView({ behavior: "smooth", block: "center" });
    row.classList.add("row-highlight");
    const cleanup = () => row.classList.remove("row-highlight");
    row.addEventListener("animationend", cleanup, { once: true });
    onHighlightDone();
  }, [highlightId, onHighlightDone]);

  const addCompany = async () => {
    await api.companies.create({});
    onReload();
  };

  const deleteCompany = async (id: string) => {
    if (!confirm("Delete this company? This can't be undone.")) return;
    await api.companies.delete(id);
    onReload();
  };

  return (
    <section>
      <div className="toolbar">
        <button onClick={addCompany}>+ Add company</button>
        <span className="count">
          {companies.length} {companies.length === 1 ? "company" : "companies"}
        </span>
      </div>

      <table>
        <thead>
          <tr>
            <th>Company</th>
            <th>Stage</th>
            <th>Interest</th>
            <th>Industry</th>
            <th>Role</th>
            <th>URL</th>
            <th>Careers Page</th>
            <th>Contact(s)</th>
            <th>Notes</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => (
            <tr key={company.id} ref={(el) => { rowRefs.current[company.id] = el; }}>
              <td>
                <input
                  type="text"
                  defaultValue={company.name ?? ""}
                  placeholder="Company"
                  onChange={(e) => save(company.id, { name: e.target.value })}
                />
              </td>
              <td>
                <select
                  defaultValue={company.stage ?? ""}
                  onChange={(e) => save(company.id, { stage: e.target.value || null })}
                >
                  <option value="">—</option>
                  {COMPANY_STAGES.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </td>
              <td>
                <select
                  defaultValue={company.interest ?? ""}
                  onChange={(e) => save(company.id, { interest: e.target.value || null })}
                >
                  <option value="">—</option>
                  {INTEREST_LEVELS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </td>
              <td>
                <select
                  defaultValue={company.industry ?? ""}
                  onChange={(e) => save(company.id, { industry: e.target.value || null })}
                >
                  <option value="">—</option>
                  {INDUSTRIES.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </td>
              <td>
                <input
                  type="text"
                  defaultValue={company.role ?? ""}
                  placeholder="Role"
                  onChange={(e) => save(company.id, { role: e.target.value })}
                />
              </td>
              <td>
                <input
                  type="url"
                  defaultValue={company.url ?? ""}
                  placeholder="https://…"
                  onChange={(e) => save(company.id, { url: e.target.value })}
                />
              </td>
              <td>
                <input
                  type="url"
                  defaultValue={company.careers_page ?? ""}
                  placeholder="https://…"
                  onChange={(e) => save(company.id, { careers_page: e.target.value })}
                />
              </td>
              <td className="derived">
                {company.contact_names.length > 0
                  ? company.contact_names.join(", ")
                  : "—"}
              </td>
              <td>
                <input
                  type="text"
                  defaultValue={company.notes ?? ""}
                  placeholder="Notes"
                  onChange={(e) => save(company.id, { notes: e.target.value })}
                />
              </td>
              <td>
                <button className="delete-btn" onClick={() => deleteCompany(company.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
