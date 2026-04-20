"""Labor Market (Empleo) page module."""

import pandas as pd
from shiny import ui, render

from data import INDICATORS
from charts import (
    create_time_series,
    create_yoy_bar_chart,
    COLORS,
)
from helpers import create_kpi_card, filter_by_period


def page_ui(data_store):
    DATA = data_store.get("ine", {})

    return ui.nav_panel(
        "Empleo",
        ui.div(
            ui.h2("Mercado Laboral", class_="section-header"),
            ui.p("Indicadores de empleo, desempleo y costes laborales de la EPA y ETCL.", class_="section-description"),

            # Filter
            ui.div(
                ui.layout_columns(
                    ui.div(
                        ui.span("Periodo", class_="filter-label"),
                        ui.input_select("labor_period", None,
                            choices={"all": "Todos", "5y": "Ultimos 5 anos", "3y": "Ultimos 3 anos", "1y": "Ultimo ano"},
                            selected="5y"),
                    ),
                    col_widths={"sm": 12, "md": 4},
                ),
                class_="filter-section",
            ),

            # Key KPIs
            ui.h5("Indicadores Clave", style="margin-top: 1.5rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_kpi_card("unemployment", DATA, show_sparkline=False),
                create_kpi_card("employment_rate", DATA, show_sparkline=False),
                create_kpi_card("activity_rate", DATA, show_sparkline=False),
                create_kpi_card("employed", DATA, show_sparkline=False),
                col_widths={"sm": 6, "md": 3}, class_="mb-4",
            ),

            # Unemployment and Employment
            ui.h5("Empleo y Desempleo", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Tasa de Paro"), ui.tags.br(),
                        ui.tags.small(INDICATORS["unemployment"]["description"], style="color: #6c757d;"))),
                    ui.output_ui("unemployment_chart", height="350px"), full_screen=True,
                ),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Tasa de Empleo"), ui.tags.br(),
                        ui.tags.small(INDICATORS["employment_rate"]["description"], style="color: #6c757d;"))),
                    ui.output_ui("employment_rate_chart", height="350px"), full_screen=True,
                ),
                col_widths={"sm": 12, "md": 6},
            ),
            ui.layout_columns(
                ui.card(ui.card_header("Variacion del Paro"), ui.output_ui("unemployment_yoy_chart", height="300px")),
                ui.card(ui.card_header("Datos Recientes - Empleo"), ui.output_data_frame("unemployment_table")),
                col_widths={"sm": 12, "md": 6}, class_="mt-3",
            ),

            # Labor Costs
            ui.h5("Costes Laborales", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_kpi_card("labor_cost", DATA, show_sparkline=False),
                create_kpi_card("labor_cost_hour", DATA, show_sparkline=False),
                col_widths={"sm": 6, "md": 6}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Coste Laboral por Trabajador"), ui.tags.br(),
                        ui.tags.small("Coste laboral total mensual por trabajador (euros)", style="color: #6c757d;"))),
                    ui.output_ui("labor_cost_chart", height="350px"), full_screen=True,
                ),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Coste Laboral por Hora"), ui.tags.br(),
                        ui.tags.small("Coste laboral por hora efectiva trabajada (euros)", style="color: #6c757d;"))),
                    ui.output_ui("labor_cost_hour_chart", height="350px"), full_screen=True,
                ),
                col_widths={"sm": 12, "md": 6},
            ),

            # Employment Quality
            ui.h5("Calidad del Empleo", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_kpi_card("temporary_rate", DATA, show_sparkline=False),
                create_kpi_card("youth_unemployment", DATA, show_sparkline=False),
                col_widths={"sm": 6, "md": 6}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Tasa de Temporalidad"), ui.tags.br(),
                        ui.tags.small("Porcentaje de asalariados con contrato temporal", style="color: #6c757d;"))),
                    ui.output_ui("temporary_rate_chart", height="350px"), full_screen=True,
                ),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Paro Juvenil vs General"), ui.tags.br(),
                        ui.tags.small("Comparativa tasa de paro menores de 25 anos vs total", style="color: #6c757d;"))),
                    ui.output_ui("youth_vs_total_unemployment_chart", height="350px"), full_screen=True,
                ),
                col_widths={"sm": 12, "md": 6},
            ),
            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    DATA = data_store.get("ine", {})

    @render.ui
    def unemployment_chart():
        df = filter_by_period(DATA.get("unemployment", pd.DataFrame()), input.labor_period())
        fig = create_time_series(df, "unemployment_rate", title="Tasa de Paro",
                                 subtitle="Trimestral, porcentaje de poblacion activa", color=COLORS["secondary"])
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def unemployment_yoy_chart():
        df = filter_by_period(DATA.get("unemployment", pd.DataFrame()), input.labor_period())
        return ui.HTML(create_yoy_bar_chart(df, title="Variacion Tasa de Paro (pp)"))

    @render.data_frame
    def unemployment_table():
        df_unemp = DATA.get("unemployment", pd.DataFrame())
        df_emp = DATA.get("employment_rate", pd.DataFrame())
        if df_unemp.empty:
            return pd.DataFrame()
        display_df = df_unemp[["date", "unemployment_rate"]].copy()
        if not df_emp.empty:
            display_df = pd.merge(display_df, df_emp[["date", "employment_rate"]], on="date", how="left")
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df["unemployment_rate"] = display_df["unemployment_rate"].apply(lambda x: f"{x:.2f}%")
        if "employment_rate" in display_df.columns:
            display_df["employment_rate"] = display_df["employment_rate"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
        display_df = display_df.rename(columns={"date": "Fecha", "unemployment_rate": "Tasa Paro", "employment_rate": "Tasa Empleo"})
        return display_df.sort_values("Fecha", ascending=False).head(12)

    @render.ui
    def employment_rate_chart():
        df = filter_by_period(DATA.get("employment_rate", pd.DataFrame()), input.labor_period())
        fig = create_time_series(df, "employment_rate", title="Tasa de Empleo",
                                 subtitle="Trimestral, % de poblacion en edad de trabajar", color=COLORS["spain"])
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def labor_cost_chart():
        df = filter_by_period(DATA.get("labor_cost", pd.DataFrame()), input.labor_period())
        fig = create_time_series(df, "labor_cost", title="Coste Laboral por Trabajador",
                                 subtitle="Trimestral, euros por trabajador y mes", color=COLORS["accent"], show_yoy=True)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def labor_cost_hour_chart():
        df = filter_by_period(DATA.get("labor_cost_hour", pd.DataFrame()), input.labor_period())
        fig = create_time_series(df, "labor_cost_hour", title="Coste Laboral por Hora",
                                 subtitle="Trimestral, euros por hora efectiva", color=COLORS["secondary"], show_yoy=True)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def temporary_rate_chart():
        df = filter_by_period(DATA.get("temporary_rate", pd.DataFrame()), input.labor_period())
        fig = create_time_series(df, "temporary_rate", title="Tasa de Temporalidad",
                                 subtitle="Trimestral, % de asalariados con contrato temporal", color="#e63946")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def youth_vs_total_unemployment_chart():
        import plotly.graph_objects as go
        df_youth = filter_by_period(DATA.get("youth_unemployment", pd.DataFrame()), input.labor_period())
        df_total = filter_by_period(DATA.get("unemployment", pd.DataFrame()), input.labor_period())

        fig = go.Figure()
        if not df_total.empty and "unemployment_rate" in df_total.columns:
            x_dates = pd.to_datetime(df_total["date"]).dt.strftime("%Y-%m-%d").tolist()
            fig.add_trace(go.Scatter(x=x_dates, y=df_total["unemployment_rate"], mode="lines", name="Total",
                line=dict(color=COLORS["spain"], width=3),
                hovertemplate="<b>Total</b><br>%{x}<br>Tasa: %{y:.1f}%<extra></extra>"))
        if not df_youth.empty and "youth_unemployment_rate" in df_youth.columns:
            x_dates = pd.to_datetime(df_youth["date"]).dt.strftime("%Y-%m-%d").tolist()
            fig.add_trace(go.Scatter(x=x_dates, y=df_youth["youth_unemployment_rate"], mode="lines", name="Menores 25 anos",
                line=dict(color="#e63946", width=3),
                hovertemplate="<b>Juvenil</b><br>%{x}<br>Tasa: %{y:.1f}%<extra></extra>"))

        fig.update_layout(
            title=dict(text="<b>Paro Juvenil vs General</b><br><span style='font-size:12px;color:#6c757d'>Comparativa tasas de paro trimestrales</span>", x=0, xanchor="left", font=dict(size=16)),
            xaxis=dict(title="", type="date", tickformat="%b %Y", showgrid=True, gridcolor=COLORS["grid"]),
            yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"], ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=50, r=30, t=70, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))
