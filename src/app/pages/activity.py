"""Economic Activity (Actividad) page module."""

import pandas as pd
import plotly.graph_objects as go
from shiny import ui, render, reactive

from charts import COLORS


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _build_gdp_chart(df, mode):
    """GDP chart: YoY % change, QoQ % change, or Index (2019=100)."""
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    if mode == "index":
        # Rebase: 2019 average = 100
        base = df.loc[df["date"].dt.year == 2019, "gdp_index"].mean()
        if pd.isna(base) or base == 0:
            return None
        df["val"] = (df["gdp_index"] / base * 100).round(1)
        # From 2019 Q1 onward (base year)
        df = df[df["date"] >= "2019-01-01"]
        hover_label = "Índice"
        tick_suffix = ""
        tick_format = ".0f"
        ref_line = 100
        ref_text = "2019 = 100"
        label_fmt = lambda v: f"<b>{v:.1f}</b>"
    elif mode == "qoq":
        df["val"] = (df["gdp_index"].pct_change(1) * 100).round(1)
        df = df.dropna(subset=["val"])
        hover_label = "QoQ"
        tick_suffix = "%"
        tick_format = ".1f"
        ref_line = 0
        ref_text = None
        label_fmt = lambda v: f"<b>{v:+.1f}%</b>"
    else:  # yoy
        df["val"] = df["yoy_change"].round(1)
        df = df.dropna(subset=["val"])
        hover_label = "YoY"
        tick_suffix = "%"
        tick_format = ".1f"
        ref_line = 0
        ref_text = None
        label_fmt = lambda v: f"<b>{v:+.1f}%</b>"

    if df.empty:
        return None

    x_dates = df["date"]

    fig = go.Figure()

    if mode == "index":
        hover_tpl = f"{hover_label}: %{{y:.1f}}<extra></extra>"
    else:
        hover_tpl = f"{hover_label}: %{{y:+.1f}}%<extra></extra>"

    fig.add_trace(go.Scatter(
        x=x_dates, y=df["val"],
        mode="lines+markers", name=hover_label,
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=7, color=COLORS["primary"]),
        hovertemplate=hover_tpl,
    ))

    # Reference line
    if ref_text:
        fig.add_hline(y=ref_line, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                      annotation_text=ref_text, annotation_position="right",
                      annotation_font_size=10, annotation_font_color=COLORS["neutral"])
    else:
        fig.add_hline(y=ref_line, line_dash="solid", line_color=COLORS["grid"], line_width=1)

    # Label on last observation
    last_x, last_y = x_dates.iloc[-1], df["val"].iloc[-1]
    fig.add_annotation(x=last_x, y=last_y, text=label_fmt(last_y),
                       showarrow=False, font=dict(size=12, color=COLORS["primary"]),
                       yshift=14, xanchor="center")

    # Only show rangeslider for change modes (not index)
    rangeslider_cfg = dict(visible=True, thickness=0.06) if mode != "index" else dict(visible=False)

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12",
                   rangeslider=rangeslider_cfg),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix=tick_suffix, tickformat=tick_format, zeroline=False),
        margin=dict(l=50, r=20, t=16, b=10),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", showlegend=False, height=380,
    )
    return fig


# Country colors and labels for GDP comparison
GDP_COUNTRY_COLORS = {
    "spain": "#dc2626",      # Red
    "germany": "#1e40af",    # Blue
    "france": "#7c3aed",     # Purple
    "italy": "#059669",      # Green
    "eu27": "#d97706",       # Orange
}

GDP_COUNTRY_LABELS = {
    "spain": "España",
    "germany": "Alemania",
    "france": "Francia",
    "italy": "Italia",
    "eu27": "UE27",
}


