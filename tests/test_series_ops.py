import unittest

import numpy as np
import pandas as pd

from src.processors.series_ops import (
    asof_values, diff_asof, diff_by_date, pct_change_asof, pct_change_by_date,
    sum_by_date, value_months_earlier,
)


def monthly(values, start="2020-01-01"):
    return pd.DataFrame({"date": pd.date_range(start, periods=len(values), freq="MS"), "value": values})


def loop_sum(df, col, months):
    lookup = dict(zip(df["date"], df[col]))
    out = []
    for d in df["date"]:
        total = 0.0
        for k in range(months):
            v = lookup.get(d - pd.DateOffset(months=k))
            if v is None or pd.isna(v):
                total = float("nan")
                break
            total += v
        out.append(total)
    return pd.Series(out, index=df.index)


class ByDateTests(unittest.TestCase):
    def test_value_months_earlier_and_gap(self):
        df = monthly([1.0, 2.0, 3.0, 4.0]).drop(index=1).reset_index(drop=True)
        got = value_months_earlier(df, "value", 1)
        self.assertTrue(np.isnan(got[0]))
        self.assertTrue(np.isnan(got[1]))  # 2020-03 vs missing 2020-02
        self.assertEqual(got[2], 3.0)

    def test_pct_change_yoy(self):
        df = monthly([100.0] * 12 + [110.0])
        self.assertAlmostEqual(pct_change_by_date(df, "value", 12).iloc[-1], 10.0)
        self.assertTrue(pct_change_by_date(df, "value", 12).iloc[:12].isna().all())

    def test_pct_change_zero_base_is_nan(self):
        df = monthly([0.0, 5.0])
        self.assertTrue(np.isnan(pct_change_by_date(df, "value", 1).iloc[1]))

    def test_diff(self):
        df = monthly([1.0, 3.5])
        self.assertEqual(diff_by_date(df, "value", 1).iloc[1], 2.5)

    def test_sum_matches_loop_bit_exact(self):
        rng = np.random.default_rng(0)
        df = monthly(list(rng.normal(size=40) * 1e3))
        pd.testing.assert_series_equal(sum_by_date(df, "value", 12), loop_sum(df, "value", 12), check_names=False)

    def test_sum_requires_all_periods(self):
        df = monthly(list(range(14))).drop(index=5).reset_index(drop=True)
        got = sum_by_date(df, "value", 12)
        self.assertTrue(got.isna().all())
        df2 = monthly([1.0] * 14)
        df2.loc[3, "value"] = np.nan
        self.assertEqual(sum_by_date(df2, "value", 12).notna().sum(), loop_sum(df2, "value", 12).notna().sum())

    def test_sum_non_first_of_month_fallback(self):
        df = pd.DataFrame({"date": pd.date_range("2020-01-31", periods=14, freq="ME"), "value": np.arange(14.0)})
        pd.testing.assert_series_equal(sum_by_date(df, "value", 3), loop_sum(df, "value", 3), check_names=False)


class AsofTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "date": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06", "2021-01-04", "2021-01-05"]),
            "value": [100.0, 110.0, 120.0, 132.0, 150.0],
        })

    def test_asof_uses_last_on_or_before(self):
        keys = self.df["date"] - pd.DateOffset(years=1)
        got = asof_values(self.df, keys, "value")
        self.assertTrue(np.isnan(got[0]))
        self.assertEqual(got[3], 110.0)  # 2020-01-04 -> last obs 2020-01-03
        self.assertEqual(got[4], 110.0)  # 2020-01-05 -> 2020-01-03 (no later obs)
    def test_pct_and_diff(self):
        off = pd.DateOffset(years=1)
        self.assertAlmostEqual(pct_change_asof(self.df, "value", off).iloc[4], (150 / 110 - 1) * 100)
        self.assertEqual(diff_asof(self.df, "value", off).iloc[4], 40.0)


if __name__ == "__main__":
    unittest.main()
