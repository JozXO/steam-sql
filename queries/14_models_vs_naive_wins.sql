-- Q14. The headline: in how many of the 5 languages does each model beat the naive baseline?
-- "Beats" means a smaller MAE than naive on the same target months (Q13).
-- One row per measure, horizon and model. Naive itself is left out (it cannot beat itself).
-- avg_vs_naive_pct is the plain average of the five languages' vs_naive_pct (negative = worse than naive).
-- It does not weight by volume, so a language with large errors counts the same as a small one.

SELECT metric,
       horizon,
       model,
       count(*) FILTER (WHERE vs_naive_pct > 0)  AS languages_better,
       count(*) FILTER (WHERE vs_naive_pct <= 0) AS languages_same_or_worse,
       round(avg(vs_naive_pct), 1)               AS avg_vs_naive_pct
FROM backtest_scores
WHERE model <> 'naive'
GROUP BY metric, horizon, model
ORDER BY metric, horizon,
         CASE model WHEN 'seasonal_naive' THEN 2 WHEN 'moving_avg_3' THEN 3 ELSE 4 END;
