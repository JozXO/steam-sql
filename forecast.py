"""
forecast.py
Simple exponential smoothing (SES), written out in plain Python, and the rolling backtest for it.
(The other three models, naive, seasonal naive and 3-month moving average, are in queries/12.)

SES in one line: the "level" is a weighted average of all months so far, where the newest
month gets weight alpha and the older months fade away.
    level_1 = value_1
    level_t = alpha * value_t + (1 - alpha) * level_(t-1)
The forecast for any later month is the latest level (a flat line).

alpha is picked from 0.05, 0.10 ... 1.00 using ONLY the months up to the forecast origin:
the alpha whose one-step forecasts (level_(t-1) for month t) had the smallest squared error
on that history. alpha = 1 means "naive" (last month repeats), so SES can match the naive
baseline but is free to do better or worse.
"""

ALPHAS = [i / 20 for i in range(1, 21)]      # 0.05, 0.10, ... 1.00
MIN_HISTORY = 12                             # same first origin as queries/12
HORIZONS = (1, 3)


def ses_levels(values, alpha):
    """Level after each month, starting from the first value."""
    level = values[0]
    levels = [level]
    for v in values[1:]:
        level = alpha * v + (1 - alpha) * level
        levels.append(level)
    return levels


def best_alpha(values):
    """The alpha with the smallest squared one-step error on `values` (first one wins a tie)."""
    best_sse, best = None, None
    for alpha in ALPHAS:
        levels = ses_levels(values, alpha)
        # month k (k >= 1) is forecast by the level after month k-1
        sse = sum((values[k] - levels[k - 1]) ** 2 for k in range(1, len(values)))
        if best_sse is None or sse < best_sse:
            best_sse, best = sse, alpha
    return best


def ses_backtest(series):
    """
    series: list of (language, month, reviews, positive_pct) rows, sorted by language and month.
    Returns rows (language, metric, horizon, target_month, alpha, ses) for every origin with at
    least MIN_HISTORY months of history, using only the months up to that origin.
    """
    by_lang = {}
    for language, month, reviews, pos in series:
        by_lang.setdefault(language, []).append((month, float(reviews), float(pos)))

    out = []
    for language, rows in by_lang.items():
        months = [r[0] for r in rows]
        for metric, col in (("volume", 1), ("positive_pct", 2)):
            values = [r[col] for r in rows]
            for h in HORIZONS:
                for origin in range(MIN_HISTORY, len(values) - h + 1):   # origin = months of history
                    history = values[:origin]
                    alpha = best_alpha(history)
                    forecast = ses_levels(history, alpha)[-1]
                    out.append((language, metric, h, months[origin + h - 1], alpha, forecast))
    return out


def add_ses_table(con):
    """Run the SES backtest on the monthly_series view and save it as the table ses_forecasts."""
    series = con.execute(
        "SELECT language, month, reviews, positive_pct FROM monthly_series ORDER BY language, month"
    ).fetchall()
    rows = ses_backtest(series)
    con.execute("DROP TABLE IF EXISTS ses_forecasts")
    con.execute("CREATE TABLE ses_forecasts (language VARCHAR, metric VARCHAR, horizon INTEGER, "
                "target_month DATE, alpha DOUBLE, ses DOUBLE)")
    con.executemany("INSERT INTO ses_forecasts VALUES (?, ?, ?, ?, ?, ?)", rows)
    return len(rows)
