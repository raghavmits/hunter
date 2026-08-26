import { useCallback, useRef } from "react";
import { api } from "./api";
import { DateCell, DeleteButton, SelectCell, TextCell, Toolbar } from "./cells";
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
      <Toolbar count={contacts.length} noun="contact" onAdd={addContact} />

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
              <TextCell
                defaultValue={contact.name ?? ""}
                placeholder="Name"
                onChange={(v) => save(contact.id, { name: v })}
              />
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
              <TextCell
                defaultValue={contact.title ?? ""}
                placeholder="Title"
                onChange={(v) => save(contact.id, { title: v })}
              />
              <SelectCell
                defaultValue={contact.contact_mode ?? ""}
                options={CONTACT_MODES}
                onChange={(v) => save(contact.id, { contact_mode: v || null })}
              />
              <SelectCell
                defaultValue={contact.warmth ?? ""}
                options={WARMTH_LEVELS}
                onChange={(v) => save(contact.id, { warmth: v || null })}
              />
              <DateCell
                defaultValue={contact.last_connected ?? ""}
                onChange={(v) => save(contact.id, { last_connected: v || null })}
              />
              <DateCell
                defaultValue={contact.next_follow_up ?? ""}
                onChange={(v) => save(contact.id, { next_follow_up: v || null })}
              />
              <SelectCell
                defaultValue={contact.status ?? ""}
                options={STATUSES}
                onChange={(v) => save(contact.id, { status: v || null })}
              />
              <HiringCompaniesCell
                value={contact.hiring_companies ?? ""}
                companies={companies}
                onChange={(v) => save(contact.id, { hiring_companies: v || null })}
                onNavigateToCompany={onNavigateToCompany}
              />
              <TextCell
                defaultValue={contact.notes ?? ""}
                placeholder="Notes"
                onChange={(v) => save(contact.id, { notes: v })}
              />
              <DeleteButton onClick={() => deleteContact(contact.id)} />
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
