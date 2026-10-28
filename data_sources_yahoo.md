# Yahoo Finance Data Sources

This document describes the financial market indicators fetched from Yahoo Finance for the CdE Macroeconomic Dashboard.

## Overview

Yahoo Finance provides real-time and historical financial data through the `yfinance` Python library. The data includes:

- Stock market indices
- Currency exchange rates
- Commodity prices
- Bond market proxies (ETFs)
- Volatility indices
- Sector ETFs

**Library:** `yfinance`
**Data Frequency:** Daily (with intraday available for recent periods)
**Historical Depth:** Up to 5 years by default (configurable)
**API Rate Limits:** No strict limits, but recommended to add delays between requests

---

## Stock Market Indices

### IBEX 35 (Spain)
| Field | Value |
|-------|-------|
| Ticker | `^IBEX` |
| Key | `ibex_35` |
| Description | Main benchmark stock index of the Bolsa de Madrid |
| Currency | EUR |
| Trading Hours | 09:00-17:30 CET |

### Euro Stoxx 50 (Eurozone)
| Field | Value |
|-------|-------|
| Ticker | `^STOXX50E` |
| Key | `euro_stoxx_50` |
| Description | Stock index of Eurozone stocks, covering 50 blue-chip companies |
| Currency | EUR |
| Trading Hours | 09:00-17:30 CET |

### STOXX Europe 600
| Field | Value |
|-------|-------|
| Ticker | `^STOXX` |
| Key | `stoxx_600` |
| Description | Broad European stock index covering 600 companies across 17 countries |
| Currency | EUR |

### S&P 500 (US)
| Field | Value |
|-------|-------|
| Ticker | `^GSPC` |
| Key | `sp_500` |
| Description | Stock market index tracking 500 largest US companies |
| Currency | USD |
| Trading Hours | 09:30-16:00 EST |

### NASDAQ Composite (US)
| Field | Value |
|-------|-------|
| Ticker | `^IXIC` |
| Key | `nasdaq_composite` |
| Description | Stock market index of all stocks listed on NASDAQ |
| Currency | USD |

### DAX (Germany)
| Field | Value |
|-------|-------|
| Ticker | `^GDAXI` |
| Key | `dax` |
| Description | German stock index representing 40 major blue-chip companies |
| Currency | EUR |

### CAC 40 (France)
| Field | Value |
|-------|-------|
| Ticker | `^FCHI` |
| Key | `cac_40` |
| Description | French stock market index representing 40 largest companies on Euronext Paris |
| Currency | EUR |

### FTSE 100 (UK)
| Field | Value |
|-------|-------|
| Ticker | `^FTSE` |
| Key | `ftse_100` |
| Description | Stock index of 100 companies with highest market cap on London Stock Exchange |
| Currency | GBP |

---

## Currency Exchange Rates

### EUR/USD
| Field | Value |
|-------|-------|
| Ticker | `EURUSD=X` |
| Key | `eur_usd` |
| Description | Euro to US Dollar exchange rate |
| Quote | How many USD per 1 EUR |

### EUR/GBP
| Field | Value |
|-------|-------|
| Ticker | `EURGBP=X` |
| Key | `eur_gbp` |
| Description | Euro to British Pound exchange rate |

### EUR/JPY
| Field | Value |
|-------|-------|
| Ticker | `EURJPY=X` |
| Key | `eur_jpy` |
| Description | Euro to Japanese Yen exchange rate |

### EUR/CHF
| Field | Value |
|-------|-------|
| Ticker | `EURCHF=X` |
| Key | `eur_chf` |
| Description | Euro to Swiss Franc exchange rate |

### US Dollar Index (DXY)
| Field | Value |
|-------|-------|
| Ticker | `DX-Y.NYB` |
| Key | `dxy` |
| Description | Index measuring USD value against basket of major currencies |

---

## Commodities

### Gold Futures
| Field | Value |
|-------|-------|
| Ticker | `GC=F` |
| Key | `gold` |
| Description | Gold futures contract price (COMEX) |
| Currency | USD per troy ounce |

