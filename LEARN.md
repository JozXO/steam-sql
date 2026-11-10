# LEARN.md: study guide for the Steam SQL project

This is for Josiah. The goal: you can explain every query in your own words and rewrite it from a blank page, with no AI. An interviewer who sees this repo will ask you to do exactly that, probably on a shared screen.

How to study each query:

1. Read "What it answers" and "How it works".
2. Close the file. Open a blank editor. Write the query from memory using the table names and column names below.
3. Run it (`python run_all.py --show`, or open `steam.duckdb` in any DuckDB client). Compare with the real file. Fix the gaps.
4. Say the interview sentence out loud once.

Do not memorise the text of the queries. Memorise the shape: what is the question, which table, which grouping, which filter, which window.

## The two tables

**`reviews`**: one row per Steam review of Apex Legends (218,380 rows).

| column | meaning |
|---|---|
| `review_id` | unique id |
| `language` | `english`, `schinese` (Simplified script), `tchinese` (Traditional script), `japanese`, `koreana` (Korean) |
| `voted_up` | 1 = positive review, 0 = negative review |
| `created_at` | when the review was written (UTC) |
| `month` | the first day of that month |
| `hours_played` | hours the reviewer had played at review time |

**`baseline`**: Steam's lifetime review totals for 14 games, one row per game and language (98 rows). The `language` values are 6 languages plus `all` (the total across languages), which is why the study page's "7 languages" is really 6 languages and a total.

| column | meaning |
|---|---|
| `game` | game name |
| `language` | `all`, `english`, `schinese`, `tchinese`, `japanese`, `koreana`, `russian` |
| `total_reviews`, `total_positive`, `total_negative` | lifetime counts |

## Words you need

- **Positive share** = positive reviews divided by all reviews. `avg(voted_up)` gives it directly, because `voted_up` is 1 or 0.
- **Gap** = English positive share minus another language's positive share, in percentage points.
- **CTE** (`WITH name AS (...)`): a named step. Read a CTE query top to bottom like a recipe.
- **Window function** (`... OVER (...)`): calculates across neighbouring rows but keeps every row. `GROUP BY` squashes rows together; `OVER` does not.
- **`FILTER (WHERE ...)`**: applies a condition to one aggregate only. `count(*) FILTER (WHERE x)` counts only rows where x is true.
- **Review bomb**: a short burst of negative reviews, driven by an outside event rather than by the game.

---

## Q1. Totals and positive share by language (`01_totals_by_language.sql`)

**What it answers:** how many reviews we have, and what share of each language is positive, before any cleaning.

**How it works**
1. `FROM reviews GROUP BY language` makes one row per language.
2. `count(*)` counts reviews. `sum(voted_up)` counts positive ones (each positive is 1). `avg(voted_up)` is the positive share; times 100 and `round(..., 1)` makes it a percentage with one decimal.
3. `UNION ALL` glues on a second query with no `GROUP BY`, which gives one grand-total row.
4. `ORDER BY reviews DESC` puts the biggest first. It sorts the combined result, so it comes last.

**The catch worth saying:** these raw shares cannot be compared across languages. The collector pulled newest first up to a cap, so each language reaches back a different distance. That is the reason for Q2.

**Interview sentence:** "This is the starting count, 218,380 reviews, and I treat it as uncomparable because each language covers a different time period."

---

## Q2. Window and bomb removal (`02_window_and_bomb_removal.sql`)

**What it answers:** how many reviews survive the two cleaning steps, to 114,739.

**How it works**
1. `span`: for each language, the first and last review time (`min`, `max`).
2. `win`: the shared window. The latest of the five start times (`max(first_at)`) and the earliest of the five end times (`min(last_at)`). Only that stretch is covered by all five languages. Result: 20 July 2024 to 21 September 2026.
3. `bomb`: the removal period, written once as two timestamps.
4. `flags`: every review gets two true/false labels, `in_window` and `in_bomb`. `CROSS JOIN` attaches the single-row `win` and `bomb` to every review.
5. The final `SELECT` counts with `FILTER`: total, in window, outside window, bomb removed, clean. `pct_removed` is everything not clean, divided by everything: 47.5%.

