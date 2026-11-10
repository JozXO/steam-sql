"""
run_all.py
Loads the data, runs every query in queries/, and prints a check table:
published number | SQL result | match yes/no.

    python run_all.py           # check table only
    python run_all.py --show    # also print the result of every query

Queries 11 to 15 are the forecasting part (monthly series, naive / seasonal naive /
moving average / exponential smoothing, rolling backtest). They have no published number to
match, so their rows in the table are checked against an independent recomputation in pandas
(forecast_checks.py), which reads the raw reviews file and does not use the SQL.

The published numbers come from the study write-up, the dashboard data_quality
table, and the study's own output CSVs (copied unchanged into data/published/).
Nothing here changes a published number. If a check says NO, the SQL is
reported as it is and the script exits with an error.
"""
import sys
from pathlib import Path

from forecast import add_ses_table
from forecast_checks import forecast_checks
from load_data import check_counts, load

HERE = Path(__file__).parent
QUERIES = HERE / "queries"
RESULTS = HERE / "results"


def run(con, prefix):
    """Run the query file that starts with prefix (e.g. '03'). Returns a list of dict rows."""
    path = next(QUERIES.glob(f"{prefix}_*.sql"))
    cur = con.execute(path.read_text(encoding="utf-8"))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fmt(v):
    if isinstance(v, float):
        return f"{v:,.1f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def write_results(con):
    """Save the forecasting tables as CSV files in results/ (the README tables come from these)."""
    RESULTS.mkdir(exist_ok=True)
    out = {
        "monthly_series.csv": "SELECT language, strftime(month, '%Y-%m') AS month, reviews, "
                              "round(positive_pct, 2) AS positive_pct FROM monthly_series ORDER BY 1, 2",
        "backtest_forecasts.csv": """SELECT b.language, b.metric, b.horizon, strftime(b.target_month, '%Y-%m') AS target_month,
                                            round(b.actual, 2) AS actual, round(b.naive, 2) AS naive,
                                            round(b.seasonal_naive, 2) AS seasonal_naive,
                                            round(b.moving_avg_3, 2) AS moving_avg_3, round(s.ses, 2) AS ses,
                                            s.alpha AS ses_alpha
                                     FROM baseline_forecasts b
                                     JOIN ses_forecasts s USING (language, metric, horizon, target_month)
                                     ORDER BY 1, 2, 3, 4""",
        "backtest_scores.csv": "SELECT language, metric, horizon, model, months_scored, round(mae, 2) AS mae, "
                               "round(mape_pct, 1) AS mape_pct, round(vs_naive_pct, 1) AS vs_naive_pct "
                               "FROM backtest_scores ORDER BY 1, 2, 3, CASE model WHEN 'naive' THEN 1 "
                               "WHEN 'seasonal_naive' THEN 2 WHEN 'moving_avg_3' THEN 3 ELSE 4 END",
    }
    for name, sql in out.items():
        con.execute(f"COPY ({sql}) TO '{(RESULTS / name).as_posix()}' (HEADER, DELIMITER ',')")


