import time
import unittest

from src.fetchers.eurostat_client import EurostatError, jsonstat_to_long
from src.fetchers.http_session import CircuitBreaker, Session, make_session, map_bounded
from src.fetchers.ine_indicators import SeriesError, validate_series


class MapBoundedTests(unittest.TestCase):
    def test_order_and_errors_are_kept(self):
        def fn(x):
            if x == 2:
                raise ValueError("boom")
            return x * 10
        out = map_bounded(fn, [1, 2, 3], max_workers=3)
        self.assertEqual(out[0], (10, None))
        self.assertIsNone(out[1][0])
        self.assertIsInstance(out[1][1], ValueError)
        self.assertEqual(out[2], (30, None))

    def test_concurrency_is_bounded(self):
        active, peak = [0], [0]

        def fn(_):
            active[0] += 1
            peak[0] = max(peak[0], active[0])
            time.sleep(0.02)
            active[0] -= 1
        map_bounded(fn, range(12), max_workers=3)
        self.assertLessEqual(peak[0], 3)

    def test_single_worker_runs_inline(self):
        self.assertEqual(map_bounded(lambda x: x + 1, [1, 2], max_workers=1), [(2, None), (3, None)])


class CircuitBreakerTests(unittest.TestCase):
    def test_opens_after_threshold_and_resets_on_success(self):
        cb = CircuitBreaker(threshold=3)
        for _ in range(2):
            cb.failure()
        cb.check()
        cb.success()
        for _ in range(3):
            cb.failure()
        with self.assertRaises(ConnectionError):
            cb.check()


class SessionTests(unittest.TestCase):
    def test_default_timeout_is_applied(self):
        s = Session()
        seen = {}
        import requests
        orig = requests.Session.request
        try:
            requests.Session.request = lambda self, method, url, **kw: seen.update(kw)
            s.request("GET", "http://x")
        finally:
            requests.Session.request = orig
        self.assertIn("timeout", seen)

    def test_make_session_retries_on_429_and_5xx(self):
        s = make_session(retries=3)
        retry = s.get_adapter("https://example.org").max_retries
        self.assertEqual(retry.total, 3)
        for code in (429, 500, 502, 503, 504):
            self.assertIn(code, retry.status_forcelist)


class ValidateSeriesTests(unittest.TestCase):
    item = {"COD": "IPC1", "Nombre": "Total Nacional. Índice general. Variación anual", "Data": [{"Valor": 1}]}

    def test_ok_and_total_nacional_normalised(self):
        validate_series("IPC1", ["Nacional", "Índice general"], self.item)

    def test_wrong_code(self):
        with self.assertRaises(SeriesError):
            validate_series("IPC2", [], self.item)

    def test_not_a_dict(self):
        with self.assertRaises(SeriesError):
            validate_series("IPC1", [], [])

    def test_empty_data(self):
        with self.assertRaises(SeriesError):
            validate_series("IPC1", [], dict(self.item, Data=[]))

    def test_name_token_missing(self):
        with self.assertRaises(SeriesError):
            validate_series("IPC1", ["Alimentos"], self.item)


def js(values, **extra):
    return {
        "id": ["freq", "geo", "time"],
        "size": [1, 2, 3],
        "dimension": {
            "freq": {"category": {"index": {"M": 0}}},
            "geo": {"category": {"index": {"ES": 0, "EU27": 1}}},
            "time": {"category": {"index": {"2024-01": 0, "2024-02": 1, "2024-03": 2}}},
        },
        "value": values,
    }


class JsonStatTests(unittest.TestCase):
    def test_row_major_layout_and_missing_values(self):
        df = jsonstat_to_long(js({"0": 1.0, "2": 3.0, "4": 5.0}), "x", [])
        got = {(r.geo, r.period): r.value for r in df.itertuples()}
        self.assertEqual(got, {("ES", "2024-01"): 1.0, ("ES", "2024-03"): 3.0, ("EU27", "2024-02"): 5.0})
        self.assertEqual(list(df.columns), ["freq", "geo", "period", "value"])

    def test_values_as_list_skips_none(self):
        df = jsonstat_to_long(js([1.0, None, 3.0, None, None, 6.0]), "x", [])
        self.assertEqual(len(df), 3)

    def test_unfiltered_dimension_raises(self):
        data = js({"0": 1.0})
        data["dimension"]["freq"]["category"]["index"] = {"M": 0, "Q": 1}
        data["size"][0] = 2
        with self.assertRaises(EurostatError):
            jsonstat_to_long(data, "x", [])
        jsonstat_to_long(data, "x", ["freq"])


if __name__ == "__main__":
    unittest.main()
