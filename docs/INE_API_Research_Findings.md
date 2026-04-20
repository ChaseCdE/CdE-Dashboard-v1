# INE API Research Findings: GDP Contributions and CPI Special Groups

## Summary

This document contains the research findings for INE (Instituto Nacional de Estadistica) API table IDs and series codes for:
1. GDP Demand-side Contributions (Quarterly National Accounts)
2. CPI Special Groups (IPC Grupos Especiales)

---

## 1. GDP Demand-side Contributions

### Table ID: 67824
**Name:** PIB pm Demanda (Indices de volumen encadenado)
**Operation:** CNTR2010 (Contabilidad Nacional Trimestral de Espana: Principales Agregados)
**Periodicity:** Quarterly
**API URL:** `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/67824?nult=40`

### Key Series for Contributions (Aportacion al crecimiento del PIB)

#### Private Consumption (Consumo privado / Hogares)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7005 | Gasto en consumo final de los hogares. Aportacion trimestral | Non-adjusted |
| CNTR7006 | Gasto en consumo final de los hogares. Aportacion anual | Non-adjusted |
| CNTR7164 | Gasto en consumo final de los hogares. Aportacion trimestral | Seasonally adjusted |
| CNTR7165 | Gasto en consumo final de los hogares. Aportacion anual | Seasonally adjusted |

#### Public Consumption (Consumo publico / AAPP)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7030 | Gasto en consumo final de las AAPP. Aportacion trimestral | Non-adjusted |
| CNTR7031 | Gasto en consumo final de las AAPP. Aportacion anual | Non-adjusted |
| CNTR7189 | Gasto en consumo final de las AAPP. Aportacion trimestral | Seasonally adjusted |
| CNTR7190 | Gasto en consumo final de las AAPP. Aportacion anual | Seasonally adjusted |

#### Gross Fixed Capital Formation (FBCF / Inversion)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7055 | Formacion bruta de capital fijo (FBCF). Aportacion trimestral | Non-adjusted |
| CNTR7056 | Formacion bruta de capital fijo (FBCF). Aportacion anual | Non-adjusted |
| CNTR7214 | Formacion bruta de capital fijo (FBCF). Aportacion trimestral | Seasonally adjusted |
| CNTR7215 | Formacion bruta de capital fijo (FBCF). Aportacion anual | Seasonally adjusted |

#### Total Gross Capital Formation (Formacion bruta de capital)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7050 | Formacion bruta de capital. Aportacion trimestral | Non-adjusted |
| CNTR7051 | Formacion bruta de capital. Aportacion anual | Non-adjusted |
| CNTR7209 | Formacion bruta de capital. Aportacion trimestral | Seasonally adjusted |
| CNTR7210 | Formacion bruta de capital. Aportacion anual | Seasonally adjusted |

#### Exports (Exportaciones)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7109 | Exportaciones de bienes y servicios. Aportacion trimestral | Non-adjusted |
| CNTR7110 | Exportaciones de bienes y servicios. Aportacion anual | Non-adjusted |
| CNTR7268 | Exportaciones de bienes y servicios. Aportacion trimestral | Seasonally adjusted |
| CNTR7269 | Exportaciones de bienes y servicios. Aportacion anual | Seasonally adjusted |

#### Imports (Importaciones)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7129 | Importaciones de bienes y servicios. Aportacion trimestral | Non-adjusted |
| CNTR7130 | Importaciones de bienes y servicios. Aportacion anual | Non-adjusted |
| CNTR7288 | Importaciones de bienes y servicios. Aportacion trimestral | Seasonally adjusted |
| CNTR7289 | Importaciones de bienes y servicios. Aportacion anual | Seasonally adjusted |

#### External Demand (Demanda externa / Saldo exterior)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7104 | Demanda externa. Aportacion trimestral | Non-adjusted |
| CNTR7105 | Demanda externa. Aportacion anual | Non-adjusted |
| CNTR7263 | Demanda externa. Aportacion trimestral | Seasonally adjusted |
| CNTR7264 | Demanda externa. Aportacion anual | Seasonally adjusted |

#### National Demand (Demanda nacional)
| Series Code | Description | Type |
|-------------|-------------|------|
| CNTR7149 | Demanda nacional. Aportacion trimestral | Seasonally adjusted |
| CNTR7150 | Demanda nacional. Aportacion anual | Seasonally adjusted |

### Recommended Configuration for Fetcher

```python
TABLE_IDS = {
    "gdp_contributions": 67824,  # PIB pm Demanda - Contribuciones
}

# Recommended series (seasonally adjusted, annual contribution)
GDP_CONTRIBUTION_SERIES = {
    "private_consumption": "CNTR7165",   # Hogares - anual ajustado
    "public_consumption": "CNTR7190",    # AAPP - anual ajustado
    "investment_fbcf": "CNTR7215",       # FBCF - anual ajustado
    "investment_total": "CNTR7210",      # FBC total - anual ajustado
    "exports": "CNTR7269",               # Exportaciones - anual ajustado
    "imports": "CNTR7289",               # Importaciones - anual ajustado
    "external_demand": "CNTR7264",       # Demanda externa - anual ajustado
    "national_demand": "CNTR7150",       # Demanda nacional - anual ajustado
}
```

---

## 2. CPI Special Groups (IPC Grupos Especiales)

### Table ID: 22349
**Name:** Indices nacionales de grupos especiales
**Operation:** IPC (Indice de Precios de Consumo)
**Periodicity:** Monthly
**API URL:** `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/22349?nult=60`

### Key Series for Special Groups

