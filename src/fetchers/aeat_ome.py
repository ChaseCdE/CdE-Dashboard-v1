"""
Observatorio de Márgenes Empresariales (OME), Agencia Tributaria: quarterly series built from
the VAT (modelos 303/322) and withholding (modelo 111) returns of private non-financial companies.

Source file: "2.1 Datos trimestrales (Población homogénea corriente)", a static Excel file on the
AEAT statistics page (link below). Its sheet "BdD" is a long table:
  AÑO, PERIODO (20262T), CNAE_agrupación (10, 41+42+43, 467 (sin 4671)...), CNAE_sección, Origen,
  VARIABLE (A. Ventas totales...), Original / CVEC, Importe (millions of euros)
and the sheet "literales actividades" holds the activity labels.

The file has no national total: it is the sum of the 73 activity groups, for original and CVEC
data alike (the AEAT adjusts the groups and adds them up; checked against the OME web application,
e.g. sales CVEC 2026-2T 695,146.23 M EUR in both). The fetcher adds those totals.

Output: data/raw/aeat/ome_quarterly.csv with columns
  PERIODO (2026-2T), VARIABLE, AGREGACION (Totales | Divisiones y grupos), LITERAL ("code - label"
  or "Total"), DATO2 (Original | CVEC), VALOR
On any failure the previous file is kept and a warning is logged, as for the other sources.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd

from .http_session import make_session

logger = logging.getLogger(__name__)

PAGE_URL = ("https://sede.agenciatributaria.gob.es/Sede/estadisticas/observatorio-margenes-empresariales/"
            "observatorio-margenes-empresariales.html")
XLSX_URL = ("https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/Estadisticas/"
            "Observatorio_margenes_empresariales/Datos_margenes_empresariales/Datos_trimestrales.xlsx")
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

VARIABLES = {
    "A. Ventas totales",
    "B. Compras totales",
    "C. Masa salarial",
    "S.2. Indicador de resultado bruto de explotación",
}
DATA_COLUMNS = ["PERIODO", "CNAE_agrupación", "VARIABLE", "Original / CVEC", "Importe"]
N_GROUPS = 73  # activity groups in the file (2026); a different count means the layout changed


def parse_workbook(content: bytes) -> pd.DataFrame:
    """Turn the Excel file into the long raw table, with national totals added."""
    book = pd.read_excel(io.BytesIO(content), sheet_name=["BdD", "literales actividades"], dtype=str)
    data, labels = book["BdD"], book["literales actividades"]
    missing = set(DATA_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"OME Excel: unexpected columns, missing {sorted(missing)}")
    data = data[data["VARIABLE"].isin(VARIABLES)].copy()
    data["Importe"] = pd.to_numeric(data["Importe"], errors="coerce")
    period = data["PERIODO"].str.extract(r"^(\d{4})([1-4])T$")
    if period.isna().any().any():
        raise ValueError("OME Excel: unexpected PERIODO labels")
    data["PERIODO"] = period[0] + "-" + period[1] + "T"

    labels = labels.dropna(axis=1, how="all")  # the sheet starts in column B
    if "CNAE_agrupación" not in labels.columns or "Literal" not in labels.columns:
        raise ValueError("OME Excel: unexpected layout of the 'literales actividades' sheet")
    code_label = dict(zip(labels["CNAE_agrupación"].astype(str).str.strip(), labels["Literal"].astype(str).str.strip()))
    if any(not v or v == "nan" for v in code_label.values()):
        raise ValueError("OME Excel: activity groups without a label")
    data["code"] = data["CNAE_agrupación"].astype(str).str.strip()
    n = data["code"].nunique()
    if n != N_GROUPS:
        raise ValueError(f"OME Excel: {n} activity groups instead of {N_GROUPS}; check the file layout")
    groups = pd.DataFrame({
        "PERIODO": data["PERIODO"], "VARIABLE": data["VARIABLE"], "AGREGACION": "Divisiones y grupos",
        "LITERAL": data["code"] + " - " + data["code"].map(code_label).fillna(""),
        "DATO2": data["Original / CVEC"], "VALOR": data["Importe"],
    })
    # National totals: sum of the groups; only quarters with every group reported.
    tot = (groups.groupby(["PERIODO", "VARIABLE", "DATO2"])["VALOR"]
           .agg(["sum", "count"]).reset_index())
    tot = tot[tot["count"].eq(N_GROUPS)]
    totals = pd.DataFrame({
        "PERIODO": tot["PERIODO"], "VARIABLE": tot["VARIABLE"], "AGREGACION": "Totales",
        "LITERAL": "Total", "DATO2": tot["DATO2"], "VALOR": tot["sum"],
    })
    return pd.concat([totals, groups], ignore_index=True)


class OmeFetcher:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self) -> bool:
        out = self.output_dir / "ome_quarterly.csv"
        try:
            session = make_session(user_agent=BROWSER_UA, headers={"Referer": PAGE_URL})
            resp = session.get(XLSX_URL, timeout=120)
            resp.raise_for_status()
            df = parse_workbook(resp.content)
        except Exception as e:  # network, web firewall, layout change
            logger.warning(f"OME (AEAT): download failed, keeping the previous file: {e}")
            return False
        sales = df[df["AGREGACION"].eq("Totales") & df["VARIABLE"].eq("A. Ventas totales")]
        if sales["VALOR"].notna().sum() < 100:
            logger.warning("OME (AEAT): the file has no national sales series, keeping the previous file")
            return False
        df.to_csv(out, index=False)
        logger.info(f"OME (AEAT): {len(df)} rows saved to {out} (latest quarter {df['PERIODO'].max()})")
        return True


if __name__ == "__main__":  # manual run: python -m src.fetchers.aeat_ome [output_dir]
    import sys

    logging.basicConfig(level=logging.INFO)
    ok = OmeFetcher(sys.argv[1] if len(sys.argv) > 1 else "data/raw/aeat").fetch()
    sys.exit(0 if ok else 1)
