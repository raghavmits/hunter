// Ten cold outreaches are ten rows in one screen, not ten form submissions
// (PLAN.md §8, countermeasure 6) — issue #34.
import { useEffect, useRef, useState } from "react";
import type { Contact } from "../api/contacts";
import { getContacts } from "../api/contacts";
import {
  bulkOutreach,
  TOUCH_CHANNEL_LABELS,
  TOUCH_KIND_LABELS,
  type TouchChannel,
  type TouchKind,
} from "../api/threads";

const INITIAL_ROW_COUNT = 5;

interface Row {
  key: number;
  companyName: string;
  contactId: number | "";
  roleTitle: string;
  error: string | null;
}

function makeRow(key: number): Row {
  return { key, companyName: "", contactId: "", roleTitle: "", error: null };
}

export function BulkOutreachPage() {
  const nextKey = useRef(0);
  const [rows, setRows] = useState<Row[]>([]);
  const [kind, setKind] = useState<TouchKind>("cold_outreach");
  const [channel, setChannel] = useState<TouchChannel>("email");
  const [date, setDate] = useState("");
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);

  useEffect(() => {
    const initial = Array.from({ length: INITIAL_ROW_COUNT }, () => makeRow(nextKey.current++));
    setRows(initial);
    getContacts()
      .then(setContacts)
      .catch(() => setContacts([]));
  }, []);

  function addRow() {
    setRows((prev) => [...prev, makeRow(nextKey.current++)]);
  }

  function removeRow(key: number) {
    setRows((prev) => prev.filter((r) => r.key !== key));
  }

  function updateRow(key: number, fields: Partial<Row>) {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...fields } : r)));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const submittable = rows.filter((r) => r.companyName.trim() !== "");
    if (submittable.length === 0) return;

    setSubmitting(true);
    setPageError(null);
    setSummary(null);
    try {
      const result = await bulkOutreach({
        kind,
        channel,
        occurred_at: date || undefined,
        rows: submittable.map((r) => ({
          company_name: r.companyName,
          contact_id: r.contactId === "" ? undefined : r.contactId,
          role_title: r.roleTitle.trim() || undefined,
        })),
      });

      const succeededKeys = new Set<number>();
      const errorsByKey = new Map<number, string>();
      result.results.forEach((rowResult, i) => {
        const row = submittable[i];
        if (rowResult.success) succeededKeys.add(row.key);
        else errorsByKey.set(row.key, rowResult.error ?? "Failed");
      });

      setRows((prev) =>
        prev
          .filter((r) => !succeededKeys.has(r.key))
          .map((r) => (errorsByKey.has(r.key) ? { ...r, error: errorsByKey.get(r.key) ?? null } : r)),
      );

      const succeeded = succeededKeys.size;
      const failed = errorsByKey.size;
      setSummary(`${succeeded} added, ${failed} failed`);
    } catch (err) {
      setPageError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Bulk outreach</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label>
            Kind
            <select value={kind} onChange={(e) => setKind(e.target.value as TouchKind)}>
              {(Object.keys(TOUCH_KIND_LABELS) as TouchKind[]).map((k) => (
                <option key={k} value={k}>
                  {TOUCH_KIND_LABELS[k]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Channel
            <select value={channel} onChange={(e) => setChannel(e.target.value as TouchChannel)}>
              {(Object.keys(TOUCH_CHANNEL_LABELS) as TouchChannel[]).map((c) => (
                <option key={c} value={c}>
                  {TOUCH_CHANNEL_LABELS[c]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Date
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
        </div>

        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Contact</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key}>
                <td>
                  <input
                    type="text"
                    disabled={submitting}
                    value={row.companyName}
                    onChange={(e) => updateRow(row.key, { companyName: e.target.value, error: null })}
                  />
                  {row.error && <p role="alert">{row.error}</p>}
                </td>
                <td>
                  <select
                    disabled={submitting}
                    value={row.contactId}
                    onChange={(e) =>
                      updateRow(row.key, { contactId: e.target.value === "" ? "" : Number(e.target.value) })
                    }
                  >
                    <option value="">—</option>
                    {contacts.map((contact) => (
                      <option key={contact.id} value={contact.id}>
                        {contact.full_name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="text"
                    disabled={submitting}
                    value={row.roleTitle}
                    onChange={(e) => updateRow(row.key, { roleTitle: e.target.value })}
                  />
                </td>
                <td>
                  <button type="button" disabled={submitting} onClick={() => removeRow(row.key)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <button type="button" disabled={submitting} onClick={addRow}>
          Add row
        </button>
        <button type="submit" disabled={submitting}>
          Submit all
        </button>
      </form>

      {summary && <p>{summary}</p>}
      {pageError && <p role="alert">Could not submit: {pageError}</p>}
    </div>
  );
}
