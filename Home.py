# Home.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.data_loader import load_train_stations, load_ems_stations
from const import MAP_CENTER, MAP_ZOOM, AVAILABLE_YEARS

st.set_page_config(
    page_title="Railway & Weather Demo",
    page_icon="🚆",
    layout="wide",
)

st.title("🚆 Railway & Weather Data Explorer")
st.caption("Finnish railway timetable and FMI meteorological observations — 2024–2025")

# --- Metrics ---
train_stations = load_train_stations()
ems_stations = load_ems_stations()

col1, col2, col3 = st.columns(3)
col1.metric("🚉 Train Stations", len(train_stations))
col2.metric("🌡️ EMS Stations", len(ems_stations))
col3.metric(
    "📅 Data Coverage",
    f"Jan {min(AVAILABLE_YEARS)} – Dec {max(AVAILABLE_YEARS)}",
)

st.divider()

# --- Map ---
st.subheader("Station Overview Map")

m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB positron")

for _, row in train_stations.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=4,
        color="#1f77b4",
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(str(row["stationName"]), max_width=200),
        tooltip=str(row["stationName"]),
    ).add_to(m)

for _, row in ems_stations.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=4,
        color="#ff7f0e",
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(str(row["station_name"]), max_width=200),
        tooltip=str(row["station_name"]),
    ).add_to(m)

# Legend (HTML overlay)
legend_html = """
<div style="position:fixed; bottom:30px; left:30px; z-index:1000; background:white;
     padding:10px 14px; border-radius:8px; box-shadow:2px 2px 6px rgba(0,0,0,0.3); font-size:13px;">
  <b>Legend</b><br>
  <span style="color:#1f77b4;">●</span> Train stations<br>
  <span style="color:#ff7f0e;">●</span> EMS stations
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, use_container_width=True, height=520, returned_objects=[])

st.divider()

# --- About ---
with st.expander("ℹ️ About this dataset"):
    st.markdown(f"""
**Train data** is sourced from the [Finnish Transport Infrastructure Agency (Väylävirasto)](https://www.digitraffic.fi/)
via the Digitraffic open data API. It covers all Finnish passenger, commuter, and freight trains
with scheduled and actual timetable rows including delay information, for the years 2024–2025.

**Weather data** is sourced from the [Finnish Meteorological Institute (FMI)](https://www.ilmatieteenlaitos.fi/)
open data service. It contains hourly observations from **{len(ems_stations)} automatic weather stations**
across Finland, including temperature, wind speed, precipitation, snow depth, pressure, and visibility.
    """)
