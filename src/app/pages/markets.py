"""Financial Markets (Mercados) page module."""

import pandas as pd
from shiny import ui, render, reactive

from charts import (
    create_stock_index_chart,
    create_multi_index_comparison,
    create_volatility_chart,
    COLORS,
    MARKET_COLORS,
    COMMON_LAYOUT,
)
from helpers import filter_market_by_period
import plotly.graph_objects as go


# Index display names
INDEX_NAMES = {
    "ibex_35": "IBEX 35",
    "sp_500": "S&P 500",
    "nasdaq_composite": "Nasdaq",
    "euro_stoxx_50": "Euro Stoxx 50",
    "dax": "DAX",
}

# Spanish month names
MESES = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
         7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"}


def _build_single_index_chart(df, index_key, show_sma_200=True):
    """Build a single index chart with 200-day moving average, from Jan 2022."""
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Filter from January 2022
    df = df[df["date"] >= "2022-01-01"].copy()

    if df.empty:
        return None

    # Create Spanish formatted date for hover
    df["date_es"] = df["date"].apply(
        lambda d: f"{d.day} {MESES.get(d.month, '')} {d.year}"
    )

    x_dates = df["date"].astype(str).tolist()
    color = MARKET_COLORS.get(index_key, COLORS["spain"])
    name = INDEX_NAMES.get(index_key, index_key)

    fig = go.Figure()

    # Main price line
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df["Close"],
            mode="lines",
            name=name,
            line=dict(color=color, width=2.5),
            customdata=df["date_es"],
            hovertemplate=f"<b>{name}</b><br>%{{customdata}}<br>Cierre: %{{y:,.2f}}<extra></extra>",
        )
    )

    # 200-day moving average
    if show_sma_200 and "sma_200" in df.columns and df["sma_200"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df["sma_200"],
                mode="lines",
                name="Media Móvil 200d",
                line=dict(color=COLORS["neutral"], width=1.5, dash="dash"),
                customdata=df["date_es"],
                hovertemplate="MM 200d: %{y:,.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
            tickformat=",",
        ),
        margin=dict(l=60, r=30, t=30, b=40),
        height=400,
    )

    return fig


def _build_comparison_chart(data, period):
    """Build comparison chart for indices normalized to 100."""
    indices = ["ibex_35", "euro_stoxx_50", "sp_500", "nasdaq_composite", "dax"]

    # Filter data based on period
    filtered_data = {}
    for key in indices:
        df = data.get(key, pd.DataFrame())
        if not df.empty:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            filtered_data[key] = filter_market_by_period(df, period)

    fig = go.Figure()

    for key in indices:
        df = filtered_data.get(key)
        if df is None or df.empty:
            continue

        df_norm = df.copy()
        first_val = df_norm["Close"].iloc[0]
        if pd.isna(first_val) or first_val == 0:
            continue
        df_norm["normalized"] = (df_norm["Close"] / first_val) * 100

        # Create Spanish formatted date for hover
        df_norm["date_es"] = df_norm["date"].apply(
            lambda d: f"{d.day} {MESES.get(d.month, '')} {d.year}"
        )

        x_dates = df_norm["date"].astype(str).tolist()
        color = MARKET_COLORS.get(key, COLORS["neutral"])
        name = INDEX_NAMES.get(key, key)

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df_norm["normalized"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
                customdata=df_norm["date_es"],
                hovertemplate=f"<b>{name}</b><br>%{{customdata}}<br>Índice: %{{y:.1f}}<extra></extra>",
            )
        )

    # Add 100 baseline
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color=COLORS["neutral"],
        line_width=1,
        annotation_text="Base = 100",
        annotation_position="right",
        annotation_font_size=10,
    )

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        margin=dict(l=50, r=30, t=30, b=40),
        height=400,
    )

    return fig


# Interest rate indicator display names
RATE_NAMES = {
    "ester_daily": "€STR (overnight)",
    "euribor_3m_daily": "Euribor 3M",
    "euribor_12m_daily": "Euribor 12M",
    "spain_5y_bond": "España 5Y",
    "spain_10y_bond": "España 10Y",
    "us_treasury_5y": "US Treasury 5Y",
    "us_treasury_10y": "US Treasury 10Y",
}


