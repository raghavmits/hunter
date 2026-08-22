import { useCallback, useRef } from "react";
import { api } from "./api";
import { HiringCompaniesCell } from "./HiringCompaniesCell";
import type { Company, Contact } from "./types";
import { CONTACT_MODES, STATUSES, WARMTH_LEVELS } from "./types";

interface Props {
  contacts: Contact[];
  companies: Company[];
  onReload: () => void;
  onNavigateToCompany: (id: string) => void;
}

export function ContactsView({ contacts, companies, onReload, onNavigateToCompany }: Props) {
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const save = useCallback(
    (id: string, patch: Partial<Contact>) => {
      clearTimeout(timers.current[id]);
      timers.current[id] = setTimeout(() => api.contacts.update(id, patch).then(onReload), 500);
    },
    [onReload],
  );

  const addContact = async () => {
    await api.contacts.create({});
    onReload();
  };

  const deleteContact = async (id: string) => {
    if (!confirm("Delete this contact? This can't be undone.")) return;
    await api.contacts.delete(id);
    onReload();
  };

  const sortedCompanies = [...companies].sort((a, b) =>
    (a.name ?? "").localeCompare(b.name ?? ""),
  );

  return (
    <section>
      <div className="toolbar">
        <button onClick={addContact}>+ Add contact</button>
        <span className="count">
          {contacts.length} {contacts.length === 1 ? "contact" : "contacts"}
        </span>
      </div>

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Company</th>
            <th>Role/Title</th>
            <th>Contact Mode</th>
            <th>Warmth</th>
            <th>Last Connected</th>
            <th>Next Follow-up</th>
            <th>Status</th>
            <th>Hiring Companies</th>
            <th>Notes</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr key={contact.id}>
              <td>
                <input
                  type="text"
                  defaultValue={contact.name ?? ""}
                  placeholder="Name"
                  onChange={(e) => save(contact.id, { name: e.target.value })}
                />
              </td>
              <td>
                <select
                  defaultValue={contact.company_id ?? ""}
                  onChange={async (e) => {
                    if (e.target.value === "__new__") {
                      const name = prompt("New company name:");
                      if (name?.trim()) {
                        const created = await api.companies.create({ name: name.trim() });
                        await api.contacts.update(contact.id, { company_id: created.id });
                        onReload();
                      } else {
                        e.target.value = contact.company_id ?? "";
                      }
                    } else {
                      await api.contacts.update(contact.id, { company_id: e.target.value || null });
                      onReload();
                    }
                  }}
                >
                  <option value="">— none —</option>
                  {sortedCompanies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name || "(unnamed)"}
                    </option>
                  ))}
                  <option value="__new__">+ Add new company…</option>
                </select>
              </td>
              <td>
                <input
                  type="text"
                  defaultValue={contact.title ?? ""}
                  placeholder="Title"
                  onChange={(e) => save(contact.id, { title: e.target.value })}
                />
              </td>
              <td>
                <select
                  defaultValue={contact.contact_mode ?? ""}
                  onChange={(e) => save(contact.id, { contact_mode: e.target.value || null })}
                >
                  <option value="">—</option>
                  {CONTACT_MODES.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </td>
              <td>
                <select
                  defaultValue={contact.warmth ?? ""}
                  onChange={(e) => save(contact.id, { warmth: e.target.value || null })}
                >
                  <option value="">—</option>
                  {WARMTH_LEVELS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </td>
              <td>
                <input
                  type="date"
                  defaultValue={contact.last_connected ?? ""}
                  onChange={(e) => save(contact.id, { last_connected: e.target.value || null })}
                />
              </td>
              <td>
                <input
                  type="date"
                  defaultValue={contact.next_follow_up ?? ""}
                  onChange={(e) => save(contact.id, { next_follow_up: e.target.value || null })}
                />
              </td>
              <td>
                <select
                  defaultValue={contact.status ?? ""}
                  onChange={(e) => save(contact.id, { status: e.target.value || null })}
                >
                  <option value="">—</option>
                  {STATUSES.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </td>
              <td>
                <HiringCompaniesCell
                  value={contact.hiring_companies ?? ""}
                  companies={companies}
                  onChange={(v) => save(contact.id, { hiring_companies: v || null })}
                  onNavigateToCompany={onNavigateToCompany}
                />
              </td>
              <td>
                <input
                  type="text"
                  defaultValue={contact.notes ?? ""}
                  placeholder="Notes"
                  onChange={(e) => save(contact.id, { notes: e.target.value })}
                />
              </td>
              <td>
                <button className="delete-btn" onClick={() => deleteContact(contact.id)}>
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
