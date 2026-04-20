# Eurostat Data Sources for Macroeconomic Dashboard

This document provides a comprehensive reference for accessing Eurostat datasets using the `eurostat` Python package. All datasets include data for Spain (ES) and EU27 aggregates for comparison.

## Table of Contents

1. [Python Package Setup](#python-package-setup)
2. [Geographic Codes](#geographic-codes)
3. [Economic Activity Indicators](#economic-activity-indicators)
4. [Labor Market Indicators](#labor-market-indicators)
5. [Prices and Inflation Indicators](#prices-and-inflation-indicators)
6. [External Sector Indicators](#external-sector-indicators)
7. [Public Finances Indicators](#public-finances-indicators)
8. [Consumer and Household Indicators](#consumer-and-household-indicators)
9. [Complete Python Code Example](#complete-python-code-example)

---

## Python Package Setup

### Installation

```bash
pip install eurostat
```

### Basic Usage

```python
import eurostat

# Get table of contents
toc = eurostat.get_toc_df()

# Get available parameters for a dataset
pars = eurostat.get_pars('namq_10_gdp')

# Get possible values for a parameter
geo_values = eurostat.get_par_values('namq_10_gdp', 'geo')

# Download data with filters
filter_pars = {
    'startPeriod': 2020,
    'endPeriod': 2025,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['CLV_PCH_PRE_HAB']
}
data = eurostat.get_data_df('namq_10_gdp', filter_pars=filter_pars)
```

---

## Geographic Codes

| Code | Description |
|------|-------------|
| `ES` | Spain |
| `EU27_2020` | European Union - 27 countries (from 2020) |
| `EA20` | Euro area - 20 countries (current composition) |

---

## Economic Activity Indicators

### 1. GDP Growth (Quarterly, Real Growth Rates)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `namq_10_gdp` |
| **Frequency** | Quarterly |
| **Description** | Gross domestic product and main components |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `CLV_PCH_PRE_HAB` | Chain linked volumes, percentage change on previous period, per capita |
| `unit` | `CLV_PCH_PRE` | Chain linked volumes, percentage change on previous period |
| `s_adj` | `SCA` | Seasonally and calendar adjusted |
| `na_item` | `B1GQ` | Gross domestic product at market prices |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['CLV_PCH_PRE'],
    's_adj': ['SCA'],
    'na_item': ['B1GQ']
}
gdp_growth = eurostat.get_data_df('namq_10_gdp', filter_pars=filter_pars)
```

**Alternative Dataset:**
- `tec00115` - Real GDP growth rate (simplified table)

---

### 2. Industrial Production Index (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `sts_inpr_m` |
| **Frequency** | Monthly |
| **Description** | Production in industry - monthly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `I21` | Index, 2021=100 |
| `unit` | `PCH_PRE` | Percentage change on previous period |
| `unit` | `PCH_SM` | Percentage change compared to same period in previous year |
| `s_adj` | `SCA` | Seasonally and calendar adjusted |
| `nace_r2` | `B-D` | Industry (except construction) |
| `nace_r2` | `MIG_CAG` | Capital goods |
| `nace_r2` | `MIG_COG` | Consumer goods |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['I21'],
    's_adj': ['SCA'],
    'nace_r2': ['B-D']
}
ipi = eurostat.get_data_df('sts_inpr_m', filter_pars=filter_pars)
```

---

### 3. Economic Sentiment Indicator (ESI) (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `ei_bssi_m_r2` |
| **Frequency** | Monthly |
| **Description** | Sentiment indicators - monthly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `indic` | `BS-ESI-I` | Economic Sentiment Indicator |
| `s_adj` | `SA` | Seasonally adjusted |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'indic': ['BS-ESI-I'],
    's_adj': ['SA']
}
esi = eurostat.get_data_df('ei_bssi_m_r2', filter_pars=filter_pars)
```

**Alternative Dataset:**
- `teibs010` - Economic sentiment indicator (simplified table)

---

## Labor Market Indicators

### 4. Unemployment Rate (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `une_rt_m` |
| **Frequency** | Monthly |
| **Description** | Unemployment by sex and age - monthly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `PC_ACT` | Percentage of active population |
| `s_adj` | `SA` | Seasonally adjusted |
| `sex` | `T` | Total |
| `age` | `Y15-74` | From 15 to 74 years |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['PC_ACT'],
    's_adj': ['SA'],
    'sex': ['T'],
    'age': ['Y15-74']
}
unemployment = eurostat.get_data_df('une_rt_m', filter_pars=filter_pars)
```

---

### 5. Employment Growth (Quarterly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `namq_10_a10_e` |
| **Frequency** | Quarterly |
| **Description** | Employment A*10 industry breakdowns - National Accounts |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `PCH_PRE_PER` | Percentage change on previous period (persons) |
| `unit` | `THS_PER` | Thousand persons |
| `s_adj` | `SCA` | Seasonally and calendar adjusted |
| `nace_r2` | `TOTAL` | Total - all NACE activities |
| `na_item` | `EMP_DC` | Total employment domestic concept |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['PCH_PRE_PER'],
    's_adj': ['SCA'],
    'nace_r2': ['TOTAL'],
    'na_item': ['EMP_DC']
}
employment_growth = eurostat.get_data_df('namq_10_a10_e', filter_pars=filter_pars)
```

**Alternative Dataset:**
- `lfsi_emp_q` - Employment and activity by sex and age - quarterly data (Labour Force Survey)

---

### 6. Labor Force Participation Rate (Quarterly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `lfsi_emp_q` |
| **Frequency** | Quarterly |
| **Description** | Employment and activity by sex and age - quarterly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `PC_POP` | Percentage of total population |
| `s_adj` | `SA` | Seasonally adjusted |
| `sex` | `T` | Total |
| `age` | `Y15-64` | From 15 to 64 years |
| `indic_em` | `ACT` | Activity rate |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['PC_POP'],
    's_adj': ['SA'],
    'sex': ['T'],
    'age': ['Y15-64'],
    'indic_em': ['ACT']
}
participation = eurostat.get_data_df('lfsi_emp_q', filter_pars=filter_pars)
```

---

## Prices and Inflation Indicators

### 7. HICP - Harmonised Index of Consumer Prices (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `prc_hicp_manr` |
| **Frequency** | Monthly |
| **Description** | HICP - monthly data (annual rate of change) |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `coicop` | `CP00` | All-items HICP |
| `unit` | `RCH_A` | Annual rate of change |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'coicop': ['CP00'],
    'unit': ['RCH_A']
}
hicp = eurostat.get_data_df('prc_hicp_manr', filter_pars=filter_pars)
```

**Alternative Datasets:**
- `prc_hicp_midx` - HICP - monthly data (index)
- `tec00118` - HICP - inflation rate (simplified table)

---

### 8. Core Inflation / HICP Excluding Energy and Food (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `prc_hicp_manr` |
| **Frequency** | Monthly |
| **Description** | HICP - monthly data (annual rate of change) |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `coicop` | `TOT_X_NRG_FOOD` | All-items excluding energy and food (core inflation) |
| `unit` | `RCH_A` | Annual rate of change |

**COICOP Special Aggregates for Analysis:**

| Code | Description |
|------|-------------|
| `CP00` | All-items HICP |
| `TOT_X_NRG_FOOD` | All-items excluding energy and food (core) |
| `TOT_X_NRG` | All-items excluding energy |
| `NRG` | Energy |
| `FOOD` | Food including alcohol and tobacco |
| `SERV` | Services |
| `IGD_NNRG` | Non-energy industrial goods |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'coicop': ['TOT_X_NRG_FOOD'],
    'unit': ['RCH_A']
}
core_inflation = eurostat.get_data_df('prc_hicp_manr', filter_pars=filter_pars)
```

---

### 9. Producer Price Index (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `sts_inppd_m` |
| **Frequency** | Monthly |
| **Description** | Producer prices in industry, domestic market - monthly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `I21` | Index, 2021=100 |
| `unit` | `PCH_PRE` | Percentage change on previous period |
| `unit` | `PCH_SM` | Percentage change compared to same period in previous year |
| `nace_r2` | `B-D` | Industry (except construction) |
| `nace_r2` | `MIG_ING` | Intermediate goods |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['I21'],
    'nace_r2': ['B-D']
}
ppi = eurostat.get_data_df('sts_inppd_m', filter_pars=filter_pars)
```

**Alternative Datasets:**
- `sts_inpp_m` - Producer prices in industry, total (includes domestic and non-domestic)
- `sts_inppnd_m` - Producer prices in industry, non-domestic market

---

## External Sector Indicators

### 10. Trade Balance (Monthly) - Spain

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `ext_lt_intratrd` |
| **Frequency** | Monthly |
| **Description** | Intra and Extra-EU trade by Member State |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES']` | Spain |
| `partner` | `WORLD` | World (total trade) |
| `partner` | `EU27_2020_INTRA` | Intra-EU trade |
| `partner` | `EU27_2020_EXTRA` | Extra-EU trade |
| `indic_et` | `TRD_BAL` | Trade balance |
| `indic_et` | `EXP_VAL` | Exports value |
| `indic_et` | `IMP_VAL` | Imports value |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES'],
    'partner': ['WORLD'],
    'indic_et': ['TRD_BAL', 'EXP_VAL', 'IMP_VAL']
}
trade_balance = eurostat.get_data_df('ext_lt_intratrd', filter_pars=filter_pars)
```

**Alternative Dataset for Detailed Monthly Data:**
- Access Comext database through Eurostat's Easy Comext application for detailed monthly trade statistics

**Note:** Trade balance data may require combining exports and imports from different sources. For the most detailed monthly data, consider using `ext_st_eu27_2020sitc` for goods trade.

---

## Public Finances Indicators

### 11. Government Debt-to-GDP (Quarterly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `gov_10q_ggdebt` |
| **Frequency** | Quarterly |
| **Description** | Quarterly government debt |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `PC_GDP` | Percentage of GDP |
| `na_item` | `GD` | Government consolidated gross debt |
| `sector` | `S13` | General government |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['PC_GDP'],
    'na_item': ['GD'],
    'sector': ['S13']
}
debt_gdp = eurostat.get_data_df('gov_10q_ggdebt', filter_pars=filter_pars)
```

**Alternative Dataset:**
- `teina230` - General government gross debt - quarterly data (simplified table)

---

### 12. Budget Deficit as % of GDP (Annual)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `gov_10dd_edpt1` |
| **Frequency** | Annual |
| **Description** | Government deficit/surplus, debt and associated data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `PC_GDP` | Percentage of GDP |
| `na_item` | `B9` | Net lending (+) / Net borrowing (-) |
| `sector` | `S13` | General government |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2015,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['PC_GDP'],
    'na_item': ['B9'],
    'sector': ['S13']
}
deficit = eurostat.get_data_df('gov_10dd_edpt1', filter_pars=filter_pars)
```

**Note:** Negative values indicate deficit, positive values indicate surplus.

---

## Consumer and Household Indicators

### 13. Consumer Confidence Indicator (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `ei_bsco_m` |
| **Frequency** | Monthly |
| **Description** | Consumer confidence indicator and survey results |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `indic` | `BS-CSMCI-BAL` | Consumer confidence indicator |
| `s_adj` | `SA` | Seasonally adjusted |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'indic': ['BS-CSMCI-BAL'],
    's_adj': ['SA']
}
consumer_confidence = eurostat.get_data_df('ei_bsco_m', filter_pars=filter_pars)
```

---

### 14. Retail Trade Volume Index (Monthly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `sts_trtu_m` |
| **Frequency** | Monthly |
| **Description** | Turnover and volume of sales in wholesale and retail trade - monthly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `I21` | Index, 2021=100 |
| `unit` | `PCH_PRE` | Percentage change on previous period |
| `unit` | `PCH_SM` | Percentage change compared to same period in previous year |
| `s_adj` | `SCA` | Seasonally and calendar adjusted |
| `nace_r2` | `G47` | Retail trade, except of motor vehicles |
| `indic_bt` | `TOVV` | Volume of sales (deflated turnover) |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['I21'],
    's_adj': ['SCA'],
    'nace_r2': ['G47'],
    'indic_bt': ['TOVV']
}
retail = eurostat.get_data_df('sts_trtu_m', filter_pars=filter_pars)
```

---

### 15. House Price Index (Quarterly)

| Attribute | Value |
|-----------|-------|
| **Dataset Code** | `prc_hpi_q` |
| **Frequency** | Quarterly |
| **Description** | House price index (2015 = 100) - quarterly data |

**Key Filters:**

| Parameter | Recommended Values | Description |
|-----------|-------------------|-------------|
| `geo` | `['ES', 'EU27_2020']` | Spain and EU27 |
| `unit` | `I15_NSA` | Index, 2015=100 (not seasonally adjusted) |
| `unit` | `RCH_A` | Annual rate of change |
| `purchase` | `TOTAL` | Total (new and existing dwellings) |
| `purchase` | `NEW` | New dwellings |
| `purchase` | `EXIST` | Existing dwellings |

**Python Example:**

```python
import eurostat

filter_pars = {
    'startPeriod': 2020,
    'geo': ['ES', 'EU27_2020'],
    'unit': ['I15_NSA'],
    'purchase': ['TOTAL']
}
house_prices = eurostat.get_data_df('prc_hpi_q', filter_pars=filter_pars)
```

**Alternative Dataset:**
- `teicp270` - House price index (2015 = 100) - quarterly data (simplified table)

---

## Complete Python Code Example

Below is a comprehensive example that downloads all indicators:

```python
"""
Eurostat Data Downloader for Macroeconomic Dashboard
Downloads key indicators for Spain (ES) and EU27
"""

import eurostat
import pandas as pd
from datetime import datetime

# Configuration
START_PERIOD = 2015
GEO_CODES = ['ES', 'EU27_2020']

def get_gdp_growth():
    """GDP Growth - Quarterly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['CLV_PCH_PRE'],
        's_adj': ['SCA'],
        'na_item': ['B1GQ']
    }
    return eurostat.get_data_df('namq_10_gdp', filter_pars=filter_pars)

def get_industrial_production():
    """Industrial Production Index - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['I21'],
        's_adj': ['SCA'],
        'nace_r2': ['B-D']
    }
    return eurostat.get_data_df('sts_inpr_m', filter_pars=filter_pars)

