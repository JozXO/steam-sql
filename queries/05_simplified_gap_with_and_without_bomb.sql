-- Q5. How big is each language's gap to English, with and without the bomb months?
-- Gap = English positive % minus the language's positive %, in points.
-- Both use the shared window (Q2). "Without" also drops the bomb period.
-- As in the study, each share is rounded to 1 decimal BEFORE subtracting.

WITH span AS (
    SELECT language, min(created_at) AS first_at, max(created_at) AS last_at
    FROM reviews
    GROUP BY language
),
win AS (
    SELECT max(first_at) AS win_start, min(last_at) AS win_end FROM span
),
in_win AS (                          -- reviews inside the shared window, with a bomb flag
    SELECT r.language,
           r.voted_up,
           r.created_at BETWEEN TIMESTAMP '2024-07-01' AND TIMESTAMP '2024-09-30' AS in_bomb
    FROM reviews r
    CROSS JOIN win w
    WHERE r.created_at BETWEEN w.win_start AND w.win_end
),
shares AS (                          -- positive % per language, both ways
    SELECT language,
           round(100.0 * avg(voted_up), 1)                            AS pct_with_bomb,
           round(100.0 * avg(voted_up) FILTER (WHERE NOT in_bomb), 1) AS pct_without_bomb
    FROM in_win
    GROUP BY language
)
SELECT language,
       pct_with_bomb,
       pct_without_bomb,
       -- the window function picks out the English value and repeats it on every row
       round(max(CASE WHEN language = 'english' THEN pct_with_bomb    END) OVER () - pct_with_bomb,    1) AS gap_with_bomb,
       round(max(CASE WHEN language = 'english' THEN pct_without_bomb END) OVER () - pct_without_bomb, 1) AS gap_without_bomb
FROM shares
ORDER BY language;
