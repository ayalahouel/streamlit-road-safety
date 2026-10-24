# Storyboard — Who pays the price on French roads?

**Audience:** departmental road-safety officers & local officials (secondary: citizens).
**One-sentence story:** *Accidents happen mostly in towns, at rush hour, to car occupants — but deaths
concentrate on rural roads, at night, among unprotected road users; that is where effort saves the most lives.*

| # | Chapter (tab) | User question | Visual | Headline (computed live) | Interaction |
|---|---|---|---|---|---|
| 0 | KPI row | How big is it? | 5 metrics | accidents, killed (Δ last vs first year), hospitalised, killed/100 accidents, % vulnerable | all sidebar filters |
| 1 | ① Why it matters (Hook) | Why should I care? | text | "Every day about N people die… X% were not protected by a car body" | filters |
| 2 | ② Big picture (Context) | Is it getting better? When in the year? | yearly bars + monthly lines per year (summer band) | "The toll has barely moved (+x%) — and it peaks every summer" | outcome selector |
| 3a | ③ Where | Where are accidents deadliest? | urban/rural share bars, bubble map, ranking dot-plot with 95% CI, road-type bars | "Rural roads: x% of accidents, y% of deaths" | top/bottom, N, min-accident threshold |
| 3b | ③ When | When does an accident turn fatal? | hour × weekday heatmap (volume ↔ lethality), lighting bars | "Rush hour brings the most accidents — the night the most deaths" | heatmap toggle |
| 3c | ③ Who | Who pays the price? | share involved vs killed by mode, small multiples by mode, age × mode heatmap | "<mode>: n× over-represented among the dead" | mode filter |
| 4 | ④ Takeaways & what-if (Insight + Implications) | What should we do? | insights list, 2 scenario simulators, 2030 target path | data-driven insights | sliders, mode picker |
| 5 | ⑤ Data quality | Can I trust it? | checks table, files table, missingness bars, limitations | — | — |
