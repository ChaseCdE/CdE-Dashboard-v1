# Dashboard Layout

## Technology Stack

- **Framework:** Shiny for Python
- **Plotting:** Plotly (interactive charts)
- **Data Processing:** Pandas
- **Styling:** Shiny UI components + custom CSS

---

## Page Structure

### Navigation

Use `ui.navset_tab()` or `ui.navset_pill()` for main navigation between sections:

```
├── Overview (Home)
├── Economic Activity
├── Labor Market
├── Prices & Inflation
├── External Sector
├── Financial Markets
├── Public Finances
└── Consumer & Household
```

---

## Page Layouts

### Overview Page

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Dashboard Title + Last Updated Timestamp           │
├─────────────────────────────────────────────────────────────┤
│  KPI Cards Row (ui.layout_columns)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ GDP     │ │ Unempl. │ │ CPI     │ │ IBEX 35 │           │
│  │ +2.1%   │ │ 11.2%   │ │ +3.4%   │ │ 10,450  │           │
│  │ ▲ +0.3  │ │ ▼ -0.5  │ │ ▲ +0.1  │ │ ▲ +1.2% │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────────────────┤
│  Summary Charts Row                                          │
│  ┌──────────────────────┐ ┌──────────────────────┐          │
│  │ GDP Trend (12m)      │ │ Inflation Trend (12m)│          │
│  │ [Sparkline Chart]    │ │ [Sparkline Chart]    │          │
│  └──────────────────────┘ └──────────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│  Market Snapshot                                             │
│  ┌──────────────────────────────────────────────┐           │
│  │ Stock Indices + Bond Yields Table            │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Category Pages (e.g., Labor Market)

```
┌─────────────────────────────────────────────────────────────┐
│  Section Title + Description                                 │
├─────────────────────────────────────────────────────────────┤
│  Filters Row                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ Country ▼    │ │ Date Range   │ │ Frequency ▼  │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  Main Content (ui.layout_columns)                           │
│  ┌────────────────────────────┐ ┌─────────────────────┐     │
│  │                            │ │ KPI Summary         │     │
│  │   Interactive Chart        │ │ • Current: 11.2%    │     │
│  │   (Plotly)                 │ │ • YoY Change: -0.5  │     │
│  │                            │ │ • Trend: ▼          │     │
│  │                            │ │                     │     │
│  └────────────────────────────┘ └─────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│  Comparison Section                                          │
│  ┌──────────────────────────────────────────────┐           │
│  │ Country Comparison Bar Chart                 │           │
│  │ [Spain | EU | US]                            │           │
│  └──────────────────────────────────────────────┘           │
├─────────────────────────────────────────────────────────────┤
│  Data Table (Expandable)                                     │
│  ┌──────────────────────────────────────────────┐           │
│  │ Date | Spain | EU | US | YoY Change          │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Shiny Components

### UI Elements

| Component | Shiny Function | Usage |
|-----------|----------------|-------|
| KPI Cards | `ui.value_box()` | Display key metrics with trends |
| Navigation | `ui.navset_tab()` | Main section navigation |
| Filters | `ui.input_select()`, `ui.input_date_range()` | User inputs |
| Charts | `output_widget()` (Plotly) | Interactive visualizations |
| Tables | `ui.output_data_frame()` | Data display |
| Layout | `ui.layout_columns()`, `ui.card()` | Page structure |

### Reactive Components

| Element | Trigger | Action |
|---------|---------|--------|
| Country selector | User selection | Filter data, update charts |
| Date range | User selection | Filter time series |
| Refresh button | User click | Fetch latest data from APIs |

---

## Visual Design

### Color Scheme

| Element | Color | Usage |
|---------|-------|-------|
| Positive trend | Green (#28a745) | Increases (when positive is good) |
| Negative trend | Red (#dc3545) | Decreases (when negative is bad) |
| Neutral | Gray (#6c757d) | No change |
| Primary accent | Blue (#007bff) | Headers, links |
| Background | Light gray (#f8f9fa) | Page background |

### Chart Styling

- Use consistent color palette across all charts
- Spain: Blue (#1f77b4)
- EU: Orange (#ff7f0e)
- US: Green (#2ca02c)
- Include gridlines for readability
- Show tooltips on hover with detailed values

### Typography

- Headers: Bold, larger font
- KPI values: Large, prominent numbers
- Trend indicators: Color-coded with arrows (▲ ▼)
- Data labels: Clear, readable font size

---

## Responsive Behavior

| Screen Size | Layout Adjustment |
|-------------|-------------------|
| Desktop (>1200px) | Full multi-column layout |
| Tablet (768-1200px) | 2-column layout |
| Mobile (<768px) | Single column, stacked cards |

Use `ui.layout_columns(col_widths={"sm": 12, "md": 6, "lg": 4})` for responsive grids.