**Detail to know:** the end of the bomb period is `2024-09-30` at 00:00. That is how the original study code wrote it, so 182 reviews from the rest of 30 September stay in. With all of 30 September removed the clean count would be 114,557. No headline gap changes at one decimal, but if an interviewer asks why the numbers are 114,739, this is the honest reason it is not 114,557.

**Interview sentence:** "I restrict to the window all five languages cover, then drop the review-bomb months, which leaves 114,739 of 218,380, so 47.5% of the collected reviews are removed."

---

## Q3. Detecting review-bomb months (`03_detect_review_bomb_months.sql`)

**What it answers:** which language-months look like a review bomb. This is the query behind "how did you identify the month".

**The rule, in words:** for each language, take months with at least 30 reviews, and only judge languages with at least 6 such months. A month is flagged if its volume is more than 2 times that language's median month AND its positive share is more than 15 points below that language's median month.

**How it works**
1. `monthly`: one row per language and month, with the review count `n` and the positive share `pos`. `HAVING count(*) >= 30` drops thin months. (`HAVING` filters after grouping; `WHERE` filters before.)
2. `typical`: per language, the median monthly volume and median monthly positive share. `median(...)` is used so the spike cannot pull "normal" up. `HAVING count(*) >= 6` drops languages with too little history.
3. The final query joins each month to its language's typical values and keeps rows where both conditions are true.

**What it returns:** 12 rows, identical to the study's published table. July 2024 is flagged in all five languages; Simplified script is the extreme (27,227 reviews, 14.9 times normal, 8.8% positive).

**The question you will be asked: "was the rule set before you saw the result?"** I cannot tell you the answer from the files, because only you know the order you did things in. The repo shows the rule is written down and applied the same way to every language. Answer with whichever is true:
- If you saw the spike on a chart first and then wrote the rule to detect it in code: say so. "I saw it in the monthly volume chart, then wrote a rule so the detection is explicit and runs the same way on every language." That is honest and perfectly normal.
- If you set the thresholds before looking: say that instead.
Do not claim the second if the first is true.

**Other things an interviewer may probe (be ready, they are real limits):**
- The thresholds (2 times, 15 points, 30 reviews) are judgement calls, not derived. Say so.
- The study removes all of July to September 2024 for every language. The rule itself flags only some months: for example September only for Simplified script, and English November 2024 is flagged by the rule but is not removed. The removal period is a wider, simpler choice than the rule's output.
- The earlier history differs by language, so "median month" is calculated on different spans.

**Interview sentence:** "A month counts as a review bomb if volume is over twice the language's median and the positive share is 15 points below its median; it flags July 2024 in all five languages, and I can show the thresholds are judgement calls."

---

## Q4. Apex English vs Traditional script gap (`04_apex_english_vs_traditional_gap.sql`)

**What it answers:** the headline gap. English 76.6% positive, Traditional script 40.1%, gap 36.5 points. This uses Steam's lifetime totals, not the 218,380 reviews.

**How it works**
1. CTE `apex`: Apex rows from `baseline`, with the positive share per language rounded to one decimal.
2. The final query joins `apex` to itself. The copy `e` is only the English row, the copy `t` is only the Traditional script row. A self-join puts two rows of one table side by side.
3. The gap is English minus Traditional script, rounded.

**Interview sentence:** "I join the Apex rows to themselves so English and Traditional script sit on one row, then subtract: 76.6 minus 40.1 is 36.5 points."

---

## Q5. Gap with and without the bomb (`05_simplified_gap_with_and_without_bomb.sql`)

**What it answers:** how much of each language's gap to English is the bomb. Simplified script goes from 20.8 points to 4.1.

**How it works**
1. `span`, `win`: the shared window, as in Q2.
2. `in_win`: reviews inside the window, each with an `in_bomb` flag.
3. `shares`: per language, the positive share with the bomb included and, using `FILTER (WHERE NOT in_bomb)`, without it. Rounded to one decimal here, as the study did.
4. Final `SELECT`: the window function `max(CASE WHEN language = 'english' THEN ... END) OVER ()` finds the English value and repeats it on every row. Subtracting the language's own value gives the gap. `OVER ()` with nothing inside means "the whole result".