#### Core Inflation (Inflacion subyacente)
**Definition:** General index excluding unprocessed food and energy products
| Series Code | Description |
|-------------|-------------|
| IPC208547 | General sin alimentos no elaborados ni productos energeticos. Indice |
| IPC208612 | General sin alimentos no elaborados ni productos energeticos. Variacion mensual |
| IPC208611 | General sin alimentos no elaborados ni productos energeticos. Variacion anual |
| IPC208610 | General sin alimentos no elaborados ni productos energeticos. Variacion en lo que va de ano |

#### Energy Products (Productos energeticos)
| Series Code | Description |
|-------------|-------------|
| IPC208552 | Productos energeticos. Indice |
| IPC208627 | Productos energeticos. Variacion mensual |
| IPC208626 | Productos energeticos. Variacion anual |
| IPC208625 | Productos energeticos. Variacion en lo que va de ano |

#### Unprocessed Food (Alimentos sin elaboracion)
| Series Code | Description |
|-------------|-------------|
| IPC208557 | Alimentos sin elaboracion. Indice |
| IPC208642 | Alimentos sin elaboracion. Variacion mensual |
| IPC208641 | Alimentos sin elaboracion. Variacion anual |
| IPC208640 | Alimentos sin elaboracion. Variacion en lo que va de ano |

#### Processed Food, Beverages and Tobacco (Alimentos elaborados)
| Series Code | Description |
|-------------|-------------|
| IPC208558 | Alimentos con elaboracion, bebidas y tabaco. Indice |
| IPC208645 | Alimentos con elaboracion, bebidas y tabaco. Variacion mensual |
| IPC208644 | Alimentos con elaboracion, bebidas y tabaco. Variacion anual |
| IPC208643 | Alimentos con elaboracion, bebidas y tabaco. Variacion en lo que va de ano |

#### Services (Servicios)
| Series Code | Description |
|-------------|-------------|
| IPC208534 | Servicios. Indice |
| IPC208573 | Servicios. Variacion mensual |
| IPC208572 | Servicios. Variacion anual |
| IPC208571 | Servicios. Variacion en lo que va de ano |

#### Industrial Goods excluding Energy (Bienes industriales sin energia)
| Series Code | Description |
|-------------|-------------|
| IPC208535 | Bienes industriales sin energia. Indice |
| IPC208576 | Bienes industriales sin energia. Variacion mensual |
| IPC208575 | Bienes industriales sin energia. Variacion anual |
| IPC208574 | Bienes industriales sin energia. Variacion en lo que va de ano |

#### All Industrial Goods (Bienes industriales)
| Series Code | Description |
|-------------|-------------|
| IPC208556 | Bienes industriales. Indice |
| IPC208639 | Bienes industriales. Variacion mensual |
| IPC208638 | Bienes industriales. Variacion anual |
| IPC208637 | Bienes industriales. Variacion en lo que va de ano |

#### Foods and Beverages (Alimentos y bebidas)
| Series Code | Description |
|-------------|-------------|
| IPC208537 | Alimentos y bebidas. Indice |
| IPC208582 | Alimentos y bebidas. Variacion mensual |
| IPC208581 | Alimentos y bebidas. Variacion anual |
| IPC208580 | Alimentos y bebidas. Variacion en lo que va de ano |

#### General Index (for reference)
| Series Code | Description |
|-------------|-------------|
| IPC206446 | Indice general. Indice |
| IPC206449 | Indice general. Variacion mensual |
| IPC206448 | Indice general. Variacion anual |
| IPC206447 | Indice general. Variacion en lo que va de ano |

### Recommended Configuration for Fetcher

```python
TABLE_IDS = {
    "cpi_special_groups": 22349,  # IPC Grupos Especiales
}

# Recommended series (annual variation for inflation analysis)
CPI_SPECIAL_GROUP_SERIES = {
    "general": "IPC206448",                  # Indice general - variacion anual
    "core_inflation": "IPC208611",           # Subyacente - variacion anual
    "energy": "IPC208626",                   # Productos energeticos - variacion anual
    "food_unprocessed": "IPC208641",         # Alimentos no elaborados - variacion anual
    "food_processed": "IPC208644",           # Alimentos elaborados - variacion anual
    "food_all": "IPC208581",                 # Alimentos y bebidas - variacion anual
    "services": "IPC208572",                 # Servicios - variacion anual
    "industrial_goods_no_energy": "IPC208575", # Bienes ind. sin energia - variacion anual
    "industrial_goods": "IPC208638",         # Bienes industriales - variacion anual
}
```

---

## API Access Examples

### Get full table data (last 60 periods)
```
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/22349?nult=60
https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/67824?nult=40
```

### Get specific series data
```
https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC208611?nult=60
https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/CNTR7165?nult=40
```

### Get table metadata (series list)
```
https://servicios.ine.es/wstempus/js/ES/SERIES_TABLA/22349
https://servicios.ine.es/wstempus/js/ES/SERIES_TABLA/67824
```

---

## Notes

1. **Base 2025 Changes:** As of January 2026, INE has implemented a new base 2025 for IPC, adopting ECOICOP v2 classification. Some table and series IDs may change. Monitor for updates.

2. **Seasonally Adjusted Data:** For GDP contributions, seasonally adjusted series (ajustados de estacionalidad y calendario) are recommended for trend analysis.

3. **Annual Variation:** For CPI special groups, annual variation series are most useful for inflation analysis, avoiding monthly volatility.

4. **Alternative Table:** Table 67198 also contains GDP demand data but with slightly different series structure.

5. **Data Format:** Values are typically in percentage points for contributions and percentage changes for CPI variations.

---

## Sources

- INE API Reference: https://www.ine.es/dyngs/DAB/index.htm?cid=1100
- INE Data Portal: https://www.ine.es/jaxiT3/Tabla.htm?t=22349
- INE Data Portal: https://www.ine.es/jaxiT3/Tabla.htm?t=67824
