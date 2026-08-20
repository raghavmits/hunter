// In-place digest row actions: log, snooze, advance, close (issue #29).
import { useState } from "react";
import type { DigestRow, Stage } from "../api/digest";
import { TERMINAL_STATUS_LABELS, TOUCH_KIND_LABELS, type TerminalStatus, type TouchKind } from "../api/threads";

const STAGE_ORDER: Stage[] = ["outreach", "replied", "screen", "interview", "offer"];
const SNOOZE_OPTIONS = [1, 3, 7];

interface Props {
  row: DigestRow;
  pending: boolean;
  error: string | null;
  onLog: (kind: TouchKind, note: string | undefined) => void;
  onSnooze: (businessDays: number) => void;
  onAdvance: (to: Stage) => void;
  onClose: (to: TerminalStatus) => void;
}

export function RowActions({ row, pending, error, onLog, onSnooze, onAdvance, onClose }: Props) {
  const [openPanel, setOpenPanel] = useState<"log" | "close" | null>(null);
  const [logKind, setLogKind] = useState<TouchKind>("cold_outreach");
  const [logNote, setLogNote] = useState("");

  const stageIndex = STAGE_ORDER.indexOf(row.stage);
  const nextStage = stageIndex >= 0 && stageIndex < STAGE_ORDER.length - 1 ? STAGE_ORDER[stageIndex + 1] : null;

  function submitLog() {
    onLog(logKind, logNote.trim() || undefined);
    setLogNote("");
    setOpenPanel(null);
  }

  return (
    <td>
      {row.is_ghost_suggested && (
        <p role="alert">
          3 unanswered nudges —{" "}
          <button type="button" disabled={pending} onClick={() => onClose("ghosted")}>
            Close as ghosted?
          </button>
        </p>
      )}

      <button type="button" disabled={pending} onClick={() => setOpenPanel(openPanel === "log" ? null : "log")}>
        Log
      </button>

      {SNOOZE_OPTIONS.map((days) => (
        <button key={days} type="button" disabled={pending} onClick={() => onSnooze(days)}>
          Snooze +{days}
        </button>
      ))}

      {nextStage && (
        <button type="button" disabled={pending} onClick={() => onAdvance(nextStage)}>
          Advance to {nextStage}
        </button>
      )}

      <button type="button" disabled={pending} onClick={() => setOpenPanel(openPanel === "close" ? null : "close")}>
        Close
      </button>

      {openPanel === "log" && (
        <div>
          <select value={logKind} onChange={(e) => setLogKind(e.target.value as TouchKind)}>
            {(Object.keys(TOUCH_KIND_LABELS) as TouchKind[]).map((kind) => (
              <option key={kind} value={kind}>
                {TOUCH_KIND_LABELS[kind]}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Note (optional)"
            value={logNote}
            onChange={(e) => setLogNote(e.target.value)}
          />
          <button type="button" disabled={pending} onClick={submitLog}>
            Submit
          </button>
          <button type="button" onClick={() => setOpenPanel(null)}>
            Cancel
          </button>
        </div>
      )}

      {openPanel === "close" && (
        <div>
          {(Object.keys(TERMINAL_STATUS_LABELS) as TerminalStatus[]).map((status) => (
            <button
              key={status}
              type="button"
              disabled={pending}
              onClick={() => {
                onClose(status);
                setOpenPanel(null);
              }}
            >
              {TERMINAL_STATUS_LABELS[status]}
            </button>
          ))}
          <button type="button" onClick={() => setOpenPanel(null)}>
            Cancel
          </button>
        </div>
      )}

      {error && <p role="alert">{error}</p>}
    </td>
  );
}
