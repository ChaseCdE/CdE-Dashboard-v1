# Data contract v1.1

Status: **FROZEN** on 2026-10-28 (v1.0); v1.1 on 2026-10-28, see changelog at the end. Changes require a version bump (`contract_version`), an entry in `docs/migration-notes.md`, and updates to the validator, exporter and frontend loader in the same PR.

This is the only interface between the Python pipeline and the HTML frontend. The pipeline writes it; the frontend reads it; neither depends on anything else from the other side.

## Layout

```
site/data/
├── manifest.json              # index of every dataset + latest values
├── ine/<indicator>.json
├── eurostat/<indicator>.json
├── bde/<indicator>.json
└── yahoo/<indicator>.json
```

- `site/data/` is generated. Nothing in it is edited by hand. `src/export/export_site_data.py` deletes and rebuilds it on every run.
- Dataset id = `<source>.<indicator>`; file = `site/data/<source>/<indicator>.json`. Both lowercase `snake_case`, English (code language). No `_processed`, `_raw`, `_comparison`, `_spain` suffixes: geography and comparisons are expressed as series inside the file.
- Sources: `ine`, `eurostat`, `bde`, `yahoo`. A new source adds a new prefix; nothing else changes.

## Dataset file

```json
{
  "contract_version": "1.1",
  "id": "eurostat.hicp",
  "title_es": "Inflación armonizada (IPCA)",
  "description_es": "Tasa de variación anual del IPCA. España frente a UE-27.",
  "source": {
    "name": "Eurostat",
    "dataset": "prc_hicp_manr",
    "url": "https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_manr/default/table"
  },
  "frequency": "M",
  "x": { "key": "date", "type": "date" },
  "fields": [
    { "key": "yoy", "label_es": "Variación anual", "unit": "pct_change", "decimals": 1 }
  ],
  "series": [
    { "key": "es",   "label_es": "España", "data": [["2025-11-01", 3.1], ["2025-12-01", 3.0]] },
    { "key": "eu27", "label_es": "UE-27",  "data": [["2025-11-01", 2.5], ["2025-12-01", 2.3]] }
  ],
  "last_observation": "2025-12-01",
  "generated_at": "2026-10-28T18:10:00Z"
}
```

### Top-level keys

| Key | Required | Rule |
|---|---|---|
| `contract_version` | yes | `"1.1"` |
| `id` | yes | `<source>.<indicator>`, matches file path |
| `title_es` | yes | Display title, Spanish, no trailing period |
| `description_es` | no | One or two sentences, Spanish |
| `source.name` | yes | `INE`, `Eurostat`, `Banco de España`, `Yahoo Finance` |
| `source.dataset` | yes | Table id / dataset code / ticker as used by the fetcher |
| `source.url` | yes | Public page a reader can open to verify the data |
| `frequency` | yes | `D` daily, `W` weekly, `M` monthly, `Q` quarterly, `A` annual, `X` not a time series |
| `x` | yes | `{key, type}`; `type` is `date`, `number` or `category`. `date` iff `frequency` ≠ `X` |
| `fields` | yes | ≥ 1 field definition, see below |
| `series` | yes | ≥ 1 series, see below |
| `last_observation` | yes | Max x over all series for date datasets; `null` for `X` |
| `generated_at` | yes | UTC ISO 8601 timestamp of the export run |

### Fields

Every series in a file has the same fields, in the same order. Each data row is `[x, field_1, field_2, ...]`.

| Key | Required | Rule |
|---|---|---|
| `key` | yes | `snake_case`, unique in file. Naming rules below |
| `label_es` | yes | Display label |
| `unit` | yes | One of the units below |
| `decimals` | yes | Display precision (0 to 4). Data is stored with up to 4 decimals regardless |
| `currency` | if unit=`currency` | ISO 4217 code |
| `scale` | no | Power of ten the stored number is expressed in: `3` = thousands, `6` = millions. Default `0` |
| `note_es` | no | E.g. `"Base 2021 = 100"`, `"Datos corregidos de estacionalidad"` |

Field keys and units (enforced by the validator):

| Key | Meaning | Unit |
|---|---|---|
| `value` | Level of the indicator | any |
| `yoy`, `qoq`, `mom` | **Relative** change vs a year / quarter / month earlier | must be `pct_change` |
| `ret_1d`, `ret_1w`, `ret_1m`, `ret_1y`, `ret_ytd` | Relative change of a market price over a window | must be `pct_change` |
| `yoy_pp`, `qoq_pp`, `mom_pp` (any `*_pp`) | **Difference** of a rate vs a year / quarter / month earlier (e.g. unemployment rate, debt/GDP) | must be `pp` |
| `chg_1d`, `chg_1w`, `chg_1m`, `chg_1y`, `chg_ytd` (any `chg_*`) | Difference of a rate or yield over a market window | must be `pp` |
| `yoy_diff` (any `*_diff`) | Difference in the field's own unit when it is not a percentage (e.g. confidence balance in points) | same unit as the level |
| `contribution` | Contribution to the growth of a total | `pp` |
| `weight` | Weight in a total | `pct` |