def _build_gdp_comparison_chart(df):
    """GDP comparison chart: Spain, Germany, France, Italy, EU27 (Index 2019Q1=100)."""
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()

    # Add each country's line, and collect last-point info for end-of-line labels
    countries = ["spain", "germany", "france", "italy", "eu27"]
    last_points = []
    for country in countries:
        col = f"gdp_index_{country}"
        if col not in df.columns:
            continue

        country_df = df[["date", col]].dropna()
        if country_df.empty:
            continue

        color = GDP_COUNTRY_COLORS.get(country, COLORS["neutral"])
        label = GDP_COUNTRY_LABELS.get(country, country)

        fig.add_trace(go.Scatter(
            x=country_df["date"],
            y=country_df[col],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2.5),
            marker=dict(size=5, color=color),
            hovertemplate=f"{label}: %{{y:.1f}}<extra></extra>",
        ))

        last_points.append({
            "date": country_df["date"].iloc[-1],
            "value": float(country_df[col].iloc[-1]),
            "color": color,
            "label": label,
        })

    # De-collide end-of-line labels: spread labels bidirectionally from center
    # when values are close, to avoid bunching at top or bottom.
    if last_points:
        last_points.sort(key=lambda p: p["value"])
        values = [p["value"] for p in last_points]
        y_range = max(values) - min(values) if len(values) > 1 else 1
        min_gap = max(y_range * 0.12, 2.8)  # ≥ ~2.8 index points or 12% of spread

        # Calculate ideal spread centered around the mean of actual values
        center = sum(values) / len(values)
        n = len(last_points)
        total_span = min_gap * (n - 1)
        start_y = center - total_span / 2

        for i, p in enumerate(last_points):
            ideal_y = start_y + i * min_gap
            # Blend between actual value and ideal spread position
            # to keep labels reasonably close to their data points
            p["display_y"] = p["value"] * 0.3 + ideal_y * 0.7

        for p in last_points:
            shifted = abs(p["display_y"] - p["value"]) > 1e-6
            fig.add_annotation(
                x=p["date"],
                y=p["display_y"],
                # When the label is offset from the actual point, draw a thin
                # leader line back to the true value so the chart stays honest.
                ax=p["date"] if shifted else None,
                ay=p["value"] if shifted else None,
                xref="x", yref="y",
                axref="x" if shifted else None,
                ayref="y" if shifted else None,
                text=f"<b>{p['label']}: {p['value']:.1f}</b>",
                showarrow=shifted,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor=p["color"],
                font=dict(size=10, color=p["color"]),
                xshift=28,
                xanchor="left",
                yanchor="middle",
            )

    # Reference line at 100
    fig.add_hline(y=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                  annotation_text="2019T1 = 100", annotation_position="left",
                  annotation_font_size=10, annotation_font_color=COLORS["neutral"])

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12"),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   tickformat=".0f", zeroline=False),
        showlegend=False,
        margin=dict(l=50, r=140, t=16, b=30),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", height=340,
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


# Productivity indices colors and labels
PRODUCTIVITY_COLORS = {
    "pib": "#1e40af",                    # Blue - PIB
    "pib_per_capita": "#dc2626",         # Red - PIB per capita
    "pib_per_working_age": "#059669",    # Green - PIB per working-age
    "pib_per_employed": "#7c3aed",       # Purple - PIB per employed
    "pib_per_hour": "#d97706",           # Orange - PIB per hour
}

PRODUCTIVITY_LABELS = {
    "pib": "PIB",
    "pib_per_capita": "PIB per cápita",
    "pib_per_working_age": "PIB por persona en edad de trabajar",
    "pib_per_employed": "PIB por ocupado",
    "pib_per_hour": "PIB por hora",
}


def _build_productivity_chart(df):
    """
    Build GDP productivity fan chart.
    Shows: PIB, PIB per capita, PIB per working-age, PIB per employed, PIB per hour.
    All indexed to 2019Q1 = 100.
    """
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Column mapping
    col_mapping = {
        "pib": "pib_index",
        "pib_per_capita": "pib_per_capita_index",
        "pib_per_working_age": "pib_per_working_age_index",
        "pib_per_employed": "pib_per_employed_index",
        "pib_per_hour": "pib_per_hour_index",
    }

    fig = go.Figure()

    # Add each line
    for key, col in col_mapping.items():
        if col not in df.columns:
            continue

        series_df = df[["date", col]].dropna()
        if series_df.empty:
            continue

        fig.add_trace(go.Scatter(
            x=series_df["date"],
            y=series_df[col],
            mode="lines+markers",
            name=PRODUCTIVITY_LABELS.get(key, key),
            line=dict(color=PRODUCTIVITY_COLORS.get(key, COLORS["neutral"]), width=2.5),
            marker=dict(size=5, color=PRODUCTIVITY_COLORS.get(key, COLORS["neutral"])),
            hovertemplate=f"{PRODUCTIVITY_LABELS.get(key, key)}: %{{y:.1f}}<extra></extra>",
        ))

        # Add label on last observation
        last_val = series_df[col].iloc[-1]
        last_date = series_df["date"].iloc[-1]
        fig.add_annotation(
            x=last_date,
            y=last_val,
            text=f"<b>{last_val:.1f}</b>",
            showarrow=False,
            font=dict(size=10, color=PRODUCTIVITY_COLORS.get(key, COLORS["neutral"])),
            xshift=30,
            yshift=0,
            xanchor="left",
        )

    # Reference line at 100
    fig.add_hline(y=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                  annotation_text="2019T1 = 100", annotation_position="left",
                  annotation_font_size=10, annotation_font_color=COLORS["neutral"])

    # Calculate y-axis range (min 90, max based on data + padding)
    all_vals = []
    for key, col in col_mapping.items():
        if col in df.columns:
            all_vals.extend(df[col].dropna().tolist())
    y_max = max(all_vals) + 5 if all_vals else 120

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12"),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   tickformat=".0f", zeroline=False, range=[90, y_max]),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0,
                    font=dict(size=10)),
        margin=dict(l=50, r=70, t=16, b=80),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", height=380,
    )
    return fig


