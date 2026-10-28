import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.fetchers.ine_series import INDICATORS, code
from src.processors.ine_processor import INEProcessor, SeriesNotFound


def write_raw(raw_dir: Path, ind: str, rows):
    pd.DataFrame(rows, columns=["series_code", "series_name", "date", "value"]).to_csv(
        raw_dir / INDICATORS[ind]["file"], index=False)


class PickTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raw = Path(self.tmp.name) / "raw"
        self.out = Path(self.tmp.name) / "out"
        self.raw.mkdir()
        self.out.mkdir()
        self.proc = INEProcessor(input_dir=str(self.raw), output_dir=str(self.out))

    def tearDown(self):
        self.tmp.cleanup()

    def test_pick_selects_by_code(self):
        role = next(iter(INDICATORS["cpi"]["series"]))
        c = code("cpi", role)
        write_raw(self.raw, "cpi", [(c, "n", "2024-01-01", 1.0), ("OTHER", "n", "2024-01-01", 9.0)])
        got = self.proc._pick("cpi", role)
        self.assertEqual(list(got["value"]), [1.0])

    def test_pick_missing_code_raises(self):
        role = next(iter(INDICATORS["cpi"]["series"]))
        write_raw(self.raw, "cpi", [("OTHER", "n", "2024-01-01", 9.0)])
        with self.assertRaises(SeriesNotFound):
            self.proc._pick("cpi", role)

    def test_pick_missing_file_raises(self):
        role = next(iter(INDICATORS["cpi"]["series"]))
        with self.assertRaises(SeriesNotFound):
            self.proc._pick("cpi", role)

    def test_gdp_productivity_requires_its_inputs(self):
        with self.assertRaises(SeriesNotFound):
            self.proc.process_gdp_productivity()

    def test_gdp_productivity_requires_base_quarter(self):
        dates = pd.date_range("2020-01-01", periods=4, freq="QS")
        pd.DataFrame({"date": dates, "gdp_index": 100.0}).to_csv(self.out / "gdp.csv", index=False)
        pd.DataFrame({"date": dates, "employed_persons": 1.0, "hours_worked": 1.0}).to_csv(self.out / "cntr_employment.csv", index=False)
        pd.DataFrame({"date": dates, "total_population": 1.0, "working_age_population": 1.0}).to_csv(self.out / "population.csv", index=False)
        with self.assertRaises(SeriesNotFound):
            self.proc.process_gdp_productivity()


if __name__ == "__main__":
    unittest.main()
