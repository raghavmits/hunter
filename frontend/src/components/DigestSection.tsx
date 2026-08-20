// A plain table per digest section — explicitly not cards (issue #28).
import type { ReactNode } from "react";
import type { DigestRow } from "../api/digest";

interface Props {
  title: string;
  rows: DigestRow[];
  emptyMessage: string;
  /** Overdue/due-today show days_overdue; at-risk shows days_in_stage —
   * days_overdue is frequently null for at-risk rows (#28's own grooming). */
  daysColumnLabel: string;
  daysValue: (row: DigestRow) => number;
  /** In-place row actions (issue #29) — an extra trailing column. */
  renderActions?: (row: DigestRow) => ReactNode;
}

export function DigestSection({ title, rows, emptyMessage, daysColumnLabel, daysValue, renderActions }: Props) {
  return (
    <section>
      <h2>{title}</h2>
      {rows.length === 0 ? (
        <p>{emptyMessage}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Contact</th>
              <th>Stage</th>
              <th>{daysColumnLabel}</th>
              {renderActions && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.thread_id}>
                <td>{row.company_name}</td>
                <td>{row.contact_name ?? "—"}</td>
                <td>{row.stage}</td>
                <td>{daysValue(row)}</td>
                {renderActions && renderActions(row)}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
