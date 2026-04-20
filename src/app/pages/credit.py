"""Credit & Banking (Credito) page module."""

import pandas as pd
from shiny import ui, render

from charts import (
    create_credit_growth_chart,
    create_debt_to_gdp_chart,
    create_debt_gauge_chart,
    create_current_account_chart,
    create_yield_curve_chart,
    create_lending_rates_chart,
)
from helpers import create_bde_kpi_card, filter_credit_by_period


def page_ui(data_store):
    BDE_CREDIT_DATA = data_store.get("bde_credit", {})
    BDE_DEBT_RATIOS = data_store.get("bde_debt", {})
    BDE_EXTERNAL_SECTOR = data_store.get("bde_external", {})

    return ui.nav_panel(
        "Credito",
        ui.div(
            ui.h2("Credito y Sector Bancario", class_="section-header"),
            ui.p("Indicadores de credito, endeudamiento y sector bancario del Banco de Espana.", class_="section-description"),

            ui.div(
                ui.layout_columns(
                    ui.div(
                        ui.span("Periodo", class_="filter-label"),
                        ui.input_select("credit_period", None,
                            choices={"all": "Todos", "5y": "Ultimos 5 anos", "3y": "Ultimos 3 anos", "1y": "Ultimo ano"},
                            selected="5y"),
                    ),
                    col_widths={"sm": 12, "md": 4},
                ),
                class_="filter-section",
            ),

            # Credit Volumes
            ui.h5("Credito al Sector Privado", style="margin-top: 1.5rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_bde_kpi_card("credit_households_total", BDE_CREDIT_DATA),
                create_bde_kpi_card("credit_nfc_total", BDE_CREDIT_DATA),
                col_widths={"sm": 6, "md": 6}, class_="mb-4",
            ),
            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Evolucion del Credito"), ui.tags.br(),
                    ui.tags.small("Credito a hogares y sociedades no financieras", style="color: #6c757d;"),
                )),
                ui.output_ui("credit_growth_chart", height="400px"), full_screen=True,
            ),

            # Bank Lending Rates
            ui.h5("Tipos Bancarios", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_bde_kpi_card("mortgage_rate", BDE_CREDIT_DATA),
                create_bde_kpi_card("consumer_credit_rate", BDE_CREDIT_DATA),
                create_bde_kpi_card("corporate_lending_rate", BDE_CREDIT_DATA),
                create_bde_kpi_card("household_deposit_rate", BDE_CREDIT_DATA),
                col_widths={"sm": 6, "md": 3}, class_="mb-3",
            ),
            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Tipos de Interes Bancarios"), ui.tags.br(),
                    ui.tags.small("Hipotecas, consumo, empresas y depositos (nuevas operaciones)", style="color: #6c757d;"),
                )),
                ui.output_ui("lending_rates_chart_credit", height="400px"), full_screen=True,
            ),

            # Debt Ratios
            ui.h5("Ratios de Endeudamiento", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_bde_kpi_card("household_debt_gdp", BDE_DEBT_RATIOS),
                create_bde_kpi_card("nfc_debt_gdp", BDE_DEBT_RATIOS),
                col_widths={"sm": 6, "md": 6}, class_="mb-3",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("Deuda sobre PIB"), ui.tags.br(),
                        ui.tags.small("Ratio de endeudamiento de hogares y empresas", style="color: #6c757d;"),
                    )),
                    ui.output_ui("debt_to_gdp_chart", height="400px"), full_screen=True),
                ui.card(ui.card_header("Indicadores de Deuda"),
                        ui.output_ui("debt_gauge_chart", height="250px")),
                col_widths={"sm": 12, "md": 6},
            ),

            # External Sector
            ui.h5("Sector Exterior", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.layout_columns(
                create_bde_kpi_card("current_account_balance", BDE_EXTERNAL_SECTOR),
                create_bde_kpi_card("tourism_receipts", BDE_EXTERNAL_SECTOR),
                col_widths={"sm": 6, "md": 6}, class_="mb-3",
            ),
            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Balanza por Cuenta Corriente"), ui.tags.br(),
                    ui.tags.small("Saldo mensual (millones EUR)", style="color: #6c757d;"),
                )),
                ui.output_ui("current_account_chart", height="400px"), full_screen=True,
            ),

            # Yield Curve
            ui.h5("Curva de Rendimientos", style="margin-top: 2rem; margin-bottom: 1rem; color: #1e2d3d; font-weight: 600;"),
            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Curva de Tipos de Deuda Publica"), ui.tags.br(),
                    ui.tags.small("Rendimientos de letras y bonos del Estado espanol", style="color: #6c757d;"),
                )),
                ui.output_ui("yield_curve_chart", height="350px"), full_screen=True,
            ),
            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    BDE_CREDIT_DATA = data_store.get("bde_credit", {})
    BDE_DEBT_RATIOS = data_store.get("bde_debt", {})
    BDE_EXTERNAL_SECTOR = data_store.get("bde_external", {})
    BDE_INTEREST_RATES = data_store.get("bde_rates", {})

    @render.ui
    def credit_growth_chart():
        filtered_data = {key: filter_credit_by_period(BDE_CREDIT_DATA.get(key, pd.DataFrame()), input.credit_period())
                         for key in ["credit_households_total", "credit_nfc_total"]}
        fig = create_credit_growth_chart(filtered_data, title="Evolucion del Credito",
            subtitle="Credito a hogares y empresas (variacion interanual)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def lending_rates_chart_credit():
        filtered_data = {key: filter_credit_by_period(BDE_CREDIT_DATA.get(key, pd.DataFrame()), input.credit_period())
                         for key in ["mortgage_rate", "consumer_credit_rate", "corporate_lending_rate", "household_deposit_rate"]}
        fig = create_lending_rates_chart(filtered_data, title="Tipos de Interes Bancarios",
            subtitle="Tipos aplicados en nuevas operaciones (BdE)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def debt_to_gdp_chart():
        filtered_data = {key: filter_credit_by_period(BDE_DEBT_RATIOS.get(key, pd.DataFrame()), input.credit_period())
                         for key in ["household_debt_gdp", "nfc_debt_gdp"]}
        fig = create_debt_to_gdp_chart(filtered_data, title="Deuda sobre PIB",
            subtitle="Ratio de endeudamiento del sector privado")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def debt_gauge_chart():
        df_hh = BDE_DEBT_RATIOS.get("household_debt_gdp", pd.DataFrame())
        df_nfc = BDE_DEBT_RATIOS.get("nfc_debt_gdp", pd.DataFrame())
        hh_value = df_hh["value"].iloc[-1] if not df_hh.empty and "value" in df_hh.columns else None
        nfc_value = df_nfc["value"].iloc[-1] if not df_nfc.empty and "value" in df_nfc.columns else None
        fig = create_debt_gauge_chart(hh_value, nfc_value, title="Ratios de Endeudamiento Actuales")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def current_account_chart():
        df = filter_credit_by_period(BDE_EXTERNAL_SECTOR.get("current_account_balance", pd.DataFrame()), input.credit_period())
        fig = create_current_account_chart(df, title="Balanza por Cuenta Corriente",
            subtitle="Saldo mensual (millones EUR)")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def yield_curve_chart():
        df = BDE_INTEREST_RATES.get("yield_curve", pd.DataFrame())
        fig = create_yield_curve_chart(df, title="Curva de Rendimientos",
            subtitle="Deuda publica espanola")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")
