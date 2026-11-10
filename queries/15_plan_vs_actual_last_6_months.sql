-- Q15. Plan vs actual: the forecast made at the end of the month before, against what happened,
-- for the last 6 months (March to August 2026), horizon 1, per language and measure.
-- "Plan" here is each model's one-month-ahead forecast. error = actual minus forecast, so a
-- positive error means the plan was too low. Volume in reviews, positive share in percentage points.
-- Use the ses column as the model's plan and naive as the baseline it has to beat.

SELECT b.language,
       b.metric,
       strftime(b.target_month, '%Y-%m')  AS month,
       round(b.actual, 1)                 AS actual,
       round(b.naive, 1)                  AS naive,
       round(b.moving_avg_3, 1)           AS moving_avg_3,
       round(s.ses, 1)                    AS ses,
       round(b.actual - b.naive, 1)       AS naive_error,
       round(b.actual - s.ses, 1)         AS ses_error
FROM baseline_forecasts b
JOIN ses_forecasts s USING (language, metric, horizon, target_month)
WHERE b.horizon = 1
  AND b.target_month >= (SELECT max(month) - INTERVAL 5 MONTH FROM monthly_series)
ORDER BY b.language, b.metric, b.target_month;
