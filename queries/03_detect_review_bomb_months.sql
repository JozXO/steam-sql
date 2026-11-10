-- Q3. Which language-months are review bombs?
-- The study's rule, written out in plain words:
--   for each language, take its months with at least 30 reviews
--   (only languages with at least 6 such months are judged);
--   a month is a review bomb if BOTH are true:
--     1. its volume is more than 2 times the language's median month, AND
--     2. its positive share is more than 15 points below the language's median month.
-- Median is used (not mean) so the spike itself cannot drag "normal" upward.

WITH monthly AS (                    -- one row per language and month
    SELECT language,
           month,
           count(*)       AS n,
           avg(voted_up)  AS pos
    FROM reviews
    GROUP BY language, month
    HAVING count(*) >= 30
),
typical AS (                         -- what a normal month looks like, per language
    SELECT language,
           median(n)   AS med_n,
           median(pos) AS med_pos
    FROM monthly
    GROUP BY language
    HAVING count(*) >= 6
)
SELECT m.language,
       strftime(m.month, '%Y-%m')           AS month,
       m.n                                  AS reviews,
       round(m.n / t.med_n, 1)              AS multiple_of_normal,
       round(100 * m.pos, 1)                AS positive_rate,
       round(100 * t.med_pos, 1)            AS language_median_positive
FROM monthly m
JOIN typical t ON t.language = m.language
WHERE m.n   > 2 * t.med_n
  AND m.pos < t.med_pos - 0.15
ORDER BY m.language, m.month;
