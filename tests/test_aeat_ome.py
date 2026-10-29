import io
import unittest

import pandas as pd

from src.fetchers import aeat_ome

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


    def test_parse_workbook_adds_totals(self):
        rows = []
        for code in ("10", "4671"):
            for kind, v in (("Original", 1.0), ("CVEC", 2.0)):
                rows.append(["2026", "20262T", code, "Sección C", "Modelos periódicos", "A. Ventas totales", kind, v])
        bdd = pd.DataFrame(rows, columns=["AÑO", "PERIODO", "CNAE_agrupación", "CNAE_sección", "Origen",
                                          "VARIABLE", "Original / CVEC", "Importe"])
        lit = pd.DataFrame({"CNAE_agrupación": ["10", "4671"], "Literal": ["Alimentación", "Combustibles"]})
        buf = io.BytesIO()
        with pd.ExcelWriter(buf) as xw:
            bdd.to_excel(xw, sheet_name="BdD", index=False)
            lit.to_excel(xw, sheet_name="literales actividades", index=False)
        old = aeat_ome.N_GROUPS
        aeat_ome.N_GROUPS = 2
        try:
            df = aeat_ome.parse_workbook(buf.getvalue())
        finally:
            aeat_ome.N_GROUPS = old
        tot = df[df["AGREGACION"].eq("Totales")].set_index("DATO2")["VALOR"]
        self.assertEqual(tot["Original"], 2.0)
        self.assertEqual(tot["CVEC"], 4.0)
        self.assertIn("4671 - Combustibles", set(df["LITERAL"]))
        self.assertEqual(set(df["PERIODO"]), {"2026-2T"})


if __name__ == "__main__":
    unittest.main()
