"""
Shared, tested helpers for date-based transformations of time series.

All of them compare by calendar date, never by position, so a missing observation gives NaN
instead of a comparison with the wrong period (and nothing is forward-filled).

  value_months_earlier   value of a column exactly N calendar months before each row's date
  pct_change_by_date     % change versus N months earlier (yoy: 12, qoq: 3, mom: 1)
  diff_by_date           difference versus N months earlier (pp for rates)
  sum_by_date            rolling sum over N monthly periods, NaN unless all N are present
  asof_values            value of the last observation on or before given dates (NaN if none)
  pct_change_asof        % change versus the last observation on or before (date - offset)
  diff_asof              difference versus the last observation on or before (date - offset)

Unit tests: tests/test_series_ops.py (python -m unittest).
"""

import pandas as pd


def value_months_earlier(df: pd.DataFrame, col: str, months: int) -> pd.Series:
    """
    Value of `col` exactly `months` calendar months before each row's date.

    If the comparison period is missing the result is NaN. Duplicated dates keep the last row.
    """
    base = df.drop_duplicates(subset=["date"], keep="last").set_index("date")[col]
    prior = pd.Series(base.values, index=base.index + pd.DateOffset(months=months))
    return df["date"].map(prior)


def pct_change_by_date(df: pd.DataFrame, col: str, months: int) -> pd.Series:
    """Percent change of `col` versus `months` calendar months earlier (NaN if that period is missing or zero)."""
    prev = value_months_earlier(df, col, months).replace(0, float("nan"))
    return (df[col] / prev - 1) * 100


def diff_by_date(df: pd.DataFrame, col: str, months: int) -> pd.Series:
    """Difference of `col` versus `months` calendar months earlier (percentage points for rates)."""
    return df[col] - value_months_earlier(df, col, months)


def sum_by_date(df: pd.DataFrame, col: str, months: int = 12) -> pd.Series:
    """
    Sum of `col` over the `months` calendar months ending at each row's date.

    NaN unless every one of the `months` consecutive monthly periods (date, date - 1 month, ...,
    date - (months - 1)) is present and not null. Terms are added most recent first, one at a
    time, so the result is bit-identical to a plain loop. Intended for monthly series dated on
    the first of the month; other days fall back to the exact per-date lookup.
    """
    base = df.drop_duplicates(subset=["date"], keep="last").set_index("date")[col].dropna()
    if base.empty:
        return pd.Series(float("nan"), index=df.index)
    if (base.index.day != 1).any() or (df["date"].dt.day != 1).any():
        lookup = base.to_dict()
        out = []
        for d in df["date"]:
            total = 0.0
            for k in range(months):
                v = lookup.get(d - pd.DateOffset(months=k))
                if v is None:
                    total = float("nan")
                    break
                total += v
            out.append(total)
        return pd.Series(out, index=df.index)
    full = pd.date_range(base.index.min() - pd.DateOffset(months=months - 1), base.index.max(), freq="MS")
    s = base.reindex(full)
    total = pd.Series(0.0, index=full)
    for k in range(months):
        total = total + s.shift(k)
    return df["date"].map(total)


def asof_values(df: pd.DataFrame, keys: pd.Series, col: str) -> pd.Series:
    """
    Value of `col` at the last observation dated on or before each of `keys` (NaN if none),
    aligned to df's index. `df` needs a `date` column; null values of `col` are ignored.
    """
    left = pd.DataFrame({"key": keys.values}, index=df.index).reset_index().sort_values("key")
    right = df[["date", col]].dropna().sort_values("date")
    merged = pd.merge_asof(left, right, left_on="key", right_on="date", direction="backward")
    return merged.set_index("index")[col].reindex(df.index)


def pct_change_asof(df: pd.DataFrame, col: str, offset: pd.DateOffset) -> pd.Series:
    """% change versus the last observation on or before (date - offset), e.g. offset=DateOffset(years=1)."""
    prev = asof_values(df, df["date"] - offset, col)
    return (df[col] / prev - 1) * 100


def diff_asof(df: pd.DataFrame, col: str, offset: pd.DateOffset) -> pd.Series:
    """Difference versus the last observation on or before (date - offset)."""
    return df[col] - asof_values(df, df["date"] - offset, col)
