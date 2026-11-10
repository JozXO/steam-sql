-- Q12. The simple forecasts, made in SQL: naive, seasonal naive and a 3-month moving average.
-- Every row is one forecast that could have been made at the end of month "origin" for month "target":
--   horizon 1: the origin is the month before the target; horizon 3: three months before.
-- Rules (fixed before looking at any score):
--   * the first origin is month 12 of the series (12 months of history), so every model, including
--     the seasonal one that needs the same month last year, is scored on the same target months;
--   * naive           = the origin month's value repeats;
--   * seasonal naive  = the value of the same calendar month one year before the target;
--   * moving average  = the average of the origin month and the 2 months before it.
-- The series has no gaps (Q11), so counting rows is the same as counting months.
-- Saved as a view called baseline_forecasts. SES (the fourth model) is made in forecast.py.

CREATE OR REPLACE VIEW baseline_forecasts AS
WITH numbered AS (                   -- month number 1, 2, 3 ... within each language
    SELECT language, month,
           row_number() OVER (PARTITION BY language ORDER BY month) AS rn,
           reviews::DOUBLE AS volume,
           positive_pct
    FROM monthly_series
),
long AS (                            -- one row per language, month and measure
    SELECT language, month, rn, 'volume'       AS metric, volume       AS value FROM numbered
    UNION ALL
    SELECT language, month, rn, 'positive_pct' AS metric, positive_pct AS value FROM numbered
),
with_ma AS (
    SELECT *,
           avg(value) OVER (PARTITION BY language, metric ORDER BY rn
                            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma3
    FROM long
)
SELECT t.language,
       t.metric,
       h.horizon,
       o.month   AS origin_month,
       t.month   AS target_month,
       t.value   AS actual,
       o.value   AS naive,
       s.value   AS seasonal_naive,
       o.ma3     AS moving_avg_3
FROM long t
CROSS JOIN (VALUES (1), (3)) AS h(horizon)
JOIN with_ma o ON o.language = t.language AND o.metric = t.metric
              AND o.rn = t.rn - h.horizon           -- the origin month
JOIN long s    ON s.language = t.language AND s.metric = t.metric
              AND s.rn = t.rn - 12                  -- same month one year earlier
WHERE o.rn >= 12;                                   -- at least 12 months of history

SELECT language, metric, horizon,
       strftime(target_month, '%Y-%m') AS target_month,
       round(actual, 1)         AS actual,
       round(naive, 1)          AS naive,
       round(seasonal_naive, 1) AS seasonal_naive,
       round(moving_avg_3, 1)   AS moving_avg_3
FROM baseline_forecasts
ORDER BY language, metric, horizon, target_month;
