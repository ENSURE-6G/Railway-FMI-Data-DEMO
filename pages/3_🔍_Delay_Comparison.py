# pages/6_🔍_Delay_Comparison.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_delay_stats, load_delay_offset

st.set_page_config(page_title="Delay Comparison", page_icon="🔍", layout="wide")
st.title("🔍 Delay Origin vs. Propagation")
st.caption("Comparing total delay (raw) with station-originated delay (offset-corrected) · 2018–2025")

with st.expander("ℹ️ What do Raw and Origin delay mean?"):
    st.markdown("""
**Raw delay** measures the total delay at every station stop — this includes delay that the train
was already carrying from previous stops (inherited/propagated delay).

**Origin delay** (offset-corrected) measures only the *new* delay introduced at each station,
after subtracting any delay the train was already carrying when it arrived.

The difference between the two reveals how much delay is **propagated** along the route vs.
**created fresh** at each station. Across 2018–2025, approximately **95.9%** of delayed stops
are carrying inherited delay — not creating new ones.
""")

# ── DATA LOAD & MERGE ──────────────────────────────────────────────────────────
raw = load_delay_stats()
off = load_delay_offset()

merged = raw.merge(
    off,
    on=["year", "month", "day_of_month"],
    suffixes=("_raw", "_off"),
)
merged["date"] = merged["date_raw"]

RAW_COLOR = "#E74C3C"
OFF_COLOR = "#1ABC9C"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ── KPI CARDS ──────────────────────────────────────────────────────────────────
raw_rate = raw["delay_rate"].mean()
off_rate = off["delay_rate"].mean()
prop_rate = raw_rate - off_rate
prop_pct = prop_rate / raw_rate

c1, c2, c3, c4 = st.columns(4)
c1.metric("📊 Raw Delay Rate", f"{raw_rate:.1%}",
          help="Total delayed stops including propagated delay")
c2.metric("🎯 Origin Delay Rate", f"{off_rate:.2%}",
          help="Stops where NEW delay was introduced (offset-corrected)")
c3.metric("🔗 Propagated Rate", f"{prop_rate:.1%}",
          help="Raw minus origin: delay carried over from earlier stops")
c4.metric("% Propagated", f"{prop_pct:.1%}",
          help="Fraction of all delays that are inherited, not newly created")

st.divider()

# ── SECTION 1: HERO DUAL TIME SERIES ──────────────────────────────────────────
st.subheader("Raw vs. Origin Delay Rate Over Time")
st.caption("7-day rolling averages. The shaded gap between the lines represents propagated (inherited) delay.")

fig_ts = go.Figure()

fig_ts.add_trace(go.Scatter(
    x=merged["date"],
    y=merged["rolling_delay_rate_7d_raw"],
    mode="lines",
    line=dict(color=RAW_COLOR, width=2.5),
    name="Raw (total delay)",
    hovertemplate="%{x|%Y-%m-%d}<br>Raw 7d avg: %{y:.1%}<extra></extra>",
))
fig_ts.add_trace(go.Scatter(
    x=merged["date"],
    y=merged["rolling_delay_rate_7d_off"],
    mode="lines",
    line=dict(color=OFF_COLOR, width=2.5),
    fill="tonexty",
    fillcolor="rgba(231,76,60,0.12)",
    name="Origin (new delay only)",
    hovertemplate="%{x|%Y-%m-%d}<br>Origin 7d avg: %{y:.1%}<extra></extra>",
))

for year in range(2019, 2026):
    jan1 = pd.Timestamp(f"{year}-01-01")
    fig_ts.add_vline(x=jan1, line_dash="dot", line_color="rgba(0,0,0,0.2)", line_width=1)
    fig_ts.add_annotation(
        x=jan1, y=0.78, text=str(year), showarrow=False,
        font=dict(size=10, color="rgba(0,0,0,0.4)"), xanchor="left",
    )

fig_ts.add_vrect(
    x0="2020-03-15", x1="2021-06-01",
    fillcolor="rgba(100,149,237,0.10)", line_width=0,
    annotation_text="COVID-19",
    annotation_position="top left",
    annotation_font_size=10,
    annotation_font_color="#3a5fa0",
)

