# Markets: official sources instead of Yahoo Finance (2026-10-29)

Why: Yahoo's terms forbid automated collection, building a database from its data and
redistribution ("You must not redistribute information displayed on or provided by Yahoo
Finance"). Everything that has a free, reusable official source was moved off Yahoo.

| Old (Yahoo) | New | Source | Notes |
|---|---|---|---|
| `yahoo.eur_usd/eur_gbp/eur_jpy/eur_chf` | `ecb.*` (same keys) | ECB euro reference rates, EXR `D.<CUR>.EUR.SP00.A` | Daily fixing ~16:00 CET, TARGET days, not a market close. ECB statistics are free to reuse with attribution. |
| `yahoo.gbp_usd`, `yahoo.usd_jpy` | `ecb.gbp_usd`, `ecb.usd_jpy` | Cross rates of the ECB reference rates | Computed in the pipeline (USD per GBP = USD/EUR ÷ GBP/EUR). |
| `yahoo.dxy` (ICE index, proprietary) | `fed.usd_broad_index` | Federal Reserve H.10, nominal broad dollar index (FRED DTWEXBGS) | Different index: broad, trade-weighted basket (Jan 2006 = 100), published weekly with daily values. |
| `yahoo.us_tbill_3m/us_treasury_5y/10y/30y` | `fed.*` (same keys) | Federal Reserve H.15 constant-maturity yields (FRED DGS3MO, DGS5, DGS10, DGS30) | The 3-month point is now a constant-maturity yield, not the 13-week bill discount rate (^IRX). |
| `yahoo.brent_crude`, `wti_crude`, `natural_gas` (futures) | `eia.*` (same keys) | EIA spot prices (FRED DCOILBRENTEU, DCOILWTICO, DHHNGSP) | Spot, not front-month futures. Published weekly with a lag of a few days: `stale_after_days = 14`. US government data, public domain. |
| `yahoo.euro_govt_bond_etf`, `us_treasury_20y_etf`, `us_treasury_7_10y_etf` | removed | | Never shown on the site. |

Still on Yahoo (no free official source): equity indices (IBEX 35, Euro Stoxx 50, STOXX 600,
S&P 500, Nasdaq, DAX, CAC 40, FTSE 100), VIX, the two ETFs, gold and silver. Pending decision.

Implementation: pipeline source `markets` (`fetch_markets_official` / `process_markets_official`),
export `src/export/markets_official.py`. Field keys are the Yahoo ones (`close`, `ret_*`, `chg_*`)
so the Markets page and its tables work unchanged; return windows are 5 and 21 observations,
1 calendar year and year to date, as before. Datasets are `optional` (previous file kept if a
download is missing). FRED drops requests whose User-Agent is not browser-compatible, so the
fetcher sends `Mozilla/5.0 (compatible; CdE-Dashboard/1.0; +<site url>)`.