Rule of thumb: a relative change of a percentage ("unemployment fell 5 %") is never exported; use `*_pp`.

Units:

| Unit | Meaning | Example |
|---|---|---|
| `pct` | A level expressed in percent | unemployment rate, interest rate, debt/GDP |
| `pct_change` | Growth rate in percent | yoy, qoq, mom, returns |
| `pp` | Difference in percentage points | contribution to growth, change in a rate |
| `index` | Index number; put the base in `note_es`. Equity index levels also use `index` | CPI, IPI, GDP volume index, IBEX 35 |
| `points` | Balance / diffusion indicator | consumer confidence |
| `currency` | Money amount; needs `currency`, often `scale` | current account balance, tourism receipts |
| `rate` | Price of one asset in another | EUR/USD, Brent in USD/bbl (with `note_es`) |
| `persons` | People; use `scale` | employed (thousands) |
| `hours` | Hours; use `scale` | hours worked |
| `years` | Duration | bond maturity |
| `count` | Plain count | — |

### Series

| Key | Required | Rule |
|---|---|---|
| `key` | yes | `snake_case`, unique in file. Geography: ISO-like (`es`, `eu27`, `de`, `fr`, `it`); categories: stable slug from the source (`total`, `energia`, ...) |
| `label_es` | yes | Display label |
| `data` | yes | Array of rows `[x, v1, v2, ...]`, length = 1 + number of fields |
| `as_of` | no | Date the snapshot refers to; used by cross-sections (yield curve) |

Data rules:
- x for `date` type: `"YYYY-MM-DD"`. Monthly, quarterly and annual periods use the **first day of the period** (`2026-04-01` = Q2 2026, `2025-01-01` = year 2025). Daily data uses the **local trading date of the exchange**, never a UTC-shifted date.
- Rows sorted ascending by x, x unique within a series.
- Missing values are `null`. Rows where every field is `null` are dropped.
- Numbers are finite and rounded to at most 4 decimals. Display rounding uses `decimals` and happens in the frontend.
- No units, thousands separators or strings inside numeric cells.

### What the frontend may and may not do

- **May:** select series and fields, slice by date range, format numbers and dates (es-ES), stack/group for display, compute display-only transforms that change nothing economically: rebasing an index or price series to 100 at the start of a user-selected window, or at a fixed reference period (a single date such as Jan 2021, or the average of a calendar year such as 2019). Rebasing changes the base, not the dynamics.
- **May not:** compute economic quantities (growth rates, contributions, seasonal adjustment, averages used as indicators). If a page needs one, the pipeline exports it as a field.

## Manifest

`site/data/manifest.json`:

```json
{
  "contract_version": "1.1",
  "generated_at": "2026-10-28T18:10:00Z",
  "datasets": [
    {
      "id": "ine.cpi",
      "path": "ine/cpi.json",
      "title_es": "Índice de Precios de Consumo",
      "source": "INE",
      "frequency": "M",
      "last_observation": "2026-09-01",
      "fields": ["value", "yoy"],
      "series": [
        {
          "key": "es",
          "label_es": "España",
          "latest": { "value": ["2026-09-01", 104.978], "yoy": ["2026-09-01", 4.9161] }
        }
      ]
    }
  ]
}
```

- One entry per dataset file, and one file per entry.
- `latest[field]` = last non-null `[x, value]` of that field in that series, or `null` if the field is entirely null. This powers headline tiles without loading every file.
- Page assignment is **not** in the manifest. Which dataset appears on which page is a frontend decision, specified in `docs/indicator-inventory.md`.

## Validation

`python scripts/validate_contract.py` checks every rule above that can be checked mechanically, plus consistency between files and manifest. It also warns when data looks stale: the age is the number of days between the **end** of the last observed period and `generated_at` (Q2 2026, dated `2026-04-01`, ends on `2026-07-01`). Thresholds are allowances for publication lags:

| Frequency | Warn if the last period ended more than |
|---|---|
| D | 7 days |
| W | 21 days |
| M | 100 days |
| Q | 200 days |
| A | 550 days |

`--strict` turns warnings into errors. The scheduled refresh (Phase 5) runs without `--strict` but reports warnings; Phase 2 acceptance runs with `--strict` unless the staleness is explained in `docs/migration-notes.md`.

## How to add a dataset (Phase 2 agents)

1. Add a `Dataset(...)` entry to `src/export/<source>.py`. Do not edit `src/export/core.py`; request changes in `docs/migration-notes.md`.
2. `python -m src.export.export_site_data && python scripts/validate_contract.py --strict`
3. Check the JSON by eye: labels in Spanish, units right, periods on the first day.

## Changelog

- **1.1** (2026-10-28). Field-key naming rules made explicit and enforced (`*_pp`, `chg_*`, `*_diff`, `ret_*`); `yoy`/`qoq`/`mom` are relative changes only. Staleness measured from the end of the last period instead of its first day (v1.0 flagged every quarterly series as stale before the next release). Frontend may rebase to a fixed reference period, not only to the window start. Data layout unchanged; the frontend accepts any 1.x.
- **1.0** (2026-10-28). Initial version.