**Interview sentence:** "Inside the same window I compute each language's positive share with and without July to September 2024, and Simplified script's gap to English drops from 20.8 to 4.1 points, so most of that gap was the bomb."

---

## Q6. Join reviews to the baseline (`06_join_reviews_to_baseline.sql`)

**What it answers:** whether the cleaned review set and Steam's lifetime totals agree, language by language.

**How it works**
1. `span`, `win`, `clean`: the cleaned set, as in Q2.
2. `sample`: positive share and count per language in the cleaned set.
3. The final query starts from `baseline` (Apex rows only) and `LEFT JOIN`s `sample` on `language`. A left join keeps every baseline row even without a match, so Russian and `all` appear with empty sample columns. An inner `JOIN` would drop them.
4. The last column is sample share minus lifetime share.

**Reading it:** the review set (after cleaning) is more negative than Steam's lifetime total for English and more positive for Simplified script. The two measure different things (a time window vs all time). Say that, and do not claim they agree.

**Interview sentence:** "I left-join the cleaned sample onto Steam's lifetime table so languages missing from my sample still show, and the two sources differ because they cover different time spans."

---

## Q7. Monthly volume with a trailing average (`07_monthly_volume_trailing_average.sql`)

**What it answers:** how a month's volume compares with its recent past. English, first 12 months of data; July 2024 is 5.6 times the previous three months.

**How it works**
1. `monthly`: reviews per month for English.
2. `avg(reviews) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`: the average of this row and the 2 rows before it. That is the trailing 3-month average. The frame is counted in rows, so a missing month would mean looking further back.
3. The second window uses `3 PRECEDING AND 1 PRECEDING`: the 3 months before this one, not including it. Dividing this month by that gives "times the previous average".
4. `ORDER BY month LIMIT 12` keeps the first 12 months.

**Interview sentence:** "A window with ROWS BETWEEN gives a trailing average per month; excluding the current row from the frame is what lets me say a month is 5.6 times its recent past."

---

## Q8. Month-on-month change and worst months (`08_month_change_lag_and_rank.sql`)

**What it answers:** for Simplified script, the five worst months by positive share and how each moved from the month before.

**How it works**
1. `monthly`: reviews and positive share per month, months with at least 30 reviews.
2. `LAG(positive_pct) OVER (ORDER BY month)` reads the previous month's value onto this row. Subtracting gives the change. The first month has no previous row, so it is `NULL`.
3. `RANK() OVER (ORDER BY positive_pct)` numbers rows from the lowest share (1). Ties get the same number.
4. A window function cannot be filtered in the same `SELECT`, so `changes` is a CTE and `WHERE worst_rank <= 5` is applied in the outer query.

**Interview sentence:** "LAG pulls the previous month onto the row for the change, RANK numbers the months, and I filter on the rank in an outer query because you cannot filter a window result where it is created."

---

## Q9. Control chart on the negative share (`09_control_chart_negative_share.sql`)

**What it answers:** which language-months have a negative share outside control limits built from earlier months only. This is a statistical process control chart written in SQL.

**How it works**
1. `monthly`: negative share (`1 - avg(voted_up)`) per language and month, months with at least 30 reviews.
2. `limits`: for each row, the mean and sample standard deviation of all earlier rows of the same language. The named window `prior` is `PARTITION BY language ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`: from the start of that language up to the row just before this one. `count(*)` over it tells us how many earlier months there are.
3. The final query keeps rows with at least 6 earlier months, calculates the limits as centre plus or minus 3 standard deviations, and prints a flag for anything outside.

**Why earlier months only:** if a spike were included in its own limits, it would widen them and could hide itself.