def _calculate_bp_change(df, days=None, ytd=False):
    """Calculate change in basis points (1bp = 0.01%)."""
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    # Normalize timezone - remove timezone info for consistent comparisons
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_localize(None)
    df = df.sort_values("date")

    # Get value column (could be 'value' for BDE or 'Close' for Yahoo)
    value_col = "value" if "value" in df.columns else "Close"
    if value_col not in df.columns:
        return None

    current_val = df[value_col].iloc[-1]
    max_date = df["date"].max()

    if ytd:
        # YTD: compare to last value of previous year
        start_of_year = pd.Timestamp(max_date.year, 1, 1)
        past_df = df[df["date"] < start_of_year]
        if past_df.empty:
            return None
        past_val = past_df[value_col].iloc[-1]
    else:
        # Days-based comparison
        target_date = max_date - pd.Timedelta(days=days)
        past_df = df[df["date"] <= target_date]
        if past_df.empty:
            return None
        past_val = past_df[value_col].iloc[-1]

    if pd.isna(current_val) or pd.isna(past_val):
        return None

    # Change in basis points (values are already in %)
    return (current_val - past_val) * 100


def _build_interest_rates_table_html(bde_data, yahoo_data):
    """Build HTML table with interest rates and changes in basis points."""
    # Define indicators: (key, source)
    indicators = [
        ("ester_daily", "bde"),
        ("euribor_3m_daily", "bde"),
        ("euribor_12m_daily", "bde"),
        ("spain_5y_bond", "bde"),
        ("spain_10y_bond", "bde"),
        ("us_treasury_5y", "yahoo"),
        ("us_treasury_10y", "yahoo"),
    ]

    rows = []
    for key, source in indicators:
        data = bde_data if source == "bde" else yahoo_data
        df = data.get(key, pd.DataFrame())
        if df.empty:
            continue

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Get current value
        value_col = "value" if "value" in df.columns else "Close"
        if value_col not in df.columns:
            continue

        current = df[value_col].iloc[-1]
        name = RATE_NAMES.get(key, key)

        # Calculate changes in basis points
        change_30d = _calculate_bp_change(df, days=30)
        change_ytd = _calculate_bp_change(df, ytd=True)
        change_1y = _calculate_bp_change(df, days=365)

        rows.append({
            "name": name,
            "current": current,
            "change_30d": change_30d,
            "change_ytd": change_ytd,
            "change_1y": change_1y,
        })

    if not rows:
        return "<p>No hay datos disponibles</p>"

    def format_rate(val):
        if val is None or pd.isna(val):
            return "-"
        return f"{val:.2f}%"

    def format_bp(val):
        if val is None or pd.isna(val):
            return "-"
        return f"{val:+.0f} pb"

    def get_color_style(val):
        if val is None or pd.isna(val):
            return ""
        if val > 0:
            return "color: #b94a48;"  # red for rate increases
        elif val < 0:
            return "color: #2d8659;"  # green for rate decreases
        return ""

    html = """
    <table class="rates-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead>
            <tr style="border-bottom: 2px solid #dee2e6; text-align: right;">
                <th style="text-align: left; padding: 8px 4px;">Indicador</th>
                <th style="padding: 8px 4px;">Actual</th>
                <th style="padding: 8px 4px;">30 días</th>
                <th style="padding: 8px 4px;">YTD</th>
                <th style="padding: 8px 4px;">1 año</th>
            </tr>
        </thead>
        <tbody>
    """

    for row in rows:
        html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="text-align: left; padding: 10px 4px; font-weight: 600;">{row['name']}</td>
                <td style="text-align: right; padding: 10px 4px;">{format_rate(row['current'])}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_style(row['change_30d'])}">{format_bp(row['change_30d'])}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_style(row['change_ytd'])}">{format_bp(row['change_ytd'])}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_style(row['change_1y'])}">{format_bp(row['change_1y'])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html


def _build_euribor_chart(bde_data, period="2y"):
    """Build chart showing €STR, Euribor 3M and Euribor 12M."""
    indicators = [
        ("ester_daily", "€STR", "#1e2d3d"),
        ("euribor_3m_daily", "Euribor 3M", "#3d6b8e"),
        ("euribor_12m_daily", "Euribor 12M", "#2d8659"),
    ]

    fig = go.Figure()

    for key, name, color in indicators:
        df = bde_data.get(key, pd.DataFrame())
        if df.empty:
            continue

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Filter by period
        max_date = df["date"].max()
        if period == "1y":
            df = df[df["date"] >= max_date - pd.DateOffset(years=1)]
        elif period == "2y":
            df = df[df["date"] >= max_date - pd.DateOffset(years=2)]
        # "all" shows all available data (no filtering)

        if df.empty:
            continue

        # Create Spanish formatted date for hover
        df["date_es"] = df["date"].apply(
            lambda d: f"{d.day} {MESES.get(d.month, '')} {d.year}"
        )

        x_dates = df["date"].astype(str).tolist()

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df["value"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
                customdata=df["date_es"],
                hovertemplate=f"<b>{name}</b><br>%{{customdata}}<br>%{{y:.2f}}%<extra></extra>",
            )
        )

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color=COLORS["neutral"],
        line_width=1,
    )

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
        ),
        margin=dict(l=50, r=30, t=30, b=40),
        height=350,
    )

    return fig


