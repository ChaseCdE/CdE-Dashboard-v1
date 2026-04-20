"""
Shared helper functions for dashboard page modules.

Extracted from app.py to allow reuse across page modules without
duplicating KPI card builders or filter logic.
"""

import logging

import pandas as pd
from shiny import ui

from data import (
    INDICATORS,
    YAHOO_INDICATORS,
    BDE_INDICATORS,
    get_latest_value,
)
from charts import format_trend_indicator, create_sparkline, COLORS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# KPI card builders
# ---------------------------------------------------------------------------

def create_kpi_card(indicator_key: str, data: dict, show_sparkline: bool = True) -> ui.Tag:
    """Create an enhanced KPI card with sparkline."""
    meta = INDICATORS.get(indicator_key)
    if meta is None:
        return ui.div(ui.div(indicator_key, class_="kpi-label"),
                      ui.div("Config error", class_="kpi-value"), class_="kpi-card")

    df = data.get(indicator_key, pd.DataFrame())

    if df.empty:
        return ui.div(
            ui.div(meta["name"], class_="kpi-label"),
            ui.div("No data", class_="kpi-value"),
            class_="kpi-card",
        )

    latest = get_latest_value(df, meta["value_col"])
    value = latest["value"]
    yoy = latest["yoy_change"]
    date = latest["date"]

    # Format value based on unit
    if meta["unit"] == "%":
        value_str = f"{value:.1f}%"
    else:
        value_str = f"{value:.1f}"

    # Get trend indicator
    arrow, css_class, color = format_trend_indicator(yoy, meta.get("positive_is_good"))
    yoy_str = f"{arrow} {abs(yoy):.1f}%" if pd.notna(yoy) else ""

    # Format date
    if pd.notna(date) and hasattr(date, 'strftime'):
        date_str = date.strftime("%b %Y")
    else:
        date_str = str(date)[:10] if date and pd.notna(date) else ""

    # Create sparkline for last 8 periods
    sparkline_widget = None
    if show_sparkline and len(df) >= 4:
        sparkline_fig = create_sparkline(df.tail(12), meta["value_col"], color=COLORS["spain"])
        sparkline_widget = ui.output_ui(f"spark_{indicator_key}", height="50px")

    return ui.div(
        ui.div(meta["name"], class_="kpi-label"),
        ui.div(value_str, class_="kpi-value"),
        ui.div(
            ui.span(yoy_str, class_=f"kpi-change {css_class}"),
            " interanual" if yoy_str else "",
            style="font-size: 0.85rem; color: #6c757d;",
        ) if yoy_str else None,
        ui.div(date_str, class_="data-period"),
        sparkline_widget,
        class_="kpi-card",
    )


def create_market_kpi_card(indicator_key: str, data: dict, show_change: str = "1d") -> ui.Tag:
    """Create a KPI card for financial market indicators."""
    meta = YAHOO_INDICATORS.get(indicator_key, {})
    df = data.get(indicator_key, pd.DataFrame())

    if df.empty or not meta:
        return ui.div(
            ui.div(meta.get("name", indicator_key), class_="kpi-label"),
            ui.div("No data", class_="kpi-value"),
            class_="kpi-card",
        )

    # Filter out NaT dates and sort by date to ensure clean data
    df = df[df["date"].notna()].sort_values("date")
    if df.empty:
        return ui.div(
            ui.div(meta.get("name", indicator_key), class_="kpi-label"),
            ui.div("No data", class_="kpi-value"),
            class_="kpi-card",
        )

    latest = df.iloc[-1]
    value = latest.get("Close")
    date = latest.get("date")

    # Format value based on type
    if meta.get("category") == "currencies":
        value_str = f"{value:.4f}" if pd.notna(value) else "-"
    elif value and value > 1000:
        value_str = f"{value:,.0f}"
    else:
        value_str = f"{value:.2f}" if pd.notna(value) else "-"

    # Get change based on selected period
    change_col_map = {
        "1d": "daily_return_pct",
        "1w": "return_1w_pct",
        "1m": "return_1m_pct",
        "ytd": "ytd_return_pct",
    }
    change_col = change_col_map.get(show_change, "daily_return_pct")
    change = latest.get(change_col)

    # Get trend indicator
    positive_is_good = meta.get("positive_is_good", True)
    arrow, css_class, color = format_trend_indicator(change, positive_is_good)
    change_str = f"{arrow} {abs(change):.2f}%" if pd.notna(change) else ""

    # Format date
    if pd.notna(date) and hasattr(date, 'strftime'):
        date_str = date.strftime("%d %b %Y")
    else:
        date_str = str(date)[:10] if date and pd.notna(date) else ""

    return ui.div(
        ui.div(meta.get("name", indicator_key), class_="kpi-label"),
        ui.div(value_str, class_="kpi-value"),
        ui.div(
            ui.span(change_str, class_=f"kpi-change {css_class}"),
            f" ({show_change})" if change_str else "",
            style="font-size: 0.85rem; color: #6c757d;",
        ) if change_str else None,
        ui.div(date_str, class_="data-period"),
        class_="kpi-card",
    )


