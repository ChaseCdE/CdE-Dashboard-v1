"""Economic Activity (Actividad) page module."""

import pandas as pd
import plotly.graph_objects as go
from shiny import ui, render, reactive

from charts import COLORS


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _build_gdp_change_chart(df, mode):
    """GDP % change line chart (YoY or QoQ)."""
    if df.empty:
        return None

    df = df.copy()
    if mode == "qoq":
        df["change"] = df["gdp_index"].pct_change(1) * 100
        hover_label = "QoQ"
    else:
        df["change"] = df["yoy_change"]
        hover_label = "YoY"

    df = df.dropna(subset=["change"])
    df["change"] = df["change"].round(1)
    x_dates = pd.to_datetime(df["date"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_dates, y=df["change"],
        mode="lines+markers", name=hover_label,
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=7, color=COLORS["primary"]),
        hovertemplate=hover_label + ": %{y:+.1f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="solid", line_color=COLORS["grid"], line_width=1)

    # Label on last observation
    last_x, last_y = x_dates.iloc[-1], df["change"].iloc[-1]
    fig.add_annotation(x=last_x, y=last_y, text=f"<b>{last_y:+.1f}%</b>",
                       showarrow=False, font=dict(size=12, color=COLORS["primary"]),
                       yshift=14, xanchor="center")

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12",
                   rangeslider=dict(visible=True, thickness=0.06)),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", tickformat=".1f", zeroline=False),
        margin=dict(l=50, r=20, t=16, b=10),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", showlegend=False, height=380,
    )
    return fig


def _build_gdp_index_chart(df):
    """GDP index rebased to 2019 = 100."""
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Rebase: 2019 average = 100
    base = df.loc[df["date"].dt.year == 2019, "gdp_index"].mean()
    if pd.isna(base) or base == 0:
        return None
    df["index_100"] = (df["gdp_index"] / base * 100).round(1)

    # From 2019 Q1 onward (base year)
    df = df[df["date"] >= "2019-01-01"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["index_100"],
        mode="lines+markers", name="PIB",
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=6, color=COLORS["primary"]),
        hovertemplate="Indice: %{y:.1f}<extra></extra>",
    ))

    # Reference line at 100
    fig.add_hline(y=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                  annotation_text="2019 = 100", annotation_position="right",
                  annotation_font_size=10, annotation_font_color=COLORS["neutral"])

    # Label on last observation
    last_x, last_y = df["date"].iloc[-1], df["index_100"].iloc[-1]
    fig.add_annotation(x=last_x, y=last_y, text=f"<b>{last_y:.1f}</b>",
                       showarrow=False, font=dict(size=12, color=COLORS["primary"]),
                       yshift=14, xanchor="center")

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12"),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   tickformat=".0f", zeroline=False),
        margin=dict(l=50, r=20, t=16, b=40),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", showlegend=False, height=340,
    )
    return fig


def _build_gdp_demand_chart(df):
    """GDP growth decomposition — stacked bar chart with original signs."""
    if df.empty or "component" not in df.columns:
        return None

    component_colors = {
        "private_consumption": COLORS["primary"],
        "public_consumption": "#3d6b8e",
        "gfcf": COLORS["accent"],
        "external_demand": "#c9943e",
    }
    component_labels = {
        "private_consumption": "Consumo Privado",
        "public_consumption": "Consumo Publico",
        "gfcf": "FBCF",
        "external_demand": "Demanda Externa",
    }

    pivot = df.pivot_table(
        index="date", columns="component", values="contribution", aggfunc="first"
    ).reset_index()

    order = ["private_consumption", "public_consumption", "gfcf", "external_demand"]
    available = [c for c in order if c in pivot.columns]
    pivot = pivot.dropna(subset=available, how="all")
    for col in available:
        pivot[col] = pivot[col].fillna(0).round(2)

    # Last 3 years only
    pivot["date"] = pd.to_datetime(pivot["date"])
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=3)
    pivot = pivot[pivot["date"] >= cutoff]

    x_dates = pd.to_datetime(pivot["date"])

    fig = go.Figure()
    for comp in order:
        if comp not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            x=x_dates, y=pivot[comp],
            name=component_labels.get(comp, comp),
            marker_color=component_colors.get(comp, COLORS["neutral"]),
            hovertemplate=(
                f"<b>{component_labels.get(comp, comp)}</b><br>"
                "%{y:+.2f} pp<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode="relative",
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12"),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix=" pp", tickformat="+.1f", zeroline=True,
                   zerolinecolor=COLORS["grid"], zerolinewidth=1),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0,
                    font=dict(size=11)),
        margin=dict(l=50, r=20, t=16, b=60),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", height=340,
    )
    return fig


