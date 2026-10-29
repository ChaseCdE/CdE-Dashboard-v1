# fill/ine notes

Branch `fill/ine`, 2026-10-29. Five INE datasets added to complete page sections. Every code was queried in the Tempus API (`SERIES_TABLA`, `DATOS_SERIE`) on 2026-10-29; the fetcher pins each series by code and fails if the name no longer carries the tokens in `src/fetchers/ine_series.py`.

| id | title | freq | series | fields | adjustment | table / series codes | latest value | check |
|---|---|---|---|---|---|---|---|---|
| `ine.gva_sectors` | Valor añadido bruto por ramas de actividad | Q | `agricultura`, `industria`, `construccion`, `servicios`, `pib` | `yoy`, `qoq` (pct_change) | SCA: "Datos corregidos de efectos estacionales y de calendario" | 67822. yoy CNTR6659 / 6664 / 6674 / 6679 / 6654; qoq CNTR6658 / 6663 / 6673 / 6678 / 6653 | 2026Q2 yoy: agricultura 6.02, industria 1.42, construcción 4.25, servicios 2.89, PIB 2.64. qoq: -0.12, 0.70, 1.01, 0.71, 0.68 | INE press release CNTR 2T26 (https://www.ine.es/dyngs/Prensa/CNTR2T26.htm): industry +1.4 yoy / +0.7 qoq, construction +4.3 / +1.0, services +2.9 / +0.7, primary qoq -0.1 (Q1: 4.2). See "Primary sector sign" below |
| `ine.employed_sectors` | Ocupados por sector económico (EPA) | Q | `agricultura`, `industria`, `construccion`, `servicios` | `value` (persons, scale 3, thousands), `yoy` | NSA: "Datos originales (sin corregir de estacionalidad)" | 65126. EPA399207 / 399208 / 399209 / 399210 (Total Nacional, ambos sexos, total edades) | 2026Q3: 728.8 / 3,043.7 / 1,587.5 / 17,492.5 thousand (sum 22,852.5 vs EPA387796 total 22,852.6) | EPA 3T26 press release (https://www.ine.es/dyngs/Prensa/EPA3T26.htm): yoy change of employed Servicios +479,400, Construcción +30,500, Industria -25,900, Agricultura -18,600; quarterly Servicios +235,600, Agricultura -58,300, Industria -54,400, Construcción -49,300. Mine from the rounded levels: +479.4, +30.4, -25.9, -18.5; +235.5, -58.2, -54.4, -49.3 (0.1 thousand rounding) |
| `ine.cpi_rent` | IPC: alquiler de vivienda principal | M | `es` | `value` (index, base 2025 = 100), `yoy` | NSA (INE publishes no adjusted CPI) | 76128 (ECOICOP ver.2 subclasses). Index IPC291807, yoy IPC291806 ("Alquiler de vivienda principal") | 2026-09: 103.102, yoy 2.6 | Oracle vs `DATOS_SERIE` (maxdiff 0). The CPI September 2026 press release has no rent figure to quote. Base year 2025 averages 100.00 in the data |
| `ine.hotel_prices` | Índice de Precios Hoteleros (IPH) | M | `es` | `value` (index, base 2008 = 100), `yoy` | NSA (no adjusted IPH exists in the API) | 12157. Index EOT14624, yoy EOT14625 (national, all categories) | 2026-09: 172.77, yoy 6.69 | Coyuntura Turística Hotelera Sep 2026 (https://www.ine.es/dyngs/Prensa/CTH0926.htm): "El Índice de Precios Hoteleros subió un 6,7% en tasa anual" |
| `ine.trade_prices` | Precios industriales de exportación e importación | M | `exportacion`, `importacion` | `value` (index, base 2021 = 100), `yoy` | NSA (IPRIX / IPRIM are published unadjusted) | `source.dataset` "61662, 61672"; url of 61662. Export (IPRIX) index IPR30874, yoy IPR30945; import (IPRIM) index IPR34018, yoy IPR34016, total industria | 2026-08: export 123.313, yoy 5.5; import 125.727, yoy 7.1 | IPRIX-IPRIM Aug 2026 (https://www.ine.es/dyngs/Prensa/IPRIX-IPRIM0826.htm): IPRIX annual 5.5 %, IPRIM annual 7.1 %. Base year 2021 averages 100.00 in both |

## Decisions

- **History.** The export keeps rows from 2016-01-01 (`Dataset.start`). The raw files hold 2015 data too, so the EPA `yoy` (computed) and the first published rates start in 2016Q1 / 2016-01. Monthly raw files request 130 observations, quarterly 48.
- **Rates.** INE's published rates are used for GVA, rent, hotel and trade. INE publishes no yoy for the EPA sector table (table 65126 has levels only), so `employed_sectors.yoy` is computed by date from the original levels (relative % change vs 12 months earlier) and its note says so.
- **No period-on-period change on original data.** Only `ine.gva_sectors` has `qoq`, and it is on SCA data. The other four datasets have `value` and `yoy` only.
- **EPA remains original data.** The adjusted EPA level exists only in an INE workbook (see `docs/audit/seasonal-adjustment.md`), so the sector levels are original data, consistent with `ine.employed`.
- **GVA branches.** "Industria" is section B-E (industrial branches including energy), "Servicios" is G-T, "Agricultura" is A (with forestry and fishing). `pib` is the same series as `ine.gdp` (CNTR6654 / 6653) and is included for the comparison with the branches. Volume indices, chained, GVA at basic prices.
- **Rent series.** ECOICOP ver.2 subclass "Alquiler de vivienda principal"; the earlier subgroup "Alquiler de vivienda" (IPC290887, table 76126) mixes in other rents. Tables 76128 and 79184 carry the same series codes; 76128 is the one cited. The index starts at base-2025 levels linked backwards by INE (2016-01 = 87.838).
- **Hotel prices.** May 2020 has no observation (hotels were closed; INE publishes none), so the series has 128 rows for 129 months and `yoy` of 2021-05 is null (INE has none). The index base is 2008 as INE names it in the series ("Base 2008"); the oracle cannot verify the base average because the published range starts in 2016.
- **Trade prices.** Two tables, two series each: `source.dataset` lists both ids and `source.url` points to the export table (the contract holds one URL). Latest period is August 2026, one month behind the CPI/hotel data, as INE publishes it.
- **SCA token.** The new GVA series require the full phrase "Datos ajustados de estacionalidad y calendario" in the INE name (`SCA_FULL`). The older registry token `SA = "ajustados de estacionalidad"` also matches INE's "Datos no ajustados de estacionalidad..." names, so it would not catch a swap to the unadjusted variant. Not changed here (outside this branch's scope); worth tightening.

## Primary sector sign (GVA, 2026Q2)

The Q2 2026 press release says "las ramas primarias descendió un 6,0%" in the paragraph on annual rates, right after "todos los grandes sectores de actividad presentaron tasas interanuales positivas". The API says the opposite sign: CNTR6659 = +6.0177 and the adjusted level CNTR6657 rose from 118.89 (2025Q2) to 126.05 (2026Q2), i.e. +6.02 %. The published dataset follows the API series and the level arithmetic; the press text looks like a typo ("descendió" for "aumentó"). Worth a look by whoever writes the page text.

## Oracle (`scripts/audit/`)

- `check_ine.py`: SPEC gains 32 (dataset, series, field) rows with the identity tokens of each INE name (including the full SCA phrase for GVA), compared against `DATOS_SERIE` on the last 24 periods. New `fill_meta()` checks, independently of `src/`: `source.dataset` and `source.url`, frequency, series and field keys and order, units and scale, the adjustment phrase of every field (SCA for GVA; original data for the rest and no `mom`/`qoq`), Spanish title and description, history starting in 2016, and last observation equal to INE's latest period. It also checks that the four EPA sectors add up to EPA387796 (maxdiff 0.1) and recomputes the EPA sector `yoy` from API levels (maxdiff 5e-5).
- `check_transforms.py`: the four published-rate fields are registered as `OFFICIAL` (compared with INE, not recomputed), `ine.employed_sectors.yoy` is excluded from the offline recompute (its first four quarters need 2015 levels), and `ine.gva_sectors` must say SCA. The existing base-year check passes for rent (2025) and trade (2021).

## Verification (2026-10-29)

- `run_pipeline.py --sources ine`: exit 0, 130 datasets.
- `validate_contract.py --strict`: 0 errors, 0 warnings.
- `smoke_test.py --run-processors`: OK.
- `python -m unittest discover -s tests -t .`: OK.
- `check_all.py`: 0 FAIL, 4 WARN (all predate this branch: two tourism display roundings, CPI contribution additivity, yield-curve text), 1 SKIP (hotel base 2008 outside the published range).
- Not committed: `data/` and `site/data/` (regenerated by the run; the five new JSON files are in the worktree's `site/data/ine/`).
