-- Q1. How many reviews do we have, and what share of each language is positive?
-- Uses all 218,380 reviews with no cleaning. Raw shares are NOT comparable yet:
-- each language reaches back a different distance in time (see Q2).

SELECT language,
       count(*)                          AS reviews,
       sum(voted_up)                     AS positive_reviews,
       round(100.0 * avg(voted_up), 1)   AS positive_pct
FROM reviews
GROUP BY language

UNION ALL

-- One extra row for the grand total.
SELECT 'ALL LANGUAGES',
       count(*),
       sum(voted_up),
       round(100.0 * avg(voted_up), 1)
FROM reviews

ORDER BY reviews DESC;
