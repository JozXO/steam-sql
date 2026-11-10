-- Q13. Backtest scores: how wrong was each model, on the same target months, per language and measure?
-- Reads the four models side by side: naive, seasonal naive, 3-month moving average (Q12)
-- and exponential smoothing, "ses" (forecast.py, saved as the table ses_forecasts).
--   mae          = average absolute miss. Volume: reviews. Positive share: percentage points.
--   mape_pct     = average absolute miss as a percent of the actual value (volume only;
--                  for a share that is already a percent, the miss in points is the clearer number).
--   vs_naive_pct = how much smaller the model's MAE is than the naive MAE.
--                  Positive = better than naive. Negative = WORSE than naive.
-- Months scored: 11 per language at horizon 1, 9 at horizon 3.
-- Saved as a view called backtest_scores (unrounded) so Q14 can read it; the SELECT at the end shows it rounded.

CREATE OR REPLACE VIEW backtest_scores AS
WITH joined AS (
    SELECT b.*, s.ses
    FROM baseline_forecasts b
    JOIN ses_forecasts s USING (language, metric, horizon, target_month)
),
long AS (                            -- one row per forecast: turn the four model columns into rows
    UNPIVOT joined
    ON naive, seasonal_naive, moving_avg_3, ses
    INTO NAME model VALUE forecast
),
scores AS (
    SELECT language, metric, horizon, model,
           count(*)                                   AS months_scored,
           avg(abs(actual - forecast))                AS mae,
           100 * avg(abs(actual - forecast) / actual) AS mape_pct
    FROM long
    GROUP BY language, metric, horizon, model
)
SELECT language, metric, horizon, model, months_scored,
       mae,
       CASE WHEN metric = 'volume' THEN mape_pct END AS mape_pct,
       100 * (1 - mae / max(mae) FILTER (WHERE model = 'naive')
                        OVER (PARTITION BY language, metric, horizon)) AS vs_naive_pct
FROM scores;

SELECT language, metric, horizon, model, months_scored,
       round(mae, 2)           AS mae,
       round(mape_pct, 1)      AS mape_pct,
       round(vs_naive_pct, 1)  AS vs_naive_pct
FROM backtest_scores
ORDER BY language, metric, horizon,
         CASE model WHEN 'naive' THEN 1 WHEN 'seasonal_naive' THEN 2
                    WHEN 'moving_avg_3' THEN 3 ELSE 4 END;
