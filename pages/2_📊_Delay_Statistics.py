# pages/5_📊_Delay_Statistics.py
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_delay_stats

st.set_page_config(page_title="Delay Statistics", page_icon="📊", layout="wide")
st.title("📊 Delay Statistics Dashboard")

df = load_delay_stats()
st.caption(f"Finnish Railway Network · 2018–2025 · {len(df):,} days analysed")

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ── KPI CARDS ──────────────────────────────────────────────────────────────────
overall_rate = df["delay_rate"].mean()
overall_avg_min = df["avg_delay_minutes"].mean()
yearly_avg = df.groupby("year")["delay_rate"].mean()
best_year = int(yearly_avg.idxmin())
worst_year = int(yearly_avg.idxmax())

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "⚠️ Avg Delay Rate", f"{overall_rate:.1%}",
    help="Fraction of all scheduled stops delayed, averaged across 2,922 days",
)
c2.metric(
    "⏱ Avg Delay Duration", f"{overall_avg_min:.1f} min",
    help="Mean delay in minutes across delayed stops only",
)
c3.metric(
    "🏆 Best Year",
    f"{best_year}  —  {yearly_avg[best_year]:.1%}",
    delta=f"{yearly_avg[best_year] - overall_rate:+.1%} vs average",
    delta_color="inverse",
)
c4.metric(
    "⚠️ Worst Year",
    f"{worst_year}  —  {yearly_avg[worst_year]:.1%}",
    delta=f"{yearly_avg[worst_year] - overall_rate:+.1%} vs average",
    delta_color="inverse",
)

st.divider()

# ── SECTION 2: YEAR × MONTH HEATMAP + ANNUAL BAR ──────────────────────────────
st.subheader("Year-over-Year Comparison")

col_hm, col_bar = st.columns([3, 2])

ym = df.groupby(["year", "month"])["delay_rate"].mean().reset_index()
pivot = ym.pivot(index="year", columns="month", values="delay_rate")

fig_hm = go.Figure(go.Heatmap(
    z=pivot.values,
    x=MONTH_NAMES,
    y=pivot.index.tolist(),
    colorscale=[
        [0.0, "#f7fbff"], [0.3, "#6baed6"],
        [0.6, "#fd8d3c"], [1.0, "#8B0000"],
    ],
    zmin=0, zmax=0.5,
    text=[[f"{v:.1%}" for v in row] for row in pivot.values],
    texttemplate="%{text}",
    textfont=dict(size=9),
    colorbar=dict(title="Delay Rate", tickformat=".0%"),
    hovertemplate="Year: %{y}<br>Month: %{x}<br>Avg delay rate: %{z:.1%}<extra></extra>",
))
fig_hm.update_layout(
    height=320,
    title="Avg Delay Rate by Year and Month",
    margin=dict(l=10, r=10, t=40, b=10),
    yaxis=dict(dtick=1),
)
with col_hm:
    st.plotly_chart(fig_hm, width="stretch")

annual = df.groupby("year")["delay_rate"].mean().reset_index()
bar_colors = ["#2ecc71" if r < overall_rate else "#e74c3c" for r in annual["delay_rate"]]
fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=annual["year"].astype(str),
    y=annual["delay_rate"],
    marker_color=bar_colors,
    text=[f"{r:.1%}" for r in annual["delay_rate"]],
    textposition="outside",
    hovertemplate="Year: %{x}<br>Avg delay rate: %{y:.1%}<extra></extra>",
))
fig_bar.add_hline(
    y=overall_rate, line_dash="dash", line_color="gray",
    annotation_text=f"Dataset avg {overall_rate:.1%}",
    annotation_position="top right",
)
fig_bar.add_annotation(
    x="2020", y=float(yearly_avg[2020]) + 0.018,
    text="COVID", showarrow=False,
    font=dict(size=10, color="#3a5fa0"),
)
fig_bar.update_layout(
    title="Average Annual Delay Rate",
    height=320,
    yaxis=dict(tickformat=".0%", range=[0, annual["delay_rate"].max() * 1.2]),
    xaxis=dict(title=""),
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False,
)
with col_bar:
    st.plotly_chart(fig_bar, width="stretch")

st.divider()

# ── SECTION 3: MONTHLY + DAY-OF-WEEK ──────────────────────────────────────────
st.subheader("Temporal Patterns")

col_mon, col_dow = st.columns(2)

monthly_avg = df.groupby("month")["delay_rate"].mean().reset_index()
max_m = monthly_avg["delay_rate"].max()
_m75 = monthly_avg["delay_rate"].quantile(0.75)
_m50 = monthly_avg["delay_rate"].quantile(0.50)
month_colors = [
    "#E74C3C" if v >= _m75 else "#F39C12" if v >= _m50 else "#5B9BD5"
    for v in monthly_avg["delay_rate"]
]
fig_mon = go.Figure(go.Bar(
    x=[MONTH_NAMES[m - 1] for m in monthly_avg["month"]],
    y=monthly_avg["delay_rate"],
    marker_color=month_colors,
    text=[f"{r:.1%}" for r in monthly_avg["delay_rate"]],
    textposition="outside",
    hovertemplate="Month: %{x}<br>Avg delay rate: %{y:.1%}<extra></extra>",
))
fig_mon.update_layout(
    title="Delay Rate by Month (2018–2025 avg)",
    height=340,
    yaxis=dict(tickformat=".0%", range=[0, max_m * 1.18]),
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False,
)
with col_mon:
    st.plotly_chart(fig_mon, width="stretch")

