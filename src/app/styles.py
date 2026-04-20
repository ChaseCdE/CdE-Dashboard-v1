"""
Custom CSS styles for the dashboard.
Aligned with the CdE corporate website dark navy/slate theme.
"""

CUSTOM_CSS = """
<style>
/* Global Styles */
:root {
    --primary-color: #1e2d3d;
    --primary-light: #2a3f55;
    --secondary-color: #4a7c9b;
    --accent-color: #5b8a9a;
    --success-color: #2d8659;
    --danger-color: #b94a48;
    --warning-color: #c9943e;
    --light-bg: #f4f6f8;
    --card-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    --border-radius: 8px;
    --grid-color: #d1d5db;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e5e7eb;
}

body {
    background-color: var(--light-bg) !important;
    font-family: Arial, Helvetica, sans-serif;
    color: var(--text-primary);
}

/* Navbar Styling */
.navbar {
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.15);
}

.navbar-brand {
    font-weight: 700 !important;
    font-size: 1.3rem !important;
    letter-spacing: 0.25px;
}

/* Card Improvements */
.card {
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--card-shadow) !important;
    transition: box-shadow 0.2s ease;
}

.card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.card-header {
    background-color: transparent !important;
    border-bottom: 1px solid var(--border-color) !important;
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 600;
    color: var(--primary-color);
    padding: 0.875rem 1.25rem !important;
    font-size: 0.95rem;
}

/* Value Box Improvements */
.bslib-value-box {
    border-radius: var(--border-radius) !important;
    overflow: hidden;
}

.bslib-value-box .value-box-value {
    font-size: 2rem !important;
    font-weight: 700 !important;
}

.bslib-value-box .value-box-title {
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.85;
}

/* Section Headers */
.section-header {
    color: var(--primary-color);
    font-weight: 700;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent-color);
    display: inline-block;
}

.section-description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}

/* KPI Summary Cards */
.kpi-card {
    background: #ffffff;
    padding: 1.25rem;
    border-radius: var(--border-radius);
    border: 1px solid var(--border-color);
    box-shadow: var(--card-shadow);
}

.kpi-value {
    font-size: 2.25rem;
    font-weight: 700;
    color: var(--primary-color);
    line-height: 1.2;
}

.kpi-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

.kpi-change {
    font-size: 0.9rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 4px;
}

.kpi-change.positive {
    background-color: rgba(45, 134, 89, 0.08);
    color: var(--success-color);
}

.kpi-change.negative {
    background-color: rgba(185, 74, 72, 0.08);
    color: var(--danger-color);
}

.kpi-change.neutral {
    background-color: rgba(100, 116, 139, 0.08);
    color: var(--text-secondary);
}

/* Data Period Badge */
.data-period {
    font-size: 0.7rem;
    color: var(--text-secondary);
    background-color: #f1f3f5;
    padding: 2px 6px;
    border-radius: 3px;
    display: inline-block;
    margin-top: 0.5rem;
}

/* Filter Controls */
.filter-section {
    background-color: #fff;
    padding: 0.875rem 1.25rem;
    border-radius: var(--border-radius);
    margin-bottom: 1.5rem;
    border: 1px solid var(--border-color);
}

.filter-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

/* Data Table Styling */
.dataframe {
    font-size: 0.85rem;
}

.dataframe th {
    background-color: var(--primary-color) !important;
    color: white !important;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
}

/* Footer */
.dashboard-footer {
    background-color: var(--primary-color);
    border-top: none;
    padding: 1.25rem;
    margin-top: 3rem;
    text-align: center;
}

.dashboard-footer p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.8rem;
}

.dashboard-footer strong {
    color: #ffffff;
}

/* Last Updated Badge */
.last-updated {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background-color: rgba(91, 138, 154, 0.1);
    color: var(--primary-color);
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
}

.last-updated::before {
    content: "●";
    color: var(--success-color);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .kpi-value {
        font-size: 1.6rem;
    }

    .section-header {
        font-size: 1.25rem;
    }
}

/* ============================================
   RESUMEN TAB - OVERVIEW STYLES
   ============================================ */

/* Economic Pulse / Health Section */
.economic-pulse {
    background: linear-gradient(135deg, #1e2d3d 0%, #2a3f55 100%);
    border-radius: var(--border-radius);
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    color: white;
}

.economic-pulse h3 {
    margin: 0 0 0.5rem 0;
    font-size: 0.85rem;
    font-weight: 600;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.pulse-headline {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 1rem;
    line-height: 1.3;
}

.pulse-indicators {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
    margin-top: 1.25rem;
}

.pulse-indicator {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.pulse-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

.pulse-dot.positive { background-color: #4ade80; box-shadow: 0 0 6px rgba(74, 222, 128, 0.5); }
.pulse-dot.warning { background-color: #fbbf24; box-shadow: 0 0 6px rgba(251, 191, 36, 0.5); }
.pulse-dot.negative { background-color: #f87171; box-shadow: 0 0 6px rgba(248, 113, 113, 0.5); }
.pulse-dot.neutral { background-color: #94a3b8; }

.pulse-label {
    font-size: 0.85rem;
    opacity: 0.8;
}

.pulse-value {
    font-weight: 700;
    margin-left: 0.25rem;
}

/* Executive Summary */
.executive-summary {
    background: #fff;
    border-left: 3px solid var(--accent-color);
    padding: 1.25rem 1.5rem;
    margin-bottom: 2rem;
    border-radius: 0 var(--border-radius) var(--border-radius) 0;
    border: 1px solid var(--border-color);
    border-left: 3px solid var(--accent-color);
}

.executive-summary h4 {
    margin: 0 0 1rem 0;
    color: var(--primary-color);
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.summary-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.summary-list li {
    padding: 0.5rem 0;
    padding-left: 1.5rem;
    position: relative;
    color: var(--text-primary);
    font-size: 0.9rem;
    line-height: 1.5;
    border-bottom: 1px solid #f1f5f9;
}

.summary-list li:last-child {
    border-bottom: none;
}

.summary-list li::before {
    content: "—";
    position: absolute;
    left: 0;
    color: var(--accent-color);
    font-weight: bold;
}

.summary-highlight {
    font-weight: 600;
    color: var(--primary-color);
}

.summary-positive { color: var(--success-color); }
.summary-negative { color: var(--danger-color); }

/* Themed Section Headers */
.theme-section {
    margin-bottom: 2rem;
}

.theme-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-color);
}

.theme-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
}

.theme-icon.growth { background: rgba(45, 134, 89, 0.12); color: var(--success-color); }
.theme-icon.labor { background: rgba(74, 124, 155, 0.12); color: var(--secondary-color); }
.theme-icon.prices { background: rgba(185, 74, 72, 0.12); color: var(--danger-color); }
.theme-icon.financial { background: rgba(107, 91, 138, 0.12); color: #6b5b8a; }
.theme-icon.external { background: rgba(201, 148, 62, 0.12); color: var(--warning-color); }

.theme-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0;
}

/* Spain vs EU Comparison Card */
.comparison-snapshot {
    background: #ffffff;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.comparison-snapshot h4 {
    margin: 0 0 1.25rem 0;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
}

.comparison-item {
    background: var(--light-bg);
    padding: 1rem;
    border-radius: 6px;
    border: 1px solid var(--border-color);
}

.comparison-metric {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

.comparison-values {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.comparison-spain {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--primary-color);
}

.comparison-eu {
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.comparison-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 600;
}

.comparison-badge.above { background: rgba(185, 74, 72, 0.08); color: var(--danger-color); }
.comparison-badge.below { background: rgba(45, 134, 89, 0.08); color: var(--success-color); }
.comparison-badge.inline { background: rgba(100, 116, 139, 0.08); color: var(--text-secondary); }

/* Enhanced KPI Cards for Overview */
.kpi-card-enhanced {
    background: white;
    padding: 1.25rem;
    border-radius: var(--border-radius);
    border: 1px solid var(--border-color);
    box-shadow: var(--card-shadow);
    border-left: 3px solid var(--primary-color);
}

.kpi-card-enhanced:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.kpi-card-enhanced.growth { border-left-color: var(--success-color); }
.kpi-card-enhanced.labor { border-left-color: var(--secondary-color); }
.kpi-card-enhanced.prices { border-left-color: var(--danger-color); }
.kpi-card-enhanced.financial { border-left-color: #6b5b8a; }

.kpi-mini-chart {
    height: 40px;
    margin-top: 0.75rem;
    opacity: 0.7;
}

/* Data freshness indicator */
.freshness-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 3px;
    background: #f1f5f9;
    color: var(--text-secondary);
}

.freshness-badge.fresh {
    background: rgba(45, 134, 89, 0.08);
    color: var(--success-color);
}

.freshness-badge.recent {
    background: rgba(201, 148, 62, 0.08);
    color: var(--warning-color);
}

/* Chart annotations */
.chart-annotation {
    background: rgba(91, 138, 154, 0.06);
    border-left: 2px solid var(--accent-color);
    padding: 0.625rem 0.875rem;
    margin-top: 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    border-radius: 0 6px 6px 0;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .economic-pulse {
        padding: 1rem 1.25rem;
    }

    .pulse-headline {
        font-size: 1.2rem;
    }

    .pulse-indicators {
        flex-direction: column;
        gap: 1rem;
    }

    .comparison-grid {
        grid-template-columns: 1fr 1fr;
    }

    .executive-summary {
        padding: 1rem;
    }
}

@media (max-width: 480px) {
    .comparison-grid {
        grid-template-columns: 1fr;
    }
}

/* Chart title */
.chart-title {
    margin: 0 0 0.75rem 0 !important;
    font-size: 1rem;
    font-weight: 700;
    color: var(--primary-color);
}

/* Toggle button group
   Shiny renders: label.radio-inline > input[type=radio] + span
   So we style the label itself, and use :has(input:checked) for active state. */
.toggle-btn-group {
    margin-bottom: 1.25rem;
}

.toggle-btn-group .shiny-options-group {
    display: inline-flex;
    gap: 8px;
}

.toggle-btn-group label.radio-inline {
    margin: 0 !important;
    padding: 7px 20px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
    border-radius: 6px;
    transition: background 0.15s, color 0.15s;
    /* Unselected: white bg, dark text, visible outline */
    background: #fff;
    color: var(--primary-color);
    border: 1.5px solid var(--primary-color);
}

.toggle-btn-group label.radio-inline input[type="radio"] {
    /* Hide the radio circle */
    display: none;
}

.toggle-btn-group label.radio-inline:hover {
    background: var(--light-bg);
}

/* Selected state: dark bg, white text */
.toggle-btn-group label.radio-inline:has(input:checked) {
    background: var(--primary-color);
    color: #fff;
    border-color: var(--primary-color);
}

/* No-data placeholder */
.no-data-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: #94a3b8;
    font-size: 1rem;
    background: var(--light-bg);
    border-radius: 6px;
    border: 1px dashed var(--border-color);
}
</style>
"""
