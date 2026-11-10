"""
forecast_checks.py
An independent recomputation of everything in the forecasting part, using pandas and numpy only.
It does NOT call the SQL queries or forecast.py to get its expected numbers: it reads the raw
reviews file, rebuilds the monthly series, makes every forecast again with different code
(pandas .rolling and .ewm instead of SQL windows and a Python loop), scores them, and
compares with what the SQL and forecast.py produced.

run_all.py calls forecast_checks(...) and adds the returned rows to the check table.
Each row is (query, what, expected, result). For these rows "expected" is the pandas number.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import forecast  # only for the constants and for the identity checks at the end

HERE = Path(__file__).parent
ALPHAS = np.round(np.arange(1, 21) * 0.05, 2)     # 0.05 ... 1.00, written differently from forecast.py
MODELS = ["naive", "seasonal_naive", "moving_avg_3", "ses"]


def pandas_series():
    df = pd.read_csv(HERE / "data" / "reviews_apex.csv.gz")
    df["created"] = pd.to_datetime(df["timestamp_created"], unit="s")
    df["month"] = df["created"].dt.to_period("M").dt.to_timestamp()
    data_end = df.groupby("language")["created"].max().min()          # earliest "last review" of the 5 languages
    part_month = data_end.to_period("M").to_timestamp()               # that month is not complete
    keep = df[(df["month"] >= "2024-10-01") & (df["month"] < part_month)]
    g = keep.groupby(["language", "month"])["voted_up"].agg(reviews="size", share="mean").reset_index()
    g["positive_pct"] = 100 * g["share"]
    return g.drop(columns="share").sort_values(["language", "month"]).reset_index(drop=True)


def pandas_forecasts(series):
    """Every forecast, one row per language, measure, horizon and target month."""
    rows = []
    for language, grp in series.groupby("language"):
        months = grp["month"].tolist()
        for metric, col in (("volume", "reviews"), ("positive_pct", "positive_pct")):
            y = grp[col].astype(float).to_numpy()
            ys = pd.Series(y)
            ma3 = ys.rolling(3).mean().to_numpy()                      # average of this and the 2 months before
            for h in forecast.HORIZONS:
                for t in range(11 + h, len(y)):                        # target position (0-based)
                    o = t - h                                          # origin position
                    hist = y[: o + 1]
                    best_sse, best_a, best_level = None, None, None
                    for a in ALPHAS:
                        lv = pd.Series(hist).ewm(alpha=a, adjust=False).mean().to_numpy()
                        sse = float(((hist[1:] - lv[:-1]) ** 2).sum())
                        if best_sse is None or sse < best_sse:
                            best_sse, best_a, best_level = sse, a, lv[-1]
                    rows.append(dict(language=language, metric=metric, horizon=h, target_month=months[t],
                                     actual=y[t], naive=y[o], seasonal_naive=y[t - 12],
                                     moving_avg_3=ma3[o], ses=best_level, alpha=best_a))
    return pd.DataFrame(rows)


def pandas_scores(fc):
    long = fc.melt(id_vars=["language", "metric", "horizon", "target_month", "actual"],
                   value_vars=MODELS, var_name="model", value_name="forecast")
    long["abs_err"] = (long["actual"] - long["forecast"]).abs()
    long["pct_err"] = long["abs_err"] / long["actual"]
    s = long.groupby(["language", "metric", "horizon", "model"]).agg(
        months_scored=("abs_err", "size"), mae=("abs_err", "mean"), mape=("pct_err", "mean")).reset_index()
    s["mape_pct"] = np.where(s["metric"] == "volume", 100 * s["mape"], np.nan)
    naive_mae = s[s["model"] == "naive"].set_index(["language", "metric", "horizon"])["mae"]
    s["naive_mae"] = [naive_mae[(a, b, c)] for a, b, c in zip(s["language"], s["metric"], s["horizon"])]
    s["vs_naive_pct"] = 100 * (1 - s["mae"] / s["naive_mae"])
    return s


def _same(a, b, tol=1e-6):
    return bool(np.isclose(a, b, rtol=tol, atol=tol))


def forecast_checks(con):
    """con: DuckDB connection after queries 11 to 15 and the SES table have been created."""
    checks = []
    add = lambda q, what, exp, res: checks.append((q, what, exp, res))

    # ---- Q11: the series
    ps = pandas_series()
    ss = con.execute("SELECT language, strftime(month, '%Y-%m') AS month, reviews, positive_pct "
                     "FROM monthly_series ORDER BY language, month").df()
    add("Q11", "Monthly series rows (5 languages x 23 months)", int(len(ps)), int(len(ss)))
    ps_m = ps.assign(month=ps["month"].dt.strftime("%Y-%m"))
    mm = ps_m.merge(ss, on=["language", "month"], suffixes=("_p", "_s"))
    ok = sum(1 for r in mm.itertuples() if r.reviews_p == r.reviews_s and _same(r.positive_pct_p, r.positive_pct_s))
    add("Q11", "Series values (reviews, positive %) identical to pandas, all rows",
        f"{len(ps)} of {len(ps)}", f"{ok} of {len(ps)}")
    add("Q11", "Series runs October 2024 to August 2026, no July to September 2024",
        f"{ps_m['month'].min()} to {ps_m['month'].max()}, {int(ps_m['month'].between('2024-07', '2024-09').sum())} bomb months",
        f"{ss['month'].min()} to {ss['month'].max()}, {int(ss['month'].between('2024-07', '2024-09').sum())} bomb months")

    # ---- Q12 and SES: every forecast
    pf = pandas_forecasts(ps)
    sf = con.execute("""SELECT b.language, b.metric, b.horizon, strftime(b.target_month, '%Y-%m') AS target_month,
                               b.actual, b.naive, b.seasonal_naive, b.moving_avg_3, s.ses, s.alpha
                        FROM baseline_forecasts b
                        JOIN ses_forecasts s USING (language, metric, horizon, target_month)""").df()
    pf["target_month"] = pf["target_month"].dt.strftime("%Y-%m")
    key = ["language", "metric", "horizon", "target_month"]
    mf = pf.merge(sf, on=key, suffixes=("_p", "_s"))
    n = len(pf)
    add("Q12", "Forecast rows: 5 languages x 2 measures x (11 + 9) target months", n, int(len(sf)))
    for name, label in (("naive", "Naive forecasts"), ("seasonal_naive", "Seasonal naive forecasts"),
                        ("moving_avg_3", "3-month moving average forecasts")):
        ok = sum(_same(r[name + "_p"], r[name + "_s"]) for _, r in mf.iterrows())
        add("Q12", f"{label} identical to pandas, all rows", f"{n} of {n}", f"{ok} of {len(mf)}")
    ok = sum(_same(r["ses_p"], r["ses_s"]) and _same(r["alpha_p"], r["alpha_s"]) for _, r in mf.iterrows())
    add("SES", "SES forecasts and chosen alpha identical to pandas (.ewm), all rows", f"{n} of {n}", f"{ok} of {len(mf)}")

    # ---- SES identities (the two ways of writing it agree; alpha = 1 is the naive forecast)
    y = ps[ps["language"] == "english"]["reviews"].astype(float).to_numpy()
    a = 0.3
    t = len(y)
    closed = sum(a * (1 - a) ** j * y[t - 1 - j] for j in range(t - 1)) + (1 - a) ** (t - 1) * y[0]
    add("SES", "SES level, loop vs weighted-average formula (English volume, alpha 0.3)",
        round(float(closed), 1), round(float(forecast.ses_levels(list(y), a)[-1]), 1))
    add("SES", "SES with alpha = 1 gives the last value (= naive)",
        float(y[-1]), float(forecast.ses_levels(list(y), 1.0)[-1]))

    # ---- Q13: scores
    sc_p = pandas_scores(pf)
    sc_s = con.execute("SELECT language, metric, horizon, model, months_scored, mae, mape_pct, vs_naive_pct "
                       "FROM backtest_scores").df()
    ms = sc_p.merge(sc_s, on=["language", "metric", "horizon", "model"], suffixes=("_p", "_s"))
    ok = 0
    for _, r in ms.iterrows():
        good = r["months_scored_p"] == r["months_scored_s"] and _same(r["mae_p"], r["mae_s"]) \
               and _same(r["vs_naive_pct_p"], r["vs_naive_pct_s"])
        if r["metric"] == "volume":
            good = good and _same(r["mape_pct_p"], r["mape_pct_s"])
        ok += bool(good)
    add("Q13", "Backtest scores (MAE, MAPE, vs naive), 80 rows, identical to pandas", f"{len(sc_p)} of {len(sc_p)}",
        f"{ok} of {len(sc_p)}")
    for metric, h, model, lang in (("volume", 1, "naive", "english"), ("volume", 1, "ses", "english"),
                                   ("positive_pct", 1, "naive", "english"), ("positive_pct", 1, "ses", "english")):
        unit = "reviews" if metric == "volume" else "points"
        p = sc_p[(sc_p.language == lang) & (sc_p.metric == metric) & (sc_p.horizon == h) & (sc_p.model == model)]["mae"].iloc[0]
        s = sc_s[(sc_s.language == lang) & (sc_s.metric == metric) & (sc_s.horizon == h) & (sc_s.model == model)]["mae"].iloc[0]
        add("Q13", f"English {metric.replace('_pct', ' share')} MAE, 1 month ahead, {model} ({unit})", round(float(p), 1), round(float(s), 1))

    # ---- Q14: wins vs naive
    wp = (sc_p[sc_p.model != "naive"].assign(better=lambda d: d.vs_naive_pct > 0)
          .groupby(["metric", "horizon", "model"])["better"].sum().astype(int))
    ws = con.execute("SELECT metric, horizon, model, languages_better FROM (SELECT metric, horizon, model, "
                     "count(*) FILTER (WHERE vs_naive_pct > 0) AS languages_better FROM backtest_scores "
                     "WHERE model <> 'naive' GROUP BY ALL)").df().set_index(["metric", "horizon", "model"])["languages_better"]
    ok = sum(int(wp[k]) == int(ws[k]) for k in wp.index)
    add("Q14", "Languages beating naive, per measure, horizon and model (12 rows)", f"{len(wp)} of {len(wp)}", f"{ok} of {len(wp)}")

    # ---- Q15: plan vs actual (last 6 months, horizon 1)
    last6 = sorted(ps_m["month"].unique())[-6:]
    pv = pf[(pf.horizon == 1) & (pf.target_month.isin(last6))]
    sv = con.execute("""SELECT b.language, b.metric, strftime(b.target_month, '%Y-%m') AS target_month,
                               b.actual, s.ses
                        FROM baseline_forecasts b JOIN ses_forecasts s USING (language, metric, horizon, target_month)
                        WHERE b.horizon = 1
                          AND b.target_month >= (SELECT max(month) - INTERVAL 5 MONTH FROM monthly_series)""").df()
    mv = pv.merge(sv, on=["language", "metric", "target_month"], suffixes=("_p", "_s"))
    ok = sum(_same(r["actual_p"], r["actual_s"]) and _same(r["ses_p"], r["ses_s"]) for _, r in mv.iterrows())
    add("Q15", "Plan vs actual, last 6 months (60 rows): actual and SES plan identical to pandas",
        f"{len(pv)} of {len(pv)}", f"{ok} of {len(pv)}")
    return checks