def get_economic_sentiment():
    """Economic Sentiment Indicator - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'indic': ['BS-ESI-I'],
        's_adj': ['SA']
    }
    return eurostat.get_data_df('ei_bssi_m_r2', filter_pars=filter_pars)

def get_unemployment_rate():
    """Unemployment Rate - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['PC_ACT'],
        's_adj': ['SA'],
        'sex': ['T'],
        'age': ['Y15-74']
    }
    return eurostat.get_data_df('une_rt_m', filter_pars=filter_pars)

def get_employment_growth():
    """Employment Growth - Quarterly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['PCH_PRE_PER'],
        's_adj': ['SCA'],
        'nace_r2': ['TOTAL'],
        'na_item': ['EMP_DC']
    }
    return eurostat.get_data_df('namq_10_a10_e', filter_pars=filter_pars)

def get_labor_force_participation():
    """Labor Force Participation Rate - Quarterly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['PC_POP'],
        's_adj': ['SA'],
        'sex': ['T'],
        'age': ['Y15-64'],
        'indic_em': ['ACT']
    }
    return eurostat.get_data_df('lfsi_emp_q', filter_pars=filter_pars)

def get_hicp():
    """HICP Inflation - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'coicop': ['CP00'],
        'unit': ['RCH_A']
    }
    return eurostat.get_data_df('prc_hicp_manr', filter_pars=filter_pars)

def get_core_inflation():
    """Core Inflation (HICP excl. energy and food) - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'coicop': ['TOT_X_NRG_FOOD'],
        'unit': ['RCH_A']
    }
    return eurostat.get_data_df('prc_hicp_manr', filter_pars=filter_pars)

