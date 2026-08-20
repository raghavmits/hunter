// Full history of one thread, with every action inline (issue #31).
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router";
import type { Stage } from "../api/digest";
import {
  changeStage,
  createTouch,
  getThread,
  MOTION_LABELS,
  nextStage,
  ROLE_FAMILY_LABELS,
  setFollowUp,
  snoozeThread,
  TERMINAL_STATUS_LABELS,
  TOUCH_CHANNEL_LABELS,
  TOUCH_DIRECTION_LABELS,
  TOUCH_KIND_LABELS,
  type TerminalStatus,
  type ThreadDetail,
  type TouchChannel,
  type TouchDirection,
  type TouchKind,
} from "../api/threads";

const SNOOZE_OPTIONS = [1, 3, 7];

interface TimelineEntry {
  key: string;
  at: string;
  render: () => React.ReactNode;
}

function timelineEntries(thread: ThreadDetail): TimelineEntry[] {
  const entries: TimelineEntry[] = [
    {
      key: "created",
      at: thread.created_at,
      render: () => <>Thread created</>,
    },
  ];

  for (const touch of thread.touches) {
    entries.push({
      key: `touch-${touch.id}`,
      at: `${touch.occurred_at}T00:00:00`,
      render: () => (
        <>
          {TOUCH_DIRECTION_LABELS[touch.direction]} {TOUCH_KIND_LABELS[touch.kind]} via{" "}
          {TOUCH_CHANNEL_LABELS[touch.channel]}
          {touch.note ? ` — ${touch.note}` : ""}
        </>
      ),
    });
  }

  for (const event of thread.stage_events) {
    entries.push({
      key: `stage-${event.id}`,
      at: event.occurred_at,
      render: () => (
        <>
          {event.from_stage ?? "—"} → {event.to_stage}
          {event.note ? ` — ${event.note}` : ""}
        </>
      ),
    });
  }

  return entries.sort((a, b) => a.at.localeCompare(b.at));
}

