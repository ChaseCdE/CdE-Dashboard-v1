"""
EPA seasonally adjusted employment (INE).

INE publishes the seasonally adjusted EPA levels (employment and unemployment, thousands of
persons) only as a spreadsheet linked from each quarterly EPA press release, not as series in
its Tempus API:

    https://www.ine.es/daco/daco42/daco4211/epa_desestacional.xlsx
    ("Series desestacionalizadas EPA. Totales (miles de personas)": Periodo | Ocupación | Paro)

The dashboard publishes the seasonally adjusted employment level (seasonal-adjustment rule:
use the adjusted variant whenever the official source publishes one). The workbook is read with
the standard library (an .xlsx is a zip of XML files), so no spreadsheet dependency is needed.

Failure semantics are those of the Tempus fetcher: if the download fails or the workbook no
longer has the expected title, header or periods, a SpreadsheetError is raised, the caller logs
"... failed ..." (exit code 3 in run_pipeline.py) and the previous raw file is kept.
"""

from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

EPA_SA_URL = "https://www.ine.es/daco/daco42/daco4211/epa_desestacional.xlsx"
EPA_SA_FILE = "employed_sa_raw.csv"
EPA_SA_CODE = "EPA_DESEST_OCUPACION"
EPA_SA_NAME = "Series desestacionalizadas EPA. Totales (miles de personas). Ocupación"
EPA_SA_NULT = 40  # quarters published, the same window as the other EPA series (nult=40 in ine_series.py)

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_PERIOD = re.compile(r"^T([1-4])-(\d{4})$")


class SpreadsheetError(Exception):
    """The EPA workbook is missing, unreadable or not laid out as expected."""


def _cells(z: zipfile.ZipFile, sheet: str, strings: list) -> dict:
    """{(row, column letters): text} of one worksheet."""
    out = {}
    root = ET.fromstring(z.read(sheet))
    for c in root.iter(f"{{{_NS['m']}}}c"):
        v = c.find("m:v", _NS)
        if v is None or v.text is None:
            continue
        ref = c.get("r")
        m = re.match(r"([A-Z]+)(\d+)$", ref)
        text = strings[int(v.text)] if c.get("t") == "s" else v.text
        out[(int(m.group(2)), m.group(1))] = text.strip()
    return out


def parse_epa_sa(content: bytes) -> pd.DataFrame:
    """Seasonally adjusted EPA employment (thousands) as date, year, value, series_code, series_name."""
    try:
        z = zipfile.ZipFile(io.BytesIO(content))
        sroot = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise SpreadsheetError(f"EPA workbook unreadable: {exc}") from exc
    strings = ["".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")) for si in sroot.findall("m:si", _NS)]
    sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    for sheet in sheets:
        cells = _cells(z, sheet, strings)
        texts = {k: v for k, v in cells.items() if k[1] == "A"}
        if not any("Series desestacionalizadas EPA" in v for v in texts.values()):
            continue
        if not any(v.startswith("Totales (miles de personas)") for v in texts.values()):
            continue
        header = next((r for (r, col), v in cells.items() if col == "A" and v == "Periodo"), None)
        if header is None:
            raise SpreadsheetError(f"{sheet}: no 'Periodo' header")
        col = next((c for (r, c), v in cells.items() if r == header and v == "Ocupación"), None)
        if col is None:
            raise SpreadsheetError(f"{sheet}: no 'Ocupación' column in the header row")
        rows = []
        for (r, c), v in cells.items():
            if c != "A" or r <= header:
                continue
            m = _PERIOD.match(v)
            if not m:
                continue
            raw = cells.get((r, col))
            if raw in (None, ""):
                continue
            q, y = int(m.group(1)), int(m.group(2))
            rows.append({"date": pd.Timestamp(year=y, month=3 * (q - 1) + 1, day=1), "year": y,
                         "value": round(float(raw), 4), "series_code": EPA_SA_CODE, "series_name": EPA_SA_NAME})
        if len(rows) < 40:
            raise SpreadsheetError(f"{sheet}: only {len(rows)} quarters of seasonally adjusted employment")
        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        if df["date"].duplicated().any():
            raise SpreadsheetError(f"{sheet}: duplicated periods")
        return df
    raise SpreadsheetError("no sheet titled 'Series desestacionalizadas EPA' / 'Totales (miles de personas)'")


def fetch_epa_sa(session) -> pd.DataFrame:
    """Download and parse the workbook with a requests-like session."""
    resp = session.get(EPA_SA_URL)
    resp.raise_for_status()
    return parse_epa_sa(resp.content)