### Brent Crude Oil
| Field | Value |
|-------|-------|
| Ticker | `BZ=F` |
| Key | `brent_crude` |
| Description | Brent crude oil futures price |
| Currency | USD per barrel |
| Relevance | European benchmark crude oil price |

### WTI Crude Oil
| Field | Value |
|-------|-------|
| Ticker | `CL=F` |
| Key | `wti_crude` |
| Description | West Texas Intermediate crude oil futures price |
| Currency | USD per barrel |
| Relevance | US benchmark crude oil price |

### Natural Gas
| Field | Value |
|-------|-------|
| Ticker | `NG=F` |
| Key | `natural_gas` |
| Description | Natural gas futures price (Henry Hub) |
| Currency | USD per MMBtu |

### Silver Futures
| Field | Value |
|-------|-------|
| Ticker | `SI=F` |
| Key | `silver` |
| Description | Silver futures contract price (COMEX) |
| Currency | USD per troy ounce |

---

## Bond Market Proxies (ETFs)

Since Yahoo Finance doesn't provide direct bond yield data, we use ETFs as proxies for bond market performance.

### Euro Government Bond ETF
| Field | Value |
|-------|-------|
| Ticker | `EUNH.DE` (Xetra; `IBGE.AS` is no longer available on Yahoo) |
| Key | `euro_govt_bond_etf` |
| Description | iShares Core EUR Govt Bond UCITS ETF |
| Currency | EUR |

### US Treasury 20+ Year ETF
| Field | Value |
|-------|-------|
| Ticker | `TLT` |
| Key | `us_treasury_20y_etf` |
| Description | iShares 20+ Year Treasury Bond ETF |
| Currency | USD |
| Notes | Tracks long-term US Treasury bonds |

### US Treasury 7-10 Year ETF
| Field | Value |
|-------|-------|
| Ticker | `IEF` |
| Key | `us_treasury_7_10y_etf` |
| Description | iShares 7-10 Year Treasury Bond ETF |
| Currency | USD |

---

## Volatility Indices

### VIX (CBOE Volatility Index)
| Field | Value |
|-------|-------|
| Ticker | `^VIX` |
| Key | `vix` |
| Description | Market's expectation of 30-day S&P 500 volatility |
| Unit | Index points (annualized % volatility) |
| Notes | Often called the "fear index" |

---

## Sector ETFs (Spain-Focused)

### iShares MSCI Spain ETF
| Field | Value |
|-------|-------|
| Ticker | `EWP` |
| Key | `msci_spain_etf` |
| Description | ETF tracking Spanish equity market |
| Currency | USD |
| Notes | Heavy weighting in financial sector |

### iShares MSCI Europe Financials ETF
| Field | Value |
|-------|-------|
| Ticker | `EUFN` |
| Key | `european_banks_etf` |
| Description | ETF tracking European financial sector companies |
| Currency | USD |

---

## Usage

### Fetching Data

```python
from fetchers.yahoo_indicators import YahooIndicatorFetcher

# Fetch all indicators
fetcher = YahooIndicatorFetcher()
results = fetcher.fetch_all()

# Fetch specific group
fetcher.fetch_group("stock_indices")

# Fetch specific indicators
fetcher.fetch_selected(["ibex_35", "sp_500", "eur_usd"])
```

### Command Line

```bash
# Fetch all indicators
python src/scripts/fetch_yahoo_data.py

# Fetch a specific group
python src/scripts/fetch_yahoo_data.py --group stock_indices

# Fetch specific indicators
python src/scripts/fetch_yahoo_data.py --indicators ibex_35 sp_500 eur_usd

# List available groups
python src/scripts/fetch_yahoo_data.py --list-groups

# Custom date range
python src/scripts/fetch_yahoo_data.py --start-date 2020-01-01 --end-date 2024-12-31
```

### Processing Data

```bash
python src/scripts/process_yahoo_data.py
```

---

## Indicator Groups

Pre-defined groups for different dashboard views:

