// Filterable threads list (issue #32) — replaces #26's placeholder.
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import type { Stage } from "../api/digest";
import {
  listThreads,
  logTouch,
  MOTION_LABELS,
  ROLE_FAMILY_LABELS,
  type Motion,
  type RoleFamily,
  type ThreadListFilters,
  type ThreadListItem,
  type ThreadStatus,
  type TouchKind,
} from "../api/threads";
import { QuickLogControl } from "../components/QuickLogControl";

const STAGES: Stage[] = ["outreach", "replied", "screen", "interview", "offer"];
const STATUSES: ThreadStatus[] = ["open", "rejected", "ghosted", "withdrawn", "closed"];
const MOTIONS = Object.keys(MOTION_LABELS) as Motion[];
const ROLE_FAMILIES = Object.keys(ROLE_FAMILY_LABELS) as RoleFamily[];

export function ThreadsPage() {
  const [filters, setFilters] = useState<ThreadListFilters>({});
  const [threads, setThreads] = useState<ThreadListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [rowErrors, setRowErrors] = useState<Record<number, string>>({});

  const refetch = useCallback(() => listThreads(filters).then(setThreads), [filters]);

  useEffect(() => {
    refetch().catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [refetch]);

  function setFilter<K extends keyof ThreadListFilters>(key: K, value: ThreadListFilters[K] | "") {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === "") delete next[key];
      else next[key] = value;
      return next;
    });
  }

  async function handleLog(threadId: number, kind: TouchKind, note: string | undefined) {
    setPendingId(threadId);
    setRowErrors((prev) => ({ ...prev, [threadId]: "" }));
    try {
      await logTouch(threadId, kind, note);
      await refetch();
    } catch (err) {
      setRowErrors((prev) => ({ ...prev, [threadId]: err instanceof Error ? err.message : String(err) }));
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div>
      <h1>Threads</h1>

      <p>
        <Link to="/threads/bulk">Bulk outreach</Link>
      </p>

      <div>
        <label>
          Status
          <select value={filters.status ?? ""} onChange={(e) => setFilter("status", e.target.value as ThreadStatus | "")}>
            <option value="">Any</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Stage
          <select value={filters.stage ?? ""} onChange={(e) => setFilter("stage", e.target.value as Stage | "")}>
            <option value="">Any</option>
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Motion
          <select value={filters.motion ?? ""} onChange={(e) => setFilter("motion", e.target.value as Motion | "")}>
            <option value="">Any</option>
            {MOTIONS.map((m) => (
              <option key={m} value={m}>
                {MOTION_LABELS[m]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Role family
          <select
            value={filters.role_family ?? ""}
            onChange={(e) => setFilter("role_family", e.target.value as RoleFamily | "")}
          >
            <option value="">Any</option>
            {ROLE_FAMILIES.map((rf) => (
              <option key={rf} value={rf}>
                {ROLE_FAMILY_LABELS[rf]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p role="alert">Could not load threads: {error}</p>}

      {!error && !threads && <p>Loading…</p>}

      {!error && threads && threads.length === 0 && <p>No threads match these filters.</p>}

      {!error && threads && threads.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Company</th>
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
                  <Link to={`/companies/${thread.company_id}`}>{thread.company_name}</Link>
                </td>
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
    </div>
  );
}