dow_avg = df.groupby("day_of_week")["delay_rate"].mean().reset_index().sort_values("day_of_week")
max_d = dow_avg["delay_rate"].max()
_d75 = dow_avg["delay_rate"].quantile(0.75)
_d50 = dow_avg["delay_rate"].quantile(0.50)
dow_colors = [
    "#E74C3C" if v >= _d75 else "#F39C12" if v >= _d50 else "#5B9BD5"
    for v in dow_avg["delay_rate"]
]
fig_dow = go.Figure(go.Bar(
    x=[DOW_NAMES[d - 1] for d in dow_avg["day_of_week"]],
    y=dow_avg["delay_rate"],
    marker_color=dow_colors,
    text=[f"{r:.1%}" for r in dow_avg["delay_rate"]],
    textposition="outside",
    hovertemplate="Day: %{x}<br>Avg delay rate: %{y:.1%}<extra></extra>",
))
fig_dow.update_layout(
    title="Delay Rate by Day of Week (2018–2025 avg)",
    height=340,
    yaxis=dict(tickformat=".0%", range=[0, max_d * 1.18]),
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False,
)
with col_dow:
    st.plotly_chart(fig_dow, width="stretch")

st.divider()

# ── SECTION 4: SEVERITY STACKED AREA ──────────────────────────────────────────
st.subheader("Delay Severity Breakdown Over Time")
st.caption("Monthly proportions of delayed stops by severity band (stacked to 100% of delayed stops).")

sev = df.groupby(["year", "month"]).agg(
    d5_15=("delays_5_15min", "sum"),
    d15_30=("delays_15_30min", "sum"),
    d30_60=("delays_30_60min", "sum"),
    d60p=("delays_over_60min", "sum"),
    total=("delay_count_by_day", "sum"),
).reset_index()
sev["date"] = pd.to_datetime({"year": sev["year"], "month": sev["month"], "day": 1})
sev = sev.sort_values("date")
for col in ["d5_15", "d15_30", "d30_60", "d60p"]:
    sev[f"p_{col}"] = sev[col] / sev["total"].replace(0, float("nan"))

fig_sev = go.Figure()
SEVERITY_BANDS = [
    ("p_d60p",  ">60 min",   "#8B0000"),
    ("p_d30_60","30–60 min", "#E84040"),
    ("p_d15_30","15–30 min", "#FF8C00"),
    ("p_d5_15", "5–15 min",  "#FFDD57"),
]
for col, name, color in SEVERITY_BANDS:
    fig_sev.add_trace(go.Scatter(
        x=sev["date"], y=sev[col],
        mode="lines",
        name=name,
        stackgroup="one",
        line=dict(width=0.5, color=color),
        fillcolor=color,
        hovertemplate=f"{name}: %{{y:.1%}}<extra></extra>",
    ))
for year in range(2019, 2026):
    fig_sev.add_vline(
        x=pd.Timestamp(f"{year}-01-01"),
        line_dash="dot", line_color="rgba(0,0,0,0.2)", line_width=1,
    )
fig_sev.update_layout(
    height=380,
    yaxis=dict(tickformat=".0%", title="Proportion of delayed stops"),
    xaxis=dict(title=""),
    legend=dict(orientation="h", y=-0.2, traceorder="reversed"),
    margin=dict(l=10, r=10, t=10, b=10),
    hovermode="x unified",
)
st.plotly_chart(fig_sev, width="stretch")

st.divider()

# ── SECTION 7: DELAY BY TRAIN TYPE ────────────────────────────────────────────
st.subheader("Delayed Stops by Train Type per Year")
st.caption("Top 6 train types by total delayed stops across 2018–2025.")

rows = []
for _, row in df.iterrows():
    try:
        types = json.loads(row["delay_count_by_train_type"])
        for train_type, count in types.items():
            rows.append({"year": row["year"], "train_type": train_type, "count": int(count)})
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

type_df = pd.DataFrame(rows)
type_agg = type_df.groupby(["year", "train_type"])["count"].sum().reset_index()
top_types = type_agg.groupby("train_type")["count"].sum().nlargest(6).index.tolist()
type_agg = type_agg[type_agg["train_type"].isin(top_types)]

TYPE_COLORS = {
    "IC": "#636EFA", "S": "#EF553B", "PVV": "#00CC96",
    "PYO": "#AB63FA", "HDM": "#FFA15A", "AE": "#19D3F3",
    "MV": "#FF6692", "HSM": "#B6E880",
}
fig_type = go.Figure()
for tt in top_types:
    sub = type_agg[type_agg["train_type"] == tt].sort_values("year")
    fig_type.add_trace(go.Bar(
        x=sub["year"].astype(str),
        y=sub["count"],
        name=tt,
        marker_color=TYPE_COLORS.get(tt, "#888"),
        hovertemplate=f"{tt}<br>Year: %{{x}}<br>Delayed stops: %{{y:,}}<extra></extra>",
    ))
fig_type.update_layout(
    barmode="group",
    height=380,
    yaxis=dict(title="Delayed stops"),
    xaxis=dict(title=""),
    legend=dict(orientation="h", y=-0.2),
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_type, width="stretch")
