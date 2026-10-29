# Observatorio de Márgenes Empresariales (AEAT)

Source of `aeat.ome_totals` and `aeat.ome_divisions` (page Empresas, section "Ventas y costes").

- **Data**: quarterly series that the Agencia Tributaria builds from the VAT (modelos 303/322) and
  withholding (modelo 111) returns of private non-financial companies. Population "homogénea
  corriente", all company sizes, CVEC (seasonally and calendar adjusted by the AEAT, RJDemetra).
- **File**: "2.1 Datos trimestrales (Población homogénea corriente)", static Excel file
  `Datos_margenes_empresariales/Datos_trimestrales.xlsx` on the AEAT statistics page
  (sede.agenciatributaria.gob.es > Estadísticas > Datos del Observatorio de márgenes empresariales).
  Sheet `BdD`: long table by period, activity group (73 CNAE groups), variable, Original/CVEC.
- **Totals**: the file has no national total. The national series are the sum of the 73 groups;
  checked against the OME web application (identical to 0.005 M EUR, original and CVEC).
- **Variables**: A. Ventas totales; B. Compras totales (current and investment goods, interior
  and imports: shown as "aprovisionamientos" but wider than the accounting item); C. Masa salarial
  (wages subject to withholding, no employer social contributions: shown as "costes de personal"
  but narrower than the accounting item); S.2 indicator of gross operating result = A - B - C.
- **Divisions**: CNAE-2009 at two digits as published (some groupings, e.g. 41+42+43). Trade
  (45, 46, 47) is published by 3-digit groups; the processor adds them up.
- **Fallback**: both datasets are `optional`; if the AEAT server is unreachable the previous JSON
  stays. The AEAT servers reset connections from some networks; if the GitHub runner cannot
  reach them, run `python -m src.fetchers.aeat_ome data/raw/aeat` from a Spanish connection, then
  `python -m src.scripts.process_aeat_data` and `python -m src.export.export_site_data`.
