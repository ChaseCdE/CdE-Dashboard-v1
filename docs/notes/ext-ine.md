# ext/ine notes

Branch `ext/ine`. Eight new INE datasets (the ninth, insolvencies, is skipped, see below). Last observations are from the 2026-10-28 run. All table ids were checked against the API (`DATOS_TABLA`, `DATOS_SERIE`, `TABLAS_OPERACION`), not guessed.

## Datasets

| id | title_es | freq | series | fields | last_observation | INE table |
|---|---|---|---|---|---|---|
| `ine.tourist_arrivals` | Llegada de turistas internacionales (FRONTUR) | M | `es` | value (persons), yoy, sum_12m | 2026-08-01 | 10822 |
| `ine.tourist_spending` | Gasto de los turistas internacionales (EGATUR) | M | `es` | value (EUR, scale 6), yoy, sum_12m (EUR, scale 6) | 2026-08-01 | 10838 |
| `ine.hotel_overnight_stays` | Pernoctaciones en establecimientos hoteleros | M | `total`, `residentes`, `no_residentes` | value (count), yoy, sum_12m | 2026-09-01 | 2009 |
| `ine.housing_transactions` | Compraventa de viviendas (ETDP) | M | `total`, `nueva`, `usada` | value (count), yoy, sum_12m | 2026-08-01 | 6150 |
| `ine.mortgages` | Hipotecas sobre viviendas | M | `es` | value (count), yoy, sum_12m, avg_amount (EUR) | 2026-08-01 | 13896 |
| `ine.companies` | Sociedades mercantiles creadas y disueltas | M | `created`, `dissolved` | value (count), yoy, sum_12m | 2026-08-01 | 13912 |
| `ine.household_saving_rate` | Tasa de ahorro de los hogares | Q | `es` | value (pct) | 2026-04-01 | 62275 |
| `ine.population_nationality` | Población residente por nacionalidad | Q | `total`, `espanola`, `extranjera` | value (persons), yoy | 2026-07-01 | 59587 |

Series codes used (the processors select by anchored name regex and fall back to the code with a warning if INE renames the series, e.g. `Total Nacional.` to `Nacional.`):
FRONTUR `FREG337`; EGATUR `FREG647`; hotel `EOT25` / `EOT33` / `EOT41`; ETDP `ETDP1826` / `ETDP1825` / `ETDP1824`; mortgages `HPT34618` (number) and `HPT34565` (amount); companies `SM21483` (created) and `SM21486` (dissolved); saving rate `CTNFSI11270`; population `ECP4961` / `ECP4901` / `ECP701`.

## Definitions and decisions

- All growth rates (`yoy`) are computed by calendar date (`pct_change_by_date`, 12 months earlier), no fill. They are relative % changes of the level.
- `sum_12m` (new helper `sum_by_date`) is the sum of the 12 consecutive monthly periods ending at the row's date; null unless all 12 exist. First valid value is 11 months after the first observation. A gap in the middle nulls every window that touches it (unit-checked with a synthetic gap).
- Original (unadjusted) data everywhere except the saving rate. FRONTUR / EGATUR / hotel / ETDP / mortgages / companies have no SA series that INE headlines.
- Tourist spending: INE unit is euros, scale "Millones" (confirmed with `tip=AM`, `T3_Escala`). Stored in millions of euros, `scale: 6`, so the frontend must multiply by 10^6 to get euros. Same for `sum_12m`.
- Mortgages: table 13896, series "Viviendas" (not "Total fincas"). INE's importe is in thousands of euros (`T3_Escala` = Miles); `avg_amount` = importe x 1000 / number, in euros. It is a computed field; INE does not publish this ratio in the API table.
- Hotel overnight stays: table 2009 (Encuesta de Ocupación Hotelera, by category) rather than 36570 ("Coyuntura turística hotelera: pernoctaciones"), because 2009 has the residents / non-residents split. `residentes` = residentes en España, `no_residentes` = residentes en el extranjero.
- Housing: `usada` = "Vivienda segunda mano"; `total` = "General", compraventa only (no donations, inheritances...).
- Household saving rate: INE's quarterly figure for hogares e ISFLSH, seasonally and calendar adjusted (CTNFSI11270). The 4-quarter cumulative rate is not a published series in the API; `note_es` states that the value is the quarterly SA rate. The non-adjusted rate (CTNFSI11271) is 18.7% in 2026Q2 and is strongly seasonal, so it was not exported.
- Population by nationality: reference date is the first day of the quarter (1 Jan / Apr / Jul / Oct). Quarterly since 2021; before that INE only publishes 1 Jan and 1 Jul, so 2002-2020 is half-yearly (stated in `note_es`; `yoy` is still correct because 12 months earlier exists). Table 59587 has 3600 series and the 59663 table is islands-only, so the fetcher requests the three national series by code (`DATOS_SERIE`). Other tables with the same series (59591, 82104) are copies; 56951 is the old frozen version (ends 2024-10).
- History depth: FRONTUR / EGATUR tables start in 2015-10 (that is all the API returns for these tables); monthly stats fetch the last 192 months (hotel, ETDP, mortgages, companies start 2010), saving rate 80 quarters (2006Q3), population 70 observations (2002).