def get_producer_prices():
    """Producer Price Index - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['I21'],
        'nace_r2': ['B-D']
    }
    return eurostat.get_data_df('sts_inppd_m', filter_pars=filter_pars)

def get_trade_balance():
    """Trade Balance - Monthly (Spain only)"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': ['ES'],
        'partner': ['WORLD'],
        'indic_et': ['TRD_BAL', 'EXP_VAL', 'IMP_VAL']
    }
    return eurostat.get_data_df('ext_lt_intratrd', filter_pars=filter_pars)

def get_government_debt():
    """Government Debt-to-GDP - Quarterly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['PC_GDP'],
        'na_item': ['GD'],
        'sector': ['S13']
    }
    return eurostat.get_data_df('gov_10q_ggdebt', filter_pars=filter_pars)

def get_budget_deficit():
    """Budget Deficit as % of GDP - Annual"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['PC_GDP'],
        'na_item': ['B9'],
        'sector': ['S13']
    }
    return eurostat.get_data_df('gov_10dd_edpt1', filter_pars=filter_pars)

def get_consumer_confidence():
    """Consumer Confidence Indicator - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'indic': ['BS-CSMCI-BAL'],
        's_adj': ['SA']
    }
    return eurostat.get_data_df('ei_bsco_m', filter_pars=filter_pars)

def get_retail_trade():
    """Retail Trade Volume Index - Monthly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['I21'],
        's_adj': ['SCA'],
        'nace_r2': ['G47'],
        'indic_bt': ['TOVV']
    }
    return eurostat.get_data_df('sts_trtu_m', filter_pars=filter_pars)