fig_ts.add_annotation(
    x=pd.Timestamp("2022-06-01"), y=0.12,
    text="~95.9% propagated",
    showarrow=False,
    font=dict(size=11, color=RAW_COLOR),
    bgcolor="rgba(255,255,255,0.7)",
)

fig_ts.update_layout(
    height=420,
    yaxis=dict(tickformat=".0%", title="Delay Rate"),
    xaxis=dict(title=""),
    legend=dict(orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=20, b=10),
    hovermode="x unified",
)
st.plotly_chart(fig_ts, width="stretch")

st.divider()

# ── SECTION 2: STACKED AREA COMPOSITION ───────────────────────────────────────
st.subheader("Delay Composition Over Time — Propagated vs. New")
st.caption("Monthly averages. Teal = newly introduced at each station. Red = inherited from earlier stops.")

monthly = merged.groupby(["year", "month"]).agg(
    raw_rate=("delay_rate_raw", "mean"),
    off_rate=("delay_rate_off", "mean"),
).reset_index()
monthly["date"] = pd.to_datetime({"year": monthly["year"], "month": monthly["month"], "day": 1})
monthly = monthly.sort_values("date")
monthly["prop_rate"] = monthly["raw_rate"] - monthly["off_rate"]

fig_stack = go.Figure()
fig_stack.add_trace(go.Scatter(
    x=monthly["date"], y=monthly["off_rate"],
    mode="lines",
    name="Origin (new delay)",
    stackgroup="one",
    line=dict(width=0.5, color=OFF_COLOR),
    fillcolor=OFF_COLOR,
    hovertemplate="New delay: %{y:.2%}<extra></extra>",
))
fig_stack.add_trace(go.Scatter(
    x=monthly["date"], y=monthly["prop_rate"],
    mode="lines",
    name="Propagated (inherited)",
    stackgroup="one",
    line=dict(width=0.5, color=RAW_COLOR),
    fillcolor=RAW_COLOR,
    hovertemplate="Propagated: %{y:.1%}<extra></extra>",
))
for year in range(2019, 2026):
    fig_stack.add_vline(
        x=pd.Timestamp(f"{year}-01-01"),
        line_dash="dot", line_color="rgba(0,0,0,0.2)", line_width=1,
    )
fig_stack.update_layout(
    height=360,
    yaxis=dict(tickformat=".0%", title="Delay Rate"),
    xaxis=dict(title=""),
    legend=dict(orientation="h", y=-0.2, traceorder="reversed"),
    margin=dict(l=10, r=10, t=10, b=10),
    hovermode="x unified",
)
st.plotly_chart(fig_stack, width="stretch")

st.divider()

# ── SECTION 3: ANNUAL GROUPED BARS ────────────────────────────────────────────
st.subheader("Raw vs. Origin Delay Rate by Year")
st.caption("Annotations show the propagation percentage for each year.")

annual = merged.groupby("year").agg(
    raw_rate=("delay_rate_raw", "mean"),
    off_rate=("delay_rate_off", "mean"),
).reset_index()
annual["prop_pct"] = (annual["raw_rate"] - annual["off_rate"]) / annual["raw_rate"]

fig_ann = go.Figure()
fig_ann.add_trace(go.Bar(
    x=annual["year"].astype(str),
    y=annual["raw_rate"],
    name="Raw (total delay)",
    marker_color=RAW_COLOR,
    hovertemplate="Year: %{x}<br>Raw rate: %{y:.1%}<extra></extra>",
))
fig_ann.add_trace(go.Bar(
    x=annual["year"].astype(str),
    y=annual["off_rate"],
    name="Origin (new delay only)",
    marker_color=OFF_COLOR,
    hovertemplate="Year: %{x}<br>Origin rate: %{y:.2%}<extra></extra>",
))
for _, row in annual.iterrows():
    fig_ann.add_annotation(
        x=str(int(row["year"])),
        y=row["raw_rate"] + 0.008,
        text=f"{row['prop_pct']:.1%}<br>prop.",
        showarrow=False,
        font=dict(size=9, color="gray"),
        align="center",
    )
