// Single source of truth for chart colours, fonts, sizes and contract thresholds.
// CSS colours live in assets/css/main.css as custom properties; keep both in sync
// (docs/style-guide.md lists them side by side).

// All URLs are derived from this file's own location so the site works under any
// sub-path (GitHub Pages serves at /<repo>/) and from pages at any depth.
const JS_URL = new URL('.', import.meta.url);
export const SITE_ROOT = new URL('../../', JS_URL).href;      // .../site/
export const DATA_ROOT = new URL('data/', SITE_ROOT).href;    // .../site/data/
export const IMG_ROOT = new URL('assets/img/', SITE_ROOT).href;

export const SUPPORTED_CONTRACT_MAJOR = '1';

// Plotly is loaded lazily by charts.js from cdnjs, pinned to an exact version.
export const PLOTLY = {
  version: '3.1.0',
  js: 'https://cdnjs.cloudflare.com/ajax/libs/plotly.js/3.1.0/plotly-basic.min.js',
  jsIntegrity: 'sha384-7U7ehGKdL5gsFu89O1kYrHLPKpTf6BJ1bIe+nke+R5+CpdiuJCH2K/TG9JuNqq5l',
  localeEs: 'https://cdnjs.cloudflare.com/ajax/libs/plotly.js/3.1.0/plotly-locale-es.min.js',
  localeEsIntegrity: 'sha384-+4A4lhfEFxK+um6pMS4oOme9iPpDoBWjqJydFJeUNUA85chLZPZ5GEHaDj8bHre6',
  localeName: 'es-cde',
};

export const COLORS = {
  navy: '#16254D',
  beige: '#C2AE93',
  ink: '#1B2236',          // body text
  inkSoft: '#4B5563',      // secondary text, axis labels (7.5:1 on white)
  muted: '#6B7280',        // captions (4.8:1 on white)
  grid: '#E6E2DA',
  axis: '#B9B2A5',
  zero: '#8C8575',
  paper: '#FFFFFF',
  positive: '#2E7D5B',
  negative: '#B03A2E',
  neutralUp: '#16254D',    // 'neutral' sign colouring: >= 0
  neutralDown: '#C2AE93',  // 'neutral' sign colouring: < 0
};

// Series colours by meaning first, then a categorical cycle.
export const SERIES_COLORS = {
  es: COLORS.navy,
  eu27: COLORS.beige,
};

// Further categorical colours (contrast on white >= 3.9:1, see style guide).
export const CATEGORICAL = [
  '#1F7A8C', // teal
  '#B5532E', // terracotta
  '#7A4E7E', // plum
  '#5F7F3A', // moss
  '#4F86B5', // steel blue
  '#A8741A', // ochre
];

// Full cycle used when a chart has no semantic colours: navy, beige, then the rest.
export const CYCLE = [COLORS.navy, COLORS.beige, ...CATEGORICAL];

export const FONT = {
  family: "Arial, 'Helvetica Neue', Helvetica, 'Liberation Sans', sans-serif",
  size: 13,
  titleSize: 15,
};

export const CHART = {
  height: 360,
  heightSmall: 280,
  lineWidth: 2.5,
  barGap: 0.25,
  defaultRange: 'max',
  ranges: [
    { id: '1A', label: '1A', years: 1 },
    { id: '5A', label: '5A', years: 5 },
    { id: 'max', label: 'Máx', years: null },
  ],
};

// Staleness thresholds in days, counted from the END of the last period (docs/data-contract.md v1.1, "Validation").
export const STALE_DAYS = { D: 7, W: 21, M: 100, Q: 200, A: 550 };
