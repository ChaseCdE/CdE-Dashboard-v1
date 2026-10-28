# ws/yahoo notes

## 1. Date fix

`yahoo_client.py` converted yfinance's tz-aware timestamps (exchange-local midnight, e.g. `00:00+02:00` for Madrid) to UTC before taking the date, so every European series was dated one day early (Monday sessions appeared as Sunday). Now the timezone is dropped without conversion (`tz_localize(None)`), which keeps the exchange's local calendar date. All raw files were refetched and all processed outputs (including `stock_indices_comparison`, `commodities_comparison`, `correlation_matrix`, `market_summary`) recomputed by `run_pipeline.py --sources yahoo`.

Spot check: IBEX 35 close on 2026-10-27 is 19160.6 in the CSV and in a direct yfinance call (`2026-10-27 00:00:00+01:00`, 19160.60). 2026-10-23: 18989.8 on both.

Rows by weekday (Mon..Sun) BEFORE:

```
ticker                      rows  Mon Tue Wed Thu Fri Sat Sun  last
brent_crude                 1256  234 260 257 252 253   0   0  2026-10-27
cac_40                      1279  260 257 256 254   0   0 252  2026-10-26
dax                         1273  258 255 256 252   0   0 252  2026-10-26
dxy                         1255  235 260 257 251 252   0   0  2026-10-27
eur_chf                     1298  261 261 259 258 108   0 151  2026-10-27
eur_gbp                     1298  261 261 259 258 108   0 151  2026-10-27
eur_jpy                     1298  261 261 259 258 108   0 151  2026-10-27
eur_usd                     1298  261 261 259 258 108   0 151  2026-10-27
euro_stoxx_50               1255  256 255 249 250   0   0 245  2026-10-26
european_banks_etf          1253  234 260 257 250 252   0   0  2026-10-27
fed_funds                   1253  234 260 257 250 252   0   0  2026-10-27
ftse_100                    1260  255 258 257 253 106   0 131  2026-10-27
gbp_usd                     1298  261 261 259 258 108   0 151  2026-10-27
gold                        1256  234 260 257 252 253   0   0  2026-10-27
ibex_35                     1277  260 257 256 252   0   0 252  2026-10-26
nasdaq_composite            1253  234 260 257 250 252   0   0  2026-10-27
natural_gas                 1256  234 260 257 252 253   0   0  2026-10-27
silver                      1255  234 260 257 251 253   0   0  2026-10-27
sp_500                      1253  234 260 257 250 252   0   0  2026-10-27
spanish_banks_etf           1253  234 260 257 250 252   0   0  2026-10-27
stoxx_600                   1255  256 255 249 250   0   0 245  2026-10-26
us_treasury_10y             1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_20y_etf         1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_30y             1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_5y              1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_7_10y_etf       1253  234 260 257 250 252   0   0  2026-10-27
usd_jpy                     1298  261 261 259 258 108   0 151  2026-10-27
vix                         1255  236 260 257 250 252   0   0  2026-10-27
wti_crude                   1255  234 260 257 251 253   0   0  2026-10-27
```

AFTER (no ticker has Saturday or Sunday rows; FX has none either, Yahoo FX daily bars are Monday to Friday once the local date is kept, so no Sunday-evening quote handling was needed):

```
ticker                      rows  Mon Tue Wed Thu Fri Sat Sun  last
brent_crude                 1256  234 260 257 252 253   0   0  2026-10-27
cac_40                      1279  252 260 257 256 254   0   0  2026-10-27
dax                         1273  252 258 255 256 252   0   0  2026-10-27
dxy                         1255  235 260 257 251 252   0   0  2026-10-27
eur_chf                     1298  260 261 259 258 260   0   0  2026-10-27
eur_gbp                     1298  260 261 259 258 260   0   0  2026-10-27
eur_jpy                     1298  260 261 259 258 260   0   0  2026-10-27
eur_usd                     1298  260 261 259 258 260   0   0  2026-10-27
euro_govt_bond_etf          1273  252 258 255 256 252   0   0  2026-10-27
euro_stoxx_50               1255  245 256 255 249 250   0   0  2026-10-27
european_banks_etf          1253  234 260 257 250 252   0   0  2026-10-27
ftse_100                    1260  234 258 258 256 254   0   0  2026-10-27
gbp_usd                     1298  260 261 259 258 260   0   0  2026-10-27
gold                        1256  234 260 257 252 253   0   0  2026-10-27
ibex_35                     1277  252 260 257 256 252   0   0  2026-10-27
nasdaq_composite            1253  234 260 257 250 252   0   0  2026-10-27
natural_gas                 1256  234 260 257 252 253   0   0  2026-10-27
silver                      1255  234 260 257 251 253   0   0  2026-10-27
sp_500                      1253  234 260 257 250 252   0   0  2026-10-27
spanish_banks_etf           1253  234 260 257 250 252   0   0  2026-10-27
stoxx_600                   1255  245 256 255 249 250   0   0  2026-10-27
us_tbill_3m                 1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_10y             1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_20y_etf         1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_30y             1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_5y              1253  234 260 257 250 252   0   0  2026-10-27
us_treasury_7_10y_etf       1253  234 260 257 250 252   0   0  2026-10-27
usd_jpy                     1298  260 261 259 258 260   0   0  2026-10-27
vix                         1255  236 260 257 250 252   0   0  2026-10-27
wti_crude                   1255  234 260 257 251 253   0   0  2026-10-27
```

Fewer Mondays than other days in US series (234 vs 260) are US holidays, not an error. The last observation is 2026-10-27 because the fetch uses an exclusive end date of today.

