"""Chapter 2 — The big picture: trend and seasonality."""

import streamlit as st

from utils import viz

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def render(acc, users, ctx):
    col, label = ctx["metric_col"], ctx["metric_label"]
    yearly = users.groupby("year", as_index=False)[col].sum().astype({col: int})
    monthly = users.groupby(["year", "month"], as_index=False)[col].sum()
    monthly = monthly.dropna(subset=["month"]).astype({"month": int})

    first, last = yearly.iloc[0], yearly.iloc[-1]
    change = (last[col] - first[col]) / first[col] if first[col] else 0
    by_month = monthly.groupby("month")[col].mean()
    peak, low = int(by_month.idxmax()), int(by_month.idxmin())
    summer = monthly[monthly["month"].between(6, 9)][col].sum() / max(monthly[col].sum(), 1)

    trend_word = "barely moved" if abs(change) < 0.03 else ("fell" if change < 0 else "rose")
    st.subheader(f"The toll has {trend_word} ({change:+.1%}) — and it peaks every summer")
    st.markdown(
        f"{label} went from **{int(first[col]):,}** in {int(first['year'])} to **{int(last[col]):,}** "
        f"in {int(last['year'])}. Year after year the same seasonal shape repeats: "
        f"**{MONTH_NAMES[peak - 1]}** is on average the worst month and **{MONTH_NAMES[low - 1]}** the "
        f"calmest; June–September alone account for **{summer:.0%}** of the total."
    )

    c1, c2 = st.columns([1, 1.6])
    with c1:
        st.markdown(f"**{label} per year**")
        viz.show(viz.yearly_bars(yearly, col, label),
                 alt=f"Bar chart of {label.lower()} per year from {int(first['year'])} to "
                     f"{int(last['year'])}; overall change {change:+.1%}.", key="yearly")
    with c2:
        st.markdown(f"**{label} per month, one line per year**")
        viz.show(viz.monthly_lines(monthly, col, label),
                 alt=f"Line chart of monthly {label.lower()}, one line per year; the shaded band marks "
                     f"June to September. Peak month on average: {MONTH_NAMES[peak - 1]}.", key="monthly")

    with st.expander("Why a flat national trend is not 'good news'"):
        st.markdown(
            "The EU Road Safety Policy Framework 2021–2030 ('Vision Zero') aims to halve road deaths "
            "over the decade. A flat curve means the trajectory is **not** consistent with that kind of "
            "goal. The next chapter "
            "shows that the national average hides very different situations — which is exactly where "
            "targeted action can make a difference. Explore the *what-if* simulator in chapter ④ to see "
            "the annual reduction this target would require."
        )
