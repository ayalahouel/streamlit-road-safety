"""Chapter 4 — Key insights, what-if scenarios, implications and next steps."""

import plotly.graph_objects as go
import streamlit as st

from utils import viz
from utils.constants import ACCENT, MODES, VULNERABLE


def _facts(acc, users):
    f = {}
    n_years = acc["year"].nunique()
    f["killed_per_year"] = users["killed"].sum() / max(n_years, 1)
    area = acc[acc["area"] != "Not recorded"].groupby("area").agg(a=("acc_uid", "size"), k=("n_killed", "sum"))
    rur = [i for i in area.index if i.startswith("Rural")]
    urb = [i for i in area.index if i.startswith("Urban")]
    if rur and urb:
        f["rural_acc"] = area.loc[rur[0], "a"] / n_years
        f["rural_rate"] = area.loc[rur[0], "k"] / area.loc[rur[0], "a"]
        f["urban_rate"] = area.loc[urb[0], "k"] / area.loc[urb[0], "a"]
        f["rural_death_share"] = area.loc[rur[0], "k"] / area["k"].sum()
    night = acc.groupby("night").agg(a=("acc_uid", "size"), k=("n_killed", "sum"))
    if {True, False} <= set(night.index):
        f["night_ratio"] = (night.loc[True, "k"] / night.loc[True, "a"]) / (night.loc[False, "k"] / night.loc[False, "a"])
    killed = users[users["killed"]]
    f["vuln_share"] = killed["mode"].isin(VULNERABLE).mean() if len(killed) else 0
    f["killed_by_mode_year"] = killed.groupby("mode").size() / max(n_years, 1)
    yearly = users.groupby("year")["killed"].sum()
    f["yearly"] = yearly
    return f


