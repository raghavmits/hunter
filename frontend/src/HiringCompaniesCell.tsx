import { useRef, useState } from "react";
import type { Company } from "./types";

interface Props {
  value: string;
  companies: Company[];
  onChange: (v: string) => void;
  onNavigateToCompany: (id: string) => void;
}

export function HiringCompaniesCell({ value, companies, onChange, onNavigateToCompany }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  const names = value.split(",").map((s) => s.trim()).filter(Boolean);

  const startEditing = () => {
    setDraft(value);
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const commit = () => {
    setEditing(false);
    onChange(draft);
  };

  if (editing) {
    return (
      <td>
        <input
          ref={inputRef}
          type="text"
          value={draft}
          placeholder="e.g. Acme, Globex"
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === "Enter") commit(); }}
        />
      </td>
    );
  }

  return (
    <td>
      <div className="hiring-display" onClick={startEditing}>
        {names.length === 0 ? (
          <span style={{ color: "var(--muted)" }}>—</span>
        ) : (
          names.map((name, i) => {
            const company = companies.find(
              (c) => (c.name ?? "").trim().toLowerCase() === name.toLowerCase(),
            );
            return (
              <span key={i}>
                {i > 0 && ", "}
                {company ? (
                  <span
                    className="hiring-link"
                    onClick={(e) => { e.stopPropagation(); onNavigateToCompany(company.id); }}
                  >
                    {name}
                  </span>
                ) : (
                  name
                )}
              </span>
            );
          })
        )}
      </div>
    </td>
  );
}
