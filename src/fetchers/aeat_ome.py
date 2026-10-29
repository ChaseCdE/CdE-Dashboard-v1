"""
Observatorio de Márgenes Empresariales (OME), Agencia Tributaria: quarterly series built from
the VAT (modelos 303/322) and withholding (modelo 111) returns of non-financial companies.

The AEAT publishes the series only through a Shiny web application
(https://www2.agenciatributaria.gob.es/sete-ome/): its "Descargas" tab serves the whole quarterly
database (about 225 MB of CSV) through a per-session download link, so there is no stable URL to
request. The fetcher therefore drives the application with a headless browser (Playwright),
selects "Series trimestrales", downloads the CSV inside that browser session and keeps only the
rows the dashboard uses:

  population   Homogénea corriente   (each year's declarants)
  colectivo    Total                 (all company sizes)
  aggregation  Totales, Divisiones y grupos (CNAE-2009 divisions; 3 digits for trade)
  variables    A. Ventas totales, B. Compras totales, C. Masa salarial,
               S.2. Indicador de resultado bruto de explotación
  measure      Nivel (millones de euros), Original and CVEC

Output: data/raw/aeat/ome_quarterly.csv (a few hundred KB). On any failure the previous file is
kept and a warning is logged, as for the other non-API sources.

Requires:  pip install playwright  &&  python -m playwright install chromium
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

APP_URL = "https://www2.agenciatributaria.gob.es/sete-ome/"
DOWNLOAD_TAB = "ome_descargas"
DATASET_INPUT = "ome_descargas-datasetDescarga"
DOWNLOAD_LINK = "#ome_descargas-downloadData"
PREVIEW = "#ome_descargas-vista_previa_descarga"

KEEP = {
    "POBLACION": {"Homogénea corriente"},
    "COLECTIVO": {"Total"},
    "AGREGACION": {"Totales", "Divisiones y grupos"},
    "VARIABLE": {
        "A. Ventas totales",
        "B. Compras totales",
        "C. Masa salarial",
        "S.2. Indicador de resultado bruto de explotación",
    },
    "DATO1": {"Nivel"},
    "DATO2": {"Original", "CVEC"},
}
COLUMNS = ["POBLACION", "COLECTIVO", "FREC", "PERIODO", "ORIGEN", "VARIABLE",
           "AGREGACION", "LITERAL", "DATO1", "DATO2", "VALOR"]


def download_quarterly_csv(dest: Path, timeout_s: int = 300) -> Path:
    """Drive the Shiny app and save the full quarterly CSV to `dest`."""
    from playwright.sync_api import sync_playwright  # imported lazily: optional dependency

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(accept_downloads=True, locale="es-ES")
            page = ctx.new_page()
            page.goto(APP_URL, wait_until="networkidle", timeout=timeout_s * 1000)
            page.wait_for_function("window.Shiny && Shiny.shinyapp && Shiny.shinyapp.isConnected()",
                                   timeout=timeout_s * 1000)
            page.click(f'a[data-value="{DOWNLOAD_TAB}"]')
            # Wait for the tab's preview table (a random sample of the selected database) to render:
            # a click on the radio before that does not reach the server. Then select "Series
            # trimestrales" and wait for the preview to be redrawn from the new database.
            preview = f"document.querySelector('{PREVIEW}')"
            page.wait_for_function(f"{preview} && {preview}.innerText.trim().length > 50", timeout=timeout_s * 1000)
            before = page.evaluate(f"{preview}.innerText")
            page.click(f'input[name="{DATASET_INPUT}"][value="trimestral"]')
            page.wait_for_function(f"{preview}.innerText !== {before!r}", timeout=timeout_s * 1000)
            page.wait_for_timeout(1000)
            with page.expect_download(timeout=timeout_s * 1000) as dl:
                page.click(DOWNLOAD_LINK)
            dl.value.save_as(str(dest))
        finally:
            browser.close()
    return dest


def filter_rows(csv_path: Path) -> pd.DataFrame:
    """Keep the dashboard rows of the full download (read in chunks to bound memory)."""
    parts = []
    for chunk in pd.read_csv(csv_path, sep=";", dtype=str, chunksize=200_000, encoding="utf-8-sig"):
        missing = set(COLUMNS) - set(chunk.columns)
        if missing:
            raise ValueError(f"OME download: unexpected columns, missing {sorted(missing)}")
        m = pd.Series(True, index=chunk.index)
        for col, allowed in KEEP.items():
            m &= chunk[col].isin(allowed)
        m &= chunk["FREC"].eq("trimestral")
        parts.append(chunk.loc[m, ["PERIODO", "VARIABLE", "AGREGACION", "LITERAL", "DATO2", "VALOR"]])
    df = pd.concat(parts, ignore_index=True)
    df["VALOR"] = pd.to_numeric(df["VALOR"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                                errors="coerce")
    return df


class OmeFetcher:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, max_age_days: float = 7) -> bool:
        """Download unless the previous file is recent: the OME is updated once a quarter and the
        full download is large, so the daily pipeline asks the AEAT at most once a week."""
        out = self.output_dir / "ome_quarterly.csv"
        if out.exists() and (time.time() - out.stat().st_mtime) < max_age_days * 86400:
            logger.info(f"OME (AEAT): download from the last {max_age_days:g} days kept ({out})")
            return True
        try:
            with tempfile.TemporaryDirectory() as tmp:
                full = download_quarterly_csv(Path(tmp) / "ome_trimestral.csv")
                df = filter_rows(full)
        except Exception as e:  # network, firewall, app layout change, missing Playwright
            logger.warning(f"OME (AEAT): download failed, keeping the previous file: {e}")
            return False
        totals = df[df["AGREGACION"].eq("Totales") & df["VARIABLE"].eq("A. Ventas totales")]
        if totals["VALOR"].notna().sum() < 100:
            # e.g. the app served another database (the radio selection did not reach the server)
            logger.warning("OME (AEAT): the download has no national sales series, keeping the previous file")
            return False
        df.to_csv(out, index=False)
        logger.info(f"OME (AEAT): {len(df)} rows saved to {out} (latest quarter {df['PERIODO'].max()})")
        return True


if __name__ == "__main__":  # manual run: python -m src.fetchers.aeat_ome [output_dir]
    import sys

    logging.basicConfig(level=logging.INFO)
    ok = OmeFetcher(sys.argv[1] if len(sys.argv) > 1 else "data/raw/aeat").fetch(max_age_days=0)
    sys.exit(0 if ok else 1)
