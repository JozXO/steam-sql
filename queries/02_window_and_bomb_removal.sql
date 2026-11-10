-- Q2. How many reviews survive the two cleaning steps?
-- Step A: keep the time window that ALL five languages cover.
-- Step B: drop the review-bomb months, July to September 2024.
-- Returns one row.

WITH span AS (                       -- first and last review time per language
    SELECT language,
           min(created_at) AS first_at,
           max(created_at) AS last_at
    FROM reviews
    GROUP BY language
),
win AS (                             -- the window every language covers
    SELECT max(first_at) AS win_start,   -- latest of the five start dates
           min(last_at)  AS win_end      -- earliest of the five end dates
    FROM span
),
bomb AS (                            -- the study's bomb period (Q3 shows how the months were found)
    SELECT TIMESTAMP '2024-07-01' AS b_start,
           TIMESTAMP '2024-09-30' AS b_end   -- midnight at the START of 30 Sep, exactly as in the study code
),
flags AS (                           -- label every review once
    SELECT r.created_at BETWEEN w.win_start AND w.win_end AS in_window,
           r.created_at BETWEEN b.b_start   AND b.b_end   AS in_bomb
    FROM reviews r
    CROSS JOIN win w
    CROSS JOIN bomb b
)
SELECT count(*)                                          AS total_reviews,
       count(*) FILTER (WHERE in_window)                 AS in_window,
       count(*) FILTER (WHERE NOT in_window)             AS outside_window,
       count(*) FILTER (WHERE in_window AND in_bomb)     AS bomb_removed,
       count(*) FILTER (WHERE in_window AND NOT in_bomb) AS clean_reviews,
       round(100.0 * (count(*) - count(*) FILTER (WHERE in_window AND NOT in_bomb))
             / count(*), 1)                              AS pct_removed,
       (SELECT win_start FROM win)                       AS win_start,
       (SELECT win_end   FROM win)                       AS win_end
FROM flags;
