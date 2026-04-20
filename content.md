# Dashboard Content

## Overview

This document defines the indicators for the CdE Macroeconomic Dashboard. All data sources are publicly available.

## Data Sources

| Source | Coverage | API/Access |
|--------|----------|------------|
| INE | Spain | INEbase API |
| Eurostat | European Union | Eurostat API |
| FRED | US & International | FRED API |
| Yahoo Finance | Financial Markets | yfinance library |

---

## Indicators by Category

### 1. Economic Activity & Growth

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| GDP Growth (real, YoY) | INE, Eurostat, FRED | Quarterly | Spain, EU, US |
| Industrial Production Index | INE, Eurostat, FRED | Monthly | Spain, EU, US |
| Economic Sentiment Indicator (ESI) | Eurostat | Monthly | Spain, EU |
| Business Confidence Index (ICE) | INE | Quarterly | Spain |

### 2. Labor Market

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| Unemployment Rate | INE, Eurostat, FRED | Monthly | Spain, EU, US |
| Employment Growth | INE, Eurostat | Quarterly | Spain, EU |
| Labor Force Participation Rate | INE, Eurostat | Quarterly | Spain, EU |
| Wage Growth (nominal) | INE, Eurostat | Quarterly | Spain, EU |

### 3. Prices & Inflation

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| CPI / HICP (headline) | INE, Eurostat, FRED | Monthly | Spain, EU, US |
| Core Inflation | INE, Eurostat, FRED | Monthly | Spain, EU, US |
| Producer Price Index (PPI) | INE, Eurostat | Monthly | Spain, EU |
| Energy Prices | Eurostat, FRED | Monthly | EU, US |

### 4. External Sector

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| Trade Balance | INE, Eurostat | Monthly | Spain, EU |
| Current Account Balance | Eurostat, FRED | Quarterly | Spain, EU |
| EUR/USD Exchange Rate | Yahoo Finance, FRED | Daily | International |

### 5. Financial Markets

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| IBEX 35 | Yahoo Finance | Daily | Spain |
| Euro Stoxx 50 | Yahoo Finance | Daily | EU |
| S&P 500 | Yahoo Finance | Daily | US |
| 10Y Government Bond Yield (Spain) | FRED | Daily | Spain |
| 10Y Government Bond Yield (Germany) | FRED | Daily | Germany |
| Spain-Germany Spread | FRED (calculated) | Daily | Spain/Germany |
| ECB Main Refinancing Rate | FRED | As announced | EU |
| Fed Funds Rate | FRED | As announced | US |

### 6. Public Finances

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| Government Debt-to-GDP | Eurostat, FRED | Quarterly | Spain, EU, US |
| Budget Deficit (% GDP) | Eurostat | Annual | Spain, EU |

### 7. Consumer & Household

| Indicator | Source | Frequency | Geographic Coverage |
|-----------|--------|-----------|---------------------|
| Consumer Confidence Index | INE, Eurostat | Monthly | Spain, EU |
| Retail Sales (YoY) | INE, Eurostat | Monthly | Spain, EU |
| House Price Index | INE, Eurostat | Quarterly | Spain, EU |

---

## Update Frequency

| Data Type | Update Schedule |
|-----------|-----------------|
| Daily (markets) | Every trading day |
| Monthly | First week of month |
| Quarterly | Within 2 weeks of release |
| Annual | As published |
