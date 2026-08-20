-- At-risk threads: open threads stuck in the same stage for more than the
-- configured threshold (config.yaml's at_risk_threshold_days, currently
-- 8 — SQL can't read config.yaml, so the "8" below is a literal that must
-- be kept in sync by hand if that value ever changes).
--
-- Unlike due_follow_ups.sql, there's no UTC-vs-local mismatch here:
-- stage_entered_at is a UTC instant and DATETIME('now', ...) is UTC too,
-- so this comparison is apples-to-apples (see SCHEMA.md).

SELECT
    thread.id AS thread_id,
    company.name AS company_name,
    contact.full_name AS contact_name,
    thread.role_title,
    thread.stage,
    thread.stage_entered_at,
    CAST(JULIANDAY('now') - JULIANDAY(thread.stage_entered_at) AS INTEGER) AS days_in_stage
FROM thread
JOIN company ON company.id = thread.company_id
LEFT JOIN contact ON contact.id = thread.contact_id
WHERE thread.status = 'open'
  AND thread.stage_entered_at <= DATETIME('now', '-8 days')
ORDER BY thread.stage_entered_at ASC;
