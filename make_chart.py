"""
make_chart.py
Draws results/forecast_vs_actual_english.png: English reviews, forecast one month ahead vs actual.
Run  python run_all.py  first (it builds the tables), then  python make_chart.py.
Needs matplotlib (pip install matplotlib).
"""
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
con = duckdb.connect(str(HERE / "steam.duckdb"), read_only=True)

series = con.execute("SELECT month, reviews, positive_pct FROM monthly_series "
                     "WHERE language = 'english' ORDER BY month").df()
fc = con.execute("""
    SELECT b.metric, b.target_month AS month, b.naive, s.ses
    FROM baseline_forecasts b JOIN ses_forecasts s USING (language, metric, horizon, target_month)
    WHERE b.language = 'english' AND b.horizon = 1
    ORDER BY b.target_month""").df()
mae = {(r.metric, r.model): r.mae for r in con.execute(
    "SELECT metric, model, mae FROM backtest_scores WHERE language = 'english' AND horizon = 1 "
    "AND model IN ('naive', 'ses')").df().itertuples()}

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
NAIVE, SES = "#eb6834", "#2a78d6"            # categorical slots 2 and 1 of the reference palette

fig, axes = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True, facecolor=SURFACE)
panels = [("volume", "reviews", "Reviews per month", "reviews"),
          ("positive_pct", "positive_pct", "Positive share (%)", "points")]
for ax, (metric, col, title, unit) in zip(axes, panels):
    ax.set_facecolor(SURFACE)
    f = fc[fc.metric == metric]
    ax.axvspan(f.month.min() - pd.Timedelta(days=15), f.month.max() + pd.Timedelta(days=15),
               color=GRID, alpha=0.45, lw=0)
    ax.plot(series.month, series[col], color=INK, lw=2, label="Actual", zorder=3)
    ax.plot(f.month, f.naive, color=NAIVE, lw=2, ls="--", marker="o", ms=5, mec=SURFACE, mew=1.5,
            label=f"Naive (last month repeats), MAE {mae[(metric, 'naive')]:,.1f} {unit}", zorder=2)
    ax.plot(f.month, f.ses, color=SES, lw=2, marker="o", ms=5, mec=SURFACE, mew=1.5,
            label=f"Exponential smoothing, MAE {mae[(metric, 'ses')]:,.1f} {unit}", zorder=2)
    ax.set_title(title, loc="left", fontsize=12, color=INK, fontweight="bold")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.legend(loc="upper right" if metric == "volume" else "upper left", frameon=False, fontsize=9, labelcolor=INK)
axes[1].set_xlabel("Shaded: the 11 backtest months (October 2025 to August 2026). Each forecast is made at the end of the "
                   "month before, using only earlier months.", fontsize=8.5, color=MUTED, loc="left")
fig.suptitle("Apex Legends, English reviews: one-month-ahead forecast vs actual", x=0.06, ha="left",
             fontsize=14, color=INK, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.96))
out = HERE / "results" / "forecast_vs_actual_english.png"
fig.savefig(out, dpi=150, facecolor=SURFACE)
print("Wrote", out)
