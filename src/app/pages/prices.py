"""Prices & Inflation (Precios) page module."""

import pandas as pd
import plotly.graph_objects as go
from shiny import ui, render

from charts import COLORS, COMMON_LAYOUT
from helpers import filter_by_period


def _build_inflation_chart(cpi_df, cpi_groups_df):
    """Build inflation chart (YoY change) with line+markers for General and Subyacente."""
    if cpi_groups_df.empty:
        return None

    cpi_groups_df = cpi_groups_df.copy()
    cpi_groups_df["date"] = pd.to_datetime(cpi_groups_df["date"])

    # Get General (headline) from cpi_special_groups
    headline_df = cpi_groups_df[cpi_groups_df["group"] == "headline"].copy()
    headline_df = headline_df.dropna(subset=["yoy_change"])
    headline_df = headline_df.sort_values("date")

    # Get Subyacente (core) from cpi_special_groups
    core_df = cpi_groups_df[cpi_groups_df["group"] == "core"].copy()
    core_df = core_df.dropna(subset=["yoy_change"])
    core_df = core_df.sort_values("date")

    if headline_df.empty and core_df.empty:
        return None

    fig = go.Figure()

    # General (headline inflation)
    if not headline_df.empty:
        fig.add_trace(go.Scatter(
            x=headline_df["date"],
            y=headline_df["yoy_change"],
            mode="lines+markers",
            name="General",
            line=dict(color=COLORS["primary"], width=2.5),
            marker=dict(size=5, color=COLORS["primary"]),
            hovertemplate="General: %{y:.1f}%<extra></extra>",
        ))

        # Add last value annotation for General
        last_date = headline_df["date"].iloc[-1]
        last_val = headline_df["yoy_change"].iloc[-1]
        fig.add_annotation(
            x=last_date, y=last_val,
            text=f"<b>{last_val:.1f}%</b>",
            showarrow=False,
            font=dict(size=11, color=COLORS["primary"]),
            yshift=14, xanchor="center",
        )

    # Subyacente (core inflation)
    if not core_df.empty:
        fig.add_trace(go.Scatter(
            x=core_df["date"],
            y=core_df["yoy_change"],
            mode="lines+markers",
            name="Subyacente",
            line=dict(color=COLORS["negative"], width=2.5),
            marker=dict(size=5, color=COLORS["negative"]),
            hovertemplate="Subyacente: %{y:.1f}%<extra></extra>",
        ))

        # Add last value annotation for Subyacente
        last_date_core = core_df["date"].iloc[-1]
        last_val_core = core_df["yoy_change"].iloc[-1]
        fig.add_annotation(
            x=last_date_core, y=last_val_core,
            text=f"<b>{last_val_core:.1f}%</b>",
            showarrow=False,
            font=dict(size=11, color=COLORS["negative"]),
            yshift=-14, xanchor="center",
        )

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=50, r=30, t=40, b=50),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            tickformat="%b %Y",
        ),
        yaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            ticksuffix="%",
        ),
    )

    return fig


def page_ui(data_store):
    return ui.nav_panel(
        "Precios",
        ui.div(
            ui.h2("Precios e Inflación", class_="section-header"),
            ui.p("Índices de precios al consumo y tendencias de inflación.", class_="section-description"),

            # Inflation chart: General vs Subyacente (YoY change)
            ui.card(
                ui.card_header(ui.div(
                    ui.tags.strong("Inflación (variación, en %)"),
                    ui.tags.br(),
                    ui.tags.small("Variación interanual del IPC", style="color: #6c757d;"),
                )),
                ui.div(
                    ui.input_radio_buttons(
                        "prices_period", None,
                        choices={"all": "Todo", "3y": "Últimos 3 años", "1y": "Último año"},
                        selected="3y", inline=True,
                    ),
                    class_="toggle-btn-group",
                ),
                ui.output_ui("inflation_chart", height="400px"), full_screen=True,
            ),
            style="padding: 1rem;",
        ),
    )


def page_server(input, output, session, data_store):
    DATA = data_store.get("ine", {})

    @render.ui
    def inflation_chart():
        cpi_df = filter_by_period(DATA.get("cpi", pd.DataFrame()), input.prices_period())
        cpi_groups_df = filter_by_period(DATA.get("cpi_special_groups", pd.DataFrame()), input.prices_period())
        fig = _build_inflation_chart(cpi_df, cpi_groups_df)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")
