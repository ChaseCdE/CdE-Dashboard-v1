import unittest
from datetime import date

from src.export.calendar import classify, normalise_period
from src.fetchers.calendars import parse_ine_ics

ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;TZID=Europe/Madrid:20261030T090000
SUMMARY:Índice de Precios de Consumo. Avance. Octubre 2026
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=Europe/Madrid:20261030T090000
SUMMARY:Contabilidad Nacional Trimestral de España. Avance. Trimestre 3/20
 26
END:VEVENT
END:VCALENDAR
"""


class CalendarTest(unittest.TestCase):
    def test_ine_ics(self):
        ev = parse_ine_ics(ICS)
        self.assertEqual(ev[0]["title"], "Índice de Precios de Consumo")
        self.assertEqual((ev[0]["date"], ev[0]["time"], ev[0]["period"], ev[0]["flash"]),
                         ("2026-10-30", "09:00", "Octubre 2026", True))
        self.assertEqual(ev[1]["period"], "Trimestre 3/2026")  # folded line joined

    def test_periods(self):
        d = date(2026, 11, 4)
        self.assertEqual(normalise_period("Octubre 2026", d), ("octubre 2026", "2026-10-01"))
        self.assertEqual(normalise_period("October 2026", d), ("octubre 2026", "2026-10-01"))
        self.assertEqual(normalise_period("Trimestre 3/2026", d), ("T3 2026", "2026-07-01"))
        self.assertEqual(normalise_period("Q3/2026", d), ("T3 2026", "2026-07-01"))
        self.assertEqual(normalise_period("III-2025", d), ("T3 2025", "2025-07-01"))
        self.assertEqual(normalise_period("Nov/25", d), ("noviembre 2025", "2025-11-01"))
        self.assertEqual(normalise_period("oct", d), ("octubre 2026", "2026-10-01"))
        self.assertEqual(normalise_period("dic", date(2026, 1, 5)), ("diciembre 2025", "2025-12-01"))

    def test_classify(self):
        self.assertEqual(classify({"source": "INE", "title": "Índice de Precios de Consumo"})["page"], "pages/precios.html")
        self.assertEqual(classify({"source": "INE", "title": "Índice de Precios de Consumo. Medias anuales"}), {})
        self.assertTrue(classify({"source": "Ministerios de Trabajo e Inclusión", "title": "Paro registrado y contratos"}))


if __name__ == "__main__":
    unittest.main()


class CalendarValueSpecsTest(unittest.TestCase):
    def test_value_specs_exist_in_manifest(self):
        import json
        from pathlib import Path
        from src.export.calendar import RULES
        m = json.loads((Path(__file__).resolve().parents[1] / "site/data/manifest.json").read_text(encoding="utf-8"))
        ids = {d["id"]: d for d in m["datasets"]}
        for r in RULES:
            if r["value"]:
                ds, ser, fld = r["value"]
                self.assertIn(ds, ids, r["label"])
                self.assertIn(fld, ids[ds]["fields"], r["label"])
                self.assertTrue(any(s["key"] == ser for s in ids[ds]["series"]), r["label"])
