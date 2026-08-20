// One company's details, contacts, and threads (issue #32).
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { getCompany, type Company } from "../api/companies";
import { getContacts, type Contact } from "../api/contacts";
import { listThreads, logTouch, MOTION_LABELS, ROLE_FAMILY_LABELS, type ThreadListItem, type TouchKind } from "../api/threads";
import { QuickLogControl } from "../components/QuickLogControl";

export function CompanyPage() {
  const { id } = useParams<{ id: string }>();
  const companyId = Number(id);

  const [company, setCompany] = useState<Company | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [threads, setThreads] = useState<ThreadListItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [rowErrors, setRowErrors] = useState<Record<number, string>>({});

  const refetchThreads = useCallback(() => listThreads({ company_id: companyId }).then(setThreads), [companyId]);

  useEffect(() => {
    Promise.all([getCompany(companyId), getContacts(companyId), refetchThreads()])
      .then(([companyResult, contactsResult]) => {
        setCompany(companyResult);
        setContacts(contactsResult);
      })
      .catch((err: unknown) => setLoadError(err instanceof Error ? err.message : String(err)));
  }, [companyId, refetchThreads]);

  async function handleLog(threadId: number, kind: TouchKind, note: string | undefined) {
    setPendingId(threadId);
    setRowErrors((prev) => ({ ...prev, [threadId]: "" }));
    try {
      await logTouch(threadId, kind, note);
      await refetchThreads();
    } catch (err) {
      setRowErrors((prev) => ({ ...prev, [threadId]: err instanceof Error ? err.message : String(err) }));
    } finally {
      setPendingId(null);
    }
  }

  if (loadError) {
    return <p role="alert">Could not load this company: {loadError}</p>;
  }

  if (!company) {
    return <p>Loading…</p>;
  }

  return (
    <div>
      <h1>{company.name}</h1>
      <p>Status: {company.status}</p>
      {company.url && (
        <p>
          <a href={company.url} target="_blank" rel="noreferrer">
            {company.url}
          </a>
        </p>
      )}
      {company.why_interested && <p>{company.why_interested}</p>}

      <section>
        <h2>Contacts</h2>
        {contacts.length === 0 ? (
          <p>No contacts yet.</p>
        ) : (
          <ul>
            {contacts.map((contact) => (
              <li key={contact.id}>
                {contact.full_name}
                {contact.title ? ` — ${contact.title}` : ""}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Threads</h2>
        {threads.length === 0 ? (
          <p>No threads yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>Stage</th>
                <th>Status</th>
                <th>Motion</th>
                <th>Role family</th>
                <th>Next follow-up</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {threads.map((thread) => (
                <tr key={thread.id}>
                  <td>
                    <Link to={`/threads/${thread.id}`}>{thread.role_title ?? "—"}</Link>
                  </td>
                  <td>{thread.stage}</td>
                  <td>{thread.status}</td>
                  <td>{thread.motion ? MOTION_LABELS[thread.motion] : "—"}</td>
                  <td>{thread.role_family ? ROLE_FAMILY_LABELS[thread.role_family] : "—"}</td>
                  <td>{thread.next_follow_up_date ?? "—"}</td>
                  <td>
                    <QuickLogControl
                      pending={pendingId === thread.id}
                      onLog={(kind, note) => handleLog(thread.id, kind, note)}
                    />
                    {rowErrors[thread.id] && <p role="alert">{rowErrors[thread.id]}</p>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
