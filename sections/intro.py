"""Chapter 1 — Hook, audience, questions, how to read the app."""

import streamlit as st

from utils.constants import DATA_DICTIONARY, DATASET_PAGE, VULNERABLE


def render(acc, users, ctx):
    n_killed = int(users["killed"].sum())
    n_days = (ctx["years"][1] - ctx["years"][0] + 1) * 365
    per_day = n_killed / n_days
    n_ksi = int(users["ksi"].sum())
    vuln = users.loc[users["killed"], "mode"].isin(VULNERABLE).mean() if n_killed else 0

    st.subheader("Why this matters")
    st.markdown(
        f"#### Every day, about **{per_day:.0f} people** die on the roads in the current selection — "
        f"and **{vuln:.0%}** of them were not protected by a car body."
    )
    st.markdown(
        f"Between {ctx['years'][0]} and {ctx['years'][1]}, the police and gendarmerie recorded "
        f"**{len(acc):,} injury accidents** in this selection, leaving **{n_killed:,} people dead** "
        f"and **{n_ksi:,} killed or hospitalised**. Behind the national total, risk is very unequally "
        "shared: by *where* you drive, *when* you drive, and *how* you travel."
    )

    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown("##### Who is this for?")
        st.markdown(
            "- **Departmental road-safety officers** (préfectures, DDT/DDTM) choosing where to "
            "focus enforcement and road works.\n"
            "- **Local elected officials** arbitrating between urban (cycle lanes, 30 km/h zones) "
            "and rural (departmental roads) investments.\n"
            "- **Curious citizens** who want to understand their own risk."
        )
        st.markdown("##### The questions this app answers")
        st.markdown(
            "1. **Is it getting better?** How has the toll evolved since 2021, and when in the year does it peak?\n"
            "2. **Where?** Which territories — and which type of road — are the deadliest *per accident*?\n"
            "3. **When?** At what hours and days does an accident turn fatal most often?\n"
            "4. **Who?** Which road users and age groups pay the highest price?\n"
            "5. **So what?** Which levers would save the most lives (what-if scenarios)?"
        )
    with c2:
        st.markdown("##### How to read this app")
        st.info(
            "Use the **sidebar** to filter years, territory, regions, urban/rural area, road-user "
            "mode and the outcome analysed. The KPI row and every chart update together. "
            "Hover any chart for exact values. Each tab is a chapter of the story — read them in order."
        )
        st.markdown("##### Two numbers to keep in mind")
        st.markdown(
            "- **Volume** (how many accidents) tells you where the *work* is.\n"
            "- **Lethality** (killed per 100 accidents, or share of fatal accidents) tells you where "
            "an accident is most likely to *kill*. The two maps are not the same — that gap is the story."
        )
        st.caption(
            f"Data: national injury-accident files (BAAC) published by ONISR on "
            f"[data.gouv.fr]({DATASET_PAGE}); field definitions in the "
            f"[official data dictionary]({DATA_DICTIONARY}). Only accidents with at least one injured "
            "person and recorded by the police are included — see the Data quality tab."
        )
