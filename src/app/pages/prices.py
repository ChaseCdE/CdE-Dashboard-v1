"""Prices & Inflation (Precios) page module."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from shiny import ui, render

from charts import COLORS, COMMON_LAYOUT
from helpers import filter_by_period

# Spain CCAA GeoJSON URL (hosted on GitHub)
SPAIN_CCAA_GEOJSON_URL = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/spain-communities.geojson"

# Colors for the 4 special groups
GROUP_COLORS = {
    "Alimentos, bebidas y tabaco": "#2563eb",      # Blue
    "Productos energéticos": "#dc2626",             # Red
    "Servicios": "#16a34a",                         # Green
    "Bienes industriales sin productos energéticos": "#9333ea",  # Purple
}

# Colors for IPRI categories
IPRI_COLORS = {
    "total": "#1e40af",              # Blue - Total
    "total_sin_energia": "#7c3aed",  # Purple - Total sin energía
    "consumo": "#059669",            # Green - Consumo
    "equipo": "#d97706",             # Orange - Equipo
    "intermedios": "#6366f1",        # Indigo - Intermedios
    "energia": "#dc2626",            # Red - Energía
}

IPRI_LABELS = {
    "total": "Total",
    "total_sin_energia": "Total sin energía",
    "consumo": "Bienes de consumo",
    "equipo": "Bienes de equipo",
    "intermedios": "Bienes intermedios",
    "energia": "Energía",
}

# Spanish month names
MESES = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
         7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"}


def _build_weights_pie_chart(ecoicop_df):
    """Build pie chart showing CPI weights by the 4 special groups."""
    if ecoicop_df.empty:
        return None

    df = ecoicop_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Get latest date data
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].copy()

    if latest_df.empty:
        return None

    # Get unique weights per group
    weights_df = latest_df[["group_name", "weight"]].drop_duplicates()

    # Sort by weight descending
    weights_df = weights_df.sort_values("weight", ascending=False)

    # Assign colors
    colors = [GROUP_COLORS.get(g, "#6b7280") for g in weights_df["group_name"]]

    fig = go.Figure(data=[go.Pie(
        labels=weights_df["group_name"],
        values=weights_df["weight"],
        hole=0.4,
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=11),
        marker=dict(colors=colors),
        hovertemplate="%{label}<br>Peso: %{value:.1f}‰<br>(%{percent})<extra></extra>",
    )])

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=350,
    )

    return fig


def _build_contributions_bar_chart(ecoicop_df):
    """Build stacked bar chart showing inflation decomposition by contribution."""
    if ecoicop_df.empty:
        return None

    df = ecoicop_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Get last 12 months of data
    latest_date = df["date"].max()
    cutoff_date = latest_date - pd.DateOffset(months=11)
    df = df[df["date"] >= cutoff_date].copy()

    if df.empty:
        return None

    # Pivot to get contributions by group over time
    pivot_df = df.pivot_table(
        index="date",
        columns="group_name",
        values="contribution",
        aggfunc="first"
    ).reset_index()

    # Define order: Servicios first (largest), then others
    col_order = ["Servicios", "Alimentos, bebidas y tabaco", "Bienes industriales sin productos energéticos", "Productos energéticos"]

    fig = go.Figure()

    # Separate positive and negative contributions for proper stacking
    for col in col_order:
        if col in pivot_df.columns:
            fig.add_trace(go.Bar(
                x=pivot_df["date"],
                y=pivot_df[col],
                name=col,
                marker_color=GROUP_COLORS.get(col, "#6b7280"),
                hovertemplate=f"{col}: %{{y:.2f}}pp<extra></extra>",
            ))

    fig.update_layout(
        **COMMON_LAYOUT,
        barmode="relative",  # Use relative for proper negative value stacking
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.30,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(l=50, r=20, t=20, b=80),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            tickformat="%b %Y",
        ),
        yaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            ticksuffix="pp",
            title="Aportación (pp)",
            zeroline=True,
            zerolinecolor="#666",
            zerolinewidth=1,
        ),
        height=400,
    )

    return fig


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


def _build_ipri_general_chart(ipri_df, metric="yoy_change"):
    """Build IPRI chart showing General and General without energy."""
    if ipri_df.empty:
        return None

    df = ipri_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Filter for the two series we want
    categories = ["total", "total_sin_energia"]

    fig = go.Figure()

    for cat in categories:
        cat_df = df[df["category"] == cat].copy()
        if cat_df.empty:
            continue

        cat_df = cat_df.sort_values("date")

        # Select the metric column
        if metric == "ipri_index":
            y_col = "ipri_index"
            suffix = ""
            hover_suffix = ""
            # Rebase to first 2021 value = 100
            base_df = cat_df[cat_df["date"].dt.year == 2021]
            if not base_df.empty:
                base_val = base_df[y_col].iloc[0]
                if base_val and base_val != 0:
                    cat_df[y_col] = (cat_df[y_col] / base_val) * 100
        elif metric == "mom_change":
            y_col = "mom_change"
            suffix = "%"
            hover_suffix = "%"
        else:  # yoy_change
            y_col = "yoy_change"
            suffix = "%"
            hover_suffix = "%"

        if y_col not in cat_df.columns:
            continue

        cat_df = cat_df.dropna(subset=[y_col])
        if cat_df.empty:
            continue

        # Create Spanish date for hover
        cat_df["date_es"] = cat_df["date"].apply(
            lambda d: f"{d.day} {MESES.get(d.month, '')} {d.year}"
        )

        color = IPRI_COLORS.get(cat, "#6b7280")
        label = IPRI_LABELS.get(cat, cat)

        fig.add_trace(go.Scatter(
            x=cat_df["date"],
            y=cat_df[y_col],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2.5),
            marker=dict(size=4, color=color),
            customdata=cat_df["date_es"],
            hovertemplate=f"<b>{label}</b><br>%{{customdata}}<br>%{{y:.1f}}{hover_suffix}<extra></extra>",
        ))

        # Add last value annotation (positioned to the right)
        if not cat_df.empty:
            last_date = cat_df["date"].iloc[-1]
            last_val = cat_df[y_col].iloc[-1]
            fig.add_annotation(
                x=last_date, y=last_val,
                text=f"<b>{last_val:.1f}{suffix}</b>",
                showarrow=False,
                font=dict(size=10, color=color),
                xshift=35,
                xanchor="left",
            )

    # Add zero line for variation metrics
    if metric in ["yoy_change", "mom_change"]:
        fig.add_hline(y=0, line_dash="dot", line_color="#666", line_width=1)

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=50, r=70, t=40, b=50),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            tickformat="%b %Y",
        ),
        yaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            ticksuffix="%" if metric != "ipri_index" else "",
        ),
        height=400,
    )

    return fig


def _build_ipri_sectors_chart(ipri_df, metric="yoy_change", period="3y"):
    """Build IPRI chart by economic destination (sectors)."""
    if ipri_df.empty:
        return None

    df = ipri_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Calculate base values for rebasing BEFORE filtering by period
    base_values = {}
    if metric == "ipri_index":
        for cat in ["total", "consumo", "equipo", "intermedios", "energia"]:
            cat_full = df[df["category"] == cat].copy()
            cat_full = cat_full.sort_values("date")
            base_df = cat_full[cat_full["date"].dt.year == 2021]
            if not base_df.empty and "ipri_index" in base_df.columns:
                base_values[cat] = base_df["ipri_index"].iloc[0]

    # Filter by period
    max_date = df["date"].max()
    if period == "1y":
        df = df[df["date"] >= max_date - pd.DateOffset(years=1)]
    elif period == "3y":
        df = df[df["date"] >= max_date - pd.DateOffset(years=3)]
    elif period == "5y":
        df = df[df["date"] >= max_date - pd.DateOffset(years=5)]

    # Sectors to show
    categories = ["total", "consumo", "equipo", "intermedios", "energia"]

    fig = go.Figure()

    for cat in categories:
        cat_df = df[df["category"] == cat].copy()
        if cat_df.empty:
            continue

        cat_df = cat_df.sort_values("date")

        # Select the metric column
        if metric == "ipri_index":
            y_col = "ipri_index"
            hover_suffix = ""
            # Rebase to first 2021 value = 100
            base_val = base_values.get(cat)
            if base_val and base_val != 0:
                cat_df[y_col] = (cat_df[y_col] / base_val) * 100
        elif metric == "mom_change":
            y_col = "mom_change"
            hover_suffix = "%"
        else:  # yoy_change
            y_col = "yoy_change"
            hover_suffix = "%"

        if y_col not in cat_df.columns:
            continue

        cat_df = cat_df.dropna(subset=[y_col])
        if cat_df.empty:
            continue

        # Create Spanish date for hover
        cat_df["date_es"] = cat_df["date"].apply(
            lambda d: f"{d.day} {MESES.get(d.month, '')} {d.year}"
        )

        color = IPRI_COLORS.get(cat, "#6b7280")
        label = IPRI_LABELS.get(cat, cat)

        fig.add_trace(go.Scatter(
            x=cat_df["date"],
            y=cat_df[y_col],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2 if cat != "total" else 2.5),
            marker=dict(size=3, color=color),
            customdata=cat_df["date_es"],
            hovertemplate=f"<b>{label}</b><br>%{{customdata}}<br>%{{y:.1f}}{hover_suffix}<extra></extra>",
        ))

        # Add last value annotation (positioned to the right)
        if not cat_df.empty:
            last_date = cat_df["date"].iloc[-1]
            last_val = cat_df[y_col].iloc[-1]
            suffix = "%" if metric != "ipri_index" else ""
            fig.add_annotation(
                x=last_date, y=last_val,
                text=f"<b>{last_val:.1f}{suffix}</b>",
                showarrow=False,
                font=dict(size=9, color=color),
                xshift=30,
                xanchor="left",
            )

    # Add zero line for variation metrics
    if metric in ["yoy_change", "mom_change"]:
        fig.add_hline(y=0, line_dash="dot", line_color="#666", line_width=1)

    fig.update_layout(
        **COMMON_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(l=50, r=70, t=30, b=70),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            tickformat="%b %Y",
        ),
        yaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=0.5,
            ticksuffix="%" if metric != "ipri_index" else "",
        ),
        height=400,
    )

    return fig


# CCAA code to GeoJSON name mapping (names must match GeoJSON exactly)
CCAA_TO_GEOJSON = {
    "AN": "Andalucia",
    "AR": "Aragon",
    "AS": "Asturias",
    "IB": "Baleares",
    "CN": "Canarias",
    "CB": "Cantabria",
    "CL": "Castilla-Leon",
    "CM": "Castilla-La Mancha",
    "CT": "Cataluña",
    "VC": "Valencia",
    "EX": "Extremadura",
    "GA": "Galicia",
    "MD": "Madrid",
    "MC": "Murcia",
    "NC": "Navarra",
    "PV": "Pais Vasco",
    "RI": "La Rioja",
    "CE": "Ceuta",
    "ML": "Melilla",
}


def _shift_canarias_coordinates(geojson):
    """Shift Canary Islands coordinates to appear as inset near mainland Spain."""
    # Offset to move Canarias: ~5 degrees east and ~7 degrees north
    lon_offset = 5.0
    lat_offset = 7.0

    def shift_coords(coords):
        """Recursively shift coordinates."""
        if isinstance(coords[0], (int, float)):
            # This is a coordinate pair [lon, lat]
            return [coords[0] + lon_offset, coords[1] + lat_offset]
        else:
            # This is a list of coordinates or polygons
            return [shift_coords(c) for c in coords]

    for feature in geojson["features"]:
        if feature["properties"]["name"] == "Canarias":
            geometry = feature["geometry"]
            geometry["coordinates"] = shift_coords(geometry["coordinates"])
            break

    return geojson


def _build_cpi_ccaa_map(cpi_ccaa_df):
    """Build choropleth map showing CPI YoY change by CCAA."""
    import requests
    import copy

    if cpi_ccaa_df.empty:
        return None

    df = cpi_ccaa_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Get latest date data
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].copy()

    if latest_df.empty:
        return None

    # Map CCAA codes to GeoJSON names
    latest_df["geojson_name"] = latest_df["ccaa_code"].map(CCAA_TO_GEOJSON)

    # Fetch GeoJSON
    try:
        response = requests.get(SPAIN_CCAA_GEOJSON_URL, timeout=10)
        geojson = copy.deepcopy(response.json())
    except Exception:
        return None

    # Shift Canarias to appear as inset near mainland
    geojson = _shift_canarias_coordinates(geojson)

    # Create custom hover text
    latest_df["hover_text"] = latest_df.apply(
        lambda row: f"<b>{row['ccaa_name']}</b><br>"
                    f"Var. anual: {row['yoy_change']:.1f}%<br>"
                    f"Var. mensual: {row['mom_change']:.1f}%" if pd.notna(row['mom_change'])
                    else f"<b>{row['ccaa_name']}</b><br>Var. anual: {row['yoy_change']:.1f}%",
        axis=1
    )

    fig = px.choropleth(
        latest_df,
        geojson=geojson,
        locations="geojson_name",
        featureidkey="properties.name",
        color="yoy_change",
        color_continuous_scale="RdYlGn_r",  # Red for high inflation, green for low
        range_color=[latest_df["yoy_change"].min() - 0.5, latest_df["yoy_change"].max() + 0.5],
        hover_name="ccaa_name",
        custom_data=["ccaa_name", "yoy_change", "mom_change"],
    )

    # Update hover template
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>"
                      "Var. anual: %{customdata[1]:.1f}%<br>"
                      "Var. mensual: %{customdata[2]:.1f}%<extra></extra>"
    )

    fig.update_geos(
        visible=False,
        fitbounds="locations",
        projection_type="mercator",
    )

    # Add a diagonal line between Canarias and mainland Spain
    canarias_separator = dict(
        type="line",
        xref="paper", yref="paper",
        x0=0.35, y0=0.38,
        x1=0.42, y1=0.31,
        line=dict(color="#999", width=1),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="Var. anual (%)",
            ticksuffix="%",
            len=0.6,
            thickness=15,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        height=450,
        shapes=[canarias_separator],
    )

    return fig, latest_date


def page_ui(data_store):
    return ui.nav_panel(
        "Precios",
        ui.div(
            ui.h2("Precios e Inflación", class_="section-header"),
            ui.p("Índices de precios al consumo y tendencias de inflación.", class_="section-description"),

            # Row 1: Inflation chart: General vs Subyacente (YoY change)
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

            # Row 2: CPI Weights pie chart and Inflation Decomposition
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Composición del IPC"),
                            ui.tags.br(),
                            ui.output_ui("weights_subtitle"),
                        )),
                        ui.output_ui("weights_pie_chart", height="350px"),
                        full_screen=True,
                    ),
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Descomposición de la inflación"),
                            ui.tags.br(),
                            ui.output_ui("contributions_subtitle"),
                        )),
                        ui.output_ui("contributions_bar_chart", height="400px"),
                        full_screen=True,
                    ),
                ),
            ),

            # Row 3: Industrial Price Index (IPRI)
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Precios Industriales (IPRI)"),
                            ui.tags.br(),
                            ui.tags.small("General y General sin energía", style="color: #6c757d;"),
                        )),
                        ui.div(
                            ui.input_radio_buttons(
                                "ipri_metric", None,
                                choices={
                                    "ipri_index": "Índice (ene2021=100)",
                                    "yoy_change": "Var. interanual",
                                    "mom_change": "Var. mensual",
                                },
                                selected="yoy_change", inline=True,
                            ),
                            class_="toggle-btn-group",
                        ),
                        ui.output_ui("ipri_general_chart", height="400px"),
                        full_screen=True,
                    ),
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("Precios industriales por destino económico"),
                            ui.tags.br(),
                            ui.output_ui("ipri_sectors_subtitle"),
                        )),
                        ui.div(
                            ui.input_radio_buttons(
                                "ipri_sectors_period", None,
                                choices={"5y": "5 años", "3y": "3 años", "1y": "1 año"},
                                selected="3y", inline=True,
                            ),
                            class_="toggle-btn-group",
                        ),
                        ui.output_ui("ipri_sectors_chart", height="400px"),
                        full_screen=True,
                    ),
                ),
            ),

            # Row 4: CPI Map by CCAA (left) and Table (right)
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("IPC por Comunidad Autónoma"),
                            ui.tags.br(),
                            ui.output_ui("cpi_ccaa_map_subtitle"),
                        )),
                        ui.output_ui("cpi_ccaa_map", height="450px"),
                        full_screen=True,
                    ),
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header(ui.div(
                            ui.tags.strong("IPC por CCAA"),
                            ui.tags.br(),
                            ui.output_ui("cpi_ccaa_table_subtitle"),
                        )),
                        ui.output_ui("cpi_ccaa_table", height="450px"),
                        full_screen=True,
                    ),
                ),
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

    @render.ui
    def weights_subtitle():
        ecoicop_df = DATA.get("cpi_ecoicop_groups", pd.DataFrame())
        if ecoicop_df.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        year = ecoicop_df["year"].iloc[-1] if "year" in ecoicop_df.columns else "N/A"
        return ui.tags.small(f"Ponderaciones por grupo especial. {year}", style="color: #6c757d;")

    @render.ui
    def weights_pie_chart():
        ecoicop_df = DATA.get("cpi_ecoicop_groups", pd.DataFrame())
        fig = _build_weights_pie_chart(ecoicop_df)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def contributions_subtitle():
        ecoicop_df = DATA.get("cpi_ecoicop_groups", pd.DataFrame())
        if ecoicop_df.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        ecoicop_df["date"] = pd.to_datetime(ecoicop_df["date"])
        latest_date = ecoicop_df["date"].max()
        period_str = latest_date.strftime("%B %Y")
        return ui.tags.small(f"Aportación de cada grupo a la inflación. Últimos 12 meses hasta {period_str}", style="color: #6c757d;")

    @render.ui
    def contributions_bar_chart():
        ecoicop_df = DATA.get("cpi_ecoicop_groups", pd.DataFrame())
        fig = _build_contributions_bar_chart(ecoicop_df)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    # IPRI charts
    @render.ui
    def ipri_general_chart():
        ipri_df = DATA.get("ipri", pd.DataFrame())
        metric = input.ipri_metric()
        fig = _build_ipri_general_chart(ipri_df, metric)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    @render.ui
    def ipri_sectors_subtitle():
        metric = input.ipri_metric()
        subtitles = {
            "ipri_index": "Índice (ene2021=100)",
            "yoy_change": "Variación interanual",
            "mom_change": "Variación mensual",
        }
        return ui.tags.small(subtitles.get(metric, ""), style="color: #6c757d;")

    @render.ui
    def ipri_sectors_chart():
        ipri_df = DATA.get("ipri", pd.DataFrame())
        metric = input.ipri_metric()
        period = input.ipri_sectors_period()
        fig = _build_ipri_sectors_chart(ipri_df, metric, period)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")) if fig else ui.div("No data", class_="no-data-placeholder")

    # CPI by CCAA Map
    @render.ui
    def cpi_ccaa_map_subtitle():
        cpi_ccaa_df = DATA.get("cpi_ccaa", pd.DataFrame())
        if cpi_ccaa_df.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        cpi_ccaa_df["date"] = pd.to_datetime(cpi_ccaa_df["date"])
        latest_date = cpi_ccaa_df["date"].max()
        period_str = latest_date.strftime("%B %Y")
        return ui.tags.small(f"Variación interanual del IPC. {period_str}", style="color: #6c757d;")

    @render.ui
    def cpi_ccaa_map():
        cpi_ccaa_df = DATA.get("cpi_ccaa", pd.DataFrame())
        result = _build_cpi_ccaa_map(cpi_ccaa_df)
        if result is None:
            return ui.div("No data available", class_="no-data-placeholder")
        fig, _ = result
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    # CPI by CCAA Table
    @render.ui
    def cpi_ccaa_table_subtitle():
        cpi_ccaa_df = DATA.get("cpi_ccaa", pd.DataFrame())
        if cpi_ccaa_df.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        cpi_ccaa_df["date"] = pd.to_datetime(cpi_ccaa_df["date"])
        latest_date = cpi_ccaa_df["date"].max()
        period_str = latest_date.strftime("%B %Y")
        return ui.tags.small(f"Datos a {period_str}", style="color: #6c757d;")

    @render.ui
    def cpi_ccaa_table():
        cpi_ccaa_df = DATA.get("cpi_ccaa", pd.DataFrame())
        if cpi_ccaa_df.empty:
            return ui.div("No data available", class_="no-data-placeholder")

        df = cpi_ccaa_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        latest_date = df["date"].max()
        latest_df = df[df["date"] == latest_date].copy()

        # Sort by YoY change descending
        latest_df = latest_df.sort_values("yoy_change", ascending=False)

        # Build HTML table
        rows = []
        for _, row in latest_df.iterrows():
            yoy_color = "#dc2626" if row["yoy_change"] > 2.5 else "#16a34a" if row["yoy_change"] < 2.0 else "#d97706"
            mom_color = "#dc2626" if row["mom_change"] > 0.3 else "#16a34a" if row["mom_change"] < 0 else "#6b7280"
            rows.append(f"""
                <tr>
                    <td style="padding: 6px 10px; border-bottom: 1px solid #e5e7eb;">{row['ccaa_name']}</td>
                    <td style="padding: 6px 10px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {yoy_color}; font-weight: 500;">{row['yoy_change']:.1f}%</td>
                    <td style="padding: 6px 10px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {mom_color};">{row['mom_change']:.1f}%</td>
                </tr>
            """)

        table_html = f"""
        <div style="max-height: 420px; overflow-y: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background: #f9fafb; position: sticky; top: 0;">
                        <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e5e7eb;">CCAA</th>
                        <th style="padding: 8px 10px; text-align: right; border-bottom: 2px solid #e5e7eb;">Var. anual</th>
                        <th style="padding: 8px 10px; text-align: right; border-bottom: 2px solid #e5e7eb;">Var. mensual</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>
        """
        return ui.HTML(table_html)