## 2. Datasets

Id rule: `yahoo.<csv stem without _processed>`. Fields: `close`, `ret_1d`, `ret_1w` (5 sessions), `ret_1m` (21), `ret_1y` (252), `ret_ytd` (all `pct_change`, 1 decimal), plus `sma_200` for equity indices (drawn on the Markets single-index chart). Series key is a geography code (`es`, `ez`, `eu`, `us`, `de`, `fr`, `uk`, `global`).

| id | title_es | fields | last_observation |
|---|---|---|---|
| yahoo.brent_crude | Petróleo Brent | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.cac_40 | CAC 40 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.dax | DAX 40 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.dxy | Índice del dólar (DXY) | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.eur_chf | Euro / franco suizo | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.eur_gbp | Euro / libra esterlina | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.eur_jpy | Euro / yen | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.eur_usd | Euro / dólar | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.euro_govt_bond_etf | ETF de deuda pública de la zona euro | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.euro_stoxx_50 | Euro Stoxx 50 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.european_banks_etf | ETF iShares MSCI Europa Financiero | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.ftse_100 | FTSE 100 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.gbp_usd | Libra esterlina / dólar | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.gold | Oro | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.ibex_35 | IBEX 35 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.nasdaq_composite | NASDAQ Composite | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.natural_gas | Gas natural (Henry Hub) | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.silver | Plata | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.sp_500 | S&P 500 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.spanish_banks_etf | ETF iShares MSCI España | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.stoxx_600 | STOXX Europe 600 | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.us_tbill_3m | Letra del Tesoro EE. UU. 3 meses | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.us_treasury_10y | Bono del Tesoro EE. UU. a 10 años | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.us_treasury_20y_etf | ETF de bonos del Tesoro EE. UU. a más de 20 años | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.us_treasury_30y | Bono del Tesoro EE. UU. a 30 años | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.us_treasury_5y | Bono del Tesoro EE. UU. a 5 años | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.us_treasury_7_10y_etf | ETF de bonos del Tesoro EE. UU. a 7-10 años | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.usd_jpy | Dólar / yen | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |
| yahoo.vix | VIX (volatilidad implícita del S&P 500) | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd, sma_200 | 2026-10-27 |
| yahoo.wti_crude | Petróleo WTI | close, ret_1d, ret_1w, ret_1m, ret_1y, ret_ytd | 2026-10-27 |

Units: equity indices `index` (note "Puntos"); FX `rate` (note "USD por EUR" etc.); commodities `rate` (note "USD por barril", "USD por onza troy", "USD por MMBtu"); US yields `pct`; ETFs `currency` with ISO code (price per share).

## 3. Ticker changes

| key | was | now | why |
|---|---|---|---|
| spain_govt_bond_etf | SPGB.L | dropped | No data on Yahoo; no replacement found (probed IBGS.L, IBGX.L, ESPGB.L, CSPGB.L, ESP10.MI, search returned nothing). Spanish 10Y yield comes from BdE. |
| euro_govt_bond_etf | IBGE.AS | EUNH.DE | Same fund family: iShares Core EUR Govt Bond UCITS ETF, Xetra, EUR. IBGE.AS returns 404. |
| vstoxx | ^V2X | dropped | No data for ^V2X, ^V2TX, V2TX.DE, ^VSTOXX. |
| fed_funds | ^IRX | us_tbill_3m | ^IRX is the 13-week T-bill rate, not the Fed Funds rate. Renamed, titled "Letra del Tesoro EE. UU. 3 meses". Old `fed_funds_*.csv` removed locally. |

## 4. Decisions

- Returns are exported for every dataset including yields and FX, because the Markets rates table shows 30d/YTD/1y changes for them. For yields these are relative changes of the yield (in %), not percentage-point changes.
- `ret_ytd` changed meaning: it used to be measured from the first close of the year (so it excluded the first session's move); now it is measured from the last close of the previous year, the usual convention. The first year in the sample (2021) is empty. Old Overview/Markets YTD values will shift slightly.
- Not exported because no page shows them: OHLC, volume, SMA 20/50, 3-month return, 20d volatility, `correlation_matrix` (the Markets page has no correlation chart; grep finds none), `stock_indices_comparison`, `commodities_comparison`, `market_summary`. The processor still writes them.
- `ret_1w/1m/1y` count trading sessions, as the processor always did. The old interest-rates table computed 30d/1y by calendar days in the page; values differ marginally.
- ETF prices use unit `currency` (price of one share), not `index`.
- `vix` is exported as an `index` (points); its returns are of the index level.

## 5. Remaining issues

- `scripts/validate_contract.py --strict` exits non-zero only because of `eurostat/hicp.json` staleness (not mine); no warnings or errors for `yahoo/*`.
- The old Shiny app (`src/app/data.py`, `markets.py`) still loads `fed_funds`, `vstoxx`, `spain_govt_bond_etf`; they now resolve to empty frames. Phase 6 deletes the app.
- Daily data stops at the day before the run (exclusive end date), so the same-day close is not included.

## 6. Requests

- REQUEST → ws/frontend: if a correlation matrix is wanted on the Markets page, say so; the contract has no clean unit for correlation coefficients (`count` is the closest and misleading), so it would need a contract extension (e.g. unit `ratio`) before `yahoo.correlation_matrix` can be exported with `frequency X`.
- REQUEST → ws/frontend: Spanish and euro-area bond comparisons should use BdE yields; there is no Spain bond ETF or VSTOXX on Yahoo any more.
