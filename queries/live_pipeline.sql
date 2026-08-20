-- Live pipeline: open threads past the initial outreach stage — i.e. an
-- actual back-and-forth is happening, not just a nudge sent into the void.
-- Matches the digest's live_conversation_count (PLAN.md FR-12e): open AND
-- stage != 'outreach'. See SCHEMA.md's "stage vs status" note — this reads
-- `stage` only after already filtering to `status = 'open'`, since a
-- closed thread's `stage` column is stale history, not current state.

SELECT
    thread.id AS thread_id,
    company.name AS company_name,
    contact.full_name AS contact_name,
    thread.role_title,
    thread.stage,
    thread.next_follow_up_date,
    thread.stage_entered_at
FROM thread
JOIN company ON company.id = thread.company_id
LEFT JOIN contact ON contact.id = thread.contact_id
WHERE thread.status = 'open'
  AND thread.stage != 'outreach'
ORDER BY thread.stage_entered_at DESC;
