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
| 75809 | Índice nacional: comercio sin estaciones de servicio |

**Example URL:**
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/75809?nult=24
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
| GDP Growth | 30679 | Quarterly | Ready |
| Industrial Production | 70178 | Monthly | Ready |
| Business Confidence | TBD (via ICE) | Quarterly | Need table ID |
| Unemployment Rate | 65349 | Quarterly | Ready |
| Employment Growth | 65349 | Quarterly | Ready |
| Labor Force Participation | 65349 | Quarterly | Ready |
| Wage Growth | TBD (via ETCL) | Quarterly | Need table ID |
| CPI (Headline) | 50904 | Monthly | Ready |
| Core Inflation | 50904 (filtered) | Monthly | Ready |
| PPI | TBD (via IPRI) | Monthly | Need table ID |
| Trade Balance | N/A | Monthly | Use Eurostat |
| Consumer Confidence | TBD (via ICE) | Quarterly | Need table ID |
| Retail Sales | 75809 | Monthly | Ready |
| House Price Index | 25171 | Quarterly | Ready |

---

## Next Steps

1. **Fetch remaining table IDs** for: ICE, ETCL, IPRI operations
2. **Proceed to Stage 2**: Build Python fetcher scripts using confirmed endpoints
3. **Trade Balance**: Use Eurostat API instead of INE

---

## Sources

- [INE API JSON Documentation](https://www.ine.es/dyngs/DataLab/manual.html?cid=45)
- [INE API Reference](https://www.ine.es/dyngs/DAB/index.htm?cid=1100)
- [Table/Series Identifier Codes](https://www.ine.es/dyngs/DAB/index.htm?cid=1104)
- [datos.gob.es Catalog](https://datos.gob.es)