def main():
    show = "--show" in sys.argv
    con = load()
    print("Loaded steam.duckdb")
    if not check_counts(con):
        sys.exit("Row counts do not match. Stopping.")

    q = {p: run(con, p) for p in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]}

    # ---- forecasting part: Q11 and Q12 save views, forecast.py adds the SES table, Q13 to Q15 read them
    q["11"] = run(con, "11")
    q["12"] = run(con, "12")
    n_ses = add_ses_table(con)
    print(f"  SES forecasts made: {n_ses} (forecast.py)")
    for p in ["13", "14", "15"]:
        q[p] = run(con, p)

    if show:
        for p, rows in q.items():
            print(f"\n--- query {p} ---")
            for r in rows:
                print(r)

    checks = []  # (query, what, published, sql_result)

    def add(query, what, published, result):
        checks.append((query, what, published, result))

    # ---- Q1, Q2: totals and cleaning
    total = next(r for r in q["01"] if r["language"] == "ALL LANGUAGES")
    add("Q1", "Reviews collected", 218380, total["reviews"])
    q2 = q["02"][0]
    add("Q2", "Reviews in the shared window (dashboard data_quality)", 169612, q2["in_window"])
    add("Q2", "Reviews removed as review bomb (dashboard data_quality)", 54873, q2["bomb_removed"])
    add("Q2", "Reviews after window and review-bomb removal", 114739, q2["clean_reviews"])
    add("Q2", "Percent of all reviews removed", 47.5, q2["pct_removed"])

    # ---- Q3: bomb detection must give the same 12 language-months as the study's table
    pub = con.execute("SELECT language, strftime(CAST(month || '-01' AS DATE), '%Y-%m'), reviews, "
                      "multiple_of_normal, positive_rate, language_median_positive "
                      "FROM published_apex_review_bombs").fetchall()
    sql = [(r["language"], r["month"], r["reviews"], r["multiple_of_normal"],
            r["positive_rate"], r["language_median_positive"]) for r in q["03"]]
    same = sorted(pub) == sorted(sql)
    add("Q3", "Review-bomb table (apex_review_bombs.csv): every row and column identical",
        f"{len(pub)} rows", f"{len(sql)} rows" if same else f"{len(sql)} rows, DIFFERENT")
    s_jul = next(r for r in q["03"] if r["language"] == "schinese" and r["month"] == "2024-07")
    add("Q3", "Simplified script, July 2024: times normal volume", 14.9, s_jul["multiple_of_normal"])
    add("Q3", "Simplified script, July 2024: positive %", 8.8, s_jul["positive_rate"])

    # ---- Q4: Apex English vs Traditional script
    q4 = q["04"][0]
    add("Q4", "Apex English positive %", 76.6, q4["english_pct"])
    add("Q4", "Apex Traditional script positive %", 40.1, q4["traditional_pct"])
    add("Q4", "Apex gap, English minus Traditional script (points)", 36.5, q4["gap_pts"])
    add("Q4", "English lifetime reviews", 450786, q4["english_reviews"])

    # ---- Q5: gaps with and without the bomb
    by_lang = {r["language"]: r for r in q["05"]}
    add("Q5", "Simplified script gap with bomb (points)", 20.8, by_lang["schinese"]["gap_with_bomb"])
    add("Q5", "Simplified script gap without bomb (points)", 4.1, by_lang["schinese"]["gap_without_bomb"])
    for lang, w, wo, _ in con.execute("SELECT * FROM published_apex_gap_bomb_effect").fetchall():
        if lang == "english":
            continue
        add("Q5", f"{lang}: gap with / without bomb (apex_gap_bomb_effect.csv)",
            f"{w} / {wo}", f"{by_lang[lang]['gap_with_bomb']} / {by_lang[lang]['gap_without_bomb']}")

    # ---- Q6, Q10: baseline table
    add("Q6", "Language values in the baseline (6 languages + 'all')", 7, len(q["06"]))
    add("Q10", "Games in the baseline", 14, len(q["10"]))
    apex_rank = next(r for r in q["10"] if r["game"] == "Apex Legends")
    add("Q10", "Apex has the widest Traditional script gap of 14 games (rank)", 1, apex_rank["gap_rank"])
    pub_gap = {g: round(v, 1) for g, v in con.execute(
        "SELECT game, tchinese_gap FROM published_gaps_by_game").fetchall()}
    sql_gap = {r["game"]: r["gap_pts"] for r in q["10"]}
    bad = [g for g in pub_gap if pub_gap[g] != sql_gap.get(g)]
    add("Q10", "Traditional script gap, all 14 games (gaps_by_game.csv)",
        "14 of 14", f"{14 - len(bad)} of 14" + (f" (differ: {', '.join(bad)})" if bad else ""))

    # ---- Q9: consistency check, not a published number
    flagged = {(r["language"], r["month"]) for r in q["09"]}
    both = {("koreana", "2024-07"), ("koreana", "2024-08")} <= flagged
    add("Q9", "Control chart flags Korean July and August 2024 (both are in the bomb table)",
        "flagged", "flagged" if both else "not flagged")

    # ---- forecasting checks: expected = independent pandas recomputation
    checks.extend(forecast_checks(con))
    write_results(con)

    # ---- print the table
    rows, failed = [], 0
    for query, what, published, result in checks:
        ok = (published == result) or (
            isinstance(published, float) and isinstance(result, float) and round(published, 1) == round(result, 1))
        failed += not ok
        rows.append((query, what, fmt(published), fmt(result), "yes" if ok else "NO"))

    w = [max(len(r[i]) for r in rows + [("Query", "Check", "Expected", "SQL result", "Match")]) for i in range(5)]
    line = lambda r: "| " + " | ".join(str(c).ljust(w[i]) for i, c in enumerate(r)) + " |"
    table = [line(("Query", "Check", "Expected", "SQL result", "Match")),
             "|-" + "-|-".join("-" * x for x in w) + "-|"] + [line(r) for r in rows]
    print("\nCHECK TABLE\n" + "\n".join(table))
    (HERE / "check_table.md").write_text("\n".join(table) + "\n", encoding="utf-8")

    print(f"\n{len(rows) - failed} of {len(rows)} checks match.")
    if failed:
        sys.exit("Some checks do NOT match. Report them; do not edit the published numbers.")


if __name__ == "__main__":
    main()
