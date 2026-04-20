"""
Chart creation utilities using Plotly.
Enhanced with better UX styling.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional


# Color scheme — aligned with CdE corporate website (dark navy/slate palette)
COLORS = {
    "spain": "#1e2d3d",      # Dark slate-navy (CdE primary)
    "primary": "#1e2d3d",    # Primary brand color
    "secondary": "#4a7c9b",  # Steel blue — muted complement
    "accent": "#5b8a9a",     # Muted teal
    "positive": "#2d8659",   # Muted forest green
    "negative": "#b94a48",   # Muted crimson
    "neutral": "#64748b",    # Slate gray
    "light": "#f4f6f8",      # Light background
    "grid": "#d1d5db",       # Subtle grid lines
}

# Common layout settings for consistency
COMMON_LAYOUT = dict(
    font=dict(family="Arial, Helvetica, sans-serif"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Arial, Helvetica, sans-serif",
    ),
)


def create_time_series(
    df: pd.DataFrame,
    value_col: str,
    title: str = "",
    subtitle: str = "",
    color: str = COLORS["spain"],
    show_yoy: bool = True,
    show_avg_line: bool = True,
) -> go.Figure:
    """
    Create an enhanced time series line chart.
    """
    fig = go.Figure()

    # Convert dates to string format for proper serialization
    x_dates = df["date"].astype(str).tolist()

    # Calculate average for reference line
    avg_value = df[value_col].mean()

    # Main line with gradient fill
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df[value_col],
            mode="lines",
            name=value_col.replace("_", " ").title(),
            line=dict(color=color, width=3, shape="spline"),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}",
            hovertemplate="<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>",
        )
    )

    # Add average reference line
    if show_avg_line:
        fig.add_hline(
            y=avg_value,
            line_dash="dot",
            line_color=COLORS["neutral"],
            line_width=1,
            annotation_text=f"Avg: {avg_value:.1f}",
            annotation_position="right",
            annotation_font_size=10,
            annotation_font_color=COLORS["neutral"],
        )

    # Add YoY change bars if requested
    yoy_col = "yoy_change" if "yoy_change" in df.columns else "inflation_rate"
    if show_yoy and yoy_col in df.columns:
        fig.add_trace(
            go.Bar(
                x=x_dates,
                y=df[yoy_col],
                name="Var. Interanual (%)",
                marker_color=[
                    COLORS["positive"] if v >= 0 else COLORS["negative"]
                    for v in df[yoy_col].fillna(0)
                ],
                opacity=0.4,
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>YoY: %{y:+.1f}%<extra></extra>",
            )
        )

        fig.update_layout(
            yaxis2=dict(
                title=dict(text="Var. %", font=dict(size=11, color=COLORS["neutral"])),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=True,
                zerolinecolor=COLORS["grid"],
            )
        )

    # Build title with subtitle
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=60, t=70, b=40),
    )

    return fig


def create_sparkline(
    df: pd.DataFrame,
    value_col: str,
    color: str = COLORS["spain"],
    height: int = 60,
    show_endpoints: bool = True,
) -> go.Figure:
    """Create an enhanced minimal sparkline chart."""
    fig = go.Figure()

    x_dates = df["date"].astype(str).tolist()
    values = df[value_col].tolist()

    # Main sparkline
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=values,
            mode="lines",
            line=dict(color=color, width=2, shape="spline"),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.15])}",
            hoverinfo="skip",
        )
    )

    # Add endpoint markers
    if show_endpoints and len(values) > 1:
        fig.add_trace(
            go.Scatter(
                x=[x_dates[-1]],
                y=[values[-1]],
                mode="markers",
                marker=dict(color=color, size=8),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, type="date"),
        yaxis=dict(visible=False),
        showlegend=False,
        **{k: v for k, v in COMMON_LAYOUT.items() if k != "hovermode"},
    )

    return fig


def create_yoy_bar_chart(
    df: pd.DataFrame,
    title: str = "Variación Interanual",
    highlight_latest: bool = True,
) -> go.Figure:
    """Create an enhanced bar chart showing YoY changes."""
    yoy_col = "yoy_change" if "yoy_change" in df.columns else "inflation_rate"

    df_recent = df.tail(12).copy()
    x_dates = df_recent["date"].astype(str).tolist()
    values = df_recent[yoy_col].fillna(0).tolist()

    # Create colors with latest highlighted
    colors = []
    for i, v in enumerate(values):
        if i == len(values) - 1 and highlight_latest:
            # Latest bar is more prominent
            colors.append(COLORS["positive"] if v >= 0 else COLORS["negative"])
        else:
            # Other bars are more muted
            if v >= 0:
                colors.append("rgba(40, 167, 69, 0.6)")
            else:
                colors.append("rgba(220, 53, 69, 0.6)")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=x_dates,
            y=values,
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>YoY: %{y:+.1f}%<extra></extra>",
        )
    )

    # Add zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=2)

    # Add latest value annotation
    if values:
        latest_val = values[-1]
        fig.add_annotation(
            x=x_dates[-1],
            y=latest_val,
            text=f"<b>{latest_val:+.1f}%</b>",
            showarrow=True,
            arrowhead=0,
            arrowsize=0.5,
            arrowwidth=1,
            arrowcolor=COLORS["neutral"],
            ax=0,
            ay=-30,
            font=dict(size=12, color=COLORS["positive"] if latest_val >= 0 else COLORS["negative"]),
        )

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=f"<b>{title}</b>", x=0, xanchor="left", font=dict(size=14)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=False,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        showlegend=False,
        margin=dict(l=50, r=30, t=50, b=40),
        bargap=0.3,
    )

    return fig


def create_multi_indicator_chart(
    data: dict,
    indicators: list,
    title: str = "Indicator Comparison",
    subtitle: str = "Normalized to 100 at start of period",
) -> go.Figure:
    """Create an enhanced chart comparing multiple indicators."""
    fig = go.Figure()

    chart_colors = [COLORS["spain"], COLORS["secondary"], "#6A1B9A", "#00695C", "#AD1457", "#37474F"]

    for i, (key, meta) in enumerate(indicators):
        df = data.get(key)
        if df is None or df.empty:
            continue

        value_col = meta["value_col"]
        df_norm = df.copy()
        first_val = df_norm[value_col].iloc[0]
        df_norm["normalized"] = (df_norm[value_col] / first_val) * 100

        x_dates = df_norm["date"].astype(str).tolist()
        color = chart_colors[i % len(chart_colors)]

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df_norm["normalized"],
                mode="lines",
                name=meta["name"],
                line=dict(color=color, width=2.5, shape="spline"),
                hovertemplate=f"<b>{meta['name']}</b><br>%{{x}}<br>Index: %{{y:.1f}}<extra></extra>",
            )
        )

    # Add 100 baseline
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color=COLORS["neutral"],
        line_width=1,
        annotation_text="Base = 100",
        annotation_position="right",
        annotation_font_size=10,
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:11px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=80, b=40),
    )

    return fig


def create_gauge_chart(
    value: float,
    title: str,
    min_val: float = 0,
    max_val: float = 100,
    thresholds: dict = None,
) -> go.Figure:
    """Create a gauge chart for KPI display."""
    if thresholds is None:
        thresholds = {"good": 30, "moderate": 70}

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title=dict(text=title, font=dict(size=14)),
            gauge=dict(
                axis=dict(range=[min_val, max_val], tickfont=dict(size=10)),
                bar=dict(color=COLORS["spain"]),
                bgcolor="white",
                borderwidth=0,
                steps=[
                    dict(range=[min_val, thresholds["good"]], color="rgba(40, 167, 69, 0.2)"),
                    dict(range=[thresholds["good"], thresholds["moderate"]], color="rgba(255, 193, 7, 0.2)"),
                    dict(range=[thresholds["moderate"], max_val], color="rgba(220, 53, 69, 0.2)"),
                ],
            ),
        )
    )

    fig.update_layout(
        height=200,
        margin=dict(l=30, r=30, t=50, b=20),
        **{k: v for k, v in COMMON_LAYOUT.items() if k != "hovermode"},
    )

    return fig


def format_trend_indicator(value: float, positive_is_good: Optional[bool] = True) -> tuple:
    """Return trend arrow and CSS class based on value."""
    if pd.isna(value):
        return ("", "neutral", COLORS["neutral"])

    if value > 0.5:  # Threshold to show arrow
        arrow = "▲"
        if positive_is_good is True:
            css_class = "positive"
            color = COLORS["positive"]
        elif positive_is_good is False:
            css_class = "negative"
            color = COLORS["negative"]
        else:
            css_class = "neutral"
            color = COLORS["neutral"]
    elif value < -0.5:
        arrow = "▼"
        if positive_is_good is True:
            css_class = "negative"
            color = COLORS["negative"]
        elif positive_is_good is False:
            css_class = "positive"
            color = COLORS["positive"]
        else:
            css_class = "neutral"
            color = COLORS["neutral"]
    else:
        arrow = "→"
        css_class = "neutral"
        color = COLORS["neutral"]

    return (arrow, css_class, color)


def create_comparison_line_chart(
    df_spain: pd.DataFrame,
    df_eu27: pd.DataFrame,
    value_col: str,
    title: str = "",
    subtitle: str = "",
    spain_name: str = "España",
    eu_name: str = "UE27",
) -> go.Figure:
    """
    Create a line chart comparing Spain and EU27 data.
    """
    fig = go.Figure()

    # Spain line
    if not df_spain.empty and value_col in df_spain.columns:
        x_dates_spain = df_spain["date"].astype(str).tolist()
        fig.add_trace(
            go.Scatter(
                x=x_dates_spain,
                y=df_spain[value_col],
                mode="lines",
                name=spain_name,
                line=dict(color=COLORS["spain"], width=3, shape="spline"),
                hovertemplate=f"<b>{spain_name}</b><br>%{{x}}<br>Value: %{{y:.2f}}<extra></extra>",
            )
        )

    # EU27 line
    if not df_eu27.empty and value_col in df_eu27.columns:
        x_dates_eu = df_eu27["date"].astype(str).tolist()
        fig.add_trace(
            go.Scatter(
                x=x_dates_eu,
                y=df_eu27[value_col],
                mode="lines",
                name=eu_name,
                line=dict(color=COLORS["secondary"], width=3, shape="spline", dash="dash"),
                hovertemplate=f"<b>{eu_name}</b><br>%{{x}}<br>Value: %{{y:.2f}}<extra></extra>",
            )
        )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=70, b=40),
    )

    return fig


def create_comparison_bar_chart(
    spain_value: float,
    eu_value: float,
    title: str,
    unit: str = "",
) -> go.Figure:
    """
    Create a horizontal bar chart comparing Spain vs EU27.
    """
    fig = go.Figure()

    spain_val = spain_value if spain_value is not None else 0
    eu_val = eu_value if eu_value is not None else 0

    categories = ["UE27", "España"]
    values = [eu_val, spain_val]
    colors = [COLORS["secondary"], COLORS["spain"]]

    fig.add_trace(
        go.Bar(
            y=categories,
            x=values,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}{unit}" for v in values],
            textposition="outside",
            textfont=dict(size=12, color="#1e293b"),
            hovertemplate="%{y}: %{x:.2f}<extra></extra>",
        )
    )

    # Calculate proper x-axis range
    max_val = max(abs(v) for v in values) if values else 1
    min_val = min(values) if values else 0

    # Determine range based on values
    if min_val >= 0:
        # All positive values - start from 0
        x_range = [0, max_val * 1.3]  # 30% padding for text
    else:
        # Has negative values - symmetric range
        x_range = [min_val * 1.3, max_val * 1.3]

    fig.update_layout(
        **{k: v for k, v in COMMON_LAYOUT.items() if k != "hovermode"},
        title=dict(text=f"<b>{title}</b>", x=0, xanchor="left", font=dict(size=14)),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            range=x_range,
            zeroline=True,
            zerolinecolor="#9ca3af",
            zerolinewidth=1,
        ),
        yaxis=dict(title="", tickfont=dict(size=11)),
        showlegend=False,
        height=180,
        margin=dict(l=60, r=50, t=50, b=30),
        bargap=0.4,
    )

    return fig


def create_difference_chart(
    df: pd.DataFrame,
    spain_col: str,
    eu_col: str,
    title: str = "Diferencial España vs UE27",
) -> go.Figure:
    """
    Create a chart showing the difference between Spain and EU27 over time.
    """
    fig = go.Figure()

    if df.empty or spain_col not in df.columns or eu_col not in df.columns:
        return fig

    df = df.copy()
    df["difference"] = df[spain_col] - df[eu_col]
    x_dates = df["date"].astype(str).tolist()

    # Color bars based on sign
    colors = [
        COLORS["positive"] if v >= 0 else COLORS["negative"]
        for v in df["difference"].fillna(0)
    ]

    fig.add_trace(
        go.Bar(
            x=x_dates,
            y=df["difference"],
            marker_color=colors,
            hovertemplate="<b>%{x}</b><br>Difference: %{y:+.2f}<extra></extra>",
        )
    )

    # Zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=2)

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=f"<b>{title}</b>", x=0, xanchor="left", font=dict(size=14)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=False,
        ),
        yaxis=dict(
            title="Difference (pp)",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        showlegend=False,
        margin=dict(l=50, r=30, t=50, b=40),
    )

    return fig


def create_yoy_line_chart(
    df: pd.DataFrame,
    value_col: str = "yoy_change",
    title: str = "Variación Interanual",
    subtitle: str = "",
    color: str = COLORS["spain"],
) -> go.Figure:
    """
    Create a line chart showing YoY variations with a zero reference line.
    Suitable for indicators where YoY change is the primary metric.
    """
    fig = go.Figure()

    if df.empty or value_col not in df.columns:
        return fig

    x_dates = df["date"].astype(str).tolist()
    values = df[value_col].fillna(0).tolist()

    # Add zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=2)

    # Main line with area fill
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=values,
            mode="lines",
            name="Var. Interanual",
            line=dict(color=color, width=3, shape="spline"),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.15])}",
            hovertemplate="<b>%{x}</b><br>YoY: %{y:+.1f}%<extra></extra>",
        )
    )

    # Add markers for positive/negative
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=values,
            mode="markers",
            marker=dict(
                color=[COLORS["positive"] if v >= 0 else COLORS["negative"] for v in values],
                size=6,
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Var. Interanual (%)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        showlegend=False,
        margin=dict(l=50, r=30, t=70, b=40),
    )

    return fig


def create_gdp_demand_chart(
    df: pd.DataFrame,
    title: str = "Contributions to GDP Growth",
    subtitle: str = "Annual contribution (percentage points)",
) -> go.Figure:
    """
    Create a stacked bar chart showing GDP demand-side contributions.
    Uses INE's pre-calculated annual contributions (Aportación anual).
    Components: Private Consumption, Public Consumption, GFCF, External Demand.
    """
    fig = go.Figure()

    if df.empty or "component" not in df.columns:
        return fig

    # Component colors - starker contrast
    component_colors = {
        "private_consumption": "#1e2d3d",
        "public_consumption": "#1565C0",
        "gfcf": "#00897B",
        "external_demand": "#c9943e",
    }

    component_labels = {
        "private_consumption": "Consumo Privado",
        "public_consumption": "Consumo Público",
        "gfcf": "FBCF",
        "external_demand": "Demanda Externa",
    }

    # Determine value column (contribution or yoy_change for backwards compatibility)
    value_col = "contribution" if "contribution" in df.columns else "yoy_change"

    # Pivot to get components as columns
    pivot_df = df.pivot_table(
        index="date",
        columns="component",
        values=value_col,
        aggfunc="first"
    ).reset_index()

    # Filter out rows where all components have NaN
    component_cols = ["private_consumption", "public_consumption", "gfcf", "external_demand"]
    available_cols = [c for c in component_cols if c in pivot_df.columns]
    pivot_df = pivot_df.dropna(subset=available_cols, how="all")

    # Fill remaining NaN values with 0 for visualization
    for col in available_cols:
        pivot_df[col] = pivot_df[col].fillna(0)

    x_dates = pivot_df["date"].astype(str).tolist()

    # Add bars for each component in stacked order
    # Note: barmode="relative" handles positive and negative stacking correctly
    for component in ["private_consumption", "public_consumption", "gfcf", "external_demand"]:
        if component in pivot_df.columns:
            fig.add_trace(
                go.Bar(
                    x=x_dates,
                    y=pivot_df[component].tolist(),
                    name=component_labels.get(component, component),
                    marker_color=component_colors.get(component, COLORS["neutral"]),
                    hovertemplate=f"<b>{component_labels.get(component, component)}</b><br>%{{x}}<br>Contribution: %{{y:+.2f}} pp<extra></extra>",
                )
            )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        barmode="relative",  # "relative" stacks positive above zero and negative below
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%Y Q%q",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Contribution (pp)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix=" pp",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(l=50, r=30, t=80, b=40),
    )

    # Add zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=2)

    return fig


def create_inflation_breakdown_chart(
    df: pd.DataFrame,
    title: str = "Inflation Breakdown",
    subtitle: str = "Componentes IPC (var. interanual)",
    show_groups: list = None,
) -> go.Figure:
    """
    Create a multi-line chart showing different inflation components.
    """
    fig = go.Figure()

    if df.empty or "group" not in df.columns:
        return fig

    # Group colors - starker contrast
    group_colors = {
        "headline": "#1e2d3d",
        "core": "#C62828",
        "energy": "#c9943e",
        "unprocessed_food": "#2E7D32",
        "processed_food": "#37474F",
        "services": "#6A1B9A",
        "non_energy_goods": "#00897B",
    }

    group_labels = {
        "headline": "Headline CPI",
        "core": "Core Inflation",
        "energy": "Energy",
        "unprocessed_food": "Unprocessed Food",
        "processed_food": "Processed Food",
        "services": "Services",
        "non_energy_goods": "Non-Energy Goods",
    }

    # Default to showing headline and core
    if show_groups is None:
        show_groups = ["headline", "core", "energy", "unprocessed_food"]

    for group in show_groups:
        group_df = df[df["group"] == group].copy()
        if group_df.empty:
            continue

        x_dates = group_df["date"].astype(str).tolist()

        # Use solid line for headline and core, dashed for others
        line_style = "solid" if group in ["headline", "core"] else "dash"
        line_width = 3 if group in ["headline", "core"] else 2

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=group_df["yoy_change"],
                mode="lines",
                name=group_labels.get(group, group),
                line=dict(
                    color=group_colors.get(group, COLORS["neutral"]),
                    width=line_width,
                    shape="spline",
                    dash=line_style,
                ),
                hovertemplate=f"<b>{group_labels.get(group, group)}</b><br>%{{x}}<br>YoY: %{{y:.1f}}%<extra></extra>",
            )
        )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Var. Interanual (%)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(l=50, r=30, t=80, b=40),
    )

    # Add zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=1, line_dash="dot")

    return fig


def create_headline_vs_core_chart(
    df: pd.DataFrame,
    title: str = "Headline vs Core Inflation",
    subtitle: str = "Variación interanual (%)",
) -> go.Figure:
    """
    Create a chart comparing headline and core inflation with shaded difference.
    """
    fig = go.Figure()

    if df.empty or "group" not in df.columns:
        return fig

    headline_df = df[df["group"] == "headline"].copy()
    core_df = df[df["group"] == "core"].copy()

    if headline_df.empty or core_df.empty:
        return fig

    # Merge on date
    merged = pd.merge(
        headline_df[["date", "yoy_change"]],
        core_df[["date", "yoy_change"]],
        on="date",
        suffixes=("_headline", "_core")
    )

    x_dates = merged["date"].astype(str).tolist()

    # Add shaded area between lines
    fig.add_trace(
        go.Scatter(
            x=x_dates + x_dates[::-1],
            y=merged["yoy_change_headline"].tolist() + merged["yoy_change_core"].tolist()[::-1],
            fill="toself",
            fillcolor="rgba(26, 95, 122, 0.1)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Headline line
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=merged["yoy_change_headline"],
            mode="lines",
            name="Headline CPI",
            line=dict(color=COLORS["spain"], width=3, shape="spline"),
            hovertemplate="<b>Headline</b><br>%{x}<br>YoY: %{y:.1f}%<extra></extra>",
        )
    )

    # Core line
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=merged["yoy_change_core"],
            mode="lines",
            name="Core Inflation",
            line=dict(color="#C62828", width=3, shape="spline"),
            hovertemplate="<b>Core</b><br>%{x}<br>YoY: %{y:.1f}%<extra></extra>",
        )
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Var. Interanual (%)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=70, b=40),
    )

    # Add ECB target line at 2%
    fig.add_hline(
        y=2,
        line_dash="dot",
        line_color="#ffc107",
        line_width=2,
        annotation_text="ECB Target (2%)",
        annotation_position="right",
        annotation_font_size=10,
        annotation_font_color="#ffc107",
    )

    return fig


# =============================================================================
# FINANCIAL MARKETS CHARTS
# =============================================================================

MARKET_COLORS = {
    "ibex_35": "#1e2d3d",       # Spain - Dark slate-navy
    "euro_stoxx_50": "#3d6b8e", # Eurozone - Steel blue
    "sp_500": "#2d8659",        # US - Muted green
    "dax": "#b94a48",           # Germany - Muted red
    "ftse_100": "#6b5b8a",      # UK - Muted purple
    "gold": "#b8963e",          # Gold - Warm amber
    "brent_crude": "#4a5568",   # Oil - Charcoal
    "vix": "#8b4a6b",           # Volatility - Muted magenta
}


def create_stock_index_chart(
    df: pd.DataFrame,
    title: str = "",
    subtitle: str = "",
    color: str = COLORS["spain"],
    show_sma: bool = True,
) -> go.Figure:
    """Create a stock index price chart with optional moving averages."""
    fig = go.Figure()

    if df.empty:
        return fig

    x_dates = df["date"].astype(str).tolist()

    # Main price line
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df["Close"],
            mode="lines",
            name="Price",
            line=dict(color=color, width=2),
            hovertemplate="<b>%{x}</b><br>Close: %{y:,.2f}<extra></extra>",
        )
    )

    # Add moving averages
    if show_sma:
        if "sma_50" in df.columns and df["sma_50"].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=df["sma_50"],
                    mode="lines",
                    name="SMA 50",
                    line=dict(color=COLORS["accent"], width=1.5, dash="dash"),
                    hovertemplate="SMA 50: %{y:,.2f}<extra></extra>",
                )
            )
        if "sma_200" in df.columns and df["sma_200"].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=df["sma_200"],
                    mode="lines",
                    name="SMA 200",
                    line=dict(color=COLORS["neutral"], width=1.5, dash="dot"),
                    hovertemplate="SMA 200: %{y:,.2f}<extra></extra>",
                )
            )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
            tickformat=",",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=60, r=30, t=70, b=40),
    )

    return fig


def create_multi_index_comparison(
    data: dict,
    indicators: list,
    title: str = "Stock Indices Comparison",
    subtitle: str = "Normalized to 100",
) -> go.Figure:
    """Create a normalized comparison chart for multiple stock indices."""
    fig = go.Figure()

    for i, key in enumerate(indicators):
        df = data.get(key)
        if df is None or df.empty:
            continue

        df_norm = df.copy()
        first_val = df_norm["Close"].iloc[0]
        if pd.isna(first_val) or first_val == 0:
            continue
        df_norm["normalized"] = (df_norm["Close"] / first_val) * 100

        x_dates = df_norm["date"].astype(str).tolist()
        color = MARKET_COLORS.get(key, COLORS["neutral"])

        # Use indicator name from the data if available
        name = df_norm["name"].iloc[0] if "name" in df_norm.columns else key.replace("_", " ").title()

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df_norm["normalized"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>Index: %{{y:.1f}}<extra></extra>",
            )
        )

    # Add 100 baseline
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color=COLORS["neutral"],
        line_width=1,
        annotation_text="Base = 100",
        annotation_position="right",
        annotation_font_size=10,
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:11px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=80, b=40),
    )

    return fig


def create_returns_bar_chart(
    df: pd.DataFrame,
    title: str = "Performance",
    periods: list = None,
) -> go.Figure:
    """Create a bar chart showing returns over different periods."""
    fig = go.Figure()

    if df.empty:
        return fig

    if periods is None:
        periods = [
            ("return_1w_pct", "1W"),
            ("return_1m_pct", "1M"),
            ("return_3m_pct", "3M"),
            ("ytd_return_pct", "YTD"),
            ("return_1y_pct", "1Y"),
        ]

    latest = df.iloc[-1]
    labels = []
    values = []
    colors = []

    for col, label in periods:
        if col in df.columns:
            val = latest[col]
            if pd.notna(val):
                labels.append(label)
                values.append(val)
                colors.append(COLORS["positive"] if val >= 0 else COLORS["negative"])

    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Return: %{y:+.2f}%<extra></extra>",
        )
    )

    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=1)

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=f"<b>{title}</b>", x=0, xanchor="left", font=dict(size=14)),
        xaxis=dict(title="", tickfont=dict(size=11)),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        showlegend=False,
        margin=dict(l=50, r=30, t=50, b=40),
        bargap=0.4,
    )

    return fig


def create_currency_chart(
    df: pd.DataFrame,
    title: str = "Tipo de Cambio",
    subtitle: str = "",
    color: str = COLORS["secondary"],
) -> go.Figure:
    """Create a currency exchange rate chart."""
    fig = go.Figure()

    if df.empty:
        return fig

    x_dates = df["date"].astype(str).tolist()

    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df["Close"],
            mode="lines",
            name="Rate",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}",
            hovertemplate="<b>%{x}</b><br>Rate: %{y:.4f}<extra></extra>",
        )
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        showlegend=False,
        margin=dict(l=60, r=30, t=70, b=40),
    )

    return fig


def create_commodity_chart(
    df: pd.DataFrame,
    title: str = "Commodity Price",
    subtitle: str = "",
    color: str = "#f59e0b",
    unit: str = "USD",
) -> go.Figure:
    """Create a commodity price chart."""
    fig = go.Figure()

    if df.empty:
        return fig

    x_dates = df["date"].astype(str).tolist()

    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df["Close"],
            mode="lines",
            name="Price",
            line=dict(color=color, width=2),
            hovertemplate=f"<b>%{{x}}</b><br>Price: %{{y:,.2f}} {unit}<extra></extra>",
        )
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
            tickformat=",",
        ),
        showlegend=False,
        margin=dict(l=70, r=30, t=70, b=40),
    )

    return fig


def create_volatility_chart(
    df: pd.DataFrame,
    title: str = "Índice de Volatilidad",
    subtitle: str = "",
    color: str = "#ef4444",
) -> go.Figure:
    """Create a volatility index chart with fear/greed zones."""
    fig = go.Figure()

    if df.empty:
        return fig

    x_dates = df["date"].astype(str).tolist()

    # Add colored zones for fear levels
    fig.add_hrect(y0=0, y1=12, fillcolor="rgba(40, 167, 69, 0.1)", line_width=0)
    fig.add_hrect(y0=12, y1=20, fillcolor="rgba(255, 193, 7, 0.1)", line_width=0)
    fig.add_hrect(y0=20, y1=30, fillcolor="rgba(255, 152, 0, 0.1)", line_width=0)
    fig.add_hrect(y0=30, y1=100, fillcolor="rgba(220, 53, 69, 0.1)", line_width=0)

    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df["Close"],
            mode="lines",
            name="VIX",
            line=dict(color=color, width=2),
            hovertemplate="<b>%{x}</b><br>VIX: %{y:.2f}<extra></extra>",
        )
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
            range=[0, max(40, df["Close"].max() * 1.1) if not df.empty else 40],
        ),
        showlegend=False,
        margin=dict(l=50, r=30, t=70, b=40),
    )

    # Add level annotations
    fig.add_annotation(x=1, xref="paper", y=6, text="Low Fear", showarrow=False,
                       font=dict(size=9, color=COLORS["positive"]), xanchor="right")
    fig.add_annotation(x=1, xref="paper", y=16, text="Moderate", showarrow=False,
                       font=dict(size=9, color="#ffc107"), xanchor="right")
    fig.add_annotation(x=1, xref="paper", y=25, text="Elevated", showarrow=False,
                       font=dict(size=9, color="#ff9800"), xanchor="right")
    fig.add_annotation(x=1, xref="paper", y=35, text="High Fear", showarrow=False,
                       font=dict(size=9, color=COLORS["negative"]), xanchor="right")

    return fig


def create_market_kpi_card_data(
    df: pd.DataFrame,
    name: str,
) -> dict:
    """Extract KPI data from a market indicator DataFrame."""
    if df.empty:
        return {
            "name": name,
            "value": None,
            "change_1d": None,
            "change_1w": None,
            "change_1m": None,
            "change_ytd": None,
            "date": None,
        }

    latest = df.iloc[-1]
    return {
        "name": name,
        "value": latest.get("Close"),
        "change_1d": latest.get("daily_return_pct"),
        "change_1w": latest.get("return_1w_pct"),
        "change_1m": latest.get("return_1m_pct"),
        "change_ytd": latest.get("ytd_return_pct"),
        "date": latest.get("date"),
    }


# =============================================================================
# BANCO DE ESPANA CHARTS
# =============================================================================

def create_euribor_chart(
    data: dict,
    title: str = "EURIBOR Rates",
    subtitle: str = "Tipos de interes de referencia",
    show_12m: bool = True,
    show_3m: bool = True,
) -> go.Figure:
    """
    Create an EURIBOR rates chart showing 12M and 3M rates over time.

    Args:
        data: Dictionary with EURIBOR data (keys: euribor_12m_daily, euribor_3m_daily)
        title: Chart title
        subtitle: Chart subtitle
        show_12m: Show 12-month EURIBOR
        show_3m: Show 3-month EURIBOR

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    euribor_colors = {
        "12m": COLORS["spain"],
        "3m": COLORS["secondary"],
    }

    # EURIBOR 12M
    if show_12m:
        df_12m = data.get("euribor_12m_daily", pd.DataFrame())
        if df_12m.empty:
            df_12m = data.get("euribor_12m_monthly", pd.DataFrame())
        if not df_12m.empty and "value" in df_12m.columns:
            x_dates = df_12m["date"].astype(str).tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=df_12m["value"],
                    mode="lines",
                    name="EURIBOR 12M",
                    line=dict(color=euribor_colors["12m"], width=2.5),
                    hovertemplate="<b>EURIBOR 12M</b><br>%{x}<br>%{y:.3f}%<extra></extra>",
                )
            )

    # EURIBOR 3M
    if show_3m:
        df_3m = data.get("euribor_3m_daily", pd.DataFrame())
        if not df_3m.empty and "value" in df_3m.columns:
            x_dates = df_3m["date"].astype(str).tolist()
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=df_3m["value"],
                    mode="lines",
                    name="EURIBOR 3M",
                    line=dict(color=euribor_colors["3m"], width=2.5, dash="dash"),
                    hovertemplate="<b>EURIBOR 3M</b><br>%{x}<br>%{y:.3f}%<extra></extra>",
                )
            )

    # Add zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=1, line_dash="dot")

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=70, b=40),
    )

    return fig


