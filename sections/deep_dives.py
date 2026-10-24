"""Chapter 3 — Deep dives: where, when and who."""

import pandas as pd
import streamlit as st

from utils import viz
from utils.constants import LUM
from utils.prep import dep_summary

MIN_ACC_DEFAULT = 300


def _where(acc, users, ctx):
    col, label = ctx["metric_col"], ctx["metric_label"]
    # ----- urban vs rural: volume vs toll
    area = (
        acc[acc["area"] != "Not recorded"]
        .groupby("area").agg(accidents=("acc_uid", "size"), killed=("n_killed", "sum")).reset_index()
    )
    if len(area) == 2:
        area["share_a"] = 100 * area["accidents"] / area["accidents"].sum()
        area["share_b"] = 100 * area["killed"] / max(area["killed"].sum(), 1)
        rural = area[area["area"].str.startswith("Rural")].iloc[0]
        ratio = (rural["killed"] / rural["accidents"]) / max(
            area.loc[~area["area"].str.startswith("Rural"), "killed"].sum()
            / area.loc[~area["area"].str.startswith("Rural"), "accidents"].sum(), 1e-9)
        st.subheader(f"Rural roads: {rural['share_a']:.0f}% of accidents, {rural['share_b']:.0f}% of deaths")
        st.markdown(
            f"Most accidents happen in towns, but an accident outside built-up areas is "
            f"**{ratio:.1f}× more deadly** (killed per accident). Typical explanations from road-safety "
            "research: higher speeds, head-on and run-off-road crashes, longer emergency response times. "
            "Volume and danger are two different maps."
        )
        viz.show(viz.share_comparison(area, "area", "Share of accidents", "Share of people killed"),
                 alt=f"Grouped bars: rural areas account for {rural['share_a']:.0f}% of accidents but "
                     f"{rural['share_b']:.0f}% of deaths; urban areas the reverse.", key="area")
    else:
        st.subheader("Where are accidents deadliest?")

    # ----- map
    st.markdown(f"**Map — bubble size: {label.lower()}; colour: killed per 100 accidents**")
    dep = dep_summary(acc)
    dep = dep.merge(users.groupby("dep")[col].sum().rename("metric").reset_index(), on="dep", how="left")
    dep["metric"] = dep["metric"].fillna(0)
    if ctx["territory"] != "Metropolitan France":
        st.caption("The map is centred on mainland France; zoom out to see overseas territories.")
    worst = dep[dep["accidents"] >= MIN_ACC_DEFAULT].nlargest(3, "killed_per_100_acc")["dep_name"].tolist()
    viz.show(viz.dep_bubble_map(dep, "metric", label),
             alt="Bubble map of French departments. Large bubbles (big cities) show where most victims are; "
                 "dark red bubbles show where accidents are most lethal"
                 + (f", for example {', '.join(worst)}." if worst else "."), key="map")

    # ----- ranking with uncertainty
    st.markdown("**Ranking — share of accidents that are fatal, with uncertainty**")
    c1, c2, c3 = st.columns(3)
    which = c1.radio("Show", ["Most lethal", "Least lethal"], horizontal=True, key="rank_dir")
    n = c2.slider("Number of departments", 5, 25, 12, key="rank_n")
    min_acc = c3.number_input("Minimum accidents per department", 50, 5000, MIN_ACC_DEFAULT, step=50,
                              help="Departments with few accidents give very noisy rates; "
                                   "the 95% Wilson interval shows that uncertainty.")
    ranked = dep[dep["accidents"] >= min_acc]
    if ranked.empty:
        st.info("No department reaches that minimum with the current filters.")
    else:
        viz.show(viz.ranking_ci(ranked, min(n, len(ranked)), top=which == "Most lethal"),
                 alt=f"Dot plot of the {which.lower()} departments by share of fatal accidents, with 95% "
                     "confidence intervals as horizontal lines. Wide intervals mean few accidents.",
                 key="rank")
        st.caption("Overlapping intervals mean two departments cannot be confidently ranked against each other.")

    # ----- road type
    road = (acc[acc["road"] != "Not recorded"].groupby("road")
            .agg(accidents=("acc_uid", "size"), killed=("n_killed", "sum")).reset_index())
    road = road[road["accidents"] >= 30]
    road["rate"] = 100 * road["killed"] / road["accidents"]
    if not road.empty:
        top = road.nlargest(1, "rate").iloc[0]
        st.markdown(f"**By type of road — the deadliest per accident: {top['road'].lower()} "
                    f"({top['rate']:.1f} killed per 100 accidents)**")
        viz.show(viz.bar_rate(road, "road", "rate", "Killed per 100 accidents", "accidents"),
                 alt="Horizontal bars of killed per 100 accidents by road category.", key="road")


