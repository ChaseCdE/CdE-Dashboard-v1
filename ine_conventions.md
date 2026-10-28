# INE Data Conventions

This document describes the data formats and conventions used by the Instituto Nacional de Estadística (INE) API and datasets.

## Date and Period Formats

### API Response Dates

| Field | Format | Description |
|-------|--------|-------------|
| `Fecha` | Unix timestamp (ms) | Milliseconds since epoch (1970-01-01) |
| `Anyo` | Integer | Year (e.g., 2025) |
| `FK_Periodo` | Integer | Period identifier |

**Python conversion:**
```python
pd.to_datetime(fecha_value, unit="ms")
```

### Period Identifiers (FK_Periodo)

| Code | Meaning | Frequency |
|------|---------|-----------|
| 1-12 | Months (1=January, 12=December) | Monthly |
| 13-16 | Quarters (13=Q1, 16=Q4) | Quarterly |
| 20 | Quarter (alternate code) | Quarterly |

### Text Period Formats

In series names and descriptions, periods may appear as:

| Format | Meaning | Example |
|--------|---------|---------|
| `M01`, `M02`...`M12` | Months | M01 = January |
| `T1`, `T2`, `T3`, `T4` | Quarters (Trimestre) | T1 = Q1 |
| `1T`, `2T`, `3T`, `4T` | Quarters (alternate) | 1T = Q1 |
| `S1`, `S2` | Semesters | S1 = First half |

---

## Number Formats

### Decimal Separator

| Context | Separator | Example |
|---------|-----------|---------|
| API JSON response | Period (`.`) | `117.6105` |
| Spanish text/display | Comma (`,`) | `117,6105` |
| CSV exports from INE website | Comma (`,`) | `117,6105` |

**Note:** The JSON API returns numbers with period decimal separators (international format). Manual CSV downloads from the INE website may use comma separators (Spanish format).

### Thousands Separator

| Context | Separator | Example |
|---------|-----------|---------|
| API JSON response | None | `1234567` |
| Spanish text/display | Period (`.`) | `1.234.567` |

### Special Values

| Value | Meaning |
|-------|---------|
| `null` | Data not available |
| `Secreto: true` | Confidential (suppressed for privacy) |
| `..` | Data not yet published (in text tables) |
| `-` | Not applicable |

---

## Text Encoding

### Character Encoding

| Issue | Example | Correct |
|-------|---------|---------|
| UTF-8 with BOM issues | `Ã­ndice` | `Índice` |
| Latin-1 vs UTF-8 | `Ã±` | `ñ` |

**Recommendation:** Always request and parse data as UTF-8. The API returns UTF-8 encoded JSON.

### Common Encoding Artifacts

| Artifact | Correct Character |
|----------|-------------------|
| `Ã¡` | á |
| `Ã©` | é |
| `Ã­` | í |
| `Ã³` | ó |
| `Ãº` | ú |
| `Ã±` | ñ |

---

## Series Naming Conventions

### Geographic Levels

| Term | Meaning |
|------|---------|
| `Total Nacional` | National total (Spain) |
| `CCAA` | Comunidades Autónomas (regions) |
| `Provincias` | Provinces |

### Data Adjustments

| Term | Meaning |
|------|---------|
| `Datos ajustados de estacionalidad` | Seasonally adjusted |
| `Datos ajustados de estacionalidad y calendario` | Seasonally and calendar adjusted |
| `Datos no ajustados` | Unadjusted (raw) |
| `Datos corregidos` | Corrected data |

### Value Types

| Term | Meaning |
|------|---------|
| `Índice` | Index value (base = 100) |
| `Variación mensual` | Month-over-month change (%) |
| `Variación anual` | Year-over-year change (%) |
| `Variación trimestral` | Quarter-over-quarter change (%) |
| `Variación en lo que va de año` | Year-to-date change (%) |
| `Dato base` | Base value |
| `Tasa` | Rate (e.g., unemployment rate) |

### Price Types

| Term | Meaning |
|------|---------|
| `Precios corrientes` | Current prices (nominal) |
| `Precios constantes` | Constant prices (real) |
| `Índices de volumen encadenado` | Chain-linked volume indices |

---

## Base Year Conventions

### Current Base Years (as of 2025)

