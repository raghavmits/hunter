// A one-click-to-open, kind+note log-touch control — always outbound/email,
// per FR-5's three-field description (#29). Shared by RowActions, the threads
// list, and the company page (#32) so there's one implementation, not three.
import { useState } from "react";
import { TOUCH_KIND_LABELS, type TouchKind } from "../api/threads";

interface Props {
  pending: boolean;
  onLog: (kind: TouchKind, note: string | undefined) => void;
}

export function QuickLogControl({ pending, onLog }: Props) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<TouchKind>("cold_outreach");
  const [note, setNote] = useState("");

  function submit() {
    onLog(kind, note.trim() || undefined);
    setNote("");
    setOpen(false);
  }

  return (
    <>
      <button type="button" disabled={pending} onClick={() => setOpen((o) => !o)}>
        Log
      </button>
      {open && (
        <div>
          <select value={kind} onChange={(e) => setKind(e.target.value as TouchKind)}>
            {(Object.keys(TOUCH_KIND_LABELS) as TouchKind[]).map((k) => (
              <option key={k} value={k}>
                {TOUCH_KIND_LABELS[k]}
              </option>
            ))}
          </select>
          <input type="text" placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          <button type="button" disabled={pending} onClick={submit}>
            Submit
          </button>
          <button type="button" onClick={() => setOpen(false)}>
            Cancel
          </button>
        </div>
      )}
    </>
  );
}
