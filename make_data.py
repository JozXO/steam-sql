"""
make_data.py  (optional, run once by the author)
Builds the small data files in data/ from the original study files.

It only READS the originals. It keeps the columns the SQL needs and drops the
review text, so the file is small enough to keep in git. Anyone cloning the
repo can skip this script and use the files already in data/.
"""
import gzip
import shutil
import sys
from pathlib import Path

import pandas as pd

STUDY = Path(r"D:\Portfolio Project\player-sentiment\01_data")
HERE = Path(__file__).parent
OUT = HERE / "data"
(OUT / "published").mkdir(parents=True, exist_ok=True)

KEEP = ["recommendationid", "language", "voted_up", "timestamp_created",
        "playtime_at_review_min"]
raw = pd.read_csv(STUDY / "raw" / "reviews_raw.csv", usecols=KEEP)
print("original rows:", len(raw))
raw.to_csv(OUT / "reviews_apex.csv.gz", index=False, compression="gzip")

base = pd.read_csv(STUDY / "raw" / "baseline_summaries.csv", encoding="utf-8")
base = base[["app_id", "game_name_expected", "language", "total_reviews",
             "total_positive", "total_negative"]]
base.to_csv(OUT / "baseline_summaries.csv", index=False)
print("baseline rows:", len(base))

# Published outputs of the study, copied unchanged, used only to check the SQL.
for name in ["apex_review_bombs.csv", "apex_gap_bomb_effect.csv", "gaps_by_game.csv"]:
    shutil.copy(STUDY / "processed" / name, OUT / "published" / name)
shutil.copy(r"D:\PROJECTS\steam-dashboards\dashboard_data\data_quality.csv",
            OUT / "published" / "data_quality.csv")
print("done")
