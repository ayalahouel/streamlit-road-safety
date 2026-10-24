"""Chapter 5 — Data quality, validation checks, limitations and license."""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import viz
from utils.constants import DATA_DICTIONARY, DATASET_PAGE, DATASET_TITLE, LICENSE

CHECK_LABELS = {
    "caract_duplicate_ids": ("Duplicate accident ids (caract.)", "dropped, first kept"),
    "caract_year_mismatch": ("Accident year ≠ file year", "kept, file year used"),
    "invalid_dates": ("Invalid dates", "excluded from date-based charts"),
    "invalid_hours": ("Invalid / missing hour", "excluded from the hour heatmap"),
    "unknown_department": ("Unknown department code", "excluded from geographic views"),
    "metro_coords_outside_france": ("Mainland GPS point outside France", "coordinate set to missing"),
    "lieux_duplicate_ids": ("Several road records for one accident", "first record kept"),
    "implausible_speed_limits": ("Speed limit outside 10–130 km/h", "set to missing"),
    "usagers_exact_duplicates": ("Exact duplicate people rows", "dropped"),
    "users_without_vehicle_match": ("People not matched to a vehicle", "mode = Other / unknown"),
    "users_orphan_accident": ("People whose accident is missing", "dropped"),
    "unknown_severity": ("Injury severity not recorded", "counted, not as casualty"),
    "implausible_ages": ("Age outside 0–105", "age set to missing"),
    "accidents_without_people": ("Accidents with no person record", "kept, toll = 0"),
}


def render(acc_all, users_all, qual, ctx):
    st.subheader("Can we trust these numbers? Data quality & limitations")
    t = qual["totals"]
    st.markdown(
        f"The cleaned dataset holds **{t['accidents']:,} accidents** and **{t['people']:,} people** "
        f"({', '.join(map(str, qual['years']))}). Every check below was run automatically by the "
        "pipeline (`utils/prep.py`); nothing was fixed by hand."
    )

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("**Validation checks (rows affected per year)**")
        rows = []
        for key, (label, action) in CHECK_LABELS.items():
            row = {"Check": label, "Treatment": action}
            for y, chk in qual["checks"].items():
                row[y] = chk.get(key, 0)
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    with c2:
        st.markdown("**Raw files ingested**")
        files = pd.DataFrame(
            [{"File": k, "Rows": v["rows"], "Columns": v["cols"]} for k, v in qual["files"].items()])
        st.dataframe(files, hide_index=True, width="stretch", height=360)

    st.markdown("**Missing values in key fields (% of rows, '-1' code counted as missing)**")
    miss = pd.DataFrame([
        {"file": k.rsplit("-", 1)[0], "year": k.rsplit("-", 1)[1], "field": f, "pct": v}
        for k, d in qual["missing_pct"].items() for f, v in d.items()
    ])
    miss["field"] = miss["file"] + " · " + miss["field"]
    fig = px.bar(miss, x="pct", y="field", color="year", barmode="group", orientation="h",
                 color_discrete_sequence=viz.YEAR_COLORS[-4:],
                 labels={"pct": "Missing (%)", "field": "", "year": "Year"})
    fig.update_traces(hovertemplate="%{y}<br>%{x:.2f}% missing<extra></extra>")
    worst = miss.nlargest(1, "pct").iloc[0]
    viz.show(viz.style(fig, height=max(400, 22 * miss["field"].nunique() * 1.6)), key="missing",
             alt=f"Grouped bars of missing-value percentage per key field and year. The most incomplete "
                 f"field is {worst['field']} ({worst['pct']:.1f}% in {worst['year']}).")

    st.markdown("##### Known limitations & biases")
    st.markdown(
        "- **Coverage:** only *injury* accidents on public roads recorded by police or gendarmerie. "
        "Material-damage-only crashes are absent, and minor injuries (especially single-bike falls) are "
        "known to be under-reported.\n"
        "- **'Killed'** = died within 30 days. **'Hospitalised'** = more than 24 h in hospital; ONISR notes "
        "this indicator is no longer certified by the official-statistics authority, so the main story uses deaths.\n"
        "- **No exposure data:** we do not know how many km each group travels, so over-representation "
        "among victims is *not* a measure of individual risk per km.\n"
        "- **Small numbers:** rates for small departments or rare situations are noisy — the ranking shows "
        "95% Wilson confidence intervals and a minimum-accident threshold.\n"
        "- **Correlation ≠ causation:** night, rural roads and speed limits are entangled; the app "
        "describes patterns, it does not isolate causes.\n"
        "- **Geography:** department positions on the map are the median GPS point of their accidents "
        "(no external boundary file needed). Overseas territories are excluded by default.\n"
        "- **Privacy:** the published files are already anonymised by ONISR; the app only shows aggregates."
    )
    st.markdown("##### Source & license")
    st.markdown(
        f"{DATASET_TITLE}. [Dataset page]({DATASET_PAGE}) · [Data dictionary (PDF)]({DATA_DICTIONARY}). "
        f"Data license: **{LICENSE}** — reuse allowed with attribution. Code: MIT."
    )