| Indicator | Base Year | Notes |
|-----------|-----------|-------|
| IPC (CPI) | 2025 | Changed January 2026 (ECOICOP v2); 2025 average = 100 in the data |
| PIB (GDP) | 2020 | CNTR chain-volume index; 2020 average = 100 in the data |
| IPI (Industrial Production) | 2021 | |
| IPSS (Services, turnover) | 2021 | 2021 average = 100 in the data |
| IPV (House Prices) | 2025 | 2025 average = 100 in the data |
| ICM (Retail Sales) | 2021 | |
| IPRI (Industrial Prices) | 2021 | per table code `2021_NAC-CCAA_MDOINT` |
| ICE (Business Confidence) | 2013 | |

**Warning:** Base year changes affect table IDs. When a base year changes, new table IDs are created and old ones become historical.

---

## API-Specific Conventions

### Table and Series Codes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `IPC` | Consumer Price Index | `IPC251852` |
| `EPA` | Labor Force Survey | `EPA438090` |
| `CNTR` | National Accounts (Quarterly) | `CNTR4865` |
| `IPI` | Industrial Production Index | `IPI13873` |
| `IPV` | House Price Index | `IPV...` |
| `ICM` | Retail Trade Index | `ICM...` |

### Operation Codes

| Code | Full Name |
|------|-----------|
| `IPC` | Índice de Precios de Consumo |
| `EPA` | Encuesta de Población Activa |
| `CNTR` | Contabilidad Nacional Trimestral |
| `IPI` | Índices de Producción Industrial |
| `IPV` | Índice de Precios de Vivienda |
| `ICM` | Índices de Comercio al por Menor |
| `ICE` | Indicadores de Confianza Empresarial |
| `ETCL` | Encuesta Trimestral de Coste Laboral |
| `IPRI` | Índices de Precios Industriales |

---

## Frequency Codes

| Code | Meaning |
|------|---------|
| 1 | Monthly |
| 3 | Quarterly |
| 6 | Semi-annual |
| 12 | Annual |

---

## Common Data Issues

### Issue 1: Missing Recent Data
Some series may lag behind others. Check the `Fecha` field to verify data freshness.

### Issue 2: Revisions
Economic data is frequently revised. The API returns the latest available values, which may differ from previously published figures.

### Issue 3: Discontinuities
Base year changes and methodological updates can cause breaks in series. Check for notes in the `Notas` field of the API response.

### Issue 4: Multiple Series per Table
Tables contain many series (by region, sex, age, etc.). Always filter to the specific series needed.
Taking "the first matching series" is fragile: table 75809 (retail) has no total, so the first
`Índice` series was a sub-universe (`Empresas unilocalizadas`). Anchor the filter on the full
series name and check the chosen name when a table is repointed.

### Issue 5: Series renames after a rebase
In 2026 INE renamed `Total Nacional.` to `Nacional.` (CPI, IPV, IPRI, ICN, IAS) and EPA population
series (`Todas las edades. Personas.` to `Total. Valor absoluto.`). A filter that no longer matches
produces an empty frame and the fetcher keeps the old cached file (`Skipping save of empty
DataFrame`), so the data silently stop updating. Look for that message in the pipeline log.

### Issue 6: Year-over-year by date, not by position
The processor computes yoy / qoq / mom by calendar date (`pct_change_by_date`), never with
`pct_change(periods=n)`: a missing period gives NaN instead of a comparison with the wrong period,
and no implicit forward fill happens. Changes of rates (unemployment, activity...) are in
percentage points (`yoy_pp`), not relative %.

### Issue 7: Dates
`Fecha` is local midnight of the first day of the period expressed in UTC milliseconds
(for example 22:00 UTC the day before). Convert to Europe/Madrid before taking the date
(`parse_ine_data` does).

### Issue 8: Large tables and monthly sums (ext/ine)
`DATOS_TABLA` refuses very large tables ("No puede mostrarse por restricciones de volumen", for
example FRONTUR 75723) and `SERIES_TABLA` often does too. Use `DATOS_SERIE/<code>` for a few
known series (population by nationality, table 59587). Inside a `DATOS_TABLA` response the order of
`Data` is not guaranteed to be ascending: sort by date before taking "the last value".
`sum_12m` is built with `sum_by_date` (null unless 12 consecutive monthly periods exist).
Money amounts: check `T3_Escala` with `tip=AM` (EGATUR is in millions of euros, mortgage amounts
in thousands of euros).
