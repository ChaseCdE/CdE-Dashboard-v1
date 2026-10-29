# Observatorio de Márgenes Empresariales (AEAT)

Source of `aeat.ome_totals` and `aeat.ome_divisions` (page Empresas, section "Ventas y costes").

- **Data**: quarterly series that the Agencia Tributaria builds from the VAT (modelos 303/322) and
  withholding (modelo 111) returns of private non-financial companies. Population "homogénea
  corriente", all company sizes, CVEC (seasonally and calendar adjusted by the AEAT, RJDemetra).
- **Variables**: A. Ventas totales; B. Compras totales (current and investment goods, interior
  and imports: shown as "aprovisionamientos" but wider than the accounting item); C. Masa salarial
  (wages subject to withholding, no employer social contributions: shown as "costes de personal"
  but narrower than the accounting item); S.2 indicator of gross operating result = A - B - C.
- **Access**: only through a Shiny app (https://www2.agenciatributaria.gob.es/sete-ome/,
  tab "Descargas"); the whole quarterly database (~225 MB CSV) is served by a per-session link.
  `src/fetchers/aeat_ome.py` drives the app with headless Chromium (Playwright), keeps the rows
  used (~5 MB) in `data/raw/aeat/ome_quarterly.csv`, and asks the AEAT at most once a week.
- **Divisions**: CNAE-2009 at two digits as published (some groupings, e.g. 41+42+43). Trade
  (45, 46, 47) is published by 3-digit groups; the processor adds up their CVEC levels.
- **Fallback**: both datasets are `optional`; if the AEAT is unreachable the previous JSON stays.
  The AEAT servers reset connections from some networks; if the GitHub runner cannot reach them,
  run `python -m src.fetchers.aeat_ome data/raw/aeat` from a Spanish connection, then
  `python run_pipeline.py --sources aeat` (or process + export) and commit `site/data/aeat`.