**What it shows, and its limit:** it flags Korean in June 2022, November 2022, April 2024, July 2024 and August 2024, and Traditional script in October 2022. It does not flag Simplified script or English in July 2024, because in this data those languages have no usable earlier history (English starts in May 2024 and Simplified script in July 2024, because the collector pulled newest first up to a cap), so there is nothing to build limits from. Say this plainly; it is a real property of the data, not a bug.

**Simplifications to be able to name:** it is an individuals-style chart (standard deviation of monthly shares). A proper p-chart for proportions would make the limits depend on each month's sample size. Mention it as the next step.

**Interview sentence:** "Each month is compared with limits from the mean and three standard deviations of the months before it, so a spike cannot widen its own limits; it works for Korean July 2024, but Simplified script has no earlier history to build limits from."

---

## Q10. Rank games by the Traditional script gap (`10_rank_games_by_traditional_gap.sql`)

**What it answers:** which of the 14 games has the widest Traditional script gap. Apex Legends is first at 36.5 points; Delta Force is second.

**How it works**
1. `rates`: one row per game. The `max(CASE WHEN language = 'english' THEN total_positive END)` trick picks the English value out of the six rows per game. This is "conditional aggregation", a standard way to turn rows into columns.
2. Final query: `RANK() OVER (ORDER BY english_pct - trad_pct DESC)` puts the widest gap at 1. Percentages are rounded only for display, so the gap is calculated from the exact values and then rounded once (this makes Delta Force 28.0, not 28.1; the dashboard note rounds before subtracting).

**Interview sentence:** "I pivot English and Traditional script onto one row per game with conditional aggregation, then RANK by the gap, and Apex comes first of 14."

---

## Practice exercises

Do these without AI. Answers are at the bottom, but try first. Each uses the same two tables. Run your own version, then compare results (not code) with the answers.

**Exercise 1: weekly rate per group.** For each language, the number of reviews and the positive percentage for each calendar week from Monday 22 July 2024 up to (not including) Monday 23 September 2024. (Hint: `date_trunc('week', created_at)`.)

**Exercise 2: above the limit three weeks running.** For each language, weekly negative share. Build limits as the mean plus 3 standard deviations of that language's earlier weeks (use only weeks with at least 30 reviews, and only judge a week with at least 8 earlier weeks). Return the language and week where the share was above the limit for three weeks in a row. (Hint: a 0/1 flag, then `sum(flag)` over the last 3 rows.)

**Exercise 3: join two tables and return the top 5 per group.** For each language, the 5 months with the most reviews, together with that language's Apex lifetime positive percentage from `baseline`. (Hint: `ROW_NUMBER() OVER (PARTITION BY ...)`, then filter in an outer step.)

**Exercise 4: a conditional share.** For each language, what percent of its reviews were written between 1 July 2024 and 30 September 2024 (use the same 30 September 00:00 end as the project)? Order from highest to lowest. (Hint: `count(*) FILTER (WHERE ...)`.)

**Exercise 5: volume above trailing mean plus 3 standard deviations.** For each language, flag months where the review count is above the mean plus 3 standard deviations of that language's earlier months. Use at least 6 earlier months. What do you notice about which languages show up, and why?

---

## Answers

Check your results against these. Several correct queries can look different.

**Exercise 1**
```sql
SELECT language,
       date_trunc('week', created_at)::DATE AS week,
       count(*)                             AS reviews,
       round(100.0 * avg(voted_up), 1)      AS positive_pct
FROM reviews
WHERE created_at >= TIMESTAMP '2024-07-22'
  AND created_at <  TIMESTAMP '2024-09-23'
GROUP BY language, week
ORDER BY language, week;
```
Check: 45 rows (5 languages, 9 weeks). English week of 22 July: 2,748 reviews, 17.0% positive. Simplified script the same week: 17,857 reviews, 8.7%.

