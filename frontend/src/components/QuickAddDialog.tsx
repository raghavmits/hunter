// Add a pursuit in under 15 seconds, from anywhere, without the mouse (issue #30).
import { useRef, useState } from "react";
import type { Company } from "../api/companies";
import { getCompanies } from "../api/companies";
import type { Contact } from "../api/contacts";
import { getContacts } from "../api/contacts";
import {
  createThread,
  MOTION_LABELS,
  ROLE_FAMILY_LABELS,
  type Motion,
  type RoleFamily,
} from "../api/threads";

const DEFAULTS_KEY = "hunter.quickAddDefaults";

interface StoredDefaults {
  motion?: Motion;
  role_family?: RoleFamily;
}

function loadDefaults(): StoredDefaults {
  try {
    const raw = localStorage.getItem(DEFAULTS_KEY);
    return raw ? (JSON.parse(raw) as StoredDefaults) : {};
  } catch {
    return {};
  }
}

function saveDefaults(defaults: StoredDefaults): void {
  localStorage.setItem(DEFAULTS_KEY, JSON.stringify(defaults));
}

export function QuickAddDialog() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [companyName, setCompanyName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [roleFamily, setRoleFamily] = useState<RoleFamily | "">("");
  const [contactId, setContactId] = useState<number | "">("");
  const [motion, setMotion] = useState<Motion | "">("");
  const [jdUrl, setJdUrl] = useState("");
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function open() {
    const defaults = loadDefaults();
    setCompanyName("");
    setRoleTitle("");
    setRoleFamily(defaults.role_family ?? "");
    setContactId("");
    setMotion(defaults.motion ?? "");
    setJdUrl("");
    setError(null);
    Promise.all([getContacts(), getCompanies()])
      .then(([contactList, companyList]) => {
        setContacts(contactList);
        setCompanies(companyList);
      })
      .catch(() => {
        setContacts([]);
        setCompanies([]);
      });
    dialogRef.current?.showModal();
  }

  function companyLabel(companyId: number | null): string {
    if (companyId === null) return "";
    const company = companies.find((c) => c.id === companyId);
    return company ? ` (${company.name})` : "";
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!companyName.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await createThread({
        company_name: companyName.trim(),
        role_title: roleTitle.trim() || undefined,
        role_family: roleFamily || undefined,
        contact_id: contactId === "" ? undefined : contactId,
        motion: motion || undefined,
        jd_url: jdUrl.trim() || undefined,
      });
      saveDefaults({ motion: motion || undefined, role_family: roleFamily || undefined });
      dialogRef.current?.close();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button type="button" onClick={open}>
        + Quick add
      </button>
      <dialog ref={dialogRef}>
        <form onSubmit={handleSubmit}>
          <h2>Quick add</h2>

          <div>
            <label htmlFor="quick-add-company">Company</label>
            <input
              id="quick-add-company"
              type="text"
              autoFocus
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="quick-add-role-title">Role title</label>
            <input
              id="quick-add-role-title"
              type="text"
              value={roleTitle}
              onChange={(e) => setRoleTitle(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="quick-add-role-family">Role family</label>
            <select
              id="quick-add-role-family"
              value={roleFamily}
              onChange={(e) => setRoleFamily(e.target.value as RoleFamily | "")}
            >
              <option value="">—</option>
              {(Object.keys(ROLE_FAMILY_LABELS) as RoleFamily[]).map((rf) => (
                <option key={rf} value={rf}>
                  {ROLE_FAMILY_LABELS[rf]}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="quick-add-contact">Contact</label>
            <select
              id="quick-add-contact"
              value={contactId}
              onChange={(e) => setContactId(e.target.value === "" ? "" : Number(e.target.value))}
            >
              <option value="">—</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.full_name}
                  {companyLabel(contact.company_id)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="quick-add-motion">Motion</label>
            <select
              id="quick-add-motion"
              value={motion}
              onChange={(e) => setMotion(e.target.value as Motion | "")}
            >
              <option value="">—</option>
              {(Object.keys(MOTION_LABELS) as Motion[]).map((m) => (
                <option key={m} value={m}>
                  {MOTION_LABELS[m]}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="quick-add-jd-url">JD URL</label>
            <input id="quick-add-jd-url" type="text" value={jdUrl} onChange={(e) => setJdUrl(e.target.value)} />
          </div>

          {error && <p role="alert">Could not add: {error}</p>}

          <button type="submit" disabled={submitting}>
            Add
          </button>
          <button type="button" onClick={() => dialogRef.current?.close()}>
            Cancel
          </button>
        </form>
      </dialog>
    </>
  );
}