def _when(acc, users, ctx):
    hw = (acc.dropna(subset=["hour", "weekday"])
          .groupby(["weekday", "hour"], observed=False)
          .agg(accidents=("acc_uid", "size"), killed=("n_killed", "sum")).reset_index())
    hw["rate"] = 100 * hw["killed"] / hw["accidents"].where(hw["accidents"] > 0)
    night = acc.groupby("night").agg(a=("acc_uid", "size"), k=("n_killed", "sum"))
    if {True, False} <= set(night.index):
        r_n = night.loc[True, "k"] / night.loc[True, "a"]
        r_d = night.loc[False, "k"] / night.loc[False, "a"]
        st.subheader(f"Rush hour brings the most accidents — the night brings the most deaths "
                     f"({r_n / r_d:.1f}× more lethal)")
    else:
        st.subheader("When do accidents happen — and when do they kill?")
    st.markdown(
        "Switch the view below: **volume** follows commuting patterns (weekday rush hours), while "
        "**lethality** concentrates on nights and weekend nights, when traffic is light, speeds are high, "
        "and alcohol or fatigue are more often involved."
    )
    view = st.radio("Heatmap shows", ["Number of accidents", "Killed per 100 accidents"],
                    horizontal=True, key="hw_view")
    value = "accidents" if view == "Number of accidents" else "rate"
    peak = hw.dropna(subset=[value]).nlargest(1, value)
    peak_txt = (f" The darkest cell is {peak['weekday'].iloc[0]} {int(peak['hour'].iloc[0]):02d}h "
                f"({peak[value].iloc[0]:,.1f})." if not peak.empty else "")
    if value == "accidents":
        fig = viz.hour_weekday_heatmap(hw, "accidents", "Accidents", "Blues")
        alt = "Heatmap of the number of accidents by hour of day and day of week." + peak_txt
    else:
        fig = viz.hour_weekday_heatmap(hw, "rate", "Killed per 100 accidents", "OrRd")
        alt = "Heatmap of killed per 100 accidents by hour of day and day of week." + peak_txt
    viz.show(fig, alt=alt, key="hw")

    lum = (acc[acc["lighting"] != "Not recorded"].groupby("lighting")
           .agg(accidents=("acc_uid", "size"), killed=("n_killed", "sum")).reset_index())
    lum["rate"] = 100 * lum["killed"] / lum["accidents"]
    if not lum.empty:
        st.markdown("**Lighting conditions — darkness without street lighting is the most dangerous**")
        lum["lighting"] = pd.Categorical(lum["lighting"], categories=list(LUM.values()), ordered=True)
        viz.show(viz.bar_rate(lum, "lighting", "rate", "Killed per 100 accidents", "accidents"),
                 alt="Horizontal bars of killed per 100 accidents by lighting condition; night without "
                     "street lighting has the highest rate.", key="lum")


def _who(acc, users, ctx):
    by_mode = users.groupby("mode").agg(involved=("acc_uid", "size"), killed=("killed", "sum")).reset_index()
    by_mode["share_a"] = 100 * by_mode["involved"] / by_mode["involved"].sum()
    by_mode["share_b"] = 100 * by_mode["killed"] / max(by_mode["killed"].sum(), 1)
    by_mode["over"] = by_mode["share_b"] / by_mode["share_a"]
    cand = by_mode[by_mode["killed"] >= 20]
    if not cand.empty:
        top = cand.nlargest(1, "over").iloc[0]
        st.subheader(f"{top['mode']}: {top['over']:.1f}× over-represented among the dead")
        st.markdown(
            f"They are **{top['share_a']:.0f}%** of the people involved in injury accidents but "
            f"**{top['share_b']:.0f}%** of those killed. Cars are where most people *are*; "
            "unprotected users are where most of the *risk* is."
        )
    else:
        st.subheader("Who pays the price?")
    viz.show(viz.share_comparison(by_mode, "mode", "Share of people involved", "Share of people killed"),
             alt="Grouped bars per road-user mode comparing the share of people involved with the share "
                 "of people killed." + (f" {top['mode']} shows the largest gap." if not cand.empty else ""),
             key="mode_share")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Trend by mode (small multiples, own y-scale each)**")
        trend = users.groupby(["year", "mode"], as_index=False)["killed"].sum()
        viz.show(viz.mode_trend_small_multiples(trend),
                 alt="Small-multiple line charts of people killed per year for each road-user mode.",
                 key="mode_trend")
    with c2:
        st.markdown("**Age × mode — people killed**")
        k = users[users["age_group"].notna()]
        cell = (k[k["killed"]].groupby(["mode", "age_group"], observed=True).size())
        cell_txt = (f" The largest cell is {cell.idxmax()[0]} aged {cell.idxmax()[1]} ({cell.max():,} killed)."
                    if not cell.empty else "")
        viz.show(viz.age_mode_heatmap(k),
                 alt="Heatmap of people killed by age group (columns) and road-user mode (rows)." + cell_txt,
                 key="age_mode")
    st.caption("Pedestrians are classified as pedestrians whatever vehicle hit them. 'E-scooter / PMD' covers "
               "personal mobility devices (motorised and not). Ages computed as accident year − birth year.")


def render(acc, users, ctx):
    t1, t2, t3 = st.tabs(["Where", "When", "Who"])
    with t1:
        _where(acc, users, ctx)
    with t2:
        _when(acc, users, ctx)
    with t3:
        _who(acc, users, ctx)
