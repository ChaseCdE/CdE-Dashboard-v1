# BdE Data Integration - Agent Specifications

This document defines the three specialized agents responsible for integrating Banco de España data into the CdE Macroeconomic Dashboard.

---

## Agent 1: BdE API Data Locator

**Role:** Specialist in locating and documenting Banco de España statistical data

**Responsibilities:**
1. Research and identify exact API endpoints for each indicator
2. Locate series codes (BIEST identifiers) for all priority indicators
3. Document API request formats, parameters, and response structures
4. Verify data availability and historical depth
5. Create `data_sources_bde.md` with complete endpoint documentation

**Input:** List of priority indicators by category
**Output:** `data_sources_bde.md` with:
- API base URLs and endpoints
- Series codes for each indicator
- Request parameters and examples
- Data frequency and availability notes

**Tools/Resources:**
- BdE API: `https://app.bde.es/bierest/resources/srdatosapp/`
- BIEST database: `https://www.bde.es/wbe/en/estadisticas/`
- Statistical Bulletin documentation

---

## Agent 2: Data Processing Specialist

**Role:** Expert in fetching and transforming financial/economic data

**Responsibilities:**
1. Create `bde_client.py` - API client for BdE web service
2. Create `bde_indicators.py` - Indicator configuration and fetcher class
3. Create `bde_processor.py` - Data transformation and normalization
4. Create fetch/process scripts following existing patterns
5. Handle data caching and error handling

**Input:** `data_sources_bde.md` from Agent 1
**Output:**
- `src/fetchers/bde_client.py`
- `src/fetchers/bde_indicators.py`
- `src/processors/bde_processor.py`
- `src/scripts/fetch_bde_data.py`
- `src/scripts/process_bde_data.py`

**Code Standards:**
- Follow patterns from existing `yahoo_client.py`, `yahoo_indicators.py`
- Use pandas for data manipulation
- Implement proper error handling and logging
- Cache responses to avoid rate limiting

---

## Agent 3: Dashboard Developer

**Role:** Expert in Shiny for Python dashboard development

**Responsibilities:**
1. Add BdE indicators to existing dashboard categories
2. Create new UI components where needed (e.g., Credit & Banking section)
3. Implement reactive data loading for BdE indicators
4. Create visualizations (Plotly charts) for new indicators
5. Update KPI cards and summary views

**Input:** Processed data from Agent 2, existing dashboard structure
**Output:**
- Updated dashboard pages with BdE indicators
- New visualizations for credit, interest rates, debt metrics
- Integration with existing country comparison features

**UI Components:**
- Interest rate trend charts
- Debt-to-GDP gauge/comparison charts
- Credit growth visualizations
- NPL ratio indicators
- Current account balance charts

---

## Priority Indicators to Integrate

### Category: Financial Markets (existing)
- EURIBOR 12M
- Spain 10Y Bond Yield (BdE source)
- Bank lending rates (households, corporations)

### Category: Credit & Banking (NEW)
- Credit to households (total, mortgages, consumer)
- Credit to non-financial corporations
- Credit growth rate (YoY)
- Non-performing loan ratio
- Bank Lending Survey indicators

### Category: Public Finances (existing)
- Household debt-to-GDP
- Corporate debt-to-GDP

### Category: External Sector (existing)
- Current account balance (monthly)
- Net International Investment Position
- Tourism receipts

### Category: Consumer & Household (existing)
- Household financial assets
- Household net wealth

---

## Status after the static-site migration (Phase 2, 2026-10-28)

The Shiny dashboard (Agent 3) is being replaced by a static HTML site. The BdE pipeline now ends in `src/export/bde.py`, which declares one contract dataset per processed series (`bde.<key>`) plus `bde.yield_curve`. Per-series metadata (Spanish title, label, public BdE URL, currency and scale) lives in `BDE_EXPORT_META` in `src/fetchers/bde_indicators.py`. To add an indicator: add it to `BDE_INDICATORS`, add its entry to `BDE_EXPORT_META`, run `python run_pipeline.py --sources bde`. Details and open issues: `docs/notes/ws-bde.md`.

---

## Execution Order

1. **Agent 1** runs first to document all API endpoints
2. **Agent 2** runs after Agent 1 completes, using the documentation
3. **Agent 3** runs after Agent 2 completes, integrating processed data

---

*Document created: February 2026*
