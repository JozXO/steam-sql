"""
load_data.py
Builds steam.duckdb (one local file) from the CSVs in data/ and checks row counts.
Run:  python load_data.py
"""
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
DB = HERE / "steam.duckdb"
DATA = (HERE / "data").as_posix()

# Row counts we expect. If a count is off, the loader stops.
EXPECTED = {"reviews": 218380, "baseline": 98}


def load(db_path=DB):
    if Path(db_path).exists():
        Path(db_path).unlink()
    con = duckdb.connect(str(db_path))

    # One row per Steam review (Apex Legends, 5 languages).
    # created_at is the review time in UTC; month is the first day of that month.
    con.execute(f"""
        CREATE TABLE reviews AS
        SELECT recommendationid                              AS review_id,
               language,
               voted_up,                                     -- 1 positive, 0 negative
               TIMESTAMP '1970-01-01' + to_seconds(timestamp_created) AS created_at,
               date_trunc('month',
                          TIMESTAMP '1970-01-01' + to_seconds(timestamp_created))::DATE AS month,
               playtime_at_review_min / 60.0                 AS hours_played
        FROM read_csv('{DATA}/reviews_apex.csv.gz')
    """)

    # Steam lifetime totals per game and language (14 games, 7 language rows each).
    con.execute(f"""
        CREATE TABLE baseline AS
        SELECT app_id,
               game_name_expected AS game,
               language,
               total_reviews,
               total_positive,
               total_negative
        FROM read_csv('{DATA}/baseline_summaries.csv')
    """)

    # Published figures from the study, loaded only so queries can be compared.
    for name in ["apex_review_bombs", "apex_gap_bomb_effect", "gaps_by_game", "data_quality"]:
        con.execute(f"CREATE TABLE published_{name} AS "
                    f"SELECT * FROM read_csv('{DATA}/published/{name}.csv')")
    return con


def check_counts(con):
    ok = True
    for table, expected in EXPECTED.items():
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        status = "OK" if n == expected else "WRONG"
        print(f"  {table:<10} {n:>9,} rows (expected {expected:,})  {status}")
        ok &= n == expected
    return ok


if __name__ == "__main__":
    con = load()
    print("Loaded steam.duckdb")
    if not check_counts(con):
        sys.exit("Row counts do not match. Stopping.")