**Exercise 2**
```sql
WITH weekly AS (
    SELECT language,
           date_trunc('week', created_at)::DATE AS week,
           count(*)          AS reviews,
           1 - avg(voted_up) AS neg_share
    FROM reviews
    GROUP BY language, week
    HAVING count(*) >= 30
),
limits AS (
    SELECT *,
           count(*)               OVER prior AS prior_weeks,
           avg(neg_share)         OVER prior AS centre,
           stddev_samp(neg_share) OVER prior AS sd
    FROM weekly
    WINDOW prior AS (PARTITION BY language ORDER BY week
                     ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
),
flagged AS (
    SELECT *,
           CASE WHEN prior_weeks >= 8 AND neg_share > centre + 3 * sd THEN 1 ELSE 0 END AS is_out
    FROM limits
),
runs AS (
    SELECT *,
           sum(is_out) OVER last3 AS out_in_last_3,
           count(*)    OVER last3 AS weeks_in_frame
    FROM flagged
    WINDOW last3 AS (PARTITION BY language ORDER BY week
                     ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
)
SELECT language, week,
       round(100 * neg_share, 1)         AS neg_pct,
       round(100 * (centre + 3 * sd), 1) AS upper_limit_pct
FROM runs
WHERE out_in_last_3 = 3
  AND weeks_in_frame = 3
ORDER BY language, week;
```
Check: 4 rows. Korean weeks starting 22 July, 29 July and 5 August 2024, and Traditional script the week of 10 October 2022. Korean weeks 8 July to 5 August 2024 were all above the limit, so every week from 22 July on completes a run of three. The window counts rows, not calendar weeks, so a missing week would silently join two runs. Say that if asked.

**Exercise 3**
```sql
WITH monthly AS (
    SELECT language, month, count(*) AS reviews
    FROM reviews
    GROUP BY language, month
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY language ORDER BY reviews DESC) AS rn
    FROM monthly
)
SELECT r.language,
       strftime(r.month, '%Y-%m') AS month,
       r.reviews,
       round(100.0 * b.total_positive / b.total_reviews, 1) AS lifetime_pct
FROM ranked r
JOIN baseline b ON b.language = r.language
               AND b.game = 'Apex Legends'
WHERE r.rn <= 5
ORDER BY r.language, r.rn;
```
Check: 25 rows. English top month is 2024-07 with 13,675; Simplified script 2024-07 with 27,227. `ROW_NUMBER` gives exactly 5 per language even with ties; `RANK` could give more.

**Exercise 4**
```sql
SELECT language,
       count(*) AS reviews,
       round(100.0 * count(*) FILTER (WHERE created_at BETWEEN TIMESTAMP '2024-07-01'
                                                          AND TIMESTAMP '2024-09-30')
             / count(*), 1) AS pct_in_bomb_period
FROM reviews
GROUP BY language
ORDER BY pct_in_bomb_period DESC;
```
Check: Simplified script 46.0%, English 24.8%, Traditional script 19.1%, Korean 9.0%, Japanese 8.6%. Alternative without `FILTER`: `sum(CASE WHEN ... THEN 1 ELSE 0 END)`.

**Exercise 5**
```sql
WITH monthly AS (
    SELECT language, month, count(*) AS reviews
    FROM reviews
    GROUP BY language, month
),
limits AS (
    SELECT *,
           count(*)             OVER prior AS prior_months,
           avg(reviews)         OVER prior AS mean_before,
           stddev_samp(reviews) OVER prior AS sd_before
    FROM monthly
    WINDOW prior AS (PARTITION BY language ORDER BY month
                     ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
)
SELECT language,
       strftime(month, '%Y-%m') AS month,
       reviews,
       round(mean_before + 3 * sd_before, 0) AS upper_limit
FROM limits
WHERE prior_months >= 6
  AND reviews > mean_before + 3 * sd_before
ORDER BY language, month;
```
Check: three rows. Japanese July 2024 (589 reviews against an upper limit of 368), Traditional script May 2022 (755 against 750, only just over), and Traditional script July 2024 (3,829 against 954). What you should notice: English and Simplified script never appear. English has only 2 earlier months before July 2024 and Simplified script has none, because the data for those languages starts at the spike. A rule that needs history cannot judge a series that starts at the spike. The study's median rule (Q3) uses the whole series, including the spike month, so it can flag English and Simplified script July 2024 where this one cannot. The trade-off: the whole-series baseline contains the spike, although the median resists it.
