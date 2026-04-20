"""Financial Markets (Mercados) page module."""

import pandas as pd
from shiny import ui, render

from charts import (
    create_stock_index_chart,
    create_multi_index_comparison,
    create_returns_bar_chart,
    create_currency_chart,
    create_commodity_chart,
    create_volatility_chart,
    create_euribor_chart,
    create_bond_yield_chart,
    create_lending_rates_chart,
    COLORS,
    MARKET_COLORS,
)
from helpers import (
    create_market_kpi_card,
    create_bde_kpi_card,
    filter_market_by_period,
)


def page_ui(data_store):
    YAHOO_DATA = data_store.get("yahoo", {})
    BDE_INTEREST_RATES = data_store.get("bde_rates", {})
    BDE_CREDIT_DATA = data_store.get("bde_credit", {})

    return ui.nav_panel(
        "Mercados",
        ui.div(
            ui.h2("Mercados Financieros", class_="section-header"),
            ui.p("Datos de mercado de indices bursatiles, divisas, materias primas e indicadores de volatilidad.", class_="section-description"),

            ui.div(
                ui.layout_columns(
                    ui.div(
                        ui.span("Periodo", class_="filter-label"),
                        ui.input_select("market_period", None,
                            choices={"all": "Todos", "1y": "Ultimo ano", "6m": "Ultimos 6 meses", "3m": "Ultimos 3 meses", "1m": "Ultimo mes"},
                            selected="1y"),
                    ),
                    col_widths={"sm": 12, "md": 4},
                ),
                class_="filter-section",
            ),

            # Stock Indices
            ui.h5("Indices Bursatiles", style="margin-top: 1.5rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_market_kpi_card("ibex_35", YAHOO_DATA),
                create_market_kpi_card("euro_stoxx_50", YAHOO_DATA),
                create_market_kpi_card("sp_500", YAHOO_DATA),
                create_market_kpi_card("dax", YAHOO_DATA),
                col_widths={"sm": 6, "md": 3}, class_="mb-4",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("IBEX 35"), ui.tags.br(),
                        ui.tags.small("Principal indice de la bolsa espanola", style="color: #6c757d;"))),
                    ui.output_ui("ibex_chart", height="350px"), full_screen=True),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Comparativa de Indices"), ui.tags.br(),
                        ui.tags.small("Rendimiento normalizado (base=100)", style="color: #6c757d;"))),
                    ui.output_ui("indices_comparison_chart", height="350px"), full_screen=True),
                col_widths={"sm": 12, "md": 6},
            ),

            # Interest Rates
            ui.h5("Tipos de Interes", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_bde_kpi_card("euribor_12m_monthly", BDE_INTEREST_RATES),
                create_bde_kpi_card("euribor_3m_daily", BDE_INTEREST_RATES),
                create_bde_kpi_card("spain_10y_bond", BDE_INTEREST_RATES),
                col_widths={"sm": 6, "md": 4}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("EURIBOR"), ui.tags.br(),
                        ui.tags.small("Tipos de referencia interbancarios (12M y 3M)", style="color: #6c757d;"))),
                    ui.output_ui("euribor_chart", height="350px"), full_screen=True),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Bono Espana 10 Anos"), ui.tags.br(),
                        ui.tags.small("Rendimiento del bono del Estado (BdE)", style="color: #6c757d;"))),
                    ui.output_ui("spain_10y_bond_chart", height="350px"), full_screen=True),
                col_widths={"sm": 12, "md": 6},
            ),

            # Currencies
            ui.h5("Divisas", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_market_kpi_card("eur_usd", YAHOO_DATA),
                create_market_kpi_card("eur_gbp", YAHOO_DATA),
                create_market_kpi_card("dxy", YAHOO_DATA),
                col_widths={"sm": 6, "md": 4}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(ui.card_header("Tipo de Cambio EUR/USD"),
                        ui.output_ui("eurusd_chart", height="300px"), full_screen=True),
                col_widths=12,
            ),

            # Commodities
            ui.h5("Materias Primas", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_market_kpi_card("brent_crude", YAHOO_DATA),
                create_market_kpi_card("gold", YAHOO_DATA),
                create_market_kpi_card("natural_gas", YAHOO_DATA),
                col_widths={"sm": 6, "md": 4}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Petroleo Brent"), ui.tags.br(),
                        ui.tags.small("Referencia europea (USD/barril)", style="color: #6c757d;"))),
                    ui.output_ui("brent_chart", height="300px"), full_screen=True),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Oro"), ui.tags.br(),
                        ui.tags.small("Precio de futuros (USD/oz)", style="color: #6c757d;"))),
                    ui.output_ui("gold_chart", height="300px"), full_screen=True),
                col_widths={"sm": 12, "md": 6},
            ),

            # Volatility
            ui.h5("Volatilidad del Mercado", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_market_kpi_card("vix", YAHOO_DATA),
                create_market_kpi_card("vstoxx", YAHOO_DATA),
                col_widths={"sm": 6, "md": 6}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("VIX - Indice de Volatilidad CBOE"), ui.tags.br(),
                        ui.tags.small("Volatilidad esperada S&P 500 (indice del miedo)", style="color: #6c757d;"))),
                    ui.output_ui("vix_chart", height="350px"), full_screen=True),
                ui.card(
                    ui.card_header(ui.div(ui.tags.strong("Rendimiento IBEX 35"), ui.tags.br(),
                        ui.tags.small("Rentabilidad en diferentes periodos", style="color: #6c757d;"))),
                    ui.output_ui("ibex_returns_chart", height="350px"), full_screen=True),
                col_widths={"sm": 12, "md": 6},
            ),
            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    YAHOO_DATA = data_store.get("yahoo", {})
    BDE_INTEREST_RATES = data_store.get("bde_rates", {})
    BDE_CREDIT_DATA = data_store.get("bde_credit", {})

    @render.ui
    def ibex_chart():
        df = filter_market_by_period(YAHOO_DATA.get("ibex_35", pd.DataFrame()), input.market_period())
        fig = create_stock_index_chart(df, title="IBEX 35",
            subtitle="Precios de cierre diarios con medias moviles",
            color=MARKET_COLORS.get("ibex_35", COLORS["spain"]))
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def indices_comparison_chart():
        period = input.market_period()
        filtered_data = {key: filter_market_by_period(YAHOO_DATA.get(key, pd.DataFrame()), period)
                         for key in ["ibex_35", "euro_stoxx_50", "sp_500", "dax"]}
        fig = create_multi_index_comparison(filtered_data, ["ibex_35", "euro_stoxx_50", "sp_500", "dax"],
            title="Comparativa de Indices",
            subtitle="IBEX 35 vs Euro Stoxx 50 vs S&P 500 vs DAX (normalizado a 100)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def eurusd_chart():
        df = filter_market_by_period(YAHOO_DATA.get("eur_usd", pd.DataFrame()), input.market_period())
        fig = create_currency_chart(df, title="Tipo de Cambio EUR/USD",
            subtitle="Euro a Dolar estadounidense", color="#2563eb")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def brent_chart():
        df = filter_market_by_period(YAHOO_DATA.get("brent_crude", pd.DataFrame()), input.market_period())
        fig = create_commodity_chart(df, title="Petroleo Brent",
            subtitle="Precio de futuros (USD por barril)", color="#374151", unit="USD")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def gold_chart():
        df = filter_market_by_period(YAHOO_DATA.get("gold", pd.DataFrame()), input.market_period())
        fig = create_commodity_chart(df, title="Oro",
            subtitle="Precio de futuros (USD por onza troy)", color="#f59e0b", unit="USD")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def vix_chart():
        df = filter_market_by_period(YAHOO_DATA.get("vix", pd.DataFrame()), input.market_period())
        fig = create_volatility_chart(df, title="VIX - Indice de Volatilidad CBOE",
            subtitle="Indicador de miedo del mercado (mayor = mas miedo)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def ibex_returns_chart():
        df = YAHOO_DATA.get("ibex_35", pd.DataFrame())
        fig = create_returns_bar_chart(df, title="Rentabilidad IBEX 35")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def euribor_chart():
        filtered_data = {key: filter_market_by_period(BDE_INTEREST_RATES.get(key, pd.DataFrame()), input.market_period())
                         for key in ["euribor_12m_daily", "euribor_3m_daily", "euribor_12m_monthly"]}
        fig = create_euribor_chart(filtered_data, title="EURIBOR",
            subtitle="Tipos de referencia interbancarios")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def spain_10y_bond_chart():
        df = filter_market_by_period(BDE_INTEREST_RATES.get("spain_10y_bond", pd.DataFrame()), input.market_period())
        fig = create_bond_yield_chart(df, title="Bono Espana 10 Anos",
            subtitle="Rendimiento del bono del Estado", color=COLORS["spain"])
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def lending_rates_chart():
        filtered_data = {key: filter_market_by_period(BDE_CREDIT_DATA.get(key, pd.DataFrame()), input.market_period())
                         for key in ["mortgage_rate", "consumer_credit_rate", "corporate_lending_rate", "household_deposit_rate"]}
        fig = create_lending_rates_chart(filtered_data, title="Tipos de Interes Bancarios",
            subtitle="Tipos aplicados en nuevas operaciones (BdE)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")
