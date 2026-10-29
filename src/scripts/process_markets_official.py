"""
Process ECB and FRED market series into data/processed/markets_official/<key>.csv.

Same derived columns as the Yahoo processor (returns over 1 day, 5 and 21 observations,
1 calendar year and year to date; absolute changes for yields; 200-observation SMA), so the
exported fields and the Markets page work unchanged. Cross rates GBP/USD and USD/JPY are
derived from the ECB euro reference rates (USD per GBP = USD per EUR / GBP per EUR).
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.processors.yahoo_processor import YahooProcessor

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw" / "markets_official"
OUT = ROOT / "data" / "processed" / "markets_official"

ECB = {"eur_usd": "ecb_usd", "eur_gbp": "ecb_gbp", "eur_jpy": "ecb_jpy", "eur_chf": "ecb_chf"}
FRED = ["us_tbill_3m", "us_treasury_5y", "us_treasury_10y", "us_treasury_30y",
        "usd_broad_index", "brent_crude", "wti_crude", "natural_gas"]


def _load(name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / f"{name}.csv", parse_dates=["date"])
    return df.dropna(subset=["value"]).drop_duplicates("date").sort_values("date").reset_index(drop=True)


def _process(df: pd.DataFrame, key: str, proc: YahooProcessor) -> None:
    out = proc.process_price_data(df.rename(columns={"value": "Close"}), key, key)
    out.to_csv(OUT / f"{key}.csv", index=False)
    last = out.dropna(subset=["Close"]).iloc[-1]
    print(f"  {key:<18} {len(out):>5} rows  last {last['date']:%Y-%m-%d} = {last['Close']:.4f}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    proc = YahooProcessor()
    frames = {}
    for key, raw in ECB.items():
        try:
            frames[key] = _load(raw)
            _process(frames[key], key, proc)
        except FileNotFoundError:
            print(f"  {key}: no raw download; skipped (previous site file kept)")
    # Cross rates from the euro reference rates, on dates where both exist.
    for key, num, den in (("gbp_usd", "eur_usd", "eur_gbp"), ("usd_jpy", "eur_jpy", "eur_usd")):
        if num in frames and den in frames:
            m = frames[num].merge(frames[den], on="date", suffixes=("_n", "_d"))
            _process(pd.DataFrame({"date": m["date"], "value": m["value_n"] / m["value_d"]}), key, proc)
    for key in FRED:
        try:
            _process(_load(f"fred_{key}"), key, proc)
        except FileNotFoundError:
            print(f"  {key}: no raw download; skipped (previous site file kept)")


if __name__ == "__main__":
    main()