def get_house_prices():
    """House Price Index - Quarterly"""
    filter_pars = {
        'startPeriod': START_PERIOD,
        'geo': GEO_CODES,
        'unit': ['I15_NSA'],
        'purchase': ['TOTAL']
    }
    return eurostat.get_data_df('prc_hpi_q', filter_pars=filter_pars)


if __name__ == "__main__":
    print("Downloading Eurostat data for macroeconomic dashboard...")

    # Example: Download GDP growth data
    try:
        gdp_data = get_gdp_growth()
        print(f"GDP Growth data: {len(gdp_data)} rows downloaded")
        print(gdp_data.head())
    except Exception as e:
        print(f"Error downloading GDP data: {e}")
```

---

## Notes and Limitations

### Data Availability

1. **Geographic Coverage:** Not all datasets may have complete data for both Spain and EU27. Always check data availability before relying on a specific series.

2. **Temporal Coverage:** Historical data availability varies by indicator. Some datasets start from the 1990s, while others only have recent data.

3. **Revisions:** Eurostat data is subject to revisions. The most recent periods may be provisional.

### Technical Considerations

1. **API Rate Limits:** The Eurostat API may have rate limits. Consider implementing delays between requests when downloading multiple datasets.

2. **Package Version:** From eurostat package version 1.0.0, SDMX functions are deprecated. Use `get_data_df()` for standard data retrieval.

3. **Data Format:** The eurostat package returns pandas DataFrames. Time columns are typically in YYYY-QN or YYYY-MM format.

4. **Parameter Discovery:** Always use `eurostat.get_pars()` and `eurostat.get_par_values()` to discover available parameters and their values for each dataset.

### HICP Classification Change (2026)

From 2026, Eurostat uses a new classification (ECOICOP ver.2) based on UN COICOP 2018. Datasets in the folder 'prc_hicp_ecoicop1' using the old classification have been archived. New datasets are in 'prc_hicp_ecoicop2'.

---

## References

- [Eurostat Python Package (PyPI)](https://pypi.org/project/eurostat/)
- [Eurostat Data Browser](https://ec.europa.eu/eurostat/databrowser/)
- [Eurostat HICP Database](https://ec.europa.eu/eurostat/web/hicp/database)
- [Eurostat National Accounts Database](https://ec.europa.eu/eurostat/web/national-accounts/database)
- [Eurostat Labour Force Survey Database](https://ec.europa.eu/eurostat/web/lfs/database)
- [Eurostat Government Finance Statistics](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Government_finance_statistics)

---

*Document generated: February 2026*
*For the CdE Macroeconomic Dashboard project*
