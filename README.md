# La economía en datos

Public dashboard of Spanish and European macroeconomic indicators by [Círculo de Empresarios](https://circulodeempresarios.org). Sources: INE, Eurostat, Banco de España, Ministerio de Vivienda y Agenda Urbana (via the Banco de España API), Colegio de Registradores (open data), European Central Bank (reference exchange rates), Federal Reserve and US EIA (via FRED), and Yahoo Finance for equity indices, VIX, ETFs and precious metals.

Pages: Portada, Actividad, Sectores (Industria, Servicios, Construcción y vivienda, Turismo), Mercado laboral, Precios, Sector exterior, Sector público, Crédito y tipos, Mercados, Comparativa UE.

## How it works

A Python pipeline downloads the data, processes it, and writes one JSON file per indicator to `site/data/` following [the data contract](docs/data-contract.md). The site in `site/` is plain HTML and JavaScript that reads those files; it has no build step. A scheduled GitHub Action refreshes the data on weekdays and publishes the site to GitHub Pages ([deploy notes](docs/deploy.md)).

## Run locally

```
pip install -r requirements.txt
python run_pipeline.py                 # ~2 min: fetch, process, export, validate
cd site && python -m http.server 8000  # then open http://localhost:8000/
```

Opening `site/index.html` directly from disk does not work (browsers block the data requests on `file://`).

## Checks

```
python scripts/smoke_test.py --run-processors   # offline pipeline checks
python scripts/validate_contract.py --strict    # site/data against the contract
```

## Documentation

- [docs/data-contract.md](docs/data-contract.md): format of `site/data/`, field naming rules, validation.
- [docs/indicator-inventory.md](docs/indicator-inventory.md): what each page shows and from which dataset.
- [docs/style-guide.md](docs/style-guide.md): colours, typography, chart rules.
- [docs/deploy.md](docs/deploy.md): GitHub Pages and the scheduled refresh.
- `data_sources_*.md`: notes on each data provider.
