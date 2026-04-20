"""Overview (Resumen) page module."""

import pandas as pd
from shiny import ui, render

from data import INDICATORS, get_last_update_time
from charts import (
    create_yoy_bar_chart,
    create_multi_indicator_chart,
    COLORS,
)
from helpers import (
    create_kpi_card,
    create_market_kpi_card,
    create_bde_kpi_card,
)


def page_ui(data_store):
    """Return the nav_panel for the Overview tab."""
    DATA = data_store.get("ine", {})
    YAHOO_DATA = data_store.get("yahoo", {})
    BDE_INTEREST_RATES = data_store.get("bde_rates", {})
    BDE_DEBT_RATIOS = data_store.get("bde_debt", {})

    return ui.nav_panel(
        "Resumen",
        ui.div(
            # === ECONOMIC PULSE HEADER ===
            ui.div(
                ui.h3("Pulso Economico"),
                ui.div(
                    ui.output_ui("economic_pulse_headline"),
                    class_="pulse-headline",
                ),
                ui.div(
                    ui.output_ui("pulse_indicators"),
                    class_="pulse-indicators",
                ),
                class_="economic-pulse",
            ),

            # === EXECUTIVE SUMMARY ===
            ui.div(
                ui.h4("Claves de la Coyuntura"),
                ui.output_ui("executive_summary"),
                class_="executive-summary",
            ),

            # === SPAIN VS EU SNAPSHOT ===
            ui.div(
                ui.h4("Espana vs Union Europea"),
                ui.div(
                    ui.output_ui("eu_comparison_snapshot"),
                    class_="comparison-grid",
                ),
                class_="comparison-snapshot",
            ),

            # === GROWTH SECTION ===
            ui.div(
                ui.div(
                    ui.div("\U0001f4c8", class_="theme-icon growth"),
                    ui.h5("Crecimiento", class_="theme-title"),
                    class_="theme-header",
                ),
                ui.layout_columns(
                    create_kpi_card("gdp", DATA, show_sparkline=False),
                    create_kpi_card("industrial_production", DATA, show_sparkline=False),
                    col_widths={"sm": 6, "md": 6},
                ),
                class_="theme-section",
            ),

            # === LABOR MARKET SECTION ===
            ui.div(
                ui.div(
                    ui.div("\U0001f465", class_="theme-icon labor"),
                    ui.h5("Mercado Laboral", class_="theme-title"),
                    class_="theme-header",
                ),
                ui.layout_columns(
                    create_kpi_card("unemployment", DATA, show_sparkline=False),
                    create_kpi_card("employment_rate", DATA, show_sparkline=False),
                    col_widths={"sm": 6, "md": 6},
                ),
                class_="theme-section",
            ),

            # === PRICES SECTION ===
            ui.div(
                ui.div(
                    ui.div("\U0001f4b0", class_="theme-icon prices"),
                    ui.h5("Precios e Inflacion", class_="theme-title"),
                    class_="theme-header",
                ),
                ui.layout_columns(
                    create_kpi_card("cpi", DATA, show_sparkline=False),
                    create_kpi_card("retail_sales", DATA, show_sparkline=False),
                    col_widths={"sm": 6, "md": 6},
                ),
                class_="theme-section",
            ),

            # === FINANCIAL CONDITIONS SECTION ===
            ui.div(
                ui.div(
                    ui.div("\U0001f3e6", class_="theme-icon financial"),
                    ui.h5("Condiciones Financieras", class_="theme-title"),
                    class_="theme-header",
                ),
                ui.layout_columns(
                    create_bde_kpi_card("euribor_12m_monthly", BDE_INTEREST_RATES),
                    create_bde_kpi_card("household_debt_gdp", BDE_DEBT_RATIOS),
                    create_market_kpi_card("ibex_35", YAHOO_DATA),
                    col_widths={"sm": 6, "md": 4},
                ),
                class_="theme-section",
            ),

            # === TREND CHARTS ===
            ui.h5("Tendencias Clave", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        ui.div(
                            ui.tags.strong("Crecimiento del PIB"),
                            ui.tags.br(),
                            ui.tags.small("Variacion trimestral, datos desestacionalizados", style="color: #6c757d;"),
                        ),
                    ),
                    ui.output_ui("overview_gdp_chart", height="320px"),
                    ui.div(
                        ui.output_ui("gdp_chart_annotation"),
                        class_="chart-annotation",
                    ),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header(
                        ui.div(
                            ui.tags.strong("Evolucion de la Inflacion"),
                            ui.tags.br(),
                            ui.tags.small("Tasa interanual IPC, linea objetivo BCE 2%", style="color: #6c757d;"),
                        ),
                    ),
                    ui.output_ui("overview_inflation_chart", height="320px"),
                    ui.div(
                        ui.output_ui("inflation_chart_annotation"),
                        class_="chart-annotation",
                    ),
                    full_screen=True,
                ),
                col_widths={"sm": 12, "md": 6},
            ),

            # === MARKET SNAPSHOT ===
            ui.h5("Mercados Financieros", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Indices Bursatiles - Rendimiento YTD"),
                    ui.output_ui("overview_markets_chart", height="280px"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Tipos de Interes"),
                    ui.output_ui("overview_rates_chart", height="280px"),
                    full_screen=True,
                ),
                col_widths={"sm": 12, "md": 6},
            ),

            # === FOOTER INFO ===
            ui.div(
                ui.layout_columns(
                    ui.div(
                        ui.span(f"Actualizado: {get_last_update_time()}", class_="last-updated"),
                    ),
                    ui.div(
                        ui.tags.small(
                            "Fuentes: INE, Eurostat, Banco de Espana, Yahoo Finance",
                            style="color: #6c757d;",
                        ),
                        style="text-align: right;",
                    ),
                    col_widths=[6, 6],
                ),
                style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;",
            ),

            style="padding: 1.5rem;",
        ),
    )


