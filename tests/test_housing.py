import unittest

import pandas as pd

from src.scripts.process_housing_data import _num, _quarter_start


class HousingParsingTest(unittest.TestCase):
    def test_spanish_numbers(self):
        s = pd.Series(["1961,66", "2392", "174711", " 2.392,5 ", "", None])
        out = _num(s).tolist()
        self.assertEqual(out[:4], [1961.66, 2392.0, 174711.0, 2392.5])
        self.assertTrue(pd.isna(out[4]) and pd.isna(out[5]))

    def test_quarter_start(self):
        out = _quarter_start(pd.Series(["2026-06-30", "2026-04-01", "2025-12-31"]))
        self.assertEqual([d.strftime("%Y-%m-%d") for d in out], ["2026-04-01", "2026-04-01", "2025-10-01"])


if __name__ == "__main__":
    unittest.main()
