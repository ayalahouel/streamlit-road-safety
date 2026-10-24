"""Who pays the price on French roads? — a data-storytelling dashboard on the
national road-accident files (BAAC, ONISR, data.gouv.fr), 2021-2024.

Run:  streamlit run app.py
"""

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from sections import conclusions, deep_dives, intro, overview, quality
from utils.constants import DATASET_PAGE, DATASET_TITLE, LICENSE, MODES, REGIONS, VULNERABLE, YEARS
from utils.io import PROCESSED_DIR

st.set_page_config(
    page_title="Who pays the price on French roads?",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(os.environ.get("ROADSAFETY_DATA_DIR", PROCESSED_DIR))

METRICS = {
    "Killed": ("killed", "People killed"),
    "Killed or hospitalised": ("ksi", "People killed or hospitalised"),
    "All casualties": ("injured", "Casualties (killed + injured)"),
}


@st.cache_data(show_spinner=False)
def load_data(data_dir: str):
    d = Path(data_dir)
    if not (d / "accidents.parquet").exists():
        # first run on a clean checkout: download + build (cached on disk afterwards)
        from utils.io import download_raw
        from utils.prep import build_tables, save_tables
        download_raw(YEARS)
        save_tables(*build_tables(YEARS), out_dir=d)
    acc = pd.read_parquet(d / "accidents.parquet")
    users = pd.read_parquet(d / "users.parquet")
    users["ksi"] = users["killed"] | users["hospitalised"]
    qual = json.loads((d / "quality.json").read_text(encoding="utf-8"))
    return acc, users, qual


@st.cache_data(show_spinner=False)
def apply_filters(_acc, _users, years, territory, regions, areas, modes):
    """Cached on the filter values only (the leading underscore tells Streamlit
    not to hash the two large, static dataframes)."""
    acc, users = _acc, _users
    a = acc[acc["year"].between(*years)]
    if territory == "Metropolitan France":
        a = a[a["metro"]]
    elif territory == "Overseas":
        a = a[a["region"] == "Overseas"]
    if regions:
        a = a[a["region"].isin(regions)]
    if areas:
        a = a[a["area"].isin(areas)]
    u = users[users["acc_uid"].isin(a["acc_uid"])]
    if modes:
        u = u[u["mode"].isin(modes)]
        a = a[a["acc_uid"].isin(u["acc_uid"])]
    return a, u


with st.spinner("Loading the national road-accident files (first run downloads ~150 MB, then cached)…"):
    try:
        acc_all, users_all, qual = load_data(str(DATA_DIR))
    except Exception as err:  # clear message instead of a stack trace
        st.error(f"Data could not be loaded: {err}. Run `python scripts/build_dataset.py` "
                 "from the project root (internet access to data.gouv.fr is required once).")
        st.stop()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Filters")
    st.caption("Every KPI and chart reacts to these filters.")
    y_min, y_max = int(acc_all["year"].min()), int(acc_all["year"].max())
    years = st.slider("Years", y_min, y_max, (y_min, y_max), help="Calendar years of the accidents.")
    territory = st.radio("Territory", ["Metropolitan France", "Overseas", "All"], index=0,
                         help="Overseas territories have very different road networks; "
                              "they are excluded from the national picture by default.")
    region_opts = [r for r in REGIONS if r != "Overseas"] if territory == "Metropolitan France" else list(REGIONS)
    regions = st.multiselect("Region(s)", region_opts, placeholder="All regions")
    areas = st.multiselect("Area", ["Rural (outside built-up area)", "Urban (built-up area)"],
                           placeholder="Urban and rural")
    modes = st.multiselect("Road-user mode", MODES, placeholder="All modes",
                           help="Pedestrians are counted as pedestrians; everyone else by the "
                                "vehicle they were in or on.")
    metric_name = st.selectbox("Outcome to analyse", list(METRICS),
                               help="'Killed' = died within 30 days of the crash (official definition).")
    st.divider()
    st.caption(f"Source: [{DATASET_TITLE}]({DATASET_PAGE}) · {LICENSE}")

metric_col, metric_label = METRICS[metric_name]
acc, users = apply_filters(acc_all, users_all, years, territory, tuple(regions), tuple(areas), tuple(modes))
ctx = dict(years=years, territory=territory, regions=regions, areas=areas, modes=modes,
           metric_col=metric_col, metric_label=metric_label, metric_name=metric_name)

# ------------------------------------------------------------------ header + KPIs
st.title("Who pays the price on French roads?")
st.caption(f"Source: {DATASET_TITLE} — data.gouv.fr — {LICENSE}. "
           f"Showing {years[0]}–{years[1]}, {territory.lower()}"
           + (f", {', '.join(regions)}" if regions else "") + ".")

if acc.empty:
    st.warning("No accident matches these filters. Widen the selection in the sidebar.")
    st.stop()

first, last = years
kill_by_year = users.groupby("year")["killed"].sum()
n_acc, n_killed, n_hosp = len(acc), int(users["killed"].sum()), int(users["hospitalised"].sum())
lethality = 100 * n_killed / n_acc
vuln_share = 100 * users.loc[users["killed"], "mode"].isin(VULNERABLE).mean() if n_killed else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Injury accidents", f"{n_acc:,}", help="Accidents with at least one injured person.")
delta = None
if first != last and kill_by_year.get(first, 0):
    delta = f"{(kill_by_year.get(last, 0) - kill_by_year[first]) / kill_by_year[first]:+.1%} {last} vs {first}"
k2.metric("People killed", f"{n_killed:,}", delta=delta, delta_color="inverse",
          help="Died within 30 days. Delta compares the last and first selected years.")
k3.metric("Hospitalised", f"{n_hosp:,}", help="Hospitalised for more than 24 hours.")
k4.metric("Killed per 100 accidents", f"{lethality:.1f}",
          help="Lethality: how deadly an accident is once it happens.")
k5.metric("Vulnerable users among the killed", f"{vuln_share:.0f}%",
          help="Pedestrians, cyclists, e-scooter users and motorised 2-3 wheelers.")

tabs = st.tabs(["① Why it matters", "② The big picture", "③ Where, when, who",
                "④ Takeaways & what-if", "⑤ Data quality"])
with tabs[0]:
    intro.render(acc, users, ctx)
with tabs[1]:
    overview.render(acc, users, ctx)
with tabs[2]:
    deep_dives.render(acc, users, ctx)
with tabs[3]:
    conclusions.render(acc, users, ctx)
with tabs[4]:
    quality.render(acc_all, users_all, qual, ctx)
