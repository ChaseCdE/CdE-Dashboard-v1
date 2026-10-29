"""
Process MIVAU appraised values and Registradores prices into data/processed/housing/.

Outputs (long format, one row per date and series):
  mivau_appraised_prices.csv     date, series, value (EUR/m2), yoy, qoq
  registradores_house_prices.csv date, series, value (EUR/m2), price_dwelling (EUR), yoy, qoq
Rates are computed by calendar date (src/processors/series_ops.py), never by position.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.processors.series_ops import pct_change_by_date

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw" / "housing"
OUT = ROOT / "data" / "processed" / "housing"


def _quarter_start(dates: pd.Series) -> pd.Series:
    return pd.to_datetime(dates).dt.to_period("Q").dt.start_time


def _add_rates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df["yoy"] = pct_change_by_date(df, "value", 12)
    df["qoq"] = pct_change_by_date(df, "value", 3)
    return df


def process_mivau() -> pd.DataFrame:
    parts = []
    for key in ("total", "new", "used"):
        raw = pd.read_csv(RAW / f"mivau_{key}.csv")
        df = pd.DataFrame({"date": _quarter_start(raw["date"]), "value": pd.to_numeric(raw["value"], errors="coerce")})
        df = _add_rates(df.dropna(subset=["value"]))
        df.insert(1, "series", key)
        parts.append(df)
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(OUT / "mivau_appraised_prices.csv", index=False)
    return out


def _num(s: pd.Series) -> pd.Series:
    """Spanish-formatted numbers in the Registradores CSV: decimal comma, no thousands separator."""
    return pd.to_numeric(s.astype(str).str.strip().str.replace(".", "", regex=False)
                         .str.replace(",", ".", regex=False), errors="coerce")


def process_registradores() -> pd.DataFrame:
    raw = pd.read_csv(RAW / "registradores_residential_sales.csv", dtype=str)
    nat = raw[raw["geo"].str.strip() == "Nacional"].copy()
    year = pd.to_numeric(nat["ano"], errors="coerce").astype(int)
    quarter = pd.to_numeric(nat["trim"], errors="coerce").astype(int)
    df = pd.DataFrame({
        "date": pd.to_datetime(dict(year=year, month=(quarter - 1) * 3 + 1, day=1)).values,
        "value": _num(nat["viv-pm2"]).values,
        "price_dwelling": _num(nat["viv-imp"]).values,
    }).dropna(subset=["value"])
    if df["date"].duplicated().any():
        raise ValueError("Registradores: duplicated national quarters")
    # Plausibility: national average price per m2 of housing in euros.
    if not df["value"].between(500, 10000).all():
        raise ValueError("Registradores: price per m2 out of the plausible range; check the CSV format")
    df = _add_rates(df)
    df.insert(1, "series", "es")
    df.to_csv(OUT / "registradores_house_prices.csv", index=False)
    return df


def main():
    """Each source is processed independently. A source without a raw download (first run in a
    fresh cache, portal unreachable) is skipped: the exporter then keeps its previous site file."""
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("MIVAU", process_mivau), ("Registradores", process_registradores)):
        try:
            df = fn()
        except FileNotFoundError as e:
            print(f"{name}: no raw download ({e.filename}); skipped, previous site file kept")
            continue
        last = df.sort_values("date").groupby("series").tail(1)
        print(f"{name}:")
        print(last.to_string(index=False))


if __name__ == "__main__":
    main()
