"""
Market series from official, freely reusable sources (replacing Yahoo Finance where one exists).

- ECB euro foreign exchange reference rates (data-api.ecb.europa.eu, dataset EXR): USD, GBP,
  JPY and CHF per euro. Daily, TARGET business days, published around 16:00 CET.
- FRED (Federal Reserve Bank of St. Louis) as the delivery channel for US public-domain series:
  Treasury constant-maturity yields (Federal Reserve H.15), the nominal broad dollar index
  (Federal Reserve H.10) and EIA spot prices for Brent, WTI and Henry Hub natural gas.
  fredgraph.csv needs no API key.

Equity indices, VIX, ETFs, gold and silver have no free official source and stay on Yahoo.
On any failure the previous raw file is kept and a warning is logged (audit H1).
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd

from .http_session import make_session

logger = logging.getLogger(__name__)

START = "2015-01-01"  # ten years of history plus the year-end base for year-to-date changes
ECB_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.{cur}.EUR.SP00.A"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

ECB_CURRENCIES = ["USD", "GBP", "JPY", "CHF"]
FRED_SERIES = {
    "DGS3MO": "us_tbill_3m",
    "DGS5": "us_treasury_5y",
    "DGS10": "us_treasury_10y",
    "DGS30": "us_treasury_30y",
    "DTWEXBGS": "usd_broad_index",
    "DCOILBRENTEU": "brent_crude",
    "DCOILWTICO": "wti_crude",
    "DHHNGSP": "natural_gas",
}


class OfficialMarketsFetcher:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # FRED drops requests whose User-Agent does not look like a browser-compatible client.
        self.session = make_session(
            user_agent="Mozilla/5.0 (compatible; CdE-Dashboard/1.0; +https://chasecde.github.io/CdE-Dashboard-v1/)",
            headers={"Accept": "text/csv, */*"}, timeout=(10, 30))

    def _save(self, df: pd.DataFrame, name: str, label: str) -> bool:
        df = df.dropna(subset=["value"])
        if len(df) < 250:
            logger.warning(f"{label}: no data or too few observations ({len(df)}); keeping the previous download")
            return False
        df.to_csv(self.output_dir / f"{name}.csv", index=False)
        return True

    def fetch_ecb(self) -> int:
        saved = 0
        for cur in ECB_CURRENCIES:
            try:
                r = self.session.get(ECB_URL.format(cur=cur), params={"startPeriod": START, "format": "csvdata"})
                r.raise_for_status()
                raw = pd.read_csv(io.StringIO(r.text))
                df = pd.DataFrame({"date": raw["TIME_PERIOD"], "value": pd.to_numeric(raw["OBS_VALUE"], errors="coerce")})
            except Exception as e:
                logger.warning(f"ECB {cur}: request failed ({type(e).__name__}: {e}); keeping the previous download")
                continue
            saved += self._save(df, f"ecb_{cur.lower()}", f"ECB {cur}")
        return saved

    def fetch_fred(self) -> int:
        saved = 0
        for code, name in FRED_SERIES.items():
            try:
                r = self.session.get(FRED_URL, params={"id": code, "cosd": START})
                r.raise_for_status()
                raw = pd.read_csv(io.StringIO(r.text))
                if code not in raw.columns:
                    raise ValueError(f"column {code} missing")
                df = pd.DataFrame({"date": raw.iloc[:, 0], "value": pd.to_numeric(raw[code], errors="coerce")})
                df = df[df["date"] >= START]
            except Exception as e:
                logger.warning(f"FRED {code}: request failed ({type(e).__name__}: {e}); keeping the previous download")
                continue
            saved += self._save(df, f"fred_{name}", f"FRED {code}")
        return saved

    def fetch_all(self) -> dict:
        return {"ecb": self.fetch_ecb(), "fred": self.fetch_fred()}