def create_bond_yield_chart(
    df: pd.DataFrame,
    title: str = "Spain 10Y Bond Yield",
    subtitle: str = "Rendimiento del bono a 10 anos",
    color: str = COLORS["spain"],
) -> go.Figure:
    """
    Create a bond yield chart for Spanish government bonds.

    Args:
        df: DataFrame with bond yield data
        title: Chart title
        subtitle: Chart subtitle
        color: Line color

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if df.empty or "value" not in df.columns:
        return fig

    x_dates = df["date"].astype(str).tolist()

    # Main yield line
    fig.add_trace(
        go.Scatter(
            x=x_dates,
            y=df["value"],
            mode="lines",
            name="Yield",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}",
            hovertemplate="<b>%{x}</b><br>Yield: %{y:.3f}%<extra></extra>",
        )
    )

    # Add moving averages if available
    if "ma_20" in df.columns and df["ma_20"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df["ma_20"],
                mode="lines",
                name="MA 20",
                line=dict(color=COLORS["accent"], width=1.5, dash="dash"),
                hovertemplate="MA 20: %{y:.3f}%<extra></extra>",
            )
        )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=30, t=70, b=40),
    )

    return fig


def create_lending_rates_chart(
    data: dict,
    title: str = "Bank Lending Rates",
    subtitle: str = "Tipos de interes bancarios (nuevas operaciones)",
) -> go.Figure:
    """
    Create a comparison chart of bank lending rates (mortgages, consumer, corporate).

    Args:
        data: Dictionary with lending rate data
        title: Chart title
        subtitle: Chart subtitle

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    rate_config = [
        ("mortgage_rate", "Hipotecas", "#1e2d3d"),
        ("consumer_credit_rate", "Consumo", "#C62828"),
        ("corporate_lending_rate", "Empresas", "#2E7D32"),
        ("household_deposit_rate", "Depositos", "#c9943e"),
    ]

    for key, name, color in rate_config:
        df = data.get(key, pd.DataFrame())
        if df.empty or "value" not in df.columns:
            continue

        x_dates = df["date"].astype(str).tolist()
        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df["value"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>%{{y:.2f}}%<extra></extra>",
            )
        )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(l=50, r=30, t=80, b=40),
    )

    return fig


