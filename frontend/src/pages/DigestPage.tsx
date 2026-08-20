// The real digest (issue #28) — #26's health-check placeholder is gone.
import { useCallback, useEffect, useState } from "react";
import { getDigest, type Digest, type Stage } from "../api/digest";
import { getQuotaProgress, QUOTA_LABELS, type QuotaSummary } from "../api/quota";
import { changeStage, logTouch, snoozeThread, type TerminalStatus, type TouchKind } from "../api/threads";
import { DigestSection } from "../components/DigestSection";
import { RowActions } from "../components/RowActions";

export function DigestPage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [quotas, setQuotas] = useState<QuotaSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [rowErrors, setRowErrors] = useState<Record<number, string>>({});

  const refetch = useCallback(() => {
    return Promise.all([getDigest(), getQuotaProgress()]).then(([digestResult, quotaResult]) => {
      setDigest(digestResult);
      setQuotas(quotaResult);
    });
  }, []);

  useEffect(() => {
    refetch().catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [refetch]);

  async function runAction(threadId: number, action: () => Promise<unknown>) {
    setPendingId(threadId);
    setRowErrors((prev) => ({ ...prev, [threadId]: "" }));
    try {
      await action();
      await refetch();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setRowErrors((prev) => ({ ...prev, [threadId]: message }));
    } finally {
      setPendingId(null);
    }
  }

  function renderActions(row: Digest["overdue"][number]) {
    return (
      <RowActions
        row={row}
        pending={pendingId === row.thread_id}
        error={rowErrors[row.thread_id] || null}
        onLog={(kind: TouchKind, note) => runAction(row.thread_id, () => logTouch(row.thread_id, kind, note))}
        onSnooze={(days) => runAction(row.thread_id, () => snoozeThread(row.thread_id, days))}
        onAdvance={(to: Stage) => runAction(row.thread_id, () => changeStage(row.thread_id, to))}
        onClose={(to: TerminalStatus) => runAction(row.thread_id, () => changeStage(row.thread_id, to))}
      />
    );
  }

  if (error) {
    return (
      <div>
        <h1>Digest</h1>
        <p role="alert">Could not load the digest: {error}</p>
      </div>
    );
  }

  if (!digest || !quotas) {
    return (
      <div>
        <h1>Digest</h1>
        <p>Loading…</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Digest</h1>

      <DigestSection
        title="Overdue"
        rows={digest.overdue}
        emptyMessage="Nothing overdue."
        daysColumnLabel="Days overdue"
        daysValue={(row) => row.days_overdue ?? 0}
        renderActions={renderActions}
      />

      <DigestSection
        title="Due today"
        rows={digest.due_today}
        emptyMessage="Nothing due today."
        daysColumnLabel="Days overdue"
        daysValue={(row) => row.days_overdue ?? 0}
        renderActions={renderActions}
      />

      <DigestSection
        title="At risk"
        rows={digest.at_risk}
        emptyMessage="Nothing at risk."
        daysColumnLabel="Days in stage"
        daysValue={(row) => row.days_in_stage}
        renderActions={renderActions}
      />

      <section>
        <h2>Today</h2>
        <p>Live conversations: {digest.live_conversation_count}</p>
        <ul>
          {(Object.keys(QUOTA_LABELS) as (keyof QuotaSummary)[]).map((key) => (
            <li key={key}>
              {QUOTA_LABELS[key]}: {quotas[key].count} / {quotas[key].target}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
