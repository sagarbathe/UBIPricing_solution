"""
Reusable KPI card and data-table components for persona pages.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ──────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────
def render_kpi_row(kpis: list[dict]) -> None:
    """
    Render a row of KPI metric cards.

    Parameters
    ----------
    kpis : list[dict]
        Each dict has keys: label, value, delta (optional), delta_color (optional).
        Example: {"label": "Loss Ratio", "value": "62.3%", "delta": "-3.1%"}
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            delta = kpi.get("delta")
            delta_color = kpi.get("delta_color", "normal")
            st.metric(
                label=kpi["label"],
                value=kpi["value"],
                delta=delta,
                delta_color=delta_color,
            )


# ──────────────────────────────────────────────
# Data table with search / download
# ──────────────────────────────────────────────
def render_gold_table(
    df: pd.DataFrame,
    title: str,
    table_name: str,
    max_rows: int = 200,
    key_suffix: str = "",
) -> None:
    """
    Render an interactive preview of a Gold table.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe to display.
    title : str
        Section heading.
    table_name : str
        Logical gold table name (for display).
    max_rows : int
        Max rows shown in the table.
    key_suffix : str
        Unique key suffix to avoid Streamlit widget conflicts.
    """
    with st.expander(f"📋 {title}  —  `{table_name}`  ({len(df):,} rows)", expanded=False):
        # Search / filter
        search = st.text_input(
            "🔍 Filter rows (searches all columns)",
            key=f"search_{table_name}_{key_suffix}",
        )
        display_df = df.head(max_rows)
        if search:
            mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            display_df = df[mask].head(max_rows)

        st.dataframe(display_df, use_container_width=True, height=350)

        # Download
        csv = df.to_csv(index=False)
        st.download_button(
            "⬇️  Download full CSV",
            csv,
            file_name=f"{table_name}.csv",
            mime="text/csv",
            key=f"dl_{table_name}_{key_suffix}",
        )


# ──────────────────────────────────────────────
# Chart helpers
# ──────────────────────────────────────────────
def render_distribution_chart(
    df: pd.DataFrame,
    column: str,
    title: str,
    nbins: int = 30,
    color: str = "#1f77b4",
) -> None:
    """Render a histogram / distribution chart."""
    fig = px.histogram(
        df, x=column, nbins=nbins, title=title,
        color_discrete_sequence=[color],
    )
    fig.update_layout(
        xaxis_title=column.replace("_", " ").title(),
        yaxis_title="Count",
        margin=dict(t=40, b=30),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    trendline: str | None = "ols",
) -> None:
    """Render a scatter plot with optional trendline."""
    fig = px.scatter(
        df, x=x, y=y, color=color, title=title,
        trendline=trendline,
        opacity=0.6,
    )
    fig.update_layout(margin=dict(t=40, b=30), height=380)
    st.plotly_chart(fig, use_container_width=True)


def render_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    orientation: str = "v",
) -> None:
    """Render a bar chart."""
    fig = px.bar(
        df, x=x, y=y, color=color, title=title,
        orientation=orientation,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(margin=dict(t=40, b=30), height=380)
    st.plotly_chart(fig, use_container_width=True)


def render_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
) -> None:
    """Render a line chart."""
    fig = px.line(
        df, x=x, y=y, color=color, title=title,
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(margin=dict(t=40, b=30), height=380)
    st.plotly_chart(fig, use_container_width=True)


def render_gauge(value: float, title: str, max_val: float = 1.0, suffix: str = "") -> None:
    """Render a gauge / bullet chart for a single metric."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": suffix},
            title={"text": title},
            gauge={
                "axis": {"range": [0, max_val]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, max_val * 0.4], "color": "#d4edda"},
                    {"range": [max_val * 0.4, max_val * 0.7], "color": "#fff3cd"},
                    {"range": [max_val * 0.7, max_val], "color": "#f8d7da"},
                ],
            },
        )
    )
    fig.update_layout(height=250, margin=dict(t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)