# Business Confidence colors and labels
CONFIDENCE_COLORS = {
    "ice": COLORS["primary"],           # Blue for ICE (main index)
    "situacion": COLORS["negative"],    # Red for Situación
    "expectativas": "#059669",          # Green for Expectativas
}

CONFIDENCE_LABELS = {
    "ice": "Índice de Confianza Empresarial",
    "situacion": "Situación trimestre anterior",
    "expectativas": "Expectativas trimestre entrante",
}


def _build_business_confidence_chart(df, period="all", mode="index"):
    """
    Build Business Confidence chart.
    Shows only ICE (Índice de Confianza Empresarial).
    mode: "index" for raw values, "yoy" for year-over-year change.
    """
    if df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Only keep ICE indicator
    df = df[df["indicator"] == "ice"].copy()
    if df.empty:
        return None

    df = df.sort_values("date")

    # Calculate YoY if needed
    if mode == "yoy":
        df["value"] = df["value"].pct_change(periods=4) * 100  # Quarterly data, 4 periods = 1 year
        df = df.dropna(subset=["value"])

    # Filter by period
    if period == "1y":
        cutoff = df["date"].max() - pd.DateOffset(years=1)
        df = df[df["date"] >= cutoff]
    elif period == "2y":
        cutoff = df["date"].max() - pd.DateOffset(years=2)
        df = df[df["date"] >= cutoff]
    # else: "all" - no filtering (data already filtered to 2021+)

    if df.empty:
        return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["value"],
        mode="lines+markers",
        name="ICE",
        line=dict(color=CONFIDENCE_COLORS.get("ice", COLORS["primary"]), width=2.5),
        marker=dict(size=5, color=CONFIDENCE_COLORS.get("ice", COLORS["primary"])),
        hovertemplate="ICE: %{y:.1f}" + ("%" if mode == "yoy" else "") + "<extra></extra>",
    ))

    # Add label on last observation
    if not df.empty:
        last_val = df["value"].iloc[-1]
        last_date = df["date"].iloc[-1]
        fig.add_annotation(
            x=last_date,
            y=last_val,
            text=f"<b>{last_val:.1f}{'%' if mode == 'yoy' else ''}</b>",
            showarrow=False,
            font=dict(size=10, color=CONFIDENCE_COLORS.get("ice", COLORS["primary"])),
            xshift=30,
            yshift=0,
            xanchor="left",
        )

    # Reference line at 100 (neutral level) only for index mode
    if mode == "index":
        fig.add_hline(y=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                      annotation_text="100 = Neutro", annotation_position="left",
                      annotation_font_size=10, annotation_font_color=COLORS["neutral"])
    else:
        fig.add_hline(y=0, line_dash="dot", line_color=COLORS["neutral"], line_width=1)

    fig.update_layout(
        xaxis=dict(title="", type="date", tickformat="%Y", hoverformat="Q%q %Y",
                   showgrid=False, dtick="M12"),
        yaxis=dict(title="", showgrid=True, gridcolor=COLORS["grid"],
                   tickformat=".1f" if mode == "yoy" else ".0f", zeroline=False),
        showlegend=False,
        margin=dict(l=50, r=70, t=16, b=30),
        font=dict(family="Arial"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", height=340,
    )
    return fig


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def page_ui(data_store):
    DATA = data_store.get("ine", {})
    EUROSTAT = data_store.get("eurostat", {})
    gdp_df = DATA.get("gdp", pd.DataFrame())

    # Pre-render defaults so they show on first load
    gdp_fig = _build_gdp_chart(gdp_df, "index")
    gdp_html = ui.HTML(gdp_fig.to_html(full_html=False, include_plotlyjs="cdn")) if gdp_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    # Pre-render GDP European comparison chart
    gdp_comparison_fig = _build_gdp_comparison_chart(EUROSTAT.get("gdp_index_comparison", pd.DataFrame()))
    gdp_comparison_html = ui.HTML(gdp_comparison_fig.to_html(full_html=False, include_plotlyjs="cdn")) if gdp_comparison_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    demand_fig = _build_gdp_demand_chart(DATA.get("gdp_demand", pd.DataFrame()))
    demand_html = ui.HTML(demand_fig.to_html(full_html=False, include_plotlyjs="cdn")) if demand_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    # Pre-render combined production chart (default: YoY)
    prod_fig = _build_combined_production_chart(
        DATA.get("industrial_production", pd.DataFrame()),
        DATA.get("services_production", pd.DataFrame()), "yoy")
    prod_html = ui.HTML(prod_fig.to_html(full_html=False, include_plotlyjs="cdn")) if prod_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    # Pre-render GDP productivity chart
    productivity_fig = _build_productivity_chart(DATA.get("gdp_productivity", pd.DataFrame()))
    productivity_html = ui.HTML(productivity_fig.to_html(full_html=False, include_plotlyjs="cdn")) if productivity_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    # Pre-render Business Confidence chart
    confidence_fig = _build_business_confidence_chart(DATA.get("business_confidence", pd.DataFrame()), "all")
    confidence_html = ui.HTML(confidence_fig.to_html(full_html=False, include_plotlyjs="cdn")) if confidence_fig else ui.div("Datos no disponibles", class_="no-data-placeholder")

    return ui.nav_panel(
        "Actividad",
        ui.div(
            # --- Row 1: GDP chart (YoY, QoQ, or Index) ---
            ui.h5("Producto Interior Bruto (PIB)",
                   class_="chart-title"),

            ui.div(
                ui.input_radio_buttons(
                    "gdp_mode", None,
                    choices={
                        "index": "Índice (2019=100)",
                        "yoy": "Var. interanual",
                        "qoq": "Var. trimestral",
                    },
                    selected="index", inline=True,
                ),
                class_="toggle-btn-group",
            ),

            ui.div(
                gdp_html,
                ui.output_ui("gdp_chart"),
                id="gdp_chart_container",
            ),

            # --- Row 2: GDP European Comparison + GDP decomposition ---
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("PIB: Comparativa Europea"),
                        ui.tags.br(),
                        ui.tags.small("Índice 2019T1=100, datos trimestrales", style="color: #6c757d;"),
                    )),
                    gdp_comparison_html,
                ),
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("Descomposición del crecimiento del PIB"),
                        ui.tags.br(),
                        ui.tags.small("Aportación en puntos porcentuales", style="color: #6c757d;"),
                    )),
                    demand_html,
                ),
                col_widths={"sm": 12, "md": 6},
                class_="mt-4",
            ),

            # --- Row 3: GDP Productivity Fan Chart + Business Confidence ---
            ui.layout_columns(
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("PIB y productividad"),
                        ui.tags.br(),
                        ui.tags.small("Índice 2019T1=100", style="color: #6c757d;"),
                    )),
                    productivity_html,
                ),
                ui.card(
                    ui.card_header(ui.div(
                        ui.tags.strong("Índice de Confianza Empresarial"),
                        ui.tags.br(),
                        ui.tags.small("Total Nacional, desde 2021", style="color: #6c757d;"),
                    )),
                    ui.div(
                        ui.input_radio_buttons(
                            "confidence_mode", None,
                            choices={"index": "Índice", "yoy": "Var. interanual"},
                            selected="index", inline=True,
                        ),
                        class_="toggle-btn-group",
                    ),
                    ui.div(
                        confidence_html,
                        ui.output_ui("confidence_chart"),
                        id="confidence_chart_container",
                    ),
                ),
                col_widths={"sm": 12, "md": 6},
                class_="mt-4",
            ),

            # --- Row 4: Combined production chart ---
            ui.h5("Índices de Producción", class_="chart-title", style="margin-top: 2rem;"),
            ui.p("Variación de la producción industrial y de servicios",
                 style="color: #6c757d; font-size: 0.9rem; margin-top: -0.5rem; margin-bottom: 0.5rem;"),

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

            # --- Row 5: Sectoral breakdown bar charts ---
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
    @reactive.event(input.gdp_mode)
    def gdp_chart():
        mode = input.gdp_mode()
        fig = _build_gdp_chart(DATA.get("gdp", pd.DataFrame()), mode)

        hide_default = ui.tags.script(
            "document.querySelectorAll('#gdp_chart_container > :not(#gdp_chart)')"
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

    # --- Business Confidence ---
    @render.ui
    @reactive.event(input.confidence_mode)
    def confidence_chart():
        mode = input.confidence_mode()
        fig = _build_business_confidence_chart(DATA.get("business_confidence", pd.DataFrame()), period="all", mode=mode)
        hide = ui.tags.script(
            "document.querySelectorAll('#confidence_chart_container > :not(#confidence_chart)')"
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
