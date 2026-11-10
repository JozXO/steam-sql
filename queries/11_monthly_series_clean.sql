-- Q11. The monthly series that the forecasts use: review volume and positive share,
-- one row per language and month.
-- It is the SAME clean sample as the study (Q2):
--   * July to September 2024 (the review bomb) is left out, and nothing before it is used
--     (the shared window starts on 20 July 2024 anyway), so every series starts in October 2024;
--   * the last month in the data is only part of a month (the data ends on 21 September 2026),
--     so it is dropped too: a part-month would look like a collapse.
-- That leaves 23 full months per language, October 2024 to August 2026.
-- The statement is saved as a view called monthly_series so Q12 and Q13 can read it.
-- Positive share is kept unrounded here (rounded only for display).

CREATE OR REPLACE VIEW monthly_series AS
WITH win AS (                        -- end of the data: the earliest last-review time of the five languages
    SELECT min(last_at) AS win_end
    FROM (SELECT max(created_at) AS last_at FROM reviews GROUP BY language)
)
SELECT r.language,
       r.month,
       count(*)                AS reviews,
       100.0 * avg(r.voted_up) AS positive_pct
FROM reviews r
CROSS JOIN win w
WHERE r.month >= DATE '2024-10-01'                -- first month after the bomb period (Jul to Sep 2024)
  AND r.month <  date_trunc('month', w.win_end)   -- drop the part-month at the end
GROUP BY r.language, r.month;

SELECT language,
       strftime(month, '%Y-%m')  AS month,
       reviews,
       round(positive_pct, 1)    AS positive_pct
FROM monthly_series
ORDER BY language, month;
