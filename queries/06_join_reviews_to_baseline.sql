-- Q6. Do the cleaned review set and Steam's lifetime totals tell the same story?
-- JOIN the review set (cleaned, grouped by language) to the baseline table.
-- LEFT JOIN from baseline keeps Russian and 'all', which have no rows in the review set.
-- Result has 7 rows: the 7 language values in the baseline (6 languages plus an 'all' total).

WITH span AS (
    SELECT language, min(created_at) AS first_at, max(created_at) AS last_at
    FROM reviews
    GROUP BY language
),
win AS (
    SELECT max(first_at) AS win_start, min(last_at) AS win_end FROM span
),
clean AS (                           -- shared window, bomb period removed
    SELECT r.language, r.voted_up
    FROM reviews r
    CROSS JOIN win w
    WHERE r.created_at BETWEEN w.win_start AND w.win_end
      AND NOT r.created_at BETWEEN TIMESTAMP '2024-07-01' AND TIMESTAMP '2024-09-30'
),
sample AS (
    SELECT language,
           count(*)                        AS sample_reviews,
           round(100.0 * avg(voted_up), 1) AS sample_pct
    FROM clean
    GROUP BY language
)
SELECT b.language,
       s.sample_reviews,
       s.sample_pct,
       b.total_reviews                                                       AS lifetime_reviews,
       round(100.0 * b.total_positive / b.total_reviews, 1)                  AS lifetime_pct,
       round(s.sample_pct - 100.0 * b.total_positive / b.total_reviews, 1)   AS sample_minus_lifetime
FROM baseline b
LEFT JOIN sample s ON s.language = b.language
WHERE b.game = 'Apex Legends'
ORDER BY b.total_reviews DESC;