def render(acc, users, ctx):
    f = _facts(acc, users)
    st.subheader("What the data tells us")

    insights = []
    if "rural_rate" in f:
        insights.append(
            f"**Danger is rural.** Roads outside built-up areas carry **{f['rural_death_share']:.0%}** of "
            f"deaths; an accident there is **{f['rural_rate'] / f['urban_rate']:.1f}×** as deadly as in town.")
    if "night_ratio" in f:
        insights.append(f"**Danger is nocturnal.** An accident at night is **{f['night_ratio']:.1f}×** as "
                        "deadly as one in daylight, with weekend nights standing out.")
    insights.append(f"**Danger is unequal between users.** **{f['vuln_share']:.0%}** of the people killed were "
                    "pedestrians, cyclists, e-scooter users or on a motorised two-/three-wheeler.")
    if len(f["yearly"]) >= 2:
        ch = (f["yearly"].iloc[-1] - f["yearly"].iloc[0]) / max(f["yearly"].iloc[0], 1)
        insights.append(f"**Progress has stalled.** Deaths changed by **{ch:+.1%}** between "
                        f"{f['yearly'].index[0]} and {f['yearly'].index[-1]}.")
    for i, txt in enumerate(insights, 1):
        st.markdown(f"{i}. {txt}")

    # ------------------------------------------------------------ what-if
    st.divider()
    st.subheader("What-if: which lever saves the most lives?")
    st.caption("Illustrative scenarios built on the filtered data. They are *not* forecasts: they hold the "
               "number of accidents constant and assume the effect is fully achieved. Treat the results as "
               "orders of magnitude to compare levers, not as causal estimates.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Lever A — make rural accidents less deadly")
        st.markdown("E.g. speed management, safer road sides, faster emergency response.")
        if "rural_rate" in f:
            gap = st.slider("Share of the rural-vs-urban lethality gap closed", 0, 100, 25, 5,
                            format="%d%%", key="gap")
            saved_a = f["rural_acc"] * (f["rural_rate"] - f["urban_rate"]) * gap / 100
            st.metric("Lives saved per year (estimate)", f"{saved_a:,.0f}",
                      help="= rural accidents per year × (rural − urban killed per accident) × share of gap closed")
            viz.show(viz.scenario_bars(f["killed_per_year"], f["killed_per_year"] - saved_a,
                                       "People killed per year"),
                     alt=f"Bars: observed {f['killed_per_year']:,.0f} deaths per year versus "
                         f"{f['killed_per_year'] - saved_a:,.0f} in scenario A.", key="scenA")
        else:
            st.info("Select both urban and rural areas to run this scenario.")
    with c2:
        st.markdown("##### Lever B — protect specific road users")
        st.markdown("E.g. segregated cycle lanes, safer crossings, motorcycle training & equipment.")
        avail = [m for m in MODES if m in f["killed_by_mode_year"].index]
        default = [m for m in avail if m in VULNERABLE][:2]
        target = st.multiselect("Road users targeted", avail, default=default, key="target_modes")
        cut = st.slider("Reduction of deaths among them", 0, 50, 20, 5, format="%d%%", key="cut")
        saved_b = f["killed_by_mode_year"].reindex(target).fillna(0).sum() * cut / 100
        st.metric("Lives saved per year (estimate)", f"{saved_b:,.0f}",
                  help="= current deaths per year in the targeted modes × reduction")
        viz.show(viz.scenario_bars(f["killed_per_year"], f["killed_per_year"] - saved_b,
                                   "People killed per year"),
                 alt=f"Bars: observed {f['killed_per_year']:,.0f} deaths per year versus "
                     f"{f['killed_per_year'] - saved_b:,.0f} in scenario B.", key="scenB")

    # ------------------------------------------------------------ target path
    if len(f["yearly"]) >= 2:
        st.markdown("##### Lever C — what would halving deaths by 2030 require?")
        y0, y1 = int(f["yearly"].index[0]), int(f["yearly"].index[-1])
        k0, k1 = f["yearly"].iloc[0], f["yearly"].iloc[-1]
        target_pct = st.slider("Reduction target by 2030 (vs first selected year)", 10, 70, 50, 5,
                               format="%d%%", key="target")
        req = 1 - (1 - target_pct / 100) ** (1 / (2030 - y0))
        obs = 1 - (k1 / k0) ** (1 / (y1 - y0)) if k0 else 0
        m1, m2 = st.columns(2)
        m1.metric("Required yearly decrease", f"{req:.1%}")
        m2.metric(f"Observed yearly change {y0}–{y1}", f"{-obs:+.1%}")
        yrs = list(range(y0, 2031))
        fig = go.Figure()
        fig.add_scatter(x=yrs, y=[k0 * (1 - req) ** (y - y0) for y in yrs], name="Target path",
                        line=dict(dash="dash", color="#009E73"),
                        hovertemplate="%{x}: %{y:,.0f}<extra>Target path</extra>")
        fig.add_scatter(x=list(f["yearly"].index), y=list(f["yearly"].values), name="Observed",
                        mode="lines+markers", line=dict(color=ACCENT, width=3),
                        hovertemplate="%{x}: %{y:,.0f}<extra>Observed</extra>")
        fig.update_layout(xaxis_title="Year", yaxis_title="People killed per year", yaxis_rangemode="tozero")
        viz.show(viz.style(fig, height=340), key="path",
                 alt=f"Line chart comparing observed deaths ({y0}–{y1}) with the path needed to reach a "
                     f"{target_pct}% cut by 2030, which requires about {req:.1%} fewer deaths every year.")

    # ------------------------------------------------------------ implications
    st.divider()
    st.subheader("Implications & next steps")
    st.markdown(
        "- **Target lethality, not only volume.** Ranking territories by number of accidents points to big "
        "cities; ranking by lethality points to rural departments. Both lists are needed.\n"
        "- **Rural, night-time, unprotected users** are the triple intersection where effort pays most.\n"
        "- **Measure progress per user group**: a flat national total can hide rising risk for "
        "e-scooter users or cyclists as these modes grow.\n"
        "- **Next analytical steps:** normalise by exposure (population, vehicle-km travelled, modal "
        "share) — the BAAC files alone cannot say whether a group is riskier or simply more present; "
        "add 2025 data when published; test the effect of local measures (30 km/h zones, speed-limit "
        "changes on departmental roads) with before/after designs."
    )
