-- Q9. Control chart: which months have an unusual share of NEGATIVE reviews?
-- Statistical process control, in SQL. For each language and month:
--   centre line = mean negative share of the EARLIER months only
--   limits      = centre line +/- 3 standard deviations of the earlier months
--   flag        = the month falls outside the limits
-- "Earlier months only" means a spike cannot hide itself by inflating its own limits.
-- Rules chosen for this exercise: at least 30 reviews in a month, at least 6 earlier months.

WITH monthly AS (
    SELECT language,
           month,
           count(*)          AS reviews,
           1 - avg(voted_up) AS neg_share
    FROM reviews
    GROUP BY language, month
    HAVING count(*) >= 30
),
limits AS (
    SELECT language,
           month,
           reviews,
           neg_share,
           count(*)               OVER prior AS prior_months,
           avg(neg_share)         OVER prior AS centre,
           stddev_samp(neg_share) OVER prior AS sd
    FROM monthly
    WINDOW prior AS (PARTITION BY language ORDER BY month
                     ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
)
SELECT language,
       strftime(month, '%Y-%m')          AS month,
       reviews,
       round(100 * neg_share, 1)         AS neg_pct,
       round(100 * centre, 1)            AS centre_pct,
       round(100 * (centre - 3 * sd), 1) AS lower_limit_pct,
       round(100 * (centre + 3 * sd), 1) AS upper_limit_pct,
       CASE WHEN neg_share > centre + 3 * sd THEN 'ABOVE UPPER LIMIT'
            WHEN neg_share < centre - 3 * sd THEN 'BELOW LOWER LIMIT'
       END                               AS flag
FROM limits
WHERE prior_months >= 6
  AND (neg_share > centre + 3 * sd OR neg_share < centre - 3 * sd)
ORDER BY language, month;
