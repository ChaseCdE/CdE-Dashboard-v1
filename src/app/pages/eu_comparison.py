"""Spain vs EU (Espana vs UE) page module."""

import pandas as pd
from shiny import ui, render

from charts import (
    create_comparison_line_chart,
    create_comparison_bar_chart,
    create_difference_chart,
)
from helpers import filter_by_period


def page_ui(data_store):
    return ui.nav_panel(
        "Espana vs UE",
        ui.div(
            ui.h2("Espana vs Union Europea", class_="section-header"),
            ui.p("Comparativa del desempeno economico de Espana frente a la media de la UE27 usando datos armonizados de Eurostat.", class_="section-description"),

            ui.div(
                ui.layout_columns(
                    ui.div(
                        ui.span("Periodo", class_="filter-label"),
                        ui.input_select("eu_period", None,
                            choices={"all": "Todos", "5y": "Ultimos 5 anos", "3y": "Ultimos 3 anos", "1y": "Ultimo ano"},
                            selected="5y"),
                    ),
                    col_widths={"sm": 12, "md": 4},
                ),
                class_="filter-section",
            ),

            # Key Comparison KPIs
            ui.h5("Comparativa Actual", style="margin-top: 1.5rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                ui.card(ui.card_header("Crecimiento PIB (TaT)"), ui.output_ui("eu_gdp_comparison_bar", height="180px")),
                ui.card(ui.card_header("Tasa de Paro"), ui.output_ui("eu_unemployment_bar", height="180px")),
                ui.card(ui.card_header("Inflacion IPCA"), ui.output_ui("eu_inflation_bar", height="180px")),
                ui.card(ui.card_header("Deuda Publica (% PIB)"), ui.output_ui("eu_debt_bar", height="180px")),
                col_widths={"sm": 6, "md": 3},
            ),

            # Trend Comparisons
            ui.h5("Comparativa de Tendencias", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                ui.card(ui.card_header("Tasa de Paro: Espana vs UE27"),
                        ui.output_ui("eu_unemployment_chart", height="350px"), full_screen=True),
                ui.card(ui.card_header("Inflacion IPCA: Espana vs UE27"),
                        ui.output_ui("eu_inflation_chart", height="350px"), full_screen=True),
                col_widths={"sm": 12, "md": 6},
            ),
            ui.layout_columns(
                ui.card(ui.card_header("Indicador de Sentimiento Economico"),
                        ui.output_ui("eu_esi_chart", height="350px"), full_screen=True),
                ui.card(ui.card_header("Deuda Publica sobre PIB"),
                        ui.output_ui("eu_debt_chart", height="350px"), full_screen=True),
                col_widths={"sm": 12, "md": 6}, class_="mt-3",
            ),

            # Differences
            ui.h5("Diferencial Espana vs UE27", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                ui.card(ui.card_header("Diferencial de Paro (Espana - UE27)"),
                        ui.output_ui("eu_unemployment_diff_chart", height="300px"), full_screen=True),
                ui.card(ui.card_header("Diferencial de Inflacion (Espana - UE27)"),
                        ui.output_ui("eu_inflation_diff_chart", height="300px"), full_screen=True),
                col_widths={"sm": 12, "md": 6},
            ),
            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    EUROSTAT_DATA = data_store.get("eurostat", {})

    @render.ui
    def eu_gdp_comparison_bar():
        df_spain = EUROSTAT_DATA.get("gdp_growth_spain", pd.DataFrame())
        df_eu = EUROSTAT_DATA.get("gdp_growth_eu27", pd.DataFrame())
        spain_val = df_spain["gdp_growth_qoq"].iloc[-1] if not df_spain.empty else None
        eu_val = df_eu["gdp_growth_qoq"].iloc[-1] if not df_eu.empty else None
        return ui.HTML(create_comparison_bar_chart(spain_val, eu_val, "Crecimiento PIB (TaT)", "%"))

    @render.ui
    def eu_unemployment_bar():
        df_spain = EUROSTAT_DATA.get("unemployment_spain_eu", pd.DataFrame())
        df_eu = EUROSTAT_DATA.get("unemployment_eu27", pd.DataFrame())
        spain_val = df_spain["unemployment_rate"].iloc[-1] if not df_spain.empty else None
        eu_val = df_eu["unemployment_rate"].iloc[-1] if not df_eu.empty else None
        return ui.HTML(create_comparison_bar_chart(spain_val, eu_val, "Tasa de Paro", "%"))

    @render.ui
    def eu_inflation_bar():
        df_spain = EUROSTAT_DATA.get("hicp_spain", pd.DataFrame())
        df_eu = EUROSTAT_DATA.get("hicp_eu27", pd.DataFrame())
        spain_val = df_spain["hicp_inflation"].iloc[-1] if not df_spain.empty else None
        eu_val = df_eu["hicp_inflation"].iloc[-1] if not df_eu.empty else None
        return ui.HTML(create_comparison_bar_chart(spain_val, eu_val, "Inflacion IPCA", "%"))

    @render.ui
    def eu_debt_bar():
        df_spain = EUROSTAT_DATA.get("debt_spain", pd.DataFrame())
        df_eu = EUROSTAT_DATA.get("debt_eu27", pd.DataFrame())
        spain_val = df_spain["debt_to_gdp"].iloc[-1] if not df_spain.empty else None
        eu_val = df_eu["debt_to_gdp"].iloc[-1] if not df_eu.empty else None
        return ui.HTML(create_comparison_bar_chart(spain_val, eu_val, "Deuda/PIB", "%"))

    @render.ui
    def eu_unemployment_chart():
        df_spain = filter_by_period(EUROSTAT_DATA.get("unemployment_spain_eu", pd.DataFrame()), input.eu_period())
        df_eu = filter_by_period(EUROSTAT_DATA.get("unemployment_eu27", pd.DataFrame()), input.eu_period())
        fig = create_comparison_line_chart(df_spain, df_eu, "unemployment_rate",
            title="Tasa de Paro", subtitle="Tasa armonizada mensual (25-74 anos)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def eu_inflation_chart():
        df_spain = filter_by_period(EUROSTAT_DATA.get("hicp_spain", pd.DataFrame()), input.eu_period())
        df_eu = filter_by_period(EUROSTAT_DATA.get("hicp_eu27", pd.DataFrame()), input.eu_period())
        fig = create_comparison_line_chart(df_spain, df_eu, "hicp_inflation",
            title="Inflacion IPCA", subtitle="Tasa de variacion anual")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def eu_esi_chart():
        df_spain = filter_by_period(EUROSTAT_DATA.get("esi_spain", pd.DataFrame()), input.eu_period())
        df_eu = filter_by_period(EUROSTAT_DATA.get("esi_eu27", pd.DataFrame()), input.eu_period())
        fig = create_comparison_line_chart(df_spain, df_eu, "esi",
            title="Indicador de Sentimiento Economico", subtitle="Mensual, 100 = media largo plazo")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def eu_debt_chart():
        df_spain = filter_by_period(EUROSTAT_DATA.get("debt_spain", pd.DataFrame()), input.eu_period())
        df_eu = filter_by_period(EUROSTAT_DATA.get("debt_eu27", pd.DataFrame()), input.eu_period())
        fig = create_comparison_line_chart(df_spain, df_eu, "debt_to_gdp",
            title="Deuda Publica sobre PIB", subtitle="Trimestral, % del PIB")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def eu_unemployment_diff_chart():
        df = filter_by_period(EUROSTAT_DATA.get("unemployment_comparison", pd.DataFrame()), input.eu_period())
        spain_col = [c for c in df.columns if "unemployment_rate" in c and "es" in c.lower()]
        eu_col = [c for c in df.columns if "unemployment_rate" in c and "eu27" in c.lower()]
        if spain_col and eu_col:
            return ui.HTML(create_difference_chart(df, spain_col[0], eu_col[0], "Diferencial de Paro"))
        return ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def eu_inflation_diff_chart():
        df = filter_by_period(EUROSTAT_DATA.get("hicp_comparison", pd.DataFrame()), input.eu_period())
        spain_col = [c for c in df.columns if "hicp_inflation" in c and "es" in c.lower()]
        eu_col = [c for c in df.columns if "hicp_inflation" in c and "eu27" in c.lower()]
        if spain_col and eu_col:
            return ui.HTML(create_difference_chart(df, spain_col[0], eu_col[0], "Diferencial de Inflacion"))
        return ui.div("No data", class_="no-data-placeholder")
