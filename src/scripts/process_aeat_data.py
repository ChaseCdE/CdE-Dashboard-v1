"""
Process the Observatorio de Márgenes Empresariales (AEAT) quarterly series into data/processed/aeat/.

Input: data/raw/aeat/ome_quarterly.csv (src/fetchers/aeat_ome.py): levels in millions of euros,
original and CVEC (seasonally and calendar adjusted), population "homogénea corriente", all sizes.

Outputs (long format):
  ome_totals.csv     date, series, value, yoy, index_2019
      series: sales (A. Ventas totales), purchases (B. Compras totales), wages (C. Masa salarial),
      gross_result (S.2. Indicador de resultado bruto de explotación). CVEC data.
  ome_divisions.csv  date, sector, sector_label, value, yoy
      Sales (CVEC) by CNAE-2009 division (2 digits). The OME publishes trade (45, 46, 47) only by
      3-digit groups: their CVEC levels are added up here into the 2-digit division (indirect
      seasonal adjustment; the sum of the groups' original data equals the division's).
Rates are computed by calendar date (src/processors/series_ops.py), never by position.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.processors.series_ops import pct_change_by_date

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw" / "aeat" / "ome_quarterly.csv"
OUT = ROOT / "data" / "processed" / "aeat"

TOTAL_VARIABLES = {
    "A. Ventas totales": "sales",
    "B. Compras totales": "purchases",
    "C. Masa salarial": "wages",
    "S.2. Indicador de resultado bruto de explotación": "gross_result",
}
TRADE_LABELS = {
    "45": "Venta y reparación de vehículos de motor y motocicletas",
    "46": "Comercio al por mayor",
    "47": "Comercio al por menor",
}


def _date(period: pd.Series) -> pd.Series:
    """'2026-2T' -> 2026-04-01."""
    m = period.str.extract(r"^(\d{4})-([1-4])T$")
    if m.isna().any().any():
        raise ValueError(f"OME: unexpected period labels {period[m.isna().any(axis=1)].unique()[:5]}")
    return pd.to_datetime(dict(year=m[0].astype(int), month=(m[1].astype(int) - 1) * 3 + 1, day=1))


def _rates(df: pd.DataFrame, base_year: int | None = 2019) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df["yoy"] = pct_change_by_date(df, "value", 12)
    if base_year:
        base = df.loc[df["date"].dt.year == base_year, "value"]
        if len(base) != 4:
            raise ValueError(f"OME: {len(base)} quarters in the base year {base_year}")
        df["index_2019"] = df["value"] / base.mean() * 100
    return df


def load() -> pd.DataFrame:
    raw = pd.read_csv(RAW)
    raw = raw[raw["DATO2"].eq("CVEC")].copy()
    raw["date"] = _date(raw["PERIODO"])
    return raw


def process_totals(raw: pd.DataFrame) -> pd.DataFrame:
    tot = raw[raw["AGREGACION"].eq("Totales") & raw["LITERAL"].eq("Total")]
    parts = []
    for var, key in TOTAL_VARIABLES.items():
        s = tot[tot["VARIABLE"].eq(var)][["date", "VALOR"]].rename(columns={"VALOR": "value"}).dropna()
        if s["date"].duplicated().any():
            raise ValueError(f"OME totals: duplicated quarters for {var}")
        if len(s) < 40:
            raise ValueError(f"OME totals: only {len(s)} quarters for {var}")
        df = _rates(s)
        df.insert(1, "series", key)
        parts.append(df)
    out = pd.concat(parts, ignore_index=True)
    sales = out[out["series"].eq("sales")]["value"]
    # Plausibility: quarterly sales of non-financial companies, millions of euros.
    if not sales.between(200_000, 2_000_000).all():
        raise ValueError("OME totals: sales out of the plausible range; check the download format")
    out.to_csv(OUT / "ome_totals.csv", index=False)
    return out


def division_key(literal: str) -> tuple[str, str]:
    """('10', 'Industria de la alimentación') for 2-digit divisions or groupings of them;
    ('46', ...) for the 3-digit trade groups, to be added up; ('', '') otherwise."""
    code, _, label = literal.partition(" - ")
    code = code.strip()
    if re.fullmatch(r"\d{2}(\+\d{2})*", code):
        return code, label.strip()
    m = re.match(r"(4[5-7])\d", code)
    if m:
        return m.group(1), TRADE_LABELS[m.group(1)]
    return "", ""


def process_divisions(raw: pd.DataFrame) -> pd.DataFrame:
    div = raw[raw["AGREGACION"].eq("Divisiones y grupos") & raw["VARIABLE"].eq("A. Ventas totales")].copy()
    keys = div["LITERAL"].map(division_key)
    div["code"] = keys.str[0]
    div["label"] = keys.str[1]
    div = div[div["code"].ne("")]
    # Trade groups: add up; every group must be present in every quarter it is summed over.
    n_groups = div.groupby("code")["LITERAL"].nunique()
    agg = (div.groupby(["code", "label", "date"])
           .agg(value=("VALOR", "sum"), n=("VALOR", "count"), nn=("VALOR", lambda v: v.notna().sum()))
           .reset_index())
    agg = agg[agg["nn"].eq(agg["code"].map(n_groups))]
    parts = []
    for (code, label), g in agg.groupby(["code", "label"], sort=True):
        df = _rates(g[["date", "value"]], base_year=None)
        df.insert(1, "sector", "d" + code.replace("+", "_"))
        df.insert(2, "sector_label", f"{label} ({code.replace('+', ', ')})")
        parts.append(df)
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(OUT / "ome_divisions.csv", index=False)
    return out


def main():
    """Without a raw download (AEAT unreachable on a first run) nothing is written: the exporter
    keeps the previous site files."""
    OUT.mkdir(parents=True, exist_ok=True)
    if not RAW.exists():
        print(f"OME (AEAT): no raw download ({RAW}); skipped, previous site files kept")
        return
    raw = load()
    tot = process_totals(raw)
    div = process_divisions(raw)
    print("OME totals, latest quarter:")
    print(tot.sort_values("date").groupby("series").tail(1).to_string(index=False))
    last = div[div["date"].eq(div["date"].max())].sort_values("yoy")
    print(f"OME divisions: {div['sector'].nunique()}; latest quarter {div['date'].max():%Y-%m}")
    print(pd.concat([last.head(5), last.tail(5)])[["sector_label", "yoy"]].to_string(index=False))


if __name__ == "__main__":
    main()
