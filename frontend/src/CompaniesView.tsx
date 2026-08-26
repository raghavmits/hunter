import { useCallback, useEffect, useRef } from "react";
import { api } from "./api";
import { DeleteButton, SelectCell, TextCell, Toolbar, UrlCell } from "./cells";
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
      <Toolbar count={companies.length} noun="company" plural="companies" onAdd={addCompany} />

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
              <TextCell
                defaultValue={company.name ?? ""}
                placeholder="Company"
                onChange={(v) => save(company.id, { name: v })}
              />
              <SelectCell
                defaultValue={company.stage ?? ""}
                options={COMPANY_STAGES}
                onChange={(v) => save(company.id, { stage: v || null })}
              />
              <SelectCell
                defaultValue={company.interest ?? ""}
                options={INTEREST_LEVELS}
                onChange={(v) => save(company.id, { interest: v || null })}
              />
              <SelectCell
                defaultValue={company.industry ?? ""}
                options={INDUSTRIES}
                onChange={(v) => save(company.id, { industry: v || null })}
              />
              <TextCell
                defaultValue={company.role ?? ""}
                placeholder="Role"
                onChange={(v) => save(company.id, { role: v })}
              />
              <UrlCell
                defaultValue={company.url ?? ""}
                placeholder="https://…"
                onChange={(v) => save(company.id, { url: v })}
              />
              <UrlCell
                defaultValue={company.careers_page ?? ""}
                placeholder="https://…"
                onChange={(v) => save(company.id, { careers_page: v })}
              />
              <td className="derived">
                {company.contact_names.length > 0
                  ? company.contact_names.join(", ")
                  : "—"}
              </td>
              <TextCell
                defaultValue={company.notes ?? ""}
                placeholder="Notes"
                onChange={(v) => save(company.id, { notes: v })}
              />
              <DeleteButton onClick={() => deleteCompany(company.id)} />
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