fig_ann.update_layout(
    barmode="group",
    height=380,
    yaxis=dict(tickformat=".0%", title="Delay Rate"),
    xaxis=dict(title=""),
    legend=dict(orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_ann, width="stretch")

st.divider()

# ── SECTION 4: MONTHLY GROUPED BARS ───────────────────────────────────────────
st.subheader("Monthly Pattern — Raw vs. Origin")
st.caption("Averaged across all years 2018–2025.")

mon_avg = merged.groupby("month").agg(
    raw_rate=("delay_rate_raw", "mean"),
    off_rate=("delay_rate_off", "mean"),
).reset_index()

fig_mon = go.Figure()
fig_mon.add_trace(go.Bar(
    x=[MONTH_NAMES[m - 1] for m in mon_avg["month"]],
    y=mon_avg["raw_rate"],
    name="Raw (total delay)",
    marker_color=RAW_COLOR,
    hovertemplate="Month: %{x}<br>Raw rate: %{y:.1%}<extra></extra>",
))
fig_mon.add_trace(go.Bar(
    x=[MONTH_NAMES[m - 1] for m in mon_avg["month"]],
    y=mon_avg["off_rate"],
    name="Origin (new delay only)",
    marker_color=OFF_COLOR,
    hovertemplate="Month: %{x}<br>Origin rate: %{y:.2%}<extra></extra>",
))
fig_mon.update_layout(
    barmode="group",
    height=360,
    yaxis=dict(tickformat=".0%", title="Delay Rate"),
    xaxis=dict(title=""),
    legend=dict(orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_mon, width="stretch")

st.divider()

# ── SECTION 5: AVG + MEDIAN DELAY DURATION ────────────────────────────────────
st.subheader("Delay Duration Comparison by Year")
st.caption("Average and median delay in minutes — raw vs. origin.")

dur = merged.groupby("year").agg(
    avg_raw=("avg_delay_minutes_raw", "mean"),
    avg_off=("avg_delay_minutes_off", "mean"),
    med_raw=("median_delay_minutes_raw", "mean"),
    med_off=("median_delay_minutes_off", "mean"),
).reset_index()

col_avg, col_med = st.columns(2)

fig_avg = go.Figure()
fig_avg.add_trace(go.Bar(
    x=dur["year"].astype(str), y=dur["avg_raw"],
    name="Raw", marker_color=RAW_COLOR,
    hovertemplate="Year: %{x}<br>Avg raw: %{y:.1f} min<extra></extra>",
))
fig_avg.add_trace(go.Bar(
    x=dur["year"].astype(str), y=dur["avg_off"],
    name="Origin", marker_color=OFF_COLOR,
    hovertemplate="Year: %{x}<br>Avg origin: %{y:.1f} min<extra></extra>",
))
fig_avg.update_layout(
    barmode="group",
    title="Avg Delay Duration (minutes) by Year",
    height=340,
    yaxis=dict(title="Minutes"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", y=-0.2),
)
with col_avg:
    st.plotly_chart(fig_avg, width="stretch")

fig_med = go.Figure()
fig_med.add_trace(go.Bar(
    x=dur["year"].astype(str), y=dur["med_raw"],
    name="Raw", marker_color=RAW_COLOR,
    hovertemplate="Year: %{x}<br>Median raw: %{y:.1f} min<extra></extra>",
))
fig_med.add_trace(go.Bar(
    x=dur["year"].astype(str), y=dur["med_off"],
    name="Origin", marker_color=OFF_COLOR,
    hovertemplate="Year: %{x}<br>Median origin: %{y:.1f} min<extra></extra>",
))
fig_med.update_layout(
    barmode="group",
    title="Median Delay Duration (minutes) by Year",
    height=340,
    yaxis=dict(title="Minutes"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", y=-0.2),
)
with col_med:
    st.plotly_chart(fig_med, width="stretch")
