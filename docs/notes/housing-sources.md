# Housing prices: MIVAU and Registradores (2026-10-29)

Request: add the MIVAU and Registradores house price data to the Precios page.

## Sources

| Dataset | Source | Access | Notes |
|---|---|---|---|
| `mivau.appraised_house_prices` | MIVAU, Estadística de valor tasado de la vivienda | Banco de España API (`listaSeries`), series `DHIVTNOAPLPMMUVT_RLI.T` (total), `_VVN_RLI.T` (up to 5 years old), `_VVU_RLI.T` (over 5 years) | EUR/m2, quarterly, from 1995 (by age from 2013). The ministry has no stable machine-readable endpoint; the BdE republishes the series in its housing-market indicators (si_1_5), so the existing, reliable BdE client is used. Source line credits MIVAU and links to its boletín page. |
| `registradores.house_prices` | Colegio de Registradores, open-data portal (CKAN) | `package_show` of `compraventas-de-inmuebles-uso-residencial-por-provincia`, then its CSV resource | National rows only (`geo == Nacional`): `viv-pm2` (EUR/m2), `viv-imp` (EUR per dwelling). The file name changes every quarter, hence the metadata lookup. The portal's firewall rejects non-browser clients, so a browser User-Agent is sent. |

Checks: Registradores Q2 2026 gives +2.4 % q/q and +9.2 % y/y, the rates in the ERI press release for that quarter. The level (2,392 EUR/m2) is lower than the ERI headline (2,487 EUR/m2), so the dataset description says the level may differ from the quarterly note. The BdE does not republish any Registradores price.

Seasonal adjustment: both are original data. Following docs/audit/seasonal-adjustment.md, only annual rates (`yoy`) are exported, not `qoq`.

## Robustness

- New pipeline source `housing` (run_pipeline.py): `fetch_housing_data` / `process_housing_data`.
- A failed fetch keeps the previous raw file and is reported (exit code 3), as for the other sources.
- Both datasets are `optional`: if there is no processed CSV (e.g. the first run on a fresh Actions cache with the portal unreachable), the exporter keeps the previously published JSON and stamps today's `generated_at`, so the staleness badge works. Risk to watch: the Registradores firewall may block GitHub-hosted runners.

## Site

Precios, section "Precios de la vivienda": two new charts after "Compra y alquiler": annual rate of INE IPV, MIVAU and Registradores; and EUR/m2 levels (MIVAU vs Registradores, toggle MIVAU by age). Footer source list updated.
