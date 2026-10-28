# Style guide: "La economía en datos"

Applies to every page and chart of the static site. The CSS tokens live in `site/assets/css/main.css` (`:root`), the chart palette in `site/assets/js/config.js`. The old Shiny palette (`#1e2d3d`, `#4a7c9b`, ...) is superseded.

## Serving

Serve `site/` with any static server (`python -m http.server` from `site/`, GitHub Pages, Cloudflare Pages). All URLs are relative or derived from `import.meta.url`, so the site works under a sub-path (`/<repo>/`). **`file://` is not supported**: browsers block `fetch` of the JSON files and ES modules from `file://`.

## Palette

| Token | Hex | Use | Contrast on white |
|---|---|---|---|
| `--navy` / `COLORS.navy` | `#16254D` | Brand, Spain series, headings, header/footer | 14.9:1 |
| `--beige` / `COLORS.beige` | `#C2AE93` | Brand accent, EU-27 series, rules, active nav | 2.2:1 (see note) |
| `--ink` | `#1B2236` | Body text | 16:1 |
| `--ink-soft` | `#4B5563` | Secondary text, axis labels | 7.6:1 |
| `--muted` | `#6B7280` | Captions, sources | 4.8:1 |
| `--line` / `COLORS.grid` | `#E3DED5` / `#E6E2DA` | Borders, gridlines | decorative |
| `--bg` | `#F8F6F2` | Page background (cards are white) | |
| `--positive` | `#2E7D5B` | Positive sign (bars, deltas) | 5.0:1 |
| `--negative` | `#B03A2E` | Negative sign | 6.0:1 |
| `--warn-bg` / `--warn-ink` | `#FBF1DC` / `#7A4B00` | "Desactualizado" badge | 6.6:1 |

Categorical cycle for charts (`CYCLE`): navy, beige, then teal `#1F7A8C` (5.0), terracotta `#B5532E` (5.0), plum `#7A4E7E` (6.5), moss `#5F7F3A` (4.6), steel blue `#4F86B5` (3.9), ochre `#A8741A` (4.1). Semantic assignment: `es` = navy, `eu27` = beige; the other series take the cycle in order, skipping colours already used.

Note on beige: the brand beige is below 3:1 on white. It is kept for EU-27 as specified. Mitigations: lines are 2.5 px, the series is always named in the legend and with an end label, and hover shows the name. If the project lead prefers strict AA for graphics, change `COLORS.beige` usage for lines to `#8C7753` (4.1:1) in `config.js` only.

Sign colouring: `colorBySign: true` uses positive/negative green/red (when positive is "good" or neutral reading is not needed); `colorBySign: 'neutral'` uses navy for >= 0 and beige for < 0 (use for inflation, rates, anything where up is not good or bad). Never rely on colour alone: values are labelled and tables carry the sign.

## Typography

- Headings and card titles: **Source Serif 4** (600/700), Google Fonts, `font-display: swap`.
- Body, UI, charts: **Source Sans 3** (400/600/700), with tabular numerals for figures.
- System fallbacks: `system-ui, -apple-system, 'Segoe UI', Roboto, Arial` (sans), `Georgia` (serif).
- Scale: h1 1.75 rem, h2 1.3 rem, card title 1.05 rem, body 1 rem, captions 0.8125 to 0.875 rem. Minimum text size 13 px (chart ticks 12 px).

## Spacing and layout

- 4 px base unit (`--space-1..7` = 4, 8, 12, 16, 24, 32, 48 px). Side gutter 16 px at every width; content max width 1200 px.
- Cards: white, 1 px `--line` border, 6 px radius, no shadow, 16 px padding.
- Grids: `.grid.grid-2 / .grid-3 / .grid-4` collapse to one column under 720 px; KPI grid is 2 columns on phones, 4 from 720 px.
- Header: navy, logo (white outlined PNG), title, nav. Under 860 px the nav collapses behind a 44 px menu button. Footer: navy, sources, Círculo link, data date.
- Breakpoints checked: 375, 768, 1440 px. No horizontal page scroll; tables scroll inside `.table-wrap`.

## Chart rules

1. Always build charts with `charts.js`; pages never pass Plotly options.
2. **Title is a sentence** that says what the chart shows ("Inflación armonizada: España frente a la UE-27"). Never "Gráfico 3". A claim that depends on the data (for example "la inflación sube") must not be typed by hand.
3. **Units in the subtitle** (taken from the field: label, unit, `note_es`), not in the axis title. Axis ticks carry only a short suffix (`%`).
4. **Source line always**: "Fuente: <name> (link) · Último dato: sep 2026", generated from the JSON. A "Desactualizado" badge appears when the last observation is older than the contract thresholds (D 7, W 21, M 100, Q 200, A 550 days, measured against `generated_at`).
5. Bars start at zero; line charts may use a non-zero baseline. A zero line is drawn for growth rates and pp.
6. No 3D, no dual axes (if unavoidable, use two charts), no gradients, no decorative colour. No Plotly logo or modebar; dragging and zoom are off so touch scrolling is not hijacked. Use the 1A / 5A / Máx buttons for windows.
7. Maximum 6 series per chart; beyond that use a table or small multiples.
8. Reference lines (2 % ECB target, 100 = base) are dotted grey with a label.
9. Rebasing to 100 is display-only (`rebasedComparison`, base = start of the visible window). Any other index base is a pipeline field.
10. The frontend must not compute economic quantities (growth rates, contributions, differences between series, YTD, averages). Request a field from the pipeline instead.

## Number and date format (es-ES)

Decimal comma, thousands dot from 4 digits ("19.160,6", "1.234 M€"), non-breaking space before units. `pct` "12,3 %", `pct_change` "+2,9 %", `pp` "+0,4 p. p.", currency with scale "1.234 M€", persons "21,9 M personas". Periods: D "26 oct 2026", M "sep 2026", Q "T2 2026", A "2025". Month names lowercase abbreviated. Implemented once in `format.js`.

## Accessibility

`lang="es"`; skip link; one `h1` per page; keyboard-navigable nav with visible focus ring (3 px navy, beige on navy); `aria-current="page"`, `aria-expanded` on the menu button, `aria-pressed` on range buttons; chart bodies have `role="img"` with an `aria-label` (title, subtitle, last date); error and empty states are visible text; KPI deltas include "sube/baja" for screen readers and an arrow, not colour alone. Text contrast is AA (4.5:1) or better; chart lines are 3:1 or better except the beige note above.