## Checks (latest value vs INE, via a separate API call per series)

| dataset | mine | INE |
|---|---|---|
| tourist_arrivals 2026-08 | 12,256,087; yoy 9.1641 | level 12,256,087; INE published yoy (FREG321) 9.16; INE YTD (FREG1173) 70,362,493 = sum of Jan-Aug in the data |
| tourist_spending 2026-08 | 17,838.23 M EUR; yoy 9.1585 | level 17,838.23; INE yoy (FREG623) 9.16; INE YTD (FREG961) 99,891.78 = sum of Jan-Aug |
| hotel 2026-09 | total 40,157,907; residentes 11,853,658; no_residentes 28,304,249 | identical (EOT25 / 33 / 41) |
| housing_transactions 2026-08 | 49,319 / 10,521 / 38,798 | identical (ETDP1826 / 1825 / 1824) |
| mortgages 2026-08 | 33,841; avg 181,285 EUR | HPT34618 = 33,841; HPT34565 = 6,134,856 thousand EUR (6,134,856,000 / 33,841 = 181,285) |
| companies 2026-08 | created 7,526; dissolved 1,315 | identical (SM21483, SM21486) |
| household_saving_rate 2026Q2 | 11.0 | CTNFSI11270 = 11.0; also SA gross saving 30,434 / SA gross disposable income 276,938 = 10.99% |
| population 2026-07-01 | 49,801,559 / 42,364,016 / 7,437,543 | identical (ECP4961 / 4901 / 701) |

Checked with INE's API only; no press release was consulted.

Pipeline: `run_pipeline.py --sources ine` exit 0; `validate_contract.py --strict`: 113 files, 0 errors, 0 warnings; `smoke_test.py --run-processors` passes.

## Skipped

- `ine.insolvencies` (Estadística del Procedimiento Concursal): not exported. INE stopped producing it ("El INE ha dejado de elaborar esta operación estadística"); the last INE data are 2020 (tables 3181 deudores por naturaleza jurídica, 3182 empresas, 2992 anual) and the statistic moved to the Colegio de Registradores from 2021Q1. The API has no 2021+ data, and a series ending in 2020 would fail the staleness check and mislead. If the page needs insolvencies, the source would be the Registradores (Portal Estadístico Registral), outside the INE pipeline. Series `total` / `empresas` / `personas_fisicas` therefore do not exist.

## Caveats

- Names: companies created is "Sociedades Constituídas" (accent on the i); the regex accepts both spellings.
- Latest monthly observations are provisional and revised by INE (ETDP, mortgages and companies are published about 6 weeks after the month).
- `tourist_arrivals` and `tourist_spending` are 75719 / 75715 duplicates in the API (same series codes); 10822 / 10838 were chosen because they were the more recent (75719 ended one month earlier at the check time). If INE retires 10822 / 10838, repoint `TABLE_IDS` only.
- Fetching `population_nationality` uses three `DATOS_SERIE` calls, not `DATOS_TABLA`.
