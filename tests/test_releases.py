import unittest

from src.export import releases


def manifest(cpi_date, flash=False, gdp_date="2026-04-01"):
    cpi = {"id": "ine.cpi_special_groups", "series": [{"key": "headline", "latest": {"yoy": [cpi_date, 4.9]}}]}
    if flash:
        cpi["provisional"] = [cpi_date]
    gdp = {"id": "ine.gdp", "series": [{"key": "es", "latest": {"qoq": [gdp_date, 0.6]}}]}
    return {"datasets": [cpi, gdp]}


class ReleasesTest(unittest.TestCase):
    def test_new_flash_and_final(self):
        ev = releases.update_events([], manifest("2026-09-01"), manifest("2026-10-01", flash=True), "2026-10-30")
        self.assertEqual(ev, [{"id": "ine.cpi_special_groups", "period": "2026-10-01", "detected": "2026-10-30", "status": "avance"}])
        ev = releases.update_events(ev, manifest("2026-10-01", flash=True), manifest("2026-10-01"), "2026-11-13")
        self.assertEqual(ev[0]["status"], "definitivo")
        self.assertEqual(len(ev), 2)

    def test_no_change_no_event_and_idempotent(self):
        m = manifest("2026-09-01")
        self.assertEqual(releases.update_events([], m, m, "2026-10-30"), [])
        ev = releases.update_events([], manifest("2026-09-01"), manifest("2026-10-01"), "2026-10-30")
        again = releases.update_events(ev, manifest("2026-09-01"), manifest("2026-10-01"), "2026-10-30")
        self.assertEqual(ev, again)

    def test_no_baseline(self):
        self.assertEqual(releases.update_events([], None, manifest("2026-10-01"), "2026-10-30"), [])

    def test_old_events_pruned(self):
        old = [{"id": "ine.gdp", "period": "2024-01-01", "detected": "2024-05-01", "status": "nuevo"}]
        self.assertEqual(releases.update_events(old, None, manifest("2026-10-01"), "2026-10-30"), [])

    def test_today_madrid(self):
        from datetime import datetime, timezone
        self.assertEqual(releases.today_madrid(datetime(2026, 10, 30, 23, 30, tzinfo=timezone.utc)), "2026-10-31")


if __name__ == "__main__":
    unittest.main()
