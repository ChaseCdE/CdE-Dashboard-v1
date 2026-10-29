"""Parser of INE's seasonally adjusted EPA workbook (src/fetchers/ine_epa_sa.py)."""

import io
import unittest
import zipfile

from src.fetchers.ine_epa_sa import EPA_SA_CODE, SpreadsheetError, parse_epa_sa

_NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'


def _workbook(title="Series desestacionalizadas EPA", subtitle="Totales (miles de personas)",
              header=("Periodo", "Ocupación", "Paro"), quarters=48) -> bytes:
    strings = [title, subtitle, *header]
    rows = [f'<row r="4"><c r="A4" t="s"><v>0</v></c></row>', f'<row r="5"><c r="A5" t="s"><v>1</v></c></row>',
            '<row r="6"><c r="A6" t="s"><v>2</v></c><c r="C6" t="s"><v>3</v></c><c r="E6" t="s"><v>4</v></c></row>']
    for i in range(quarters):
        y, q = 2010 + i // 4, i % 4 + 1
        strings.append(f"T{q}-{y}")
        r = 7 + i
        rows.append(f'<row r="{r}"><c r="A{r}" t="s"><v>{len(strings) - 1}</v></c>'
                    f'<c r="C{r}"><v>{18000 + i}.5</v></c><c r="E{r}"><v>{3000 - i}</v></c></row>')
    sst = "".join(f"<si><t>{s}</t></si>" for s in strings)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", f"<sst {_NS}>{sst}</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {_NS}><sheetData>{"".join(rows)}</sheetData></worksheet>')
    return buf.getvalue()


class ParseEpaSa(unittest.TestCase):
    def test_reads_employment_column_by_header(self):
        df = parse_epa_sa(_workbook())
        self.assertEqual(len(df), 48)
        self.assertEqual(str(df["date"].iloc[0].date()), "2010-01-01")
        self.assertEqual(str(df["date"].iloc[-1].date()), "2021-10-01")
        self.assertEqual(df["value"].iloc[-1], 18047.5)  # Ocupación, not Paro
        self.assertTrue((df["series_code"] == EPA_SA_CODE).all())

    def test_wrong_title_fails(self):
        with self.assertRaises(SpreadsheetError):
            parse_epa_sa(_workbook(title="Series originales EPA"))

    def test_missing_column_fails(self):
        with self.assertRaises(SpreadsheetError):
            parse_epa_sa(_workbook(header=("Periodo", "Activos", "Paro")))

    def test_too_short_fails(self):
        with self.assertRaises(SpreadsheetError):
            parse_epa_sa(_workbook(quarters=8))

    def test_not_a_workbook_fails(self):
        with self.assertRaises(SpreadsheetError):
            parse_epa_sa(b"<html>not found</html>")


if __name__ == "__main__":
    unittest.main()