def page_server(input, output, session, data_store):
    """Register reactive outputs for the Overview tab."""
    DATA = data_store.get("ine", {})
    EUROSTAT_DATA = data_store.get("eurostat", {})
    YAHOO_DATA = data_store.get("yahoo", {})
    BDE_INTEREST_RATES = data_store.get("bde_rates", {})

    @render.ui
    def economic_pulse_headline():
        gdp_df = DATA.get("gdp", pd.DataFrame())
        unemp_df = DATA.get("unemployment", pd.DataFrame())

        gdp_growth = gdp_df["yoy_change"].iloc[-1] if not gdp_df.empty and "yoy_change" in gdp_df.columns else None

        if gdp_growth and gdp_growth > 2:
            headline = "La economia espanola mantiene un crecimiento solido"
        elif gdp_growth and gdp_growth > 0:
            headline = "La economia espanola crece a ritmo moderado"
        elif gdp_growth and gdp_growth < 0:
            headline = "La economia espanola muestra signos de desaceleracion"
        else:
            headline = "Situacion economica de Espana"

        return ui.div(headline)

    @render.ui
    def pulse_indicators():
        gdp_df = DATA.get("gdp", pd.DataFrame())
        unemp_df = DATA.get("unemployment", pd.DataFrame())
        cpi_df = DATA.get("cpi", pd.DataFrame())
        euribor_df = BDE_INTEREST_RATES.get("euribor_12m_monthly", pd.DataFrame())

        indicators = []

        # Growth indicator
        gdp_growth = gdp_df["yoy_change"].iloc[-1] if not gdp_df.empty and "yoy_change" in gdp_df.columns else None
        if gdp_growth:
            status = "positive" if gdp_growth > 1.5 else ("warning" if gdp_growth > 0 else "negative")
            indicators.append(ui.div(
                ui.span(class_=f"pulse-dot {status}"),
                ui.span("Crecimiento: ", class_="pulse-label"),
                ui.span(f"{gdp_growth:+.1f}%", class_="pulse-value"),
                class_="pulse-indicator",
            ))

        # Employment indicator
        unemp_rate = unemp_df["unemployment_rate"].iloc[-1] if not unemp_df.empty else None
        if unemp_rate:
            status = "positive" if unemp_rate < 10 else ("warning" if unemp_rate < 15 else "negative")
            indicators.append(ui.div(
                ui.span(class_=f"pulse-dot {status}"),
                ui.span("Paro: ", class_="pulse-label"),
                ui.span(f"{unemp_rate:.1f}%", class_="pulse-value"),
                class_="pulse-indicator",
            ))

        # Inflation indicator
        inflation = cpi_df["inflation_rate"].iloc[-1] if not cpi_df.empty and "inflation_rate" in cpi_df.columns else None
        if inflation:
            status = "positive" if 1 < inflation < 3 else ("warning" if inflation < 4 else "negative")
            indicators.append(ui.div(
                ui.span(class_=f"pulse-dot {status}"),
                ui.span("Inflacion: ", class_="pulse-label"),
                ui.span(f"{inflation:.1f}%", class_="pulse-value"),
                class_="pulse-indicator",
            ))

        # EURIBOR indicator
        euribor = euribor_df["value"].iloc[-1] if not euribor_df.empty and "value" in euribor_df.columns else None
        if euribor:
            status = "positive" if euribor < 2.5 else ("warning" if euribor < 4 else "negative")
            indicators.append(ui.div(
                ui.span(class_=f"pulse-dot {status}"),
                ui.span("EURIBOR 12M: ", class_="pulse-label"),
                ui.span(f"{euribor:.2f}%", class_="pulse-value"),
                class_="pulse-indicator",
            ))

        return ui.div(*indicators) if indicators else ui.span("Cargando indicadores...")

    @render.ui
    def executive_summary():
        gdp_df = DATA.get("gdp", pd.DataFrame())
        unemp_df = DATA.get("unemployment", pd.DataFrame())
        cpi_df = DATA.get("cpi", pd.DataFrame())
        gdp_eu = EUROSTAT_DATA.get("gdp_growth_eu27", pd.DataFrame())

        bullets = []

        # GDP comparison with EU
        gdp_spain = gdp_df["yoy_change"].iloc[-1] if not gdp_df.empty and "yoy_change" in gdp_df.columns else None
        gdp_eu_val = gdp_eu["gdp_growth_qoq"].iloc[-1] if not gdp_eu.empty and "gdp_growth_qoq" in gdp_eu.columns else None

        if gdp_spain and gdp_eu_val:
            if gdp_spain > gdp_eu_val:
                bullets.append(ui.tags.li(
                    "Espana crece ",
                    ui.span(f"{gdp_spain - gdp_eu_val:.1f} pp", class_="summary-highlight summary-positive"),
                    " por encima de la media europea"
                ))
            else:
                bullets.append(ui.tags.li(
                    "El crecimiento espanol es ",
                    ui.span(f"{gdp_eu_val - gdp_spain:.1f} pp", class_="summary-highlight"),
                    " inferior a la media de la UE"
                ))

        # Unemployment trend
        if not unemp_df.empty and len(unemp_df) > 4:
            current = unemp_df["unemployment_rate"].iloc[-1]
            year_ago = unemp_df["unemployment_rate"].iloc[-4] if len(unemp_df) > 4 else current
            change = current - year_ago
            if change < 0:
                bullets.append(ui.tags.li(
                    "El paro ha bajado ",
                    ui.span(f"{abs(change):.1f} pp", class_="summary-highlight summary-positive"),
                    f" en el ultimo ano, hasta el {current:.1f}%"
                ))
            else:
                bullets.append(ui.tags.li(
                    f"La tasa de paro se situa en el {current:.1f}%, ",
                    ui.span(f"+{change:.1f} pp", class_="summary-highlight summary-negative"),
                    " interanual"
                ))

        # Inflation context
        inflation = cpi_df["inflation_rate"].iloc[-1] if not cpi_df.empty and "inflation_rate" in cpi_df.columns else None
        if inflation:
            if inflation > 3:
                bullets.append(ui.tags.li(
                    "La inflacion (",
                    ui.span(f"{inflation:.1f}%", class_="summary-highlight summary-negative"),
                    ") se mantiene por encima del objetivo del BCE (2%)"
                ))
            elif inflation >= 1.5 and inflation <= 2.5:
                bullets.append(ui.tags.li(
                    "La inflacion (",
                    ui.span(f"{inflation:.1f}%", class_="summary-highlight summary-positive"),
                    ") se situa en linea con el objetivo del BCE"
                ))
            else:
                bullets.append(ui.tags.li(f"La inflacion se modera hasta el {inflation:.1f}%"))

        # IBEX performance
        ibex_df = YAHOO_DATA.get("ibex_35", pd.DataFrame())
        if not ibex_df.empty and "ytd_return_pct" in ibex_df.columns:
            ytd = ibex_df["ytd_return_pct"].iloc[-1]
            if pd.notna(ytd):
                direction = "sube" if ytd > 0 else "baja"
                color_class = "summary-positive" if ytd > 0 else "summary-negative"
                bullets.append(ui.tags.li(
                    f"El IBEX 35 {direction} un ",
                    ui.span(f"{abs(ytd):.1f}%", class_=f"summary-highlight {color_class}"),
                    " en lo que va de ano"
                ))

        return ui.tags.ul(*bullets, class_="summary-list") if bullets else ui.p("Cargando resumen...")

    @render.ui
    def eu_comparison_snapshot():
        comparisons = []

        pairs = [
            ("PIB (TaT)", "gdp_growth_spain", "gdp_growth_eu27", "gdp_growth_qoq", ".1f", "%"),
            ("TASA DE PARO", "unemployment_spain_eu", "unemployment_eu27", "unemployment_rate", ".1f", "%"),
            ("INFLACION (IPCA)", "hicp_spain", "hicp_eu27", "hicp_inflation", ".1f", "%"),
            ("DEUDA PUBLICA (% PIB)", "debt_spain", "debt_eu27", "debt_to_gdp", ".0f", "%"),
        ]

        for label, es_key, eu_key, col, fmt, suffix in pairs:
            df_es = EUROSTAT_DATA.get(es_key, pd.DataFrame())
            df_eu = EUROSTAT_DATA.get(eu_key, pd.DataFrame())
            if df_es.empty or df_eu.empty or col not in df_es.columns or col not in df_eu.columns:
                continue
            es_val = df_es[col].iloc[-1]
            eu_val = df_eu[col].iloc[-1]
            if pd.isna(es_val) or pd.isna(eu_val):
                continue
            diff = es_val - eu_val
            badge_class = "above" if diff > 0 else ("below" if diff < 0 else "inline")
            badge_text = f"{diff:+{fmt}} pp"
            comparisons.append(ui.div(
                ui.div(label, class_="comparison-metric"),
                ui.div(
                    ui.span(f"{es_val:{fmt}}{suffix}", class_="comparison-spain"),
                    ui.span(f"UE: {eu_val:{fmt}}{suffix}", class_="comparison-eu"),
                    class_="comparison-values",
                ),
                ui.span(badge_text, class_=f"comparison-badge {badge_class}"),
                class_="comparison-item",
            ))

        return ui.div(*comparisons) if comparisons else ui.p("Cargando comparativa...")

    @render.ui
    def gdp_chart_annotation():
        gdp_df = DATA.get("gdp", pd.DataFrame())
        if gdp_df.empty:
            return ui.span("")
        growth = gdp_df["yoy_change"].iloc[-1] if "yoy_change" in gdp_df.columns else None
        if growth:
            if growth > 2:
                return ui.HTML(ui.span(f"El PIB crece un {growth:.1f}% interanual, por encima del potencial estimado (1.5-2%)."))
            elif growth > 0:
                return ui.span(f"Crecimiento moderado del {growth:.1f}% interanual.")
            else:
                return ui.span(f"Contraccion del PIB: {growth:.1f}% interanual.")

    @render.ui
    def inflation_chart_annotation():
        cpi_df = DATA.get("cpi", pd.DataFrame())
        if cpi_df.empty:
            return ui.span("")
        inflation = cpi_df["inflation_rate"].iloc[-1] if "inflation_rate" in cpi_df.columns else None
        if inflation:
            if inflation > 3:
                return ui.HTML(ui.span(f"Inflacion del {inflation:.1f}%, {inflation - 2:.1f} pp por encima del objetivo del BCE (2%)."))
            elif inflation >= 1.5:
                return ui.span(f"Inflacion contenida en el {inflation:.1f}%, cerca del objetivo del 2%.")
            else:
                return ui.HTML(ui.span(f"Inflacion baja ({inflation:.1f}%), por debajo del objetivo del BCE."))

    @render.ui
    def overview_gdp_chart():
        df = DATA.get("gdp", pd.DataFrame())
        if df.empty:
            return ui.div("No data", class_="no-data-placeholder")
        fig = create_yoy_bar_chart(df.tail(20), title="")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def overview_inflation_chart():
        import plotly.graph_objects as go
        df = DATA.get("cpi", pd.DataFrame())
        if df.empty:
            return ui.div("No data available", class_="no-data-placeholder")

        df_display = df.tail(24).copy()
        if "inflation_rate" not in df_display.columns:
            return ui.div("No data available", class_="no-data-placeholder")

        fig = go.Figure()
        colors = ["#ef4444" if v > 2 else "#10b981" for v in df_display["inflation_rate"]]
        x_dates = pd.to_datetime(df_display["date"]).dt.strftime("%Y-%m-%d").tolist()

        fig.add_trace(go.Bar(
            x=x_dates, y=df_display["inflation_rate"],
            marker_color=colors, name="Inflacion",
            hovertemplate="<b>%{x}</b><br>Inflacion: %{y:.1f}%<extra></extra>",
        ))
        fig.add_hline(y=2, line_dash="dash", line_color="#6b7280",
                      annotation_text="Objetivo BCE: 2%", annotation_position="top right",
                      annotation_font_size=10)
        fig.update_layout(
            title="", xaxis=dict(title="", type="date", tickformat="%b %Y", showgrid=False),
            yaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9", ticksuffix="%"),
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, hovermode="x unified",
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    @render.ui
    def overview_markets_chart():
        import plotly.graph_objects as go

        indices = ["ibex_35", "euro_stoxx_50", "sp_500", "dax"]
        names = ["IBEX 35", "Euro Stoxx 50", "S&P 500", "DAX"]

        ytd_returns = []
        for key in indices:
            df = YAHOO_DATA.get(key, pd.DataFrame())
            if not df.empty and "ytd_return_pct" in df.columns:
                ytd = df["ytd_return_pct"].iloc[-1]
                ytd_returns.append(ytd if pd.notna(ytd) else 0)
            else:
                ytd_returns.append(0)

        fig = go.Figure()
        bar_colors = ["#10b981" if v >= 0 else "#ef4444" for v in ytd_returns]
        fig.add_trace(go.Bar(
            x=names, y=ytd_returns, marker_color=bar_colors,
            text=[f"{v:+.1f}%" for v in ytd_returns], textposition="outside",
            hovertemplate="<b>%{x}</b><br>YTD: %{y:+.1f}%<extra></extra>",
        ))
        fig.update_layout(
            title="", xaxis=dict(title=""),
            yaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9", ticksuffix="%", zeroline=True, zerolinecolor="#9ca3af"),
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    @render.ui
    def overview_rates_chart():
        import plotly.graph_objects as go
        fig = go.Figure()

        euribor_df = BDE_INTEREST_RATES.get("euribor_12m_monthly", pd.DataFrame())
        if not euribor_df.empty and "value" in euribor_df.columns:
            x_dates = pd.to_datetime(euribor_df["date"]).dt.strftime("%Y-%m-%d").tolist()
            fig.add_trace(go.Scatter(
                x=x_dates[-36:], y=euribor_df["value"].iloc[-36:],
                mode="lines", name="EURIBOR 12M",
                line=dict(color="#1e2d3d", width=2.5),
                hovertemplate="<b>EURIBOR 12M</b><br>%{x}<br>%{y:.2f}%<extra></extra>",
            ))

        bond_df = BDE_INTEREST_RATES.get("spain_10y_bond", pd.DataFrame())
        if not bond_df.empty and "value" in bond_df.columns:
            bond_monthly = bond_df.copy()
            bond_monthly["date"] = pd.to_datetime(bond_monthly["date"])
            bond_monthly = bond_monthly.set_index("date").resample("ME").last().reset_index()
            x_dates = bond_monthly["date"].dt.strftime("%Y-%m-%d").tolist()
            fig.add_trace(go.Scatter(
                x=x_dates[-36:], y=bond_monthly["value"].iloc[-36:],
                mode="lines", name="Bono Espana 10A",
                line=dict(color="#059669", width=2.5),
                hovertemplate="<b>Bono 10A</b><br>%{x}<br>%{y:.2f}%<extra></extra>",
            ))

        fig.update_layout(
            title="", xaxis=dict(title="", type="date", tickformat="%b %Y", showgrid=False),
            yaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9", ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=20, t=30, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    @render.ui
    def overview_comparison_chart():
        indicators = [
            ("gdp", INDICATORS["gdp"]),
            ("industrial_production", INDICATORS["industrial_production"]),
            ("retail_sales", INDICATORS["retail_sales"]),
        ]
        fig = create_multi_indicator_chart(DATA, indicators,
            title="Comparativa de Actividad Economica",
            subtitle="Todos los indicadores normalizados a 100 al inicio del periodo",
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")
