"""Chart helpers: one place for style so every visual is consistent
(colour-blind-safe palette, labelled axes with units, readable fonts,
hover tooltips) and every chart ships with a text alternative."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.constants import ACCENT, MODES, NEUTRAL, PALETTE, WEEKDAYS

FONT = dict(family="Inter, Segoe UI, Arial, sans-serif", size=13)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
YEAR_COLORS = ["#BBBBBB", "#88CCEE", "#0072B2", "#D55E00", "#009E73", "#CC79A7"]


def style(fig: go.Figure, height: int = 420, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        font=FONT,
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(font_size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None) if legend else None,
        showlegend=legend,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)")
    return fig


def show(fig: go.Figure, alt: str, key: str | None = None):
    """Render a chart followed by its text alternative (accessibility)."""
    st.plotly_chart(fig, width="stretch", key=key)
    st.caption(f"Chart description: {alt}")


# ------------------------------------------------------------------ charts
def monthly_lines(df: pd.DataFrame, value: str, label: str) -> go.Figure:
    """One line per year, x = month: shows seasonality and year-on-year shift."""
    fig = go.Figure()
    years = sorted(df["year"].unique())
    for i, y in enumerate(years):
        d = df[df["year"] == y].sort_values("month")
        fig.add_trace(go.Scatter(
            x=[MONTHS[m - 1] for m in d["month"]], y=d[value], name=str(y), mode="lines+markers",
            line=dict(color=YEAR_COLORS[(i + len(YEAR_COLORS) - len(years)) % len(YEAR_COLORS)],
                      width=3 if y == years[-1] else 2),
            hovertemplate=f"%{{x}} {y}<br>{label}: %{{y:,}}<extra></extra>",
        ))
    fig.add_vrect(x0="Jun", x1="Sep", fillcolor="#E69F00", opacity=0.10, line_width=0,
                  annotation_text="Summer", annotation_position="top left")
    fig.update_layout(xaxis_title="Month", yaxis_title=label)
    return style(fig)


def yearly_bars(df: pd.DataFrame, value: str, label: str) -> go.Figure:
    fig = px.bar(df, x="year", y=value, text=value, color_discrete_sequence=[NEUTRAL],
                 labels={"year": "Year", value: label})
    fig.update_traces(texttemplate="%{text:,}", textposition="outside",
                      hovertemplate="Year %{x}<br>" + label + ": %{y:,}<extra></extra>")
    fig.update_xaxes(type="category")
    if len(df) >= 2:
        first, last = df[value].iloc[0], df[value].iloc[-1]
        if first:
            fig.add_annotation(x=str(df["year"].iloc[-1]), y=last, yshift=40, showarrow=False,
                               text=f"{(last - first) / first:+.1%} vs {df['year'].iloc[0]}",
                               font=dict(color=ACCENT, size=14))
    return style(fig, height=360, legend=False)


def dep_bubble_map(dep: pd.DataFrame, size_col: str, size_label: str) -> go.Figure:
    d = dep.dropna(subset=["lat", "lon"]).copy()
    d = d[d[size_col] > 0]
    fig = px.scatter_map(
        d, lat="lat", lon="lon", size=size_col, color="killed_per_100_acc",
        color_continuous_scale="OrRd", size_max=38, zoom=4.3,
        center={"lat": 46.6, "lon": 2.4}, map_style="carto-positron",
        hover_name="dep_name",
        hover_data={"lat": False, "lon": False, "region": True, size_col: ":,",
                    "accidents": ":,", "killed_per_100_acc": ":.1f"},
        labels={size_col: size_label, "killed_per_100_acc": "Killed per 100 accidents",
                "accidents": "Accidents", "region": "Region"},
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Killed per<br>100 accidents"))
    return style(fig, height=560, legend=False)


def share_comparison(df: pd.DataFrame, cat: str, title_a: str, title_b: str) -> go.Figure:
    """Grouped bars: share of A vs share of B per category (over-representation)."""
    long = df.melt(id_vars=cat, value_vars=["share_a", "share_b"], var_name="what", value_name="pct")
    long["what"] = long["what"].map({"share_a": title_a, "share_b": title_b})
    fig = px.bar(long, x="pct", y=cat, color="what", barmode="group", orientation="h",
                 text="pct", color_discrete_sequence=["#BBBBBB", ACCENT],
                 labels={"pct": "Share (%)", cat: "", "what": ""})
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside",
                      hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>")
    fig.update_yaxes(categoryorder="total ascending")
    return style(fig, height=max(260, 60 * df[cat].nunique()))


def ranking_ci(dep: pd.DataFrame, n: int, top: bool) -> go.Figure:
    d = dep.sort_values("fatal_share", ascending=not top).head(n).iloc[::-1]
    fig = go.Figure(go.Scatter(
        x=d["fatal_share"], y=d["dep_name"], mode="markers",
        marker=dict(size=10, color=ACCENT if top else NEUTRAL),
        error_x=dict(type="data", symmetric=False, array=d["ci_high"] - d["fatal_share"],
                     arrayminus=d["fatal_share"] - d["ci_low"], color="#888", thickness=1.5),
        customdata=d[["accidents", "fatal_accidents", "ci_low", "ci_high"]],
        hovertemplate="<b>%{y}</b><br>Fatal accidents: %{x:.1f}%"
                      "<br>95% CI: %{customdata[2]:.1f}–%{customdata[3]:.1f}%"
                      "<br>%{customdata[1]:,} fatal / %{customdata[0]:,} accidents<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Share of accidents that are fatal (%) with 95% confidence interval",
                      yaxis_title="")
    return style(fig, height=max(300, 28 * n), legend=False)


def hour_weekday_heatmap(df: pd.DataFrame, value: str, label: str, scale="Blues") -> go.Figure:
    pv = df.pivot_table(index="weekday", columns="hour", values=value, observed=False).reindex(WEEKDAYS)
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=[f"{h:02d}h" for h in pv.columns], y=pv.index, colorscale=scale,
        colorbar=dict(title=label.replace(" ", "<br>", 1)),
        hovertemplate="%{y} %{x}<br>" + label + ": %{z:,.1f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Hour of day", yaxis_title="Day of week")
    fig.update_yaxes(autorange="reversed")
    return style(fig, height=360, legend=False)


def mode_trend_small_multiples(df: pd.DataFrame) -> go.Figure:
    order = [m for m in MODES if m in df["mode"].unique()]
    fig = px.line(df, x="year", y="killed", facet_col="mode", facet_col_wrap=4, markers=True,
                  category_orders={"mode": order}, color="mode", color_discrete_map=PALETTE,
                  labels={"year": "Year", "killed": "Killed (people)", "mode": "Mode"})
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_yaxes(matches=None, rangemode="tozero", showticklabels=True)
    fig.update_xaxes(dtick=1)
    fig.update_traces(hovertemplate="%{x}: %{y:,} killed<extra></extra>")
    return style(fig, height=460, legend=False)


def age_mode_heatmap(df: pd.DataFrame) -> go.Figure:
    pv = df.pivot_table(index="mode", columns="age_group", values="killed", aggfunc="sum",
                        observed=False).fillna(0)
    pv = pv.reindex([m for m in MODES if m in pv.index])
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=list(pv.columns.astype(str)), y=list(pv.index), colorscale="OrRd",
        text=pv.values.astype(int), texttemplate="%{text}",
        colorbar=dict(title="Killed"),
        hovertemplate="%{y}, age %{x}<br>Killed: %{z:,}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Age group (years)", yaxis_title="")
    return style(fig, height=380, legend=False)


def bar_rate(df: pd.DataFrame, cat: str, rate: str, label: str, n_col: str) -> go.Figure:
    d = df.sort_values(rate)
    fig = go.Figure(go.Bar(
        x=d[rate], y=d[cat], orientation="h", marker_color=NEUTRAL, text=d[rate],
        texttemplate="%{text:.1f}", textposition="outside", customdata=d[[n_col]],
        hovertemplate="%{y}<br>" + label + ": %{x:.2f}<br>Accidents: %{customdata[0]:,}<extra></extra>",
    ))
    fig.update_layout(xaxis_title=label, yaxis_title="")
    return style(fig, height=max(260, 48 * len(d)), legend=False)


def scenario_bars(baseline: float, scenario: float, label: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=["Observed", "Scenario"], y=[baseline, scenario], marker_color=["#BBBBBB", "#009E73"],
        text=[f"{baseline:,.0f}", f"{scenario:,.0f}"], textposition="outside",
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(yaxis_title=label, xaxis_title="")
    return style(fig, height=320, legend=False)