def _prepare_production_series(df, mode, value_col):
    """Prepare a single production series for a given mode. Returns (dates, values) or None."""
    if df.empty:
        return None, None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    if mode == "index":
        # Use January 2021 as base (= 100)
        jan_2021_mask = (df["date"].dt.year == 2021) & (df["date"].dt.month == 1)
        base = df.loc[jan_2021_mask, value_col].values
        if len(base) == 0 or pd.isna(base[0]) or base[0] == 0:
            return None, None
        df["val"] = (df[value_col] / base[0] * 100).round(1)
    elif mode == "mom":
        df["val"] = (df[value_col].pct_change(1) * 100).round(1)
    else:  # yoy
        df["val"] = df["yoy_change"].round(1) if "yoy_change" in df.columns else None

    df = df.dropna(subset=["val"])
    if df.empty:
        return None, None

    if mode == "index":
        df = df[df["date"] >= "2021-01-01"]
    else:
        cutoff = pd.Timestamp.now() - pd.DateOffset(years=3)
        df = df[df["date"] >= cutoff]

    return df["date"], df["val"]


def _build_sector_bar_chart(df, mode="ytd"):
    """Build a horizontal bar chart for sectoral breakdown."""
    if df.empty:
        return None, None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    value_col = "ytd_change" if mode == "ytd" else "yoy_change"

    # Get latest date's data with valid values for the selected mode
    df_valid = df.dropna(subset=[value_col])
    if df_valid.empty:
        return None, None

    latest_date = df_valid["date"].max()
    latest_df = df_valid[df_valid["date"] == latest_date].copy()

    if latest_df.empty:
        return None, None

    # Sort by value for better visualization
    latest_df = latest_df.sort_values(value_col, ascending=True)

    # Create colors based on positive/negative values
    colors = [COLORS["positive"] if v >= 0 else COLORS["negative"] for v in latest_df[value_col]]

    # Hide bar text for zero values (will use annotations instead)
    bar_texts = [f"{v:+.1f}%" if v != 0 else "" for v in latest_df[value_col]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=latest_df[value_col],
        y=latest_df["sector_label"],
        orientation="h",
        marker_color=colors,
        text=bar_texts,
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="%{y}: %{x:+.1f}%<extra></extra>",
        cliponaxis=False,  # Allow text to show outside plot area
    ))

    # Add annotations for zero values to ensure they're visible
    for idx, (_, row) in enumerate(latest_df.iterrows()):
        if row[value_col] == 0:
            fig.add_annotation(
                x=0.5,  # Small offset to the right
                y=row["sector_label"],
                text="+0.0%",
                showarrow=False,
                font=dict(size=10),
                xanchor="left",
            )

    fig.update_layout(
        xaxis=dict(
            title="", showgrid=True, gridcolor=COLORS["grid"],
            ticksuffix="%", zeroline=True, zerolinecolor=COLORS["grid"],
        ),
        yaxis=dict(title="", showgrid=False),
        margin=dict(l=120, r=50, t=10, b=40),
        font=dict(family="Arial"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280,
        showlegend=False,
    )

    # Format period string
    period_str = latest_date.strftime("%B %Y")

    return fig, period_str


def _build_combined_production_chart(ipi_df, services_df, mode):
    """Combined IPI + Services production chart."""
    ipi_x, ipi_y = _prepare_production_series(ipi_df, mode, "ipi_index")
    srv_x, srv_y = _prepare_production_series(services_df, mode, "services_prod_index")

    if ipi_x is None and srv_x is None:
        return None

    if mode == "index":
        tick_sfx, tick_fmt = "", ".0f"
        ref_line, ref_text = 100, "Ene 2021 = 100"
    else:
        tick_sfx, tick_fmt = "%", ".1f"
        ref_line, ref_text = 0, None

    hover_labels = {"yoy": "YoY", "mom": "MoM", "index": "Indice"}
    h = hover_labels.get(mode, "YoY")

    ipi_color = COLORS["primary"]
    srv_color = "#b94a48"  # reddish

    fig = go.Figure()

    if ipi_x is not None:
        hover_tpl = f"{h}: %{{y:.1f}}<extra></extra>" if mode == "index" else f"{h}: %{{y:+.1f}}%<extra></extra>"
        fig.add_trace(go.Scatter(
            x=ipi_x, y=ipi_y, mode="lines+markers",
            name="Produccion Industrial",
            line=dict(color=ipi_color, width=2.5),
            marker=dict(size=5, color=ipi_color),
            hovertemplate=hover_tpl,
        ))
        last_y = ipi_y.iloc[-1]
        lbl = f"<b>{last_y:.1f}</b>" if mode == "index" else f"<b>{last_y:+.1f}%</b>"
        fig.add_annotation(x=ipi_x.iloc[-1], y=last_y, text=lbl, showarrow=False,
                           font=dict(size=11, color=ipi_color), yshift=14, xanchor="center")

    if srv_x is not None:
        hover_tpl = f"{h}: %{{y:.1f}}<extra></extra>" if mode == "index" else f"{h}: %{{y:+.1f}}%<extra></extra>"
        fig.add_trace(go.Scatter(
            x=srv_x, y=srv_y, mode="lines+markers",
            name="Produccion de Servicios",
            line=dict(color=srv_color, width=2.5),
            marker=dict(size=5, color=srv_color),
            hovertemplate=hover_tpl,
        ))
        last_y = srv_y.iloc[-1]
        lbl = f"<b>{last_y:.1f}</b>" if mode == "index" else f"<b>{last_y:+.1f}%</b>"
        fig.add_annotation(x=srv_x.iloc[-1], y=last_y, text=lbl, showarrow=False,
                           font=dict(size=11, color=srv_color), yshift=-18, xanchor="center")

    if ref_line is not None:
        kwargs = {}
        if ref_text:
            kwargs.update(annotation_text=ref_text, annotation_position="right",
                          annotation_font_size=10, annotation_font_color=COLORS["neutral"])
        fig.add_hline(y=ref_line, line_dash="dot" if ref_text else "solid",
                      line_color=COLORS["grid"], line_width=1, **kwargs)

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="%b %Y",
                   showgrid=False, dtick="M12"),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix=tick_sfx, tickformat=tick_fmt, zeroline=False),
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="left", x=0,
                    font=dict(size=11)),
        margin=dict(l=50, r=20, t=16, b=55),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", height=380,
    )
    return fig


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def page_ui(data_store):
    DATA = data_store.get("ine", {})
    gdp_df = DATA.get("gdp", pd.DataFrame())

    # Pre-render defaults so they show on first load
    change_fig = _build_gdp_change_chart(gdp_df, "yoy")
    change_html = ui.HTML(change_fig.to_html(full_html=False, include_plotlyjs="cdn")) if change_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    index_fig = _build_gdp_index_chart(gdp_df)
    index_html = ui.HTML(index_fig.to_html(full_html=False, include_plotlyjs="cdn")) if index_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    demand_fig = _build_gdp_demand_chart(DATA.get("gdp_demand", pd.DataFrame()))
    demand_html = ui.HTML(demand_fig.to_html(full_html=False, include_plotlyjs="cdn")) if demand_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    # Pre-render combined production chart (default: YoY)
    prod_fig = _build_combined_production_chart(
        DATA.get("industrial_production", pd.DataFrame()),
        DATA.get("services_production", pd.DataFrame()), "yoy")
    prod_html = ui.HTML(prod_fig.to_html(full_html=False, include_plotlyjs="cdn")) if prod_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    return ui.nav_panel(
        "Actividad",
        ui.div(
            # --- Row 1: GDP % change chart ---
            ui.h5("Producto Interior Bruto (variacion, en porcentaje)",
                   class_="chart-title"),

            ui.div(
                ui.input_radio_buttons(
                    "gdp_change_type", None,
                    choices={"yoy": "Interanual", "qoq": "Trimestral"},
                    selected="yoy", inline=True,
                ),
                class_="toggle-btn-group",
            ),

            ui.div(
                change_html,
                ui.output_ui("gdp_change_chart"),
                id="gdp_chart_container",
            ),

            # --- Row 2: GDP index + GDP decomposition ---
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.tags.strong("PIB (Indice, 2019=100)")),
                    index_html,
                ),
                ui.card(
                    ui.card_header(ui.tags.strong("Descomposicion del crecimiento del PIB (aportacion, en pp)")),
                    demand_html,
                ),
                col_widths={"sm": 12, "md": 6},
                class_="mt-4",
            ),

            # --- Row 3: Combined production chart ---
            ui.h5("Indices de Produccion", class_="chart-title", style="margin-top: 2rem;"),

            ui.div(
                ui.input_radio_buttons(
                    "production_mode", None,
                    choices={
                        "yoy": "Interanual",
                        "mom": "Mensual",
                        "index": "Indice (2021=100)",
                    },
                    selected="yoy", inline=True,
                ),
                class_="toggle-btn-group",
            ),

            ui.div(
                prod_html,
                ui.output_ui("production_chart"),
                id="production_chart_container",
            ),

            # --- Row 4: Sectoral breakdown bar charts ---
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("Producción industrial por sector"),
                        ui.tags.br(),
                        ui.output_ui("ipi_sector_subtitle"),
                    )),
                    ui.div(
                        ui.input_radio_buttons(
                            "ipi_sector_mode", None,
                            choices={"ytd": "En lo que va de año", "yoy": "Interanual"},
                            selected="ytd", inline=True,
                        ),
                        class_="toggle-btn-group",
                        style="margin-bottom: 0.5rem;",
                    ),
                    ui.output_ui("ipi_sectors_chart"),
                ),
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("Producción del sector servicios por sector"),
                        ui.tags.br(),
                        ui.output_ui("ipss_sector_subtitle"),
                    )),
                    ui.div(
                        ui.input_radio_buttons(
                            "ipss_sector_mode", None,
                            choices={"ytd": "En lo que va de año", "yoy": "Interanual"},
                            selected="ytd", inline=True,
                        ),
                        class_="toggle-btn-group",
                        style="margin-bottom: 0.5rem;",
                    ),
                    ui.output_ui("ipss_sectors_chart"),
                ),
                col_widths={"sm": 12, "md": 6},
                class_="mt-4",
            ),

            style="padding: 1.5rem;",
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def page_server(input, output, session, data_store):
    DATA = data_store.get("ine", {})

    @render.ui
    @reactive.event(input.gdp_change_type)
    def gdp_change_chart():
        mode = input.gdp_change_type()
        fig = _build_gdp_change_chart(DATA.get("gdp", pd.DataFrame()), mode)

        hide_default = ui.tags.script(
            "document.querySelectorAll('#gdp_chart_container > :not(#gdp_change_chart)')"
            ".forEach(function(el){ el.style.display='none'; });"
        )
        if fig is None:
            return ui.TagList(hide_default, ui.div("Datos no disponibles", class_="no-data-placeholder"))
        return ui.TagList(hide_default, ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")))

    @render.ui
    @reactive.event(input.production_mode)
    def production_chart():
        mode = input.production_mode()
        fig = _build_combined_production_chart(
            DATA.get("industrial_production", pd.DataFrame()),
            DATA.get("services_production", pd.DataFrame()), mode)
        hide = ui.tags.script(
            "document.querySelectorAll('#production_chart_container > :not(#production_chart)')"
            ".forEach(function(el){ el.style.display='none'; });")
        if fig is None:
            return ui.TagList(hide, ui.div("Datos no disponibles", class_="no-data-placeholder"))
        return ui.TagList(hide, ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn")))

    # --- IPI Sectors ---
    @render.ui
    def ipi_sector_subtitle():
        mode = input.ipi_sector_mode()
        df = DATA.get("ipi_sectors", pd.DataFrame())
        if df.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        df["date"] = pd.to_datetime(df["date"])
        value_col = "ytd_change" if mode == "ytd" else "yoy_change"
        df_valid = df.dropna(subset=[value_col])
        if df_valid.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        latest_date = df_valid["date"].max()
        period_str = latest_date.strftime("%B %Y")
        return ui.tags.small(f"Variación, en porcentaje. {period_str}", style="color: #6c757d;")

    @render.ui
    def ipi_sectors_chart():
        mode = input.ipi_sector_mode()
        fig, _ = _build_sector_bar_chart(DATA.get("ipi_sectors", pd.DataFrame()), mode)
        if fig is None:
            return ui.div("Datos no disponibles", class_="no-data-placeholder")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    # --- IPSS Sectors ---
    @render.ui
    def ipss_sector_subtitle():
        mode = input.ipss_sector_mode()
        df = DATA.get("ipss_sectors", pd.DataFrame())
        if df.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        df["date"] = pd.to_datetime(df["date"])
        value_col = "ytd_change" if mode == "ytd" else "yoy_change"
        df_valid = df.dropna(subset=[value_col])
        if df_valid.empty:
            return ui.tags.small("Sin datos", style="color: #6c757d;")
        latest_date = df_valid["date"].max()
        period_str = latest_date.strftime("%B %Y")
        return ui.tags.small(f"Variación, en porcentaje. {period_str}", style="color: #6c757d;")

    @render.ui
    def ipss_sectors_chart():
        mode = input.ipss_sector_mode()
        fig, _ = _build_sector_bar_chart(DATA.get("ipss_sectors", pd.DataFrame()), mode)
        if fig is None:
            return ui.div("Datos no disponibles", class_="no-data-placeholder")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))