| Group | Indicators |
|-------|------------|
| `stock_indices` | IBEX 35, Euro Stoxx 50, STOXX 600, S&P 500, NASDAQ, DAX, CAC 40, FTSE 100 |
| `currencies` | EUR/USD, EUR/GBP, EUR/JPY, EUR/CHF, DXY |
| `commodities` | Gold, Brent Crude, WTI Crude, Natural Gas, Silver |
| `bonds` | Euro Govt Bond ETF, TLT, IEF |
| `volatility` | VIX |
| `sector` | Spanish Banks ETF, European Banks ETF |
| `dashboard_summary` | IBEX 35, Euro Stoxx 50, S&P 500, EUR/USD, Brent, Gold, VIX |
| `spain_focus` | IBEX 35, Spanish Banks ETF, Spain Govt Bond ETF, EUR/USD |

---

## Output Files

### Raw Data (`data/raw/yahoo/`)

| File | Description |
|------|-------------|
| `{indicator}_raw.csv` | Raw OHLCV data from Yahoo Finance |

### Processed Data (`data/processed/yahoo/`)

| File | Description |
|------|-------------|
| `{indicator}_processed.csv` | Cleaned data with returns and technical indicators |
| `{indicator}_monthly.csv` | Monthly resampled data |
| `market_summary.csv` | Latest values and key metrics for all indicators |
| `stock_indices_comparison.csv` | Normalized comparison of stock indices |
| `commodities_comparison.csv` | Normalized comparison of commodities |
| `correlation_matrix.csv` | Correlation matrix of daily returns |

---

## Data Fields (Processed)

| Column | Description |
|--------|-------------|
| `date` | Trading date |
| `Open` | Opening price |
| `High` | Daily high |
| `Low` | Daily low |
| `Close` | Closing price |
| `Volume` | Trading volume |
| `daily_return_pct` | Daily percentage return |
| `cumulative_return_pct` | Cumulative return from start of data |
| `ytd_return_pct` | Year-to-date return |
| `return_1w_pct` | 1-week rolling return |
| `return_1m_pct` | 1-month rolling return |
| `return_3m_pct` | 3-month rolling return |
| `return_1y_pct` | 1-year rolling return |
| `sma_20` | 20-day simple moving average |
| `sma_50` | 50-day simple moving average |
| `sma_200` | 200-day simple moving average |
| `volatility_20d` | 20-day annualized volatility |

---

## Notes and Limitations

1. **Data Availability**: Some tickers may have limited historical data or may become unavailable.

2. **Market Hours**: Data reflects end-of-day prices; intraday data requires separate API calls.

3. **Timezone**: Dates are the exchange's local calendar date (the timezone is dropped, not converted to UTC). Converting to UTC shifts European local-midnight timestamps to the previous day.

4. **Dividends/Splits**: yfinance automatically adjusts for dividends and splits unless specified otherwise.

5. **Bond Yields**: For actual bond yield data (e.g., Spain 10Y yield), use FRED API instead.

6. **Currency Rates**: Currency data may have gaps on weekends and holidays.

7. **Futures**: Futures data represents the front-month contract; may have rollover gaps.

---

## Related Files

- `src/fetchers/yahoo_client.py` - Yahoo Finance API client
- `src/fetchers/yahoo_indicators.py` - Indicator configuration and fetcher class
- `src/processors/yahoo_processor.py` - Data processing and transformation
- `src/scripts/fetch_yahoo_data.py` - Fetch script
- `src/scripts/process_yahoo_data.py` - Processing script

---

## Removed or renamed tickers (2026-10)

| Key | Change |
|-----|--------|
| `spain_govt_bond_etf` (`SPGB.L`) | Dropped: no data on Yahoo, no replacement found |
| `vstoxx` (`^V2X`) | Dropped: no VSTOXX symbol returns data |
| `euro_govt_bond_etf` | `IBGE.AS` replaced by `EUNH.DE` |
| `fed_funds` (`^IRX`) | Renamed `us_tbill_3m`: it is the 13-week T-bill rate, not Fed Funds |
