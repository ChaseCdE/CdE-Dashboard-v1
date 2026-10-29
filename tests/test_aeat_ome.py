import unittest

import pandas as pd

from src.scripts.process_aeat_data import _date, division_key


class OmeTest(unittest.TestCase):
    def test_division_key(self):
        self.assertEqual(division_key("10 - Industria de la alimentación"), ("10", "Industria de la alimentación"))
        self.assertEqual(division_key("41+42+43 - Construcción")[0], "41+42+43")
        self.assertEqual(division_key("4671 - Comercio al por mayor de combustibles")[0], "46")
        self.assertEqual(division_key("467 (sin 4671) - Otro comercio al por mayor especializado")[0], "46")
        self.assertEqual(division_key("471 - Comercio al por menor en establecimientos no especializados")[0], "47")
        self.assertEqual(division_key("Total"), ("", ""))

    def test_date(self):
        d = _date(pd.Series(["2026-2T", "2009-1T"]))
        self.assertEqual(list(d.dt.strftime("%Y-%m-%d")), ["2026-04-01", "2009-01-01"])
        with self.assertRaises(ValueError):
            _date(pd.Series(["2026"]))


if __name__ == "__main__":
    unittest.main()