export function ThreadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const threadId = Number(id);

  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [advancePrompt, setAdvancePrompt] = useState<Stage | null>(null);
  const [closePanelOpen, setClosePanelOpen] = useState(false);

  const [logKind, setLogKind] = useState<TouchKind>("cold_outreach");
  const [logDirection, setLogDirection] = useState<TouchDirection>("outbound");
  const [logChannel, setLogChannel] = useState<TouchChannel>("email");
  const [logDate, setLogDate] = useState("");
  const [logNote, setLogNote] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");

  const refetch = useCallback(() => {
    return getThread(threadId).then(setThread);
  }, [threadId]);

  useEffect(() => {
    refetch().catch((err: unknown) => setLoadError(err instanceof Error ? err.message : String(err)));
  }, [refetch]);

  async function runAction(action: () => Promise<unknown>) {
    setPending(true);
    setActionError(null);
    try {
      await action();
      await refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  }

  async function submitLog(e: React.FormEvent) {
    e.preventDefault();
    const wasInbound = logDirection === "inbound";
    const currentStage = thread?.stage;
    await runAction(() =>
      createTouch(threadId, {
        kind: logKind,
        direction: logDirection,
        channel: logChannel,
        occurred_at: logDate || undefined,
        note: logNote.trim() || undefined,
      }),
    );
    setLogNote("");
    setLogDate("");
    if (wasInbound && currentStage) {
      const next = nextStage(currentStage);
      if (next) setAdvancePrompt(next);
    }
  }

  async function submitFollowUp(e: React.FormEvent) {
    e.preventDefault();
    if (!followUpDate) return;
    await runAction(() => setFollowUp(threadId, followUpDate));
    setFollowUpDate("");
  }

  if (loadError) {
    return <p role="alert">Could not load this thread: {loadError}</p>;
  }

  if (!thread) {
    return <p>Loading…</p>;
  }

  const next = nextStage(thread.stage);

  return (
    <div>
      <h1>
        {thread.company.name}
        {thread.role_title ? ` — ${thread.role_title}` : ""}
      </h1>

      <section>
        <p>Contact: {thread.contact?.full_name ?? "—"}</p>
        <p>Role family: {thread.role_family ? ROLE_FAMILY_LABELS[thread.role_family] : "—"}</p>
        <p>Motion: {thread.motion ? MOTION_LABELS[thread.motion] : "—"}</p>
        <p>
          Stage: {thread.stage} ({thread.status})
        </p>
        <p>Next follow-up: {thread.next_follow_up_date ?? "—"}</p>
        <p>Nudge count: {thread.nudge_number}</p>
        {thread.is_ghost_suggested && <p role="alert">3 unanswered nudges — consider closing as ghosted.</p>}
      </section>

      {actionError && <p role="alert">{actionError}</p>}

      {advancePrompt && (
        <p role="alert">
          Reply logged —{" "}
          <button
            type="button"
            disabled={pending}
            onClick={() => {
              runAction(() => changeStage(threadId, advancePrompt));
              setAdvancePrompt(null);
            }}
          >
            advance to {advancePrompt}?
          </button>{" "}
          <button type="button" onClick={() => setAdvancePrompt(null)}>
            Dismiss
          </button>
        </p>
      )}

      <section>
        <h2>Log a touch</h2>
        <form onSubmit={submitLog}>
          <select value={logKind} onChange={(e) => setLogKind(e.target.value as TouchKind)}>
            {(Object.keys(TOUCH_KIND_LABELS) as TouchKind[]).map((kind) => (
              <option key={kind} value={kind}>
                {TOUCH_KIND_LABELS[kind]}
              </option>
            ))}
          </select>
          <select value={logDirection} onChange={(e) => setLogDirection(e.target.value as TouchDirection)}>
            {(Object.keys(TOUCH_DIRECTION_LABELS) as TouchDirection[]).map((direction) => (
              <option key={direction} value={direction}>
                {TOUCH_DIRECTION_LABELS[direction]}
              </option>
            ))}
          </select>
          <select value={logChannel} onChange={(e) => setLogChannel(e.target.value as TouchChannel)}>
            {(Object.keys(TOUCH_CHANNEL_LABELS) as TouchChannel[]).map((channel) => (
              <option key={channel} value={channel}>
                {TOUCH_CHANNEL_LABELS[channel]}
              </option>
            ))}
          </select>
          <input
            type="date"
            aria-label="Date (defaults to today)"
            value={logDate}
            onChange={(e) => setLogDate(e.target.value)}
          />
          <input
            type="text"
            placeholder="Note (optional)"
            value={logNote}
            onChange={(e) => setLogNote(e.target.value)}
          />
          <button type="submit" disabled={pending}>
            Log touch
          </button>
        </form>
      </section>

      <section>
        <h2>Follow-up date</h2>
        <form onSubmit={submitFollowUp}>
          <input type="date" value={followUpDate} onChange={(e) => setFollowUpDate(e.target.value)} />
          <button type="submit" disabled={pending || !followUpDate}>
            Set
          </button>
        </form>

        {SNOOZE_OPTIONS.map((days) => (
          <button key={days} type="button" disabled={pending} onClick={() => runAction(() => snoozeThread(threadId, days))}>
            Snooze +{days}
          </button>
        ))}
      </section>

      <section>
        <h2>Stage</h2>
        {next && (
          <button type="button" disabled={pending} onClick={() => runAction(() => changeStage(threadId, next))}>
            Advance to {next}
          </button>
        )}
        <button type="button" disabled={pending} onClick={() => setClosePanelOpen((open) => !open)}>
          Close
        </button>
        {closePanelOpen && (
          <div>
            {(Object.keys(TERMINAL_STATUS_LABELS) as TerminalStatus[]).map((status) => (
              <button
                key={status}
                type="button"
                disabled={pending}
                onClick={() => {
                  runAction(() => changeStage(threadId, status));
                  setClosePanelOpen(false);
                }}
              >
                {TERMINAL_STATUS_LABELS[status]}
              </button>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2>History</h2>
        <ul>
          {timelineEntries(thread).map((entry) => (
            <li key={entry.key}>
              {entry.at.slice(0, 10)} — {entry.render()}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
