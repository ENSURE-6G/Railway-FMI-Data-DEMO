from pathlib import Path

import streamlit as st

st.set_page_config(page_title="AI Results", page_icon="🤖", layout="wide")
st.title("🤖 AI Results — XGBoost Delay Prediction")
st.caption("Oulu central station · 101,146 observations · XGBoost · Chronological 80/20 split")

ASSETS = Path(__file__).parent.parent / "assets"

# ── EXPERIMENTAL SETUP ─────────────────────────────────────────────────────────
st.subheader("Experimental Setup")

col_setup, col_table = st.columns([1, 2])

with col_setup:
    st.markdown("""
**Station:** Oulu central station
- Delay rate: **19.0 %**
- Observations: **101,146**

**Model:** XGBoost

**Split:** Chronological 80 / 20
_(prevents future data leakage)_

**Validation:** 5-fold expanding-window
time-series cross-validation
""")

with col_table:
    st.markdown("**Feature sets by scenario**")
    st.markdown("""
| Feature group | Sc. 1 — Full | Sc. 2 — Instant only | Sc. 3 — Categories only |
|---|:---:|:---:|:---:|
| Operational | ✔ | ✔ | ✔ |
| Instant weather obs. | ✔ | ✔ | — |
| Weather categories | ✔ | — | ✔ |
| **Total features** | **28** | **18** | **19** |
""")

st.divider()

# ── WEATHER CATEGORIES ─────────────────────────────────────────────────────────
st.subheader("Hierarchical Weather Categorization")
st.caption("Severity-based priority — most disruptive conditions take precedence.")

CATEGORIES = [
    ("🌨️", "Blizzard",       "#5B8DB8"),
    ("❄️", "Heavy Snow",     "#7BB3D4"),
    ("🥶", "Extreme Cold",   "#A8C8E8"),
    ("🌧️", "Heavy Rain",     "#4A90A4"),
    ("🌨️", "Freezing Rain",  "#6BA5B8"),
    ("🧊", "Black Ice",      "#89BDD3"),
    ("🌫️", "Dense Fog",      "#9E9E9E"),
    ("💨", "High Winds",     "#78909C"),
    ("🔥", "Extreme Heat",   "#E07B54"),
    ("☀️", "Normal / Clear", "#66BB6A"),
]

cols = st.columns(5)
for i, (icon, name, color) in enumerate(CATEGORIES):
    with cols[i % 5]:
        st.markdown(
            f"""<div style="background:{color}22;border-left:4px solid {color};
                border-radius:6px;padding:0.45rem 0.7rem;margin-bottom:0.6rem;">
              <span style="font-size:1.1rem;">{icon}</span>
              <span style="font-weight:600;font-size:0.9rem;color:{color};margin-left:0.3rem;">{name}</span>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ── METRIC CHARTS ──────────────────────────────────────────────────────────────
st.subheader("Model Performance Across Iterations")
st.caption(
    "Each line is one feature scenario. "
    "Sc. 1 (Full, 28 features) consistently outperforms the partial sets on all three metrics."
)

st.markdown("""
<div style="display:flex;gap:2.5rem;align-items:center;padding:0.6rem 1rem;
            background:#f8f9fa;border-radius:8px;margin-bottom:0.8rem;width:fit-content;">
  <span style="display:flex;align-items:center;gap:0.5rem;">
    <svg width="36" height="16">
      <line x1="0" y1="8" x2="36" y2="8" stroke="#1f77b4" stroke-width="2.5"/>
      <circle cx="18" cy="8" r="5" fill="white" stroke="#1f77b4" stroke-width="2.5"/>
    </svg>
    <span style="font-size:0.95rem;color:#1f77b4;font-weight:600;">Full weather data</span>
  </span>
  <span style="display:flex;align-items:center;gap:0.5rem;">
    <svg width="36" height="16">
      <line x1="0" y1="8" x2="36" y2="8" stroke="#ff7f0e" stroke-width="2.5"/>
      <rect x="13" y="3" width="10" height="10" fill="white" stroke="#ff7f0e" stroke-width="2.5"/>
    </svg>
    <span style="font-size:0.95rem;color:#ff7f0e;font-weight:600;">Instant weather observations only</span>
  </span>
  <span style="display:flex;align-items:center;gap:0.5rem;">
    <svg width="36" height="16">
      <line x1="0" y1="8" x2="36" y2="8" stroke="#2ca02c" stroke-width="2.5"/>
      <polygon points="18,2 24,14 12,14" fill="white" stroke="#2ca02c" stroke-width="2.5"/>
    </svg>
    <span style="font-size:0.95rem;color:#2ca02c;font-weight:600;">Derived weather category only</span>
  </span>
</div>
""", unsafe_allow_html=True)

col_r2, col_rmse, col_mae = st.columns(3)

with col_r2:
    st.markdown("**R² Score** _(higher is better)_")
    st.image(str(ASSETS / "xgb_r2.png"), use_container_width=True)

with col_rmse:
    st.markdown("**RMSE — Root Mean Squared Error (min)** _(lower is better)_")
    st.image(str(ASSETS / "xgb_rmse.png"), use_container_width=True)

with col_mae:
    st.markdown("**MAE — Mean Absolute Error (min)** _(lower is better)_")
    st.image(str(ASSETS / "xgb_mae.png"), use_container_width=True)

st.divider()

# ── KEY FINDINGS ───────────────────────────────────────────────────────────────
st.subheader("Key Findings")

k1, k2, k3 = st.columns(3)

k1.metric(
    "Best R² (Sc. 1, 100 iter.)", "0.78",
    help="Full feature set with 100 boosting iterations",
)
k2.metric(
    "Best RMSE (Sc. 1, 100 iter.)", "8.5 min",
    help="Full feature set with 100 boosting iterations",
)
k3.metric(
    "Best MAE (Sc. 1, 100 iter.)", "3.7 min",
    help="Full feature set with 100 boosting iterations",
)

st.markdown("""
- **Sc. 1 (Full)** — combining operational features with both instant weather observations and
  weather categories — outperforms the partial feature sets on every metric by a clear margin.
- **Sc. 2 vs Sc. 3** perform nearly identically, suggesting instant weather observations and
  categorical weather summaries carry similar predictive signal when used alone.
- All scenarios converge around **80–100 iterations**; further boosting rounds yield
  diminishing returns.
""")
