// The real digest (issue #28) — #26's health-check placeholder is gone.
import { useEffect, useState } from "react";
import { getDigest, type Digest } from "../api/digest";
import { getQuotaProgress, type QuotaSummary } from "../api/quota";
import { DigestSection } from "../components/DigestSection";

const QUOTA_LABELS: Record<keyof QuotaSummary, string> = {
  cold_outreach_sent: "Cold outreach sent",
  warm_intro_requests_sent: "Warm intro requests sent",
  cold_applications_submitted: "Cold applications submitted",
  referral_asks_made: "Referral asks made",
};

export function DigestPage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [quotas, setQuotas] = useState<QuotaSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getDigest(), getQuotaProgress()])
      .then(([digestResult, quotaResult]) => {
        setDigest(digestResult);
        setQuotas(quotaResult);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

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
      />

      <DigestSection
        title="Due today"
        rows={digest.due_today}
        emptyMessage="Nothing due today."
        daysColumnLabel="Days overdue"
        daysValue={(row) => row.days_overdue ?? 0}
      />

      <DigestSection
        title="At risk"
        rows={digest.at_risk}
        emptyMessage="Nothing at risk."
        daysColumnLabel="Days in stage"
        daysValue={(row) => row.days_in_stage}
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
