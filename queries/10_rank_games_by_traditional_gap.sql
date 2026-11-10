-- Q10. Which games have the widest Traditional-script gap, and where does Apex rank?
-- For each of the 14 games: gap = English positive % minus Traditional script positive %.
-- RANK() puts the widest gap at 1. Lifetime Steam totals (baseline table).

WITH rates AS (                      -- positive % for the two languages we need, per game
    SELECT game,
           100.0 * max(CASE WHEN language = 'english'  THEN total_positive END)
                 / max(CASE WHEN language = 'english'  THEN total_reviews  END) AS english_pct,
           100.0 * max(CASE WHEN language = 'tchinese' THEN total_positive END)
                 / max(CASE WHEN language = 'tchinese' THEN total_reviews  END) AS trad_pct
    FROM baseline
    GROUP BY game
)
SELECT RANK() OVER (ORDER BY english_pct - trad_pct DESC) AS gap_rank,
       game,
       round(english_pct, 1)            AS english_pct,
       round(trad_pct, 1)               AS trad_pct,
       round(english_pct - trad_pct, 1) AS gap_pts
FROM rates
ORDER BY gap_rank;