# 10Y Bond colors
BOND_10Y_COLORS = {
    "spain": "#dc2626",      # Red - Spain
    "germany": "#1e40af",    # Blue - Germany
    "france": "#7c3aed",     # Purple - France
    "italy": "#059669",      # Green - Italy
    "us": "#d97706",         # Orange - US
}

BOND_10Y_NAMES = {
    "spain": "España",
    "germany": "Alemania",
    "france": "Francia",
    "italy": "Italia",
    "us": "EE.UU.",
}


def _build_bond_10y_chart(bde_data, yahoo_data, selected_bonds):
    """Build chart comparing 10Y government bond yields across countries."""
    if not selected_bonds:
        return None

    # Map selection keys to data keys and sources (all monthly from BDE except US)
    bond_mapping = {
        "spain": ("spain_10y_bond_monthly", bde_data, "M"),  # Monthly
        "germany": ("germany_10y_bond", bde_data, "M"),       # Monthly
        "france": ("france_10y_bond", bde_data, "M"),         # Monthly
        "italy": ("italy_10y_bond", bde_data, "M"),           # Monthly
        "us": ("us_treasury_10y", yahoo_data, "D"),           # Daily (no BDE data available)
    }

    fig = go.Figure()

    for bond_key in selected_bonds:
        if bond_key not in bond_mapping:
            continue

        data_key, data_source, freq = bond_mapping[bond_key]
        df = data_source.get(data_key, pd.DataFrame())

        if df.empty:
            continue

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        # Remove timezone if present
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_localize(None)
        df = df.sort_values("date")

        # Filter to last 5 years
        max_date = df["date"].max()
        df = df[df["date"] >= max_date - pd.DateOffset(years=5)]

        if df.empty:
            continue

        # Get value column
        value_col = "value" if "value" in df.columns else "Close"
        if value_col not in df.columns:
            continue

        df = df.dropna(subset=[value_col])

        # Create Spanish date for hover
        df["date_es"] = df["date"].apply(
            lambda d: f"{d.day} {MESES.get(d.month, '')} {d.year}"
        )

        color = BOND_10Y_COLORS.get(bond_key, "#6b7280")
        name = BOND_10Y_NAMES.get(bond_key, bond_key)

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[value_col],
            mode="lines",
            name=name,
            line=dict(color=color, width=2),
            customdata=df["date_es"],
            hovertemplate=f"<b>{name}</b><br>%{{customdata}}<br>%{{y:.2f}}%<extra></extra>",
        ))

    if not fig.data:
        return None

    # Add zero line
    fig.add_hline(y=0, line_dash="dot", line_color="#666", line_width=1)

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=30, b=40),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        yaxis=dict(
            title="",
            ticksuffix="%",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        height=400,
    )

    return fig


