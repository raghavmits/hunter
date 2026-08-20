// In-place digest row actions: log, snooze, advance, close (issue #29).
import { useState } from "react";
import type { DigestRow, Stage } from "../api/digest";
import {
  nextStage as computeNextStage,
  TERMINAL_STATUS_LABELS,
  type TerminalStatus,
  type TouchKind,
} from "../api/threads";
import { QuickLogControl } from "./QuickLogControl";

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
  const [openPanel, setOpenPanel] = useState<"close" | null>(null);

  const next = computeNextStage(row.stage);

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

      <QuickLogControl pending={pending} onLog={onLog} />

      {SNOOZE_OPTIONS.map((days) => (
        <button key={days} type="button" disabled={pending} onClick={() => onSnooze(days)}>
          Snooze +{days}
        </button>
      ))}

      {next && (
        <button type="button" disabled={pending} onClick={() => onAdvance(next)}>
          Advance to {next}
        </button>
      )}

      <button type="button" disabled={pending} onClick={() => setOpenPanel(openPanel === "close" ? null : "close")}>
        Close
      </button>

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
