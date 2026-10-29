"""
Housing price sources beyond INE: MIVAU appraised values and Registradores prices.

- MIVAU (Ministerio de Vivienda y Agenda Urbana), "Valor tasado de la vivienda": average
  appraised value of free-market housing in EUR per m2, quarterly. Downloaded from the
  Banco de España API, which republishes it in its housing-market indicators (BE si_1_5),
  because the ministry offers no stable machine-readable endpoint.
- Colegio de Registradores, open-data portal (CKAN): residential sales by province with the
  average price per m2 and per dwelling, quarterly. The CSV file name changes every quarter,
  so its URL is looked up in the dataset metadata (package_show) on each run. The portal sits
  behind a web firewall that rejects non-browser clients, hence the browser User-Agent.

On any failure the previous raw file is kept and a warning is logged; run_pipeline.py turns
those warnings into a "not refreshed" report (audit H1).
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd

from .bde_client import BdeClient
from .http_session import make_session

logger = logging.getLogger(__name__)

MIVAU_SERIES = {
    "total": "DHIVTNOAPLPMMUVT_RLI.T",
    "new": "DHIVTNOAPLPMMUVT_VVN_RLI.T",   # up to 5 years old
    "used": "DHIVTNOAPLPMMUVT_VVU_RLI.T",  # more than 5 years old
}

REGISTRADORES_API = "https://opendata.registradores.org/dataset/api/3/action/package_show"
REGISTRADORES_DATASET = "compraventas-de-inmuebles-uso-residencial-por-provincia"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
REGISTRADORES_COLUMNS = {"ano", "trim", "geo", "viv-num", "viv-imp", "viv-pm2"}


class HousingFetcher:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ MIVAU
    def fetch_mivau(self) -> int:
        """Download the three MIVAU series via the BdE API. Returns the number saved."""
        saved = 0
        with BdeClient(language="ES") as client:
            data = client.get_series(list(MIVAU_SERIES.values()), "MAX")
            by_code = {d.get("serie"): d for d in (data or [])}
            for key, code in MIVAU_SERIES.items():
                df = client.series_to_dataframe(by_code.get(code, {}))
                if df.empty or df["value"].notna().sum() < 8:
                    logger.warning(f"MIVAU {key} ({code}): no data returned, keeping the previous download")
                    continue
                df[["date", "value", "series_code"]].to_csv(self.output_dir / f"mivau_{key}.csv", index=False)
                saved += 1
        return saved

    # ----------------------------------------------------------- Registradores
    def fetch_registradores(self) -> bool:
        """Download the residential sales CSV of the Colegio de Registradores."""
        session = make_session(user_agent=BROWSER_UA, headers={"Accept": "application/json, text/csv, */*"})
        try:
            meta = session.get(REGISTRADORES_API, params={"id": REGISTRADORES_DATASET})
            meta.raise_for_status()
            resources = meta.json()["result"]["resources"]
            url = next(r["url"] for r in resources if str(r.get("format", "")).upper() == "CSV")
            resp = session.get(url)
            resp.raise_for_status()
            text = resp.content.decode("utf-8-sig")
            df = pd.read_csv(io.StringIO(text), sep=";", dtype=str)
        except Exception as e:  # network, firewall page, JSON or CSV shape
            logger.warning(f"Registradores fetch failed ({type(e).__name__}: {e}); keeping the previous download")
            return False
        df.columns = [c.strip() for c in df.columns]
        missing = REGISTRADORES_COLUMNS - set(df.columns)
        if missing or (df["geo"] == "Nacional").sum() < 8:
            logger.warning(f"Registradores CSV has an unexpected shape (missing {sorted(missing)}); keeping the previous download")
            return False
        df.to_csv(self.output_dir / "registradores_residential_sales.csv", index=False)
        logger.info(f"Registradores: {len(df)} rows from {url}")
        return True

    def fetch_all(self) -> dict:
        return {"mivau": self.fetch_mivau(), "registradores": self.fetch_registradores()}
