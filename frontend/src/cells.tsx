interface FieldProps {
  defaultValue: string;
  placeholder?: string;
  onChange: (value: string) => void;
}

export function TextCell({ defaultValue, placeholder, onChange }: FieldProps) {
  return (
    <td>
      <input
        type="text"
        defaultValue={defaultValue}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </td>
  );
}

export function UrlCell({ defaultValue, placeholder, onChange }: FieldProps) {
  return (
    <td>
      <input
        type="url"
        defaultValue={defaultValue}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </td>
  );
}

export function DateCell({ defaultValue, onChange }: Omit<FieldProps, "placeholder">) {
  return (
    <td>
      <input type="date" defaultValue={defaultValue} onChange={(e) => onChange(e.target.value)} />
    </td>
  );
}

interface SelectCellProps {
  defaultValue: string;
  options: readonly string[];
  onChange: (value: string) => void;
}

export function SelectCell({ defaultValue, options, onChange }: SelectCellProps) {
  return (
    <td>
      <select defaultValue={defaultValue} onChange={(e) => onChange(e.target.value)}>
        <option value="">—</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </td>
  );
}

interface ToolbarProps {
  count: number;
  noun: string;
  plural?: string;
  onAdd: () => void;
}

export function Toolbar({ count, noun, plural, onAdd }: ToolbarProps) {
  return (
    <div className="toolbar">
      <button onClick={onAdd}>+ Add {noun}</button>
      <span className="count">
        {count} {count === 1 ? noun : (plural ?? `${noun}s`)}
      </span>
    </div>
  );
}

export function DeleteButton({ onClick }: { onClick: () => void }) {
  return (
    <td>
      <button className="delete-btn" onClick={onClick}>
        Delete
      </button>
    </td>
  );
}