def create_credit_growth_chart(
    data: dict,
    title: str = "Credit to Private Sector",
    subtitle: str = "Credito a hogares y empresas (variacion interanual)",
) -> go.Figure:
    """
    Create a chart showing credit growth to households and NFCs.

    Args:
        data: Dictionary with credit data
        title: Chart title
        subtitle: Chart subtitle

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    credit_config = [
        ("credit_households_total", "Hogares", COLORS["spain"]),
        ("credit_nfc_total", "Empresas (SNF)", COLORS["secondary"]),
    ]

    for key, name, color in credit_config:
        df = data.get(key, pd.DataFrame())
        if df.empty:
            continue

        # Use YoY change if available, otherwise calculate
        value_col = "yoy_change_pct" if "yoy_change_pct" in df.columns else "value"

        if value_col not in df.columns:
            continue

        x_dates = df["date"].astype(str).tolist()

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df[value_col],
                mode="lines",
                name=name,
                line=dict(color=color, width=2.5),
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
            )
        )

    # Zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=2)

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Var. Interanual (%)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=60, r=30, t=70, b=40),
    )

    return fig


def create_debt_to_gdp_chart(
    data: dict,
    title: str = "Private Sector Debt-to-GDP",
    subtitle: str = "Ratio de endeudamiento sobre PIB",
) -> go.Figure:
    """
    Create a chart showing household and corporate debt-to-GDP ratios.

    Args:
        data: Dictionary with debt ratio data
        title: Chart title
        subtitle: Chart subtitle

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    debt_config = [
        ("household_debt_gdp", "Hogares", COLORS["spain"]),
        ("nfc_debt_gdp", "Empresas (SNF)", COLORS["secondary"]),
    ]

    for key, name, color in debt_config:
        df = data.get(key, pd.DataFrame())
        if df.empty or "value" not in df.columns:
            continue

        x_dates = df["date"].astype(str).tolist()

        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df["value"],
                mode="lines",
                name=name,
                line=dict(color=color, width=2.5),
                fill="tozeroy",
                fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}",
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>%{{y:.1f}}% PIB<extra></extra>",
            )
        )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="% PIB",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=70, r=30, t=70, b=40),
    )

    return fig