def _build_market_table_html(data):
    """Build HTML table with market quotes and variations."""
    indices = ["ibex_35", "sp_500", "nasdaq_composite", "euro_stoxx_50", "dax"]

    rows = []
    for key in indices:
        df = data.get(key, pd.DataFrame())
        if df.empty:
            continue

        latest = df.iloc[-1]
        name = INDEX_NAMES.get(key, key)

        # Get values
        current = latest.get("Close", None)
        change_1w = latest.get("return_1w_pct", None)
        change_30d = latest.get("return_1m_pct", None)
        change_ytd = latest.get("ytd_return_pct", None)
        change_1y = latest.get("return_1y_pct", None)

        rows.append({
            "name": name,
            "current": current,
            "change_1w": change_1w,
            "change_30d": change_30d,
            "change_ytd": change_ytd,
            "change_1y": change_1y,
        })

    if not rows:
        return "<p>No hay datos disponibles</p>"

    def format_value(val, is_price=False):
        if val is None or pd.isna(val):
            return "-"
        if is_price:
            return f"{val:,.2f}"
        return f"{val:+.1f}%"

    def get_color_class(val):
        if val is None or pd.isna(val):
            return ""
        if val > 0:
            return "color: #2d8659;"  # positive
        elif val < 0:
            return "color: #b94a48;"  # negative
        return ""

    html = """
    <table class="market-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead>
            <tr style="border-bottom: 2px solid #dee2e6; text-align: right;">
                <th style="text-align: left; padding: 8px 4px;">Índice</th>
                <th style="padding: 8px 4px;">Actual</th>
                <th style="padding: 8px 4px;">Semana</th>
                <th style="padding: 8px 4px;">30 días</th>
                <th style="padding: 8px 4px;">YTD</th>
                <th style="padding: 8px 4px;">1 año</th>
            </tr>
        </thead>
        <tbody>
    """

    for row in rows:
        html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="text-align: left; padding: 10px 4px; font-weight: 600;">{row['name']}</td>
                <td style="text-align: right; padding: 10px 4px;">{format_value(row['current'], is_price=True)}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_class(row['change_1w'])}">{format_value(row['change_1w'])}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_class(row['change_30d'])}">{format_value(row['change_30d'])}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_class(row['change_ytd'])}">{format_value(row['change_ytd'])}</td>
                <td style="text-align: right; padding: 10px 4px; {get_color_class(row['change_1y'])}">{format_value(row['change_1y'])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html


def page_ui(data_store):
    return ui.nav_panel(
        "Mercados financieros",
        ui.div(
            ui.h2("Mercados Financieros", class_="section-header"),
            ui.p("Evolución de los principales índices bursátiles y volatilidad del mercado.", class_="section-description"),

            # Row 1: Single index chart + Comparison chart
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Índices Bursátiles"),
                            ui.tags.br(),
                            ui.tags.small("Precio de cierre diario con media móvil 200 días (desde ene-2022)", style="color: #6c757d;"),
                        )),
                        ui.div(
                            ui.input_radio_buttons(
                                "market_index_select", None,
                                choices={
                                    "ibex_35": "IBEX 35",
                                    "sp_500": "S&P 500",
                                    "nasdaq_composite": "Nasdaq",
                                    "euro_stoxx_50": "Euro Stoxx 50",
                                    "dax": "DAX",
                                },
                                selected="ibex_35", inline=True,
                            ),
                            class_="toggle-btn-group",
                        ),
                        ui.output_ui("single_index_chart", height="400px"),
                        full_screen=True,
                    ),
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Comparativa de Índices"),
                            ui.tags.br(),
                            ui.tags.small("Rendimiento normalizado (base=100)", style="color: #6c757d;"),
                        )),
                        ui.div(
                            ui.input_radio_buttons(
                                "comparison_period", None,
                                choices={"all": "Todo", "3y": "3 años", "1y": "1 año"},
                                selected="3y", inline=True,
                            ),
                            class_="toggle-btn-group",
                        ),
                        ui.output_ui("comparison_chart", height="400px"),
                        full_screen=True,
                    ),
                ),
            ),

            # Row 2: Market table + VIX chart
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Cotizaciones"),
                            ui.tags.br(),
                            ui.output_ui("market_table_subtitle"),
                        )),
                        ui.output_ui("market_table"),
                        full_screen=True,
                        style="min-height: 420px;",
                    ),
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("VIX - Índice de Volatilidad"),
                            ui.tags.br(),
                            ui.tags.small("Volatilidad esperada S&P 500 (índice del miedo)", style="color: #6c757d;"),
                        )),
                        ui.div(
                            ui.input_radio_buttons(
                                "vix_period", None,
                                choices={"5y": "5 años", "1y": "1 año", "6m": "6 meses"},
                                selected="1y", inline=True,
                            ),
                            class_="toggle-btn-group",
                        ),
                        ui.output_ui("vix_chart", height="280px"),
                        full_screen=True,
                    ),
                ),
            ),

            # Row 3: Interest rates table + Euribor chart
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Tipos de Interés"),
                            ui.tags.br(),
                            ui.output_ui("rates_table_subtitle"),
                        )),
                        ui.output_ui("interest_rates_table"),
                        full_screen=True,
                    ),
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Tipos de Referencia"),
                            ui.tags.br(),
                            ui.tags.small("€STR y Euribor", style="color: #6c757d;"),
                        )),
                        ui.div(
                            ui.input_radio_buttons(
                                "euribor_period", None,
                                choices={"all": "Todo", "2y": "2 años", "1y": "1 año"},
                                selected="2y", inline=True,
                            ),
                            class_="toggle-btn-group",
                        ),
                        ui.output_ui("euribor_chart", height="350px"),
                        full_screen=True,
                    ),
                ),
            ),

            # Row 4: 10Y Bond Yields Comparison
            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Rendimientos de Deuda Pública a 10 Años"),
                    ui.tags.br(),
                    ui.tags.small("Comparativa europea y EE.UU. (últimos 5 años)", style="color: #6c757d;"),
                )),
                ui.div(
                    ui.input_checkbox_group(
                        "bond_10y_select",
                        None,
                        choices={
                            "spain": "España",
                            "germany": "Alemania",
                            "france": "Francia",
                            "italy": "Italia",
                            "us": "EE.UU.",
                        },
                        selected=["spain", "germany", "italy"],
                        inline=True,
                    ),
                    class_="toggle-btn-group",
                ),
                ui.output_ui("bond_10y_chart", height="400px"),
                full_screen=True,
            ),

            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    YAHOO_DATA = data_store.get("yahoo", {})
    BDE_RATES = data_store.get("bde_rates", {})

    @render.ui
    def single_index_chart():
        index_key = input.market_index_select()
        df = YAHOO_DATA.get(index_key, pd.DataFrame())
        fig = _build_single_index_chart(df, index_key)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No hay datos", class_="no-data-placeholder")

    @render.ui
    def comparison_chart():
        period = input.comparison_period()
        fig = _build_comparison_chart(YAHOO_DATA, period)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No hay datos", class_="no-data-placeholder")

    @render.ui
    def market_table_subtitle():
        # Get latest date from any available index
        for key in ["ibex_35", "sp_500", "nasdaq_composite", "euro_stoxx_50", "dax"]:
            df = YAHOO_DATA.get(key, pd.DataFrame())
            if not df.empty:
                df = df.copy()
                df["date"] = pd.to_datetime(df["date"])
                latest_date = df["date"].max()
                mes = MESES.get(latest_date.month, latest_date.strftime("%b"))
                date_str = f"{latest_date.day} {mes} {latest_date.year}"
                return ui.tags.small(f"Variaciones a {date_str}", style="color: #6c757d;")
        return ui.tags.small("Sin datos", style="color: #6c757d;")

    @render.ui
    def market_table():
        html = _build_market_table_html(YAHOO_DATA)
        return ui.HTML(html)

    @render.ui
    def vix_chart():
        df = YAHOO_DATA.get("vix", pd.DataFrame())
        if df.empty:
            return ui.div("No hay datos", class_="no-data-placeholder")

        # Filter based on selected period
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        period = input.vix_period()
        max_date = df["date"].max()

        if period == "6m":
            df = df[df["date"] >= max_date - pd.DateOffset(months=6)]
        elif period == "1y":
            df = df[df["date"] >= max_date - pd.DateOffset(years=1)]
        elif period == "5y":
            df = df[df["date"] >= max_date - pd.DateOffset(years=5)]

        fig = create_volatility_chart(df, title="", subtitle="")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No hay datos", class_="no-data-placeholder")

    @render.ui
    def rates_table_subtitle():
        # Get latest date from BDE data
        for key in ["euribor_12m_daily", "spain_10y_bond", "ester_daily"]:
            df = BDE_RATES.get(key, pd.DataFrame())
            if not df.empty:
                df = df.copy()
                df["date"] = pd.to_datetime(df["date"])
                latest_date = df["date"].max()
                mes = MESES.get(latest_date.month, latest_date.strftime("%b"))
                date_str = f"{latest_date.day} {mes} {latest_date.year}"
                return ui.tags.small(f"Variaciones en puntos básicos a {date_str}", style="color: #6c757d;")
        return ui.tags.small("Sin datos", style="color: #6c757d;")

    @render.ui
    def interest_rates_table():
        html = _build_interest_rates_table_html(BDE_RATES, YAHOO_DATA)
        return ui.HTML(html)

    @render.ui
    def euribor_chart():
        period = input.euribor_period()
        fig = _build_euribor_chart(BDE_RATES, period)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No hay datos", class_="no-data-placeholder")

    @render.ui
    def bond_10y_chart():
        selected = input.bond_10y_select()
        fig = _build_bond_10y_chart(BDE_RATES, YAHOO_DATA, selected)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("Seleccione al menos un país", class_="no-data-placeholder")
