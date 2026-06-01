# pages/3_🌤️_Weather_Viewer.py
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_weather_data, load_ems_stations
from utils.weather_utils import get_station_timeseries
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, DEFAULT_YEAR, DEFAULT_MONTH, MAP_CENTER, MAP_ZOOM

st.set_page_config(page_title="Weather Viewer", page_icon="🌤️", layout="wide")
st.title("🌤️ Weather Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=AVAILABLE_YEARS.index(DEFAULT_YEAR))
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=AVAILABLE_MONTHS.index(DEFAULT_MONTH), format_func=lambda m: f"{m:02d}")

with st.spinner("Loading weather data..."):
    weather_df = load_weather_data(year, month)

if weather_df.empty:
    st.error(f"No weather data available for {year}-{month:02d}.")
    st.stop()

ems_stations = load_ems_stations()

st.divider()

# --- EMS map for station selection ---
st.subheader("📍 Select a Weather Station")
st.caption("Click a marker on the map to select a station.")

m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB positron")

for _, row in ems_stations.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5,
        color="#ff7f0e",
        fill=True,
        fill_opacity=0.8,
        popup=folium.Popup(str(row["station_name"]), max_width=200),
        tooltip=str(row["station_name"]),
    ).add_to(m)

map_result = st_folium(m, width='stretch', height=450, returned_objects=["last_object_clicked_popup"])

# Extract selected station name from map click
selected_station = None
if map_result and map_result.get("last_object_clicked_popup"):
    selected_station = map_result["last_object_clicked_popup"]

# Also offer a selectbox fallback
station_names = sorted(ems_stations["station_name"].tolist())
fallback = st.selectbox(
    "Or select a station from the list",
    ["— select —"] + station_names,
    index=0,
)
if fallback != "— select —":
    selected_station = fallback

# --- Station detail ---
if selected_station:
    ts_df = get_station_timeseries(weather_df, selected_station)

    if ts_df.empty:
        st.info(f"No data available for **{selected_station}** in {year}-{month:02d}.")
        st.stop()

    st.divider()
    st.subheader(f"📊 {selected_station}")
    st.caption(f"Showing data for {year}-{month:02d}")

    def make_line_chart(df, col, title, unit):
        fig = go.Figure()
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df[col],
                mode="lines",
                line=dict(width=2),
                hovertemplate=f"%{{x}}<br>{title}: %{{y}} {unit}<extra></extra>",
            ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title=unit,
            height=280,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        st.plotly_chart(
            make_line_chart(ts_df, "Air temperature", "Air Temperature", "°C"),
            width='stretch',
        )
    with row1_col2:
        st.plotly_chart(
            make_line_chart(ts_df, "Wind speed", "Wind Speed", "m/s"),
            width='stretch',
        )
    with row2_col1:
        st.plotly_chart(
            make_line_chart(ts_df, "Precipitation amount", "Precipitation Amount", "mm"),
            width='stretch',
        )
    with row2_col2:
        st.plotly_chart(
            make_line_chart(ts_df, "Snow depth", "Snow Depth", "cm"),
            width='stretch',
        )

    # --- Raw data table ---
    st.markdown("**Raw Station Data**")
    st.dataframe(ts_df, width='stretch', hide_index=True)
else:
    st.info("Click a station on the map or select one from the dropdown to see its data.")
