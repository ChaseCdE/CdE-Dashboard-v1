# Data Sources: Banco de Espana (BdE) API

## API Overview

| Property | Value |
|----------|-------|
| Base URL | `https://app.bde.es/bierest/resources/srdatosapp/` |
| Format | JSON (gzip compressed) |
| Authentication | None required (public API) |
| Language | `idioma=EN` (English) or `idioma=ES` (Spanish) |
| Documentation | [API Reference](https://www.bde.es/webbe/en/estadisticas/recursos/api-estadisticas-bde.html) |

---

## API Endpoints

### 1. Latest Data (`/favoritas`)

Retrieve the most recent published data for specified series.

**URL Pattern:**
```
https://app.bde.es/bierest/resources/srdatosapp/favoritas?idioma=EN&series={codes}
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| `idioma` | Language code | `EN` or `ES` |
| `series` | Comma-separated series codes | `D_1NBAF472,D_DNBAD172` |

**Response Fields:**
| Field | Description |
|-------|-------------|
| `serie` | Series identification code |
| `descripcionCorta` | Brief series description |
| `codFrecuencia` | Update frequency (D=daily, M=monthly, Q=quarterly, A=annual) |
| `decimales` | Maximum decimal places |
| `simbolo` | Data unit symbol |
| `tendencia` | Directional change indicator (+, -, =) |
| `fechaValor` | Timestamp in `yyyy-mm-ddThh:mm:ssZ` format |
| `valor` | Latest published numeric value |

### 2. Full Time Series (`/listaSeries`)

Obtain complete series data with metadata across specified timeframes.

**URL Pattern:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series={codes}&rango={range}
```

**Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| `idioma` | Language code | `EN` |
| `series` | Comma-separated series codes | `D_1NBAF472` |
| `rango` | Time period specification | See table below |

**Range Parameter Values:**
| Frequency | Range Options |
|-----------|---------------|
| Daily | `3M`, `12M`, `36M` |
| Monthly/Quarterly | `30M`, `60M`, `MAX` |
| Annual | `60M`, `MAX` |

**Additional Response Fields:**
| Field | Description |
|-------|-------------|
| `descripcion` | Extended series description |
| `informacion` | Additional metadata pairs |
| `fechaInicio` | Series start date |
| `fechaFin` | Series end date |
| `fechas` | Array of timestamps |
| `valores` | Corresponding data values |

---

## Date Interpretation by Frequency

| Frequency | Date Format |
|-----------|-------------|
| Daily (D) | Reference date |
| Monthly (M) | 1st of reference month |
| Quarterly (Q) | 1st of first month of quarter (e.g., 2025-04-01 for Q2) |
| Annual (A) | January 1st of reference year |

**Timestamps.** The API returns every observation stamped `T08:15:00Z` (summer) or `T09:15:00Z` (winter), which is 10:15 in Madrid. The fetcher (`to_local_date` in `bde_client.py`) converts to Europe/Madrid and stores a plain `YYYY-MM-DD`; the processor does the same for older raw files. No observation can shift day.

**Site export.** Each processed series is exported as `site/data/bde/<key>.json` (dataset id `bde.<key>`, `<key>` = CSV stem without `_processed`) by `src/export/bde.py`, using the Spanish titles, URLs and money units in `BDE_EXPORT_META` (`src/fetchers/bde_indicators.py`). The `*_comparison.csv` files and `bde_summary.csv` are still produced but not exported. See `docs/notes/ws-bde.md`.

**Units of money series.** `credit_households_total` and the two balance-of-payments series are in millions of EUR; `credit_nfc_total` is in billions of EUR.

---

## Indicator Endpoints

### HIGH PRIORITY INDICATORS

---

### 1. EURIBOR 12M (Monthly Average)

| Property | Value |
|----------|-------|
| Series Code | `D_1NBAF472` |
| Description | One-year Euribor - Monthly average |
| Unit | Percentage (%) |
| Frequency | Monthly |
| Source | European Banking Federation / ECB |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=D_1NBAF472&rango=60M
```

---

### 2. EURIBOR 3M (Daily)

| Property | Value |
|----------|-------|
| Series Code | `D_DNBAD172` |
| Description | 3-month Euribor - Daily |
| Unit | Percentage (%) |
| Frequency | Daily |
| Source | European Banking Federation / ECB |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=D_DNBAD172&rango=12M
```

---

### 3. EURIBOR 12M (Daily)

| Property | Value |
|----------|-------|
| Series Code | `D_DNBAF172` |
| Description | 12-month Euribor - Daily |
| Unit | Percentage (%) |
| Frequency | Daily |
| Source | European Banking Federation / ECB |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=D_DNBAF172&rango=12M
```

---

### 4. Spain 10Y Government Bond Yield (Secondary Market)

| Property | Value |
|----------|-------|
| Series Code | `D_G0B1F0ZP` |
| Description | 10-year government bond yield - Secondary market |
| Unit | Percentage (%) |
| Frequency | Daily |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=D_G0B1F0ZP&rango=12M
```

---

### 5. Bank Lending Rate - Mortgages (New Business)

| Property | Value |
|----------|-------|
| Series Code | `DN_1TI2T0135` |
| Description | NEDR. Loans to households & NPISHs. House purchase. New business |
| Unit | Percentage (%) |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DN_1TI2T0135&rango=60M
```

---

### 6. Bank Lending Rate - Consumer Credit (New Business)

| Property | Value |
|----------|-------|
| Series Code | `DN_1TI2T0138` |
| Description | NEDR. Loans to households & NPISHs. Consumption. New business |
| Unit | Percentage (%) |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DN_1TI2T0138&rango=60M
```

---

### 7. Bank Lending Rate - Corporations (New Business)

| Property | Value |
|----------|-------|
| Series Code | `DN_1TI2T0144` |
| Description | NEDR. Loans to NFCs. New business |
| Unit | Percentage (%) |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DN_1TI2T0144&rango=60M
```

---

### 8. Bank Deposit Rate - Households (New Business)

| Property | Value |
|----------|-------|
| Series Code | `DN_1TI2T0024` |
| Description | NEDR. Deposits from households & NPISHs. Term deposits. Weighted average rate |
| Unit | Percentage (%) |
| Frequency | Monthly |

**Additional series:**
- `DN_1TI1T0010` - Overnight deposits rate

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DN_1TI2T0024&rango=60M
```

---

### 9. Credit to Households - Total

| Property | Value |
|----------|-------|
| Series Code | `DF_MESNAA20A1U62250Z01E` |
| Description | OIFM. Loans and credits. To households and NPISHs |
| Unit | Millions of euros |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DF_MESNAA20A1U62250Z01E&rango=60M
```

---

### 10. Credit to Non-Financial Corporations - Total

| Property | Value |
|----------|-------|
| Series Code | `DF_MESNAA20A1U62240Z01E` |
| Description | Total lending to NFCs |
| Unit | Billions of euros |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DF_MESNAA20A1U62240Z01E&rango=60M
```

---

### 11. Household Debt-to-GDP Ratio

| Property | Value |
|----------|-------|
| Series Code | `DMZ10S80ZH0_TPRPIB.Q` |
| Description | Debt households & NPISH. % of GDP (4 quarters) |
| Unit | Percentage (%) |
| Frequency | Quarterly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DMZ10S80ZH0_TPRPIB.Q&rango=MAX
```

---

### 12. Corporate (NFC) Debt-to-GDP Ratio

| Property | Value |
|----------|-------|
| Series Code | `DMZ10S80ZN0_TPRPIB.Q` |
| Description | Debt NFCs. % of GDP (4 quarters) |
| Unit | Percentage (%) |
| Frequency | Quarterly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DMZ10S80ZN0_TPRPIB.Q&rango=MAX
```

---

### 13. Current Account Balance (Monthly)

| Property | Value |
|----------|-------|
| Series Code | `DEEM.N.ES.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL` |
| Description | Balance of Payments. Current Account. Total Current Account. Balance |
| Unit | Millions of euros |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DEEM.N.ES.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL&rango=60M
```

---

### MEDIUM PRIORITY INDICATORS

---

### 14. Tourism Receipts

| Property | Value |
|----------|-------|
| Series Code | `DEEM.N.ES.W1.S1.S1.T.C.SD._Z._Z._Z.EUR._T._X.N.ALL` |
| Description | Balance of Payments. Current Account. Services. Tourism. Income |
| Unit | Millions of euros |
| Frequency | Monthly |

**Example URL:**
```
https://app.bde.es/bierest/resources/srdatosapp/listaSeries?idioma=EN&series=DEEM.N.ES.W1.S1.S1.T.C.SD._Z._Z._Z.EUR._T._X.N.ALL&rango=60M
```

---

### 15. Additional Interest Rate Series

**EURIBOR by Maturity (Daily):**
| Series Code | Description |
|-------------|-------------|
| `D_DNBAA572` | ESTER (overnight) |
| `D_DNBAS172` | Euribor 1 week |
| `D_DNBAC172` | Euribor 1 month |
| `D_DNBAD172` | Euribor 3 months |
| `D_DNBAE172` | Euribor 6 months |
| `D_DNBAF172` | Euribor 12 months |

**Government Bond Yields (Daily):**
| Series Code | Description |
|-------------|-------------|
| `D_DTES00B7` | Treasury bills 1-3 months |
| `D_DTES00S7` | Treasury bills 6 months |
| `D_DTES00U7` | Treasury bills 1 year |
| `D_G0B1F0ZE` | Bonds 2+ years |
| `D_G0B1F0ZN` | Bonds 3 years |
| `D_G0B1F0ZO` | Bonds 5 years |
| `D_G0B1F0ZP` | Bonds 10 years |
| `D_G0B1F0ZQ` | Bonds 15 years |

---

## Summary Table

| Indicator | Series Code | Frequency | Status |
|-----------|-------------|-----------|--------|
| EURIBOR 12M (monthly) | `D_1NBAF472` | Monthly | Verified |
| EURIBOR 3M (daily) | `D_DNBAD172` | Daily | Verified |
| EURIBOR 12M (daily) | `D_DNBAF172` | Daily | Verified |
| Spain 10Y Bond Yield | `D_G0B1F0ZP` | Daily | Verified |
| Mortgage Rate (new) | `DN_1TI2T0135` | Monthly | Verified |
| Consumer Credit Rate (new) | `DN_1TI2T0138` | Monthly | Verified |
| Corporate Lending Rate (new) | `DN_1TI2T0144` | Monthly | Verified |
| Household Deposit Rate | `DN_1TI2T0024` | Monthly | Verified |
| Credit to Households | `DF_MESNAA20A1U62250Z01E` | Monthly | Verified |
| Credit to NFCs | `DF_MESNAA20A1U62240Z01E` | Monthly | Verified |
| Household Debt/GDP | `DMZ10S80ZH0_TPRPIB.Q` | Quarterly | Verified |
| NFC Debt/GDP | `DMZ10S80ZN0_TPRPIB.Q` | Quarterly | Verified |
| Current Account Balance | `DEEM.N.ES.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL` | Monthly | Verified |
| Tourism Receipts | `DEEM.N.ES.W1.S1.S1.T.C.SD._Z._Z._Z.EUR._T._X.N.ALL` | Monthly | Verified |

---

## Python Usage Example

```python
import requests
import json

def get_bde_latest(series_codes: list, language: str = "EN") -> dict:
    """
    Get latest values for BdE series.

    Args:
        series_codes: List of series codes
        language: 'EN' for English, 'ES' for Spanish

    Returns:
        JSON response with latest values
    """
    base_url = "https://app.bde.es/bierest/resources/srdatosapp/favoritas"
    params = {
        "idioma": language,
        "series": ",".join(series_codes)
    }

    response = requests.get(base_url, params=params)
    return response.json()


def get_bde_series(series_code: str, time_range: str = "60M", language: str = "EN") -> dict:
    """
    Get full time series data from BdE.

    Args:
        series_code: BdE series code
        time_range: Time range (3M, 12M, 36M for daily; 30M, 60M, MAX for monthly/quarterly)
        language: 'EN' for English, 'ES' for Spanish

    Returns:
        JSON response with time series data
    """
    base_url = "https://app.bde.es/bierest/resources/srdatosapp/listaSeries"
    params = {
        "idioma": language,
        "series": series_code,
        "rango": time_range
    }

    response = requests.get(base_url, params=params)
    return response.json()


# Example usage
if __name__ == "__main__":
    # Get latest EURIBOR rates
    euribor_series = ["D_1NBAF472", "D_DNBAD172"]
    latest = get_bde_latest(euribor_series)

    for item in latest:
        print(f"{item['descripcionCorta']}: {item['valor']}%")

    # Get 5-year history of EURIBOR 12M
    euribor_12m = get_bde_series("D_1NBAF472", "60M")

    if euribor_12m:
        series = euribor_12m[0]
        print(f"\nSeries: {series['descripcion']}")
        print(f"Start: {series['fechaInicio']}")
        print(f"End: {series['fechaFin']}")
        print(f"Latest value: {series['valores'][0]}%")
```

---

## Notes

### Data Availability
1. **Response Format**: Data is returned gzip-compressed; use `requests` with automatic decompression or `curl --compressed`.
2. **Series Codes**: Codes are case-sensitive and may use different naming conventions (D_, DN_, DF_, DMZ, DEEM formats).
3. **Historical Data**: Most series have data going back to 1999 (euro introduction) or earlier.

### API Limitations
1. No explicit rate limits documented, but use responsibly.
2. CSV bulk downloads are only available in Spanish; English API responses are available.
3. Some series may be discontinued (marked with `[discontinuada]` in descriptions).

### Related Resources
- [BdE Statistics Portal](https://www.bde.es/webbe/en/estadisticas/)
- [BIEST Database Application](https://www.bde.es/biest/)
- [Statistical Bulletin](https://www.bde.es/webbe/en/estadisticas/otras-clasificaciones/publicaciones/boletin-estadistico/)
- [Time-series Bulk Download](https://www.bde.es/webbe/en/estadisticas/recursos/descargas-completas.html)

---

## Series Codes Not Found

The following indicators were searched but specific series codes could not be verified:

| Indicator | Notes |
|-----------|-------|
| Credit to Households - Mortgages | Available in aggregated credit data; specific mortgage breakdown requires further CSV analysis |
| Credit Growth Rate (YoY) | Can be calculated from credit level series |
| Non-performing Loan Ratio (NPL) | Available in Chapter 4 tables but specific API series code requires BIEST search |
| NIIP | Available in Balance of Payments tables; requires specific series code lookup |
| Household Financial Assets | Available in Financial Accounts; requires specific series code lookup |

---

*Document generated: February 2026*
*For the CdE Macroeconomic Dashboard project*

---

## Additions (ext/bde, 2026-10-28)

Series codes were located in the Boletín Estadístico chapter CSVs (`https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/beNNNN.csv`, header rows give code, alias and description) and verified against `/listaSeries?rango=MAX`.

| Key | Series code | Boletín table | Unit in API | Notes |
|---|---|---|---|---|
| npl_ratio | D_BEEA2020 | 4.3 | % | Entidades de crédito y EFC, créditos dudosos / crédito total a otros sectores residentes |
| social_security_affiliates | DEPSEGS1AF_XRTODS.M | 24.19 | persons (CSV header says thousands, values are persons) | Afiliados a fin de mes, total regímenes, sin desestacionalizar. No average-monthly or SA series in BdE API |
| registered_unemployment | D_1JA0D000 | 24.15 | persons | Paro registrado total, fin de mes, sin desestacionalizar |
| government_debt_pde | DMNPDE2010_P00000_PS_APU | 3.22 | thousands of EUR | Divided by 1000 in the processor (`value_divisor`) to give millions of EUR |
| spread_10y_de (derived) | D_1NBBO320 - D_1NBBO308 | 1.x | pp | Spain minus Germany, monthly |
| spread_10y_it (derived) | D_1NBBO320 - D_1NBBO309 | 1.x | pp | Spain minus Italy, monthly |

Corrections to earlier codes: France 10Y is `D_1NBBO303` (the former `D_1NBBO314` is Finland) and Italy 10Y is `D_1NBBO309` (the former `D_1NBBO316` is Portugal). Other `D_1NBBO3xx` country codes: 305 Irlanda, 307 Bélgica, 308 Alemania, 310 Países Bajos, 311 Suecia, 315 Austria, 320 España.