def create_debt_gauge_chart(
    household_debt: float,
    nfc_debt: float,
    title: str = "Debt-to-GDP Ratios",
) -> go.Figure:
    """
    Create a gauge chart showing debt-to-GDP ratios.

    Args:
        household_debt: Household debt-to-GDP ratio
        nfc_debt: NFC debt-to-GDP ratio
        title: Chart title

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Household debt gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=household_debt if pd.notna(household_debt) else 0,
            title=dict(text="Hogares", font=dict(size=14)),
            domain=dict(x=[0, 0.45], y=[0, 1]),
            gauge=dict(
                axis=dict(range=[0, 150], tickfont=dict(size=10)),
                bar=dict(color=COLORS["spain"]),
                bgcolor="white",
                borderwidth=0,
                steps=[
                    dict(range=[0, 60], color="rgba(40, 167, 69, 0.2)"),
                    dict(range=[60, 100], color="rgba(255, 193, 7, 0.2)"),
                    dict(range=[100, 150], color="rgba(220, 53, 69, 0.2)"),
                ],
            ),
            number=dict(suffix="% PIB", font=dict(size=16)),
        )
    )

    # NFC debt gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=nfc_debt if pd.notna(nfc_debt) else 0,
            title=dict(text="Empresas (SNF)", font=dict(size=14)),
            domain=dict(x=[0.55, 1], y=[0, 1]),
            gauge=dict(
                axis=dict(range=[0, 150], tickfont=dict(size=10)),
                bar=dict(color=COLORS["secondary"]),
                bgcolor="white",
                borderwidth=0,
                steps=[
                    dict(range=[0, 60], color="rgba(40, 167, 69, 0.2)"),
                    dict(range=[60, 100], color="rgba(255, 193, 7, 0.2)"),
                    dict(range=[100, 150], color="rgba(220, 53, 69, 0.2)"),
                ],
            ),
            number=dict(suffix="% PIB", font=dict(size=16)),
        )
    )

    fig.update_layout(
        height=250,
        margin=dict(l=30, r=30, t=60, b=20),
        title=dict(text=f"<b>{title}</b>", x=0, xanchor="left", font=dict(size=14)),
        **{k: v for k, v in COMMON_LAYOUT.items() if k != "hovermode"},
    )

    return fig


def create_current_account_chart(
    df: pd.DataFrame,
    title: str = "Current Account Balance",
    subtitle: str = "Saldo por cuenta corriente (millones EUR)",
    color: str = COLORS["spain"],
) -> go.Figure:
    """
    Create a chart for current account balance.

    Args:
        df: DataFrame with current account data
        title: Chart title
        subtitle: Chart subtitle
        color: Line color

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if df.empty or "value" not in df.columns:
        return fig

    x_dates = df["date"].astype(str).tolist()
    values = df["value"].tolist()

    # Color bars based on sign
    colors = [COLORS["positive"] if v >= 0 else COLORS["negative"] for v in values]

    fig.add_trace(
        go.Bar(
            x=x_dates,
            y=values,
            marker_color=colors,
            hovertemplate="<b>%{x}</b><br>Balance: %{y:,.0f} M EUR<extra></extra>",
        )
    )

    # Add rolling 12-month sum if available
    if "rolling_12m_sum" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_dates,
                y=df["rolling_12m_sum"],
                mode="lines",
                name="Acumulado 12M",
                line=dict(color=color, width=2.5),
                hovertemplate="<b>12M Acumulado</b><br>%{y:,.0f} M EUR<extra></extra>",
                yaxis="y2",
            )
        )

        fig.update_layout(
            yaxis2=dict(
                title="12M Acum. (M EUR)",
                overlaying="y",
                side="right",
                showgrid=False,
                tickfont=dict(size=10),
            )
        )

    # Zero line
    fig.add_hline(y=0, line_color=COLORS["neutral"], line_width=2)

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="",
            type="date",
            tickformat="%b %Y",
            showgrid=False,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="M EUR",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=70, r=70, t=70, b=40),
        bargap=0.3,
    )

    return fig


