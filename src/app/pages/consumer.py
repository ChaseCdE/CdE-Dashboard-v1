"""Consumer & Households (Consumo) page module."""

import pandas as pd
from shiny import ui, render

from data import INDICATORS
from charts import create_time_series, COLORS
from helpers import create_kpi_card, filter_by_period


def page_ui(data_store):
    DATA = data_store.get("ine", {})

    return ui.nav_panel(
        "Consumo",
        ui.div(
            ui.h2("Consumo y Hogares", class_="section-header"),
            ui.p("Indicadores de comercio minorista y mercado de vivienda.", class_="section-description"),

            ui.div(
                ui.layout_columns(
                    ui.div(
                        ui.span("Periodo", class_="filter-label"),
                        ui.input_select("consumer_period", None,
                            choices={"all": "Todos", "5y": "Ultimos 5 anos", "3y": "Ultimos 3 anos", "1y": "Ultimo ano"},
                            selected="5y"),
                    ),
                    col_widths={"sm": 12, "md": 4},
                ),
                class_="filter-section",
            ),

            ui.layout_columns(
                create_kpi_card("retail_sales", DATA, show_sparkline=False),
                create_kpi_card("house_prices", DATA, show_sparkline=False),
                col_widths={"sm": 12, "md": 6}, class_="mb-4",
            ),

            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Indice de Comercio Minorista"),
                    ui.tags.br(),
                    ui.tags.small(INDICATORS["retail_sales"]["description"], style="color: #6c757d;"),
                )),
                ui.output_ui("retail_chart", height="400px"), full_screen=True,
            ),

            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Indice de Precios de Vivienda"),
                    ui.tags.br(),
                    ui.tags.small(INDICATORS["house_prices"]["description"], style="color: #6c757d;"),
                )),
                ui.output_ui("house_prices_chart", height="400px"),
                full_screen=True, class_="mt-4",
            ),
            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    DATA = data_store.get("ine", {})

    @render.ui
    def retail_chart():
        df = filter_by_period(DATA.get("retail_sales", pd.DataFrame()), input.consumer_period())
        fig = create_time_series(df, "retail_index", title="Indice de Comercio Minorista",
                                 subtitle="Mensual, indice de ventas deflactado")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def house_prices_chart():
        df = filter_by_period(DATA.get("house_prices", pd.DataFrame()), input.consumer_period())
        fig = create_time_series(df, "hpi_index", title="Indice de Precios de Vivienda",
                                 subtitle="Trimestral, base 2015 = 100", color=COLORS["secondary"])
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")
