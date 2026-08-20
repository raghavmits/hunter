// Funnel + daily quotas + campaign targets on one screen (issue #33).
import { useCallback, useEffect, useState } from "react";
import { getFunnel, type Funnel, type FunnelFilters, type Window } from "../api/funnel";
import { getQuotaProgress, QUOTA_LABELS, type QuotaSummary } from "../api/quota";
import { getTargets, INPUT_TARGET_LABELS, OUTCOME_TARGET_LABELS, type TargetsSummary } from "../api/targets";
import { MOTION_LABELS, ROLE_FAMILY_LABELS, type Motion, type RoleFamily } from "../api/threads";

const MOTIONS = Object.keys(MOTION_LABELS) as Motion[];
const ROLE_FAMILIES = Object.keys(ROLE_FAMILY_LABELS) as RoleFamily[];
const WINDOW_LABELS: Record<Window, string> = {
  today: "Today",
  "7d": "7 days",
  "30d": "30 days",
  all: "All time",
};

function formatConversion(rate: number | null): string {
  return rate === null ? "—" : `${Math.round(rate * 100)}%`;
}

export function FunnelPage() {
  const [filters, setFilters] = useState<FunnelFilters>({});
  const [funnel, setFunnel] = useState<Funnel | null>(null);
  const [quotas, setQuotas] = useState<QuotaSummary | null>(null);
  const [targets, setTargets] = useState<TargetsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetchFunnel = useCallback(() => getFunnel(filters).then(setFunnel), [filters]);

  useEffect(() => {
    Promise.all([refetchFunnel(), getQuotaProgress().then(setQuotas), getTargets().then(setTargets)]).catch(
      (err: unknown) => setError(err instanceof Error ? err.message : String(err)),
    );
  }, [refetchFunnel]);

  function setFilter<K extends keyof FunnelFilters>(key: K, value: FunnelFilters[K] | "") {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === "") delete next[key];
      else next[key] = value;
      return next;
    });
  }

  if (error) {
    return <p role="alert">Could not load this page: {error}</p>;
  }

  if (!funnel || !quotas || !targets) {
    return <p>Loading…</p>;
  }

  return (
    <div>
      <h1>Funnel &amp; targets</h1>

      <section>
        <h2>Funnel</h2>
        <div>
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
          <label>
            Window
            <select value={filters.window ?? "all"} onChange={(e) => setFilter("window", e.target.value as Window)}>
              {(Object.keys(WINDOW_LABELS) as Window[]).map((w) => (
                <option key={w} value={w}>
                  {WINDOW_LABELS[w]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <table>
          <thead>
            <tr>
              <th>Stage</th>
              <th>Count</th>
              <th>Conversion from previous</th>
            </tr>
          </thead>
          <tbody>
            {funnel.stages.map((s) => (
              <tr key={s.stage}>
                <td>{s.stage}</td>
                <td>{s.count}</td>
                <td>{formatConversion(s.conversion_from_previous)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Today's quotas</h2>
        <ul>
          {(Object.keys(QUOTA_LABELS) as (keyof QuotaSummary)[]).map((key) => (
            <li key={key}>
              {QUOTA_LABELS[key]}: {quotas[key].count} / {quotas[key].target} ({quotas[key].remaining} remaining)
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Campaign targets</h2>

        <h3>Inputs</h3>
        <ul>
          {(Object.keys(INPUT_TARGET_LABELS) as (keyof typeof INPUT_TARGET_LABELS)[]).map((key) => {
            const t = targets[key];
            return (
              <li key={key}>
                {INPUT_TARGET_LABELS[key]}: {t.count} / {t.target} ({t.target - t.count} remaining) — deadline:{" "}
                {t.deadline ?? "No deadline set"}
              </li>
            );
          })}
        </ul>

        <h3>Outcomes (tracked, not a quota — never a number you can fail)</h3>
        <ul>
          {(Object.keys(OUTCOME_TARGET_LABELS) as (keyof typeof OUTCOME_TARGET_LABELS)[]).map((key) => {
            const t = targets[key];
            return (
              <li key={key}>
                {OUTCOME_TARGET_LABELS[key]}: {t.count} so far
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
