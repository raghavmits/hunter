-- Funnel this week: distinct threads reaching each of the 5 pipeline
-- stages, in a rolling 7-day window ending now — NOT a calendar week
-- (Monday-to-now). Matches the app's own funnel endpoint's window=7d
-- (issue #22), so this doesn't quietly disagree with what the app itself
-- reports for "recent." stage_event.occurred_at is a UTC instant (see
-- SCHEMA.md), so the window boundary below is UTC too.
--
-- Counts DISTINCT thread_id, not raw stage_event rows — a thread that
-- bounces back into a stage more than once (a backward correction) would
-- otherwise be double-counted. Restricted to the 5 pipeline stages;
-- terminal transitions (rejected/ghosted/withdrawn/closed) aren't part of
-- the funnel. This gives raw per-stage counts, not conversion rates —
-- the app's /api/funnel endpoint computes those; this is the building
-- block, not a replacement.

SELECT
    to_stage AS stage,
    COUNT(DISTINCT thread_id) AS threads_reached
FROM stage_event
WHERE to_stage IN ('outreach', 'replied', 'screen', 'interview', 'offer')
  AND occurred_at >= DATETIME('now', '-7 days')
GROUP BY to_stage
ORDER BY CASE to_stage
    WHEN 'outreach' THEN 1
    WHEN 'replied' THEN 2
    WHEN 'screen' THEN 3
    WHEN 'interview' THEN 4
    WHEN 'offer' THEN 5
END;