def create_yield_curve_chart(
    df: pd.DataFrame,
    title: str = "Spanish Government Yield Curve",
    subtitle: str = "Curva de rendimientos de deuda publica",
) -> go.Figure:
    """
    Create a yield curve chart for Spanish government bonds.

    Args:
        df: DataFrame with yield curve data (maturity_years, yield)
        title: Chart title
        subtitle: Chart subtitle

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if df.empty or "maturity_years" not in df.columns or "yield" not in df.columns:
        return fig

    df_sorted = df.sort_values("maturity_years")

    fig.add_trace(
        go.Scatter(
            x=df_sorted["maturity_years"],
            y=df_sorted["yield"],
            mode="lines+markers",
            name="Yield",
            line=dict(color=COLORS["spain"], width=3),
            marker=dict(size=10, color=COLORS["spain"]),
            hovertemplate="<b>%{x}Y</b><br>Yield: %{y:.3f}%<extra></extra>",
        )
    )

    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        **COMMON_LAYOUT,
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=16)),
        xaxis=dict(
            title="Vencimiento (anos)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            tickfont=dict(size=10),
            tickvals=[0.25, 0.5, 1, 2, 3, 5, 10, 15],
            ticktext=["3M", "6M", "1A", "2A", "3A", "5A", "10A", "15A"],
        ),
        yaxis=dict(
            title="Rendimiento (%)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            ticksuffix="%",
            tickfont=dict(size=10),
        ),
        showlegend=False,
        margin=dict(l=60, r=30, t=70, b=50),
    )

    return fig


def create_bde_kpi_card_data(
    df: pd.DataFrame,
    name: str,
    value_col: str = "value",
) -> dict:
    """
    Extract KPI data from a BdE indicator DataFrame.

    Args:
        df: DataFrame with indicator data
        name: Indicator name
        value_col: Name of the value column

    Returns:
        Dictionary with KPI data
    """
    if df.empty:
        return {
            "name": name,
            "value": None,
            "change_pct": None,
            "yoy_change_pct": None,
            "date": None,
        }

    latest = df.iloc[-1]
    return {
        "name": name,
        "value": latest.get(value_col),
        "change_pct": latest.get("change_pct"),
        "yoy_change_pct": latest.get("yoy_change_pct"),
        "date": latest.get("date"),
    }
