-- Q8. Which months moved the most, and which were the worst months overall?
-- LAG looks at the previous row; RANK orders months by a value.
-- Measure: positive share, Simplified script, months with at least 30 reviews.

WITH monthly AS (
    SELECT month,
           count(*)                        AS reviews,
           round(100.0 * avg(voted_up), 1) AS positive_pct
    FROM reviews
    WHERE language = 'schinese'
    GROUP BY month
    HAVING count(*) >= 30
),
changes AS (
    SELECT month,
           reviews,
           positive_pct,
           -- LAG(x) = the value of x in the previous month (NULL for the first month)
           positive_pct - LAG(positive_pct) OVER (ORDER BY month) AS change_vs_prev_month,
           -- RANK 1 = lowest positive share; ties share a rank
           RANK() OVER (ORDER BY positive_pct)                    AS worst_rank
    FROM monthly
)
SELECT strftime(month, '%Y-%m')       AS month,
       reviews,
       positive_pct,
       round(change_vs_prev_month, 1) AS change_vs_prev_month,
       worst_rank
FROM changes
WHERE worst_rank <= 5
ORDER BY worst_rank;
