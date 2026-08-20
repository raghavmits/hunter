-- Due follow-ups: open threads whose next_follow_up_date has arrived or
-- passed. This is the digest's "overdue" + "due today" sections combined
-- (PLAN.md FR-12 a/b), unsorted by days-overdue here — see SCHEMA.md's
-- "stage vs status" note for why the filter is on `status`, not `stage`.
--
-- CAVEAT: next_follow_up_date is a LOCAL calendar date (see SCHEMA.md's
-- UTC-vs-local note), but SQLite's DATE('now') is UTC. If you're running
-- this from a machine west of UTC (e.g. US timezones), DATE('now') can
-- still show "today" as UTC-tomorrow for several hours after your local
-- midnight, making a thread due at local midnight look one day early.
-- Safest read: treat a row as due if next_follow_up_date <= DATE('now'),
-- and treat anything within a day of that boundary as "check by hand" if
-- the exact day matters, rather than trusting this query's boundary to
-- the hour.

SELECT
    thread.id AS thread_id,
    company.name AS company_name,
    contact.full_name AS contact_name,
    thread.role_title,
    thread.stage,
    thread.next_follow_up_date,
    thread.nudge_number
FROM thread
JOIN company ON company.id = thread.company_id
LEFT JOIN contact ON contact.id = thread.contact_id
WHERE thread.status = 'open'
  AND thread.next_follow_up_date IS NOT NULL
  AND thread.next_follow_up_date <= DATE('now')
ORDER BY thread.next_follow_up_date ASC;
