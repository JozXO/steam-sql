# steam-sql: a Steam review study, reproduced in SQL

A small SQL project that rebuilds the figures of my published Steam review study using only SQL, in DuckDB.

The study asks why Apex Legends reviews are far less positive in some languages than in English. It found that most of the Simplified script gap was a single review-bombing month. The study and its dashboards are already published; this repo reproduces its numbers from the data with SQL, so every figure can be traced to a query.

- Study page: https://jozxo.github.io/player-sentiment/ (code: https://github.com/JozXO/player-sentiment)
- Dashboards (Tableau Public and Power BI): https://github.com/JozXO/steam-dashboards

## What is in here

| Path | What it is |
|---|---|
| `queries/` | 10 numbered SQL files, one question each, with plain-English comments |
| `run_all.py` | Runs every query and prints a check table: published number, SQL result, match yes/no |
| `load_data.py` | Builds `steam.duckdb` from the CSVs in `data/` and checks row counts |
| `data/` | The data the SQL needs (see "Data" below) |
| `make_data.py` | How `data/` was made from the original study files (only needed by the author) |
| `LEARN.md` | Study guide: what each query does, line by line, plus practice exercises |

## What the queries show

SQL skills used: `GROUP BY` and `HAVING`, `JOIN` (inner, left, self-join), CTEs, conditional aggregation (`FILTER`, `CASE`), window functions (`LAG`, `RANK`, `ROW_NUMBER`, running and trailing frames, named windows), medians and standard deviations.

| Query | Question |
|---|---|
| 01 | How many reviews, and what share is positive, per language? |
| 02 | How many reviews survive the shared time window and the review-bomb removal? |
| 03 | Which language-months are review bombs? (a stated rule: volume over 2 times the median and positive share 15 points under it) |
| 04 | What is the Apex gap between English and Traditional script reviews? |
| 05 | How big is each language's gap to English, with and without the bomb months? |
| 06 | Do the cleaned reviews and Steam's lifetime totals agree? (join to the baseline table) |
| 07 | How does monthly volume compare with its trailing average? |
| 08 | Which months moved most? (`LAG` and `RANK`) |
| 09 | Control chart: which months have a negative share outside limits built from earlier months? |
| 10 | Which of the 14 games has the widest Traditional script gap? |

## How to run it

```bash
pip install duckdb
python run_all.py            # check table only
python run_all.py --show     # also prints every query result
```

Python 3.10 or later. The script rebuilds `steam.duckdb` from `data/` each time, so there is nothing else to set up. You can also open `steam.duckdb` in the DuckDB command line and paste any file from `queries/`.

## Check table

`run_all.py` compares each SQL result with the number I published (from the write-up, the dashboard data tables, or the study's own output files). Latest run: all 23 match.

| Query | Check                                                                        | Published   | SQL result  | Match |
|-------|------------------------------------------------------------------------------|-------------|-------------|-------|
| Q1    | Reviews collected                                                            | 218,380     | 218,380     | yes   |
| Q2    | Reviews in the shared window (dashboard data_quality)                        | 169,612     | 169,612     | yes   |
| Q2    | Reviews removed as review bomb (dashboard data_quality)                      | 54,873      | 54,873      | yes   |
| Q2    | Reviews after window and review-bomb removal                                 | 114,739     | 114,739     | yes   |
| Q2    | Percent of all reviews removed                                               | 47.5        | 47.5        | yes   |
| Q3    | Review-bomb table (apex_review_bombs.csv): every row and column identical    | 12 rows     | 12 rows     | yes   |
| Q3    | Simplified script, July 2024: times normal volume                            | 14.9        | 14.9        | yes   |
| Q3    | Simplified script, July 2024: positive %                                     | 8.8         | 8.8         | yes   |
| Q4    | Apex English positive %                                                      | 76.6        | 76.6        | yes   |
| Q4    | Apex Traditional script positive %                                           | 40.1        | 40.1        | yes   |
| Q4    | Apex gap, English minus Traditional script (points)                          | 36.5        | 36.5        | yes   |
| Q4    | English lifetime reviews                                                     | 450,786     | 450,786     | yes   |
| Q5    | Simplified script gap with bomb (points)                                     | 20.8        | 20.8        | yes   |
| Q5    | Simplified script gap without bomb (points)                                  | 4.1         | 4.1         | yes   |
| Q5    | japanese: gap with / without bomb (apex_gap_bomb_effect.csv)                 | 16.7 / 18.1 | 16.7 / 18.1 | yes   |
| Q5    | koreana: gap with / without bomb (apex_gap_bomb_effect.csv)                  | 3.3 / -0.9  | 3.3 / -0.9  | yes   |
| Q5    | schinese: gap with / without bomb (apex_gap_bomb_effect.csv)                 | 20.8 / 4.1  | 20.8 / 4.1  | yes   |
| Q5    | tchinese: gap with / without bomb (apex_gap_bomb_effect.csv)                 | 27.9 / 23.1 | 27.9 / 23.1 | yes   |
| Q6    | Language values in the baseline (6 languages + 'all')                        | 7           | 7           | yes   |
| Q10   | Games in the baseline                                                        | 14          | 14          | yes   |
| Q10   | Apex has the widest Traditional script gap of 14 games (rank)                | 1           | 1           | yes   |
| Q10   | Traditional script gap, all 14 games (gaps_by_game.csv)                      | 14 of 14    | 14 of 14    | yes   |
| Q9    | Control chart flags Korean July and August 2024 (both are in the bomb table) | flagged     | flagged     | yes   |

The full output, one row per check, is written to `check_table.md` every run.

## Notes on the data and the method

- **Data.** The reviews are 218,380 Apex Legends reviews from the public Steam review API in five languages. `data/reviews_apex.csv.gz` holds five columns (id, language, positive or negative, timestamp, hours played) and leaves out the review text, which the SQL does not need. `data/baseline_summaries.csv` has Steam's lifetime totals for 14 games. `data/published/` holds the study's own output files, used only to check the SQL. `make_data.py` shows how they were made. Times are UTC.
- **The bomb period.** The study removes July to September 2024 as a block. As in the study code, the end of the period is 30 September at 00:00, so 182 reviews from later on 30 September stay in. Removing all of September would give 114,557 clean reviews instead of 114,739 and leave every headline gap unchanged to one decimal.
- **Rounding.** As in the study, positive shares are rounded to one decimal before they are subtracted to get a gap.
- **Q9 limit.** English data starts two months before the July 2024 spike and Simplified script data starts at it, so a control chart built from earlier months cannot judge that spike for those two languages. `LEARN.md` explains this.

## How this was built

The queries were drafted with Claude Code, an AI coding assistant, as a coding partner. I then ran them against my own data and checked every result against the figures I had already published. I wrote `LEARN.md` so that I can explain each query and rewrite it myself.