def create_bde_kpi_card(indicator_key: str, data: dict) -> ui.Tag:
    """Create a KPI card for BdE indicators."""
    meta = BDE_INDICATORS.get(indicator_key, {})
    df = data.get(indicator_key, pd.DataFrame())

    if df.empty or not meta:
        return ui.div(
            ui.div(meta.get("name", indicator_key), class_="kpi-label"),
            ui.div("Sin datos", class_="kpi-value"),
            class_="kpi-card",
        )

    # Filter out NaT dates and sort by date to ensure clean data
    df = df[df["date"].notna()].sort_values("date")
    if df.empty:
        return ui.div(
            ui.div(meta.get("name", indicator_key), class_="kpi-label"),
            ui.div("Sin datos", class_="kpi-value"),
            class_="kpi-card",
        )

    latest = df.iloc[-1]
    value = latest.get("value")
    change = latest.get("change_pct") or latest.get("yoy_change_pct")
    date = latest.get("date")

    # Format value based on unit
    unit = meta.get("unit", "")
    if unit == "%":
        value_str = f"{value:.2f}%" if pd.notna(value) else "-"
    elif unit in ["M EUR", "Billions EUR"]:
        value_str = f"{value:,.0f}" if pd.notna(value) else "-"
    else:
        value_str = f"{value:.2f}" if pd.notna(value) else "-"

    # Get trend indicator
    positive_is_good = meta.get("positive_is_good")
    arrow, css_class, color = format_trend_indicator(change, positive_is_good)
    change_str = f"{arrow} {abs(change):.1f}%" if pd.notna(change) else ""

    # Format date
    if pd.notna(date) and hasattr(date, 'strftime'):
        date_str = date.strftime("%b %Y")
    else:
        date_str = str(date)[:10] if date and pd.notna(date) else ""

    return ui.div(
        ui.div(meta.get("name", indicator_key), class_="kpi-label"),
        ui.div(value_str, class_="kpi-value"),
        ui.div(
            ui.span(change_str, class_=f"kpi-change {css_class}"),
            " var." if change_str else "",
            style="font-size: 0.85rem; color: #6c757d;",
        ) if change_str else None,
        ui.div(date_str, class_="data-period"),
        class_="kpi-card",
    )


# ---------------------------------------------------------------------------
# Period filter helpers
# ---------------------------------------------------------------------------

def filter_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filter data by standard period (all / 5y / 3y / 1y)."""
    if df.empty or period == "all":
        return df
    now = pd.Timestamp.now()
    years = {"5y": 5, "3y": 3, "1y": 1}.get(period, 5)
    cutoff = now - pd.DateOffset(years=years)
    return df[df["date"] >= cutoff]


def filter_market_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filter market data with more granular options (1y / 6m / 3m / 1m)."""
    if df.empty or period == "all":
        return df
    now = pd.Timestamp.now()
    offsets = {
        "1y": pd.DateOffset(years=1),
        "6m": pd.DateOffset(months=6),
        "3m": pd.DateOffset(months=3),
        "1m": pd.DateOffset(months=1),
    }
    cutoff = now - offsets.get(period, pd.DateOffset(years=1))
    return df[df["date"] >= cutoff]


def filter_credit_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filter credit data by period (all / 5y / 3y / 1y)."""
    if df.empty or period == "all":
        return df
    now = pd.Timestamp.now()
    years = {"5y": 5, "3y": 3, "1y": 1}.get(period, 5)
    cutoff = now - pd.DateOffset(years=years)
    return df[df["date"] >= cutoff]


# ---------------------------------------------------------------------------
# Safe chart render wrapper
# ---------------------------------------------------------------------------

def safe_render_chart(chart_fn, *args, fallback_msg="Datos no disponibles", **kwargs):
    """Call a chart function wrapped in try/except.

    Returns a Shiny HTML element with the Plotly chart, or a styled
    placeholder if the chart fails to render.
    """
    try:
        fig = chart_fn(*args, **kwargs)
        if fig is None:
            return ui.div(fallback_msg, class_="no-data-placeholder")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    except Exception as e:
        logger.warning("Chart render failed (%s): %s", chart_fn.__name__, e)
        return ui.div(fallback_msg, class_="no-data-placeholder")
