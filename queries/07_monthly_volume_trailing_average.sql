-- Q7. How does monthly review volume move, against its own recent past?
-- Window function: the average of this month and the 2 months before it (a "trailing 3-month average"),
-- and this month's volume as a multiple of the average of the 3 months BEFORE it.
-- Shown for English, first 12 months of data (May 2024 onward), so the July 2024 spike is visible.
-- Change the language in the WHERE line to look at another one.
-- Months with no reviews are absent, so "2 PRECEDING" means "2 earlier months that have data".

WITH monthly AS (
    SELECT month,
           count(*) AS reviews
    FROM reviews
    WHERE language = 'english'
    GROUP BY month
)
SELECT strftime(month, '%Y-%m')                                                 AS month,
       reviews,
       round(avg(reviews) OVER (ORDER BY month
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0)   AS trailing_3m_avg,
       round(reviews / avg(reviews) OVER (ORDER BY month
                                ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING), 1)   AS times_previous_3m_avg
FROM monthly
ORDER BY month
LIMIT 12;
