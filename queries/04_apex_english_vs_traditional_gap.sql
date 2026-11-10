-- Q4. What is the Apex Legends gap between English and Traditional script reviews?
-- Uses Steam's lifetime totals (the baseline table), not the 218,380-review set.
-- Language code 'tchinese' = Traditional script, 'english' = English.

WITH apex AS (
    SELECT language,
           total_reviews,
           round(100.0 * total_positive / total_reviews, 1) AS positive_pct
    FROM baseline
    WHERE game = 'Apex Legends'
)
SELECT e.total_reviews                           AS english_reviews,
       e.positive_pct                            AS english_pct,
       t.positive_pct                            AS traditional_pct,
       round(e.positive_pct - t.positive_pct, 1) AS gap_pts
FROM apex e
JOIN apex t ON e.language = 'english'
           AND t.language = 'tchinese';   -- joins the table to itself: one row, two languages side by side
