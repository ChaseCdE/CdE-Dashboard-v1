# Data Sources: INE (Instituto Nacional de Estadística)

## Stage 1: Data Locator Output

### API Overview

| Property | Value |
|----------|-------|
| Base URL | `https://servicios.ine.es/wstempus/js/ES/` |
| Format | JSON |
| Authentication | None required (public API) |
| Rate Limits | Not strictly enforced, but use responsibly |
| Documentation | [API Reference](https://www.ine.es/dyngs/DAB/index.htm?cid=1100) |

### Key API Endpoints

| Function | URL Pattern | Description |
|----------|-------------|-------------|
| Get table data | `DATOS_TABLA/{table_id}` | Retrieve all data from a table |
| Get series data | `DATOS_SERIE/{series_id}` | Retrieve data from a specific series |
| List table series | `SERIES_TABLA/{table_id}` | List all series in a table |
| List operations | `OPERACIONES_DISPONIBLES` | List all available statistical operations |
| Tables by operation | `TABLAS_OPERACION/{operation_code}` | Get tables for an operation |

### Common Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `date` | `YYYYMMDD:YYYYMMDD` | Filter by date range |
| `nult` | Integer | Get last N observations |
| `det` | 0, 1, 2 | Detail level (2 = most detail) |
| `tip` | A, M, AM | A=friendly, M=metadata, AM=both |
| `page` | Integer | Pagination (max 500 results/page) |

---

## Indicator Endpoints

### 1. GDP Growth (PIB)

| Property | Value |
|----------|-------|
| Operation | Contabilidad Nacional Trimestral (CNTR) |
| Operation Code | `CNTR` |
| Frequency | Quarterly |

| Table ID | Description | Notes |
|----------|-------------|-------|
| 30679 | PIB Oferta (Índices volumen encadenado) | Volume indices - for real growth |
| 30681 | PIB Demanda (Índices volumen encadenado) | Demand-side volume indices |
| 30678 | PIB Oferta (Precios corrientes) | Current prices |
| 30680 | PIB Demanda (Precios corrientes) | Current prices |

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/30679?nult=20
```

---

### 2. Industrial Production Index (IPI)

| Property | Value |
|----------|-------|
| Operation | Índices de Producción Industrial |
| Operation Code | `IPI` |
| Frequency | Monthly |

| Table ID | Description |
|----------|-------------|
| 70178 | Secciones - Nacional (base 2021) |
| 26064 | Grupos - Nacional |

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/70178?nult=24
```

---

### 3. Business Confidence Index (ICE)

| Property | Value |
|----------|-------|
| Operation | Indicadores de Confianza Empresarial |
| Operation Code | `ICE` |
| Frequency | Quarterly |

**To get tables:**
```
https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/ICE
```

---

### 4. Unemployment Rate (EPA)

| Property | Value |
|----------|-------|
| Operation | Encuesta de Población Activa |
| Operation Code | `EPA` |
| Frequency | Quarterly |

| Table ID | Description |
|----------|-------------|
| 65349 | Tasas de actividad, paro y empleo por provincia y sexo |
| 65334 | Tasas de paro por edad, sexo y CCAA |
| 65227 | Tasas de paro por nivel de formación |
| 65331 | Parados por sector económico y CCAA |

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/65349?nult=20
```

---

### 5. Employment & Labor Force

| Property | Value |
|----------|-------|
| Operation | Encuesta de Población Activa |
| Operation Code | `EPA` |
| Frequency | Quarterly |

Uses same tables as unemployment (65349, etc.) - different series within tables.

---

### 6. Wage Growth

| Property | Value |
|----------|-------|
| Operation | Encuesta Trimestral de Coste Laboral (ETCL) |
| Operation Code | `ETCL` |
| Frequency | Quarterly |

**To get tables:**
```
https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/ETCL
```

---

### 7. CPI / Inflation (IPC)

| Property | Value |
|----------|-------|
| Operation | Índice de Precios de Consumo |
| Operation Code | `IPC` |
| Frequency | Monthly |

| Table ID | Description |
|----------|-------------|
| 50904 | Índices nacionales por clases |
| 24077 | Índice general nacional (series desde 1961) |
| 50937 | Índices nacionales por subclases |

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/50904?nult=24
```

**Note:** IPC base changed to 2025 starting January 2026. Table IDs may update.

---

### 8. Core Inflation

Derived from IPC tables - exclude energy and unprocessed food components.
Use table 50904 or 50937 and filter by appropriate categories.

---

### 9. Producer Price Index (PPI / IPRI)

| Property | Value |
|----------|-------|
| Operation | Índice de Precios Industriales |
| Operation Code | `IPRI` |
| Frequency | Monthly |
| Table used | **76655** (national + CCAA, general and by economic destination; mercado interior) |

Since the 2026 rebase the series are named `Nacional. Mercado interior. <categoría>. Índice.` (before: `Total Nacional. ...`). The fetcher and processor accept both prefixes and anchor the category (`. Energía.` cannot match `Total industria sin energía`). Data reach the latest published month (2026-09 at the time of writing).

**To get tables:**
```
https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/IPRI
```

---

### 10. Trade Balance

| Property | Value |
|----------|-------|
| Source | **Not directly from INE** |
| Alternative | Agencia Tributaria / DataComex |
| URL | https://comercio.gob.es/ |

**Note:** Trade balance data comes from Agencia Tributaria (Customs). Consider using Eurostat for this indicator instead.

---

### 11. Consumer Confidence

| Property | Value |
|----------|-------|
| Operation | Indicadores de Confianza Empresarial |
| Notes | Consumer confidence included in ICE survey |

**To get tables:**
```
https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/ICE
```

---

### 12. Retail Sales (ICM)

| Property | Value |
|----------|-------|
| Operation | Índices de Comercio al por Menor |
| Operation Code | `ICM` |
| Frequency | Monthly |

| Table ID | Description |
|----------|-------------|
| 67178 | Índices de especiales agregados: contiene `General` (ICM4062), el índice usado |
| 75809 | Por modos de distribución: **no tiene total**; no usar (la primera serie era "Empresas unilocalizadas") |

Series used: `Total Nacional. Cifra de negocio a precios constantes. Comercio al por menor sin Estaciones de Servicio (47 sin 473). General. Índice. Datos ajustados de estacionalidad y calendario.` (base 2021).

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/67178?nult=24
```

---

### 13. House Price Index (IPV)

| Property | Value |
|----------|-------|
| Operation | Índice de Precios de Vivienda |
| Operation Code | `IPV` |
| Frequency | Quarterly |

| Table ID | Description |
|----------|-------------|
| 25171 | Índices por CCAA: general, vivienda nueva y segunda mano |

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/25171?nult=20
```

---

## Summary Table

| Indicator | Table ID | Frequency | Status |
|-----------|----------|-----------|--------|
| GDP Growth | 67822 | Quarterly | Ready |
| Industrial Production | 60280 | Monthly | Ready |
| Business Confidence | 8027 | Quarterly | Ready |
| Unemployment Rate | 65349 | Quarterly | Ready |
| Employment Growth | 65349 | Quarterly | Ready |
| Labor Force Participation | 65349 | Quarterly | Ready |
| Wage Growth | 6030 / 6034 (ETCL) | Quarterly | Ready |
| CPI (Headline) | 79181 | Monthly | Ready |
| Core Inflation | 76130 | Monthly | Ready |
| PPI | 76655 | Monthly | Ready |
| Trade Balance | N/A | Monthly | Use Eurostat |
| Consumer Confidence | TBD (via ICE) | Quarterly | Need table ID |
| Retail Sales | 67178 | Monthly | Ready |
| House Price Index | 80270 | Quarterly | Ready |

---

## Next Steps

The authoritative list of table ids is `TABLE_IDS` in `src/fetchers/ine_indicators.py`; the site export (`src/export/ine.py`) reads source ids and URLs from it. Notes on current choices are in `docs/notes/ws-ine.md`.

Other table notes (2026-10):
- Part-time rate: table **65148** (EPA, quarterly). Table 65970 is the annual version and stopped at 2025.
- Population by age: table 65061. Series were renamed in 2026 (`... Todas las edades. Personas.` became `... Total. Valor absoluto.`); the fetcher filter accepts both.
- Trade Balance: use Eurostat API instead of INE.

---

## Sources

- [INE API JSON Documentation](https://www.ine.es/dyngs/DataLab/manual.html?cid=45)
- [INE API Reference](https://www.ine.es/dyngs/DAB/index.htm?cid=1100)
- [Table/Series Identifier Codes](https://www.ine.es/dyngs/DAB/index.htm?cid=1104)
- [datos.gob.es Catalog](https://datos.gob.es)

---

## Extended indicators (ext/ine)

Table ids verified against the API on 2026-10-28. Series are selected in the processor by anchored name regex with fallback to the series code. See `docs/notes/ext-ine.md` for definitions and checks.

| Indicator | Operation | Table | Series codes | Frequency | Notes |
|-----------|-----------|-------|--------------|-----------|-------|
| `tourist_arrivals` | FRONTUR (`FR`) | 10822 | `FREG337` | Monthly | Total turistas, original data; starts 2015-10 |
| `tourist_spending` | EGATUR (`EG`) | 10838 | `FREG647` | Monthly | Gasto total, **millions of euros** |
| `hotel_overnight_stays` | EOH (`EOH`) | 2009 | `EOT25`, `EOT33`, `EOT41` | Monthly | Total / residentes en España / en el extranjero |
| `housing_transactions` | ETDP | 6150 | `ETDP1826`, `ETDP1825`, `ETDP1824` | Monthly | Compraventa: general / nueva / segunda mano |
| `mortgages` | HPT | 13896 | `HPT34618` (number), `HPT34565` (amount, thousand euros) | Monthly | Viviendas, base nueva |
| `companies` | SM | 13912 | `SM21483` (created), `SM21486` (dissolved) | Monthly | Mercantiles, total nacional |
| `household_saving_rate` | CTNFSI | 62275 | `CTNFSI11270` | Quarterly | Hogares e ISFLSH, seasonally and calendar adjusted |
| `population_nationality` | ECP | 59587 | `ECP4961`, `ECP4901`, `ECP701` | Quarterly (half-yearly before 2021) | Fetched by series code: the table has 3600 series |

Not available: Estadística del Procedimiento Concursal (operation 13) was discontinued by INE after 2020 (moved to the Colegio de Registradores).
