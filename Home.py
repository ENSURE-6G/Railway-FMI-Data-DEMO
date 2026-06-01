# Home.py
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.data_loader import load_train_stations, load_ems_stations
from const import MAP_CENTER, MAP_ZOOM, AVAILABLE_YEARS, METADATA_PATH

st.set_page_config(
    page_title="Railway & Weather Demo",
    page_icon="🚆",
    layout="wide",
)

st.title("🚆 Railway & Weather Data Explorer")
st.caption(f"Finnish railway timetable and FMI meteorological observations — {min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}")

# --- Metrics ---
train_stations = load_train_stations()
ems_stations = load_ems_stations()

@st.cache_data
def load_top5_ems() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_top5_closest_ems.csv")

top5_df = load_top5_ems()

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

selected_code = st.session_state.get("selected_train_station")

if selected_code:
    sel_name = train_stations.loc[
        train_stations["stationShortCode"] == selected_code, "stationName"
    ].values
    sel_display = sel_name[0] if len(sel_name) > 0 else selected_code
    col_info, col_clear = st.columns([5, 1])
    col_info.info(f"Showing top 5 closest EMS stations for **{sel_display}** — click another station to switch, or clear.")
    if col_clear.button("✕ Clear"):
        st.session_state.pop("selected_train_station", None)
        st.rerun()

map_zoom = st.session_state.get("map_zoom", MAP_ZOOM)
map_center = st.session_state.get("map_center", MAP_CENTER)

m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="CartoDB positron")

# Train station markers
for _, row in train_stations.iterrows():
    is_selected = row["stationShortCode"] == selected_code
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=6 if is_selected else 4,
        color="#e76f51" if is_selected else "#1f77b4",
        fill=True,
        fill_opacity=1.0 if is_selected else 0.7,
        popup=folium.Popup(str(row["stationName"]), max_width=200),
        tooltip=str(row["stationName"]),
    ).add_to(m)

# EMS station markers
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

# Draw top-5 EMS lines for the selected train station
_EMS_COLORS = ["#ff69b4"] * 5

if selected_code:
    top5_row = top5_df[top5_df["train_station_short_code"] == selected_code]
    if not top5_row.empty:
        r = top5_row.iloc[0]
        for i in range(1, 6):
            ems_lat = r[f"ems_{i}_lat"]
            ems_lng = r[f"ems_{i}_long"]
            ems_name = r[f"ems_{i}_station"]
            dist = r[f"ems_{i}_distance_km"]
            color = _EMS_COLORS[i - 1]
            folium.PolyLine(
                [[r["train_lat"], r["train_long"]], [ems_lat, ems_lng]],
                color=color,
                weight=2.5,
                opacity=0.9,
                tooltip=f"#{i} {ems_name} ({dist:.1f} km)",
            ).add_to(m)
            folium.CircleMarker(
                location=[ems_lat, ems_lng],
                radius=8,
                color=color,
                fill=True,
                fill_opacity=0.95,
                popup=folium.Popup(f"<b>#{i} {ems_name}</b><br>{dist:.1f} km", max_width=220),
                tooltip=f"#{i} {ems_name} ({dist:.1f} km)",
            ).add_to(m)
            folium.Marker(
                location=[ems_lat, ems_lng],
                icon=folium.DivIcon(
                    html=(
                        f'<div style="font-size:11px; font-weight:bold; color:{color}; '
                        f'white-space:nowrap; text-shadow:1px 1px 2px white, -1px -1px 2px white, '
                        f'1px -1px 2px white, -1px 1px 2px white;">'
                        f'#{i} {ems_name}<br>{dist:.1f} km</div>'
                    ),
                    icon_size=(200, 30),
                    icon_anchor=(-10, 10),
                ),
            ).add_to(m)

# Legend (HTML overlay)
legend_html = """
<div style="position:fixed; bottom:30px; left:30px; z-index:1000; background:white;
     padding:10px 14px; border-radius:8px; box-shadow:2px 2px 6px rgba(0,0,0,0.3); font-size:13px; color:black;">
  <b>Legend</b><br>
  <span style="color:#1f77b4;">●</span> Train stations<br>
  <span style="color:#ff7f0e;">●</span> EMS stations
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

map_data = st_folium(
    m,
    use_container_width=True,
    height=750,
    returned_objects=["last_object_clicked"],
    center=tuple(map_center),
    zoom=map_zoom,
)

# Persist zoom and center so the view is restored after rerun
if map_data:
    new_zoom = map_data.get("zoom")
    if new_zoom is not None:
        st.session_state["map_zoom"] = int(new_zoom)
    new_center = map_data.get("center")
    if new_center and isinstance(new_center, dict):
        lat = new_center.get("lat")
        lng = new_center.get("lng")
        if lat is not None and lng is not None:
            st.session_state["map_center"] = [lat, lng]

# Handle train station click: match click lat/lng to nearest train station
if map_data and map_data.get("last_object_clicked"):
    click = map_data["last_object_clicked"]
    click_lat, click_lng = click["lat"], click["lng"]
    ts = train_stations.copy()
    ts["_dist"] = (
        (ts["latitude"] - click_lat) ** 2 + (ts["longitude"] - click_lng) ** 2
    ) ** 0.5
    nearest = ts.loc[ts["_dist"].idxmin()]
    if nearest["_dist"] < 0.05:  # ~5 km tolerance
        new_code = nearest["stationShortCode"]
        if st.session_state.get("selected_train_station") != new_code:
            st.session_state["selected_train_station"] = new_code
            st.rerun()

st.divider()

# --- About ---
with st.expander("ℹ️ About this dataset"):
    st.markdown(f"""
**Train data** is sourced from the [Finnish Transport Infrastructure Agency (Väylävirasto)](https://www.digitraffic.fi/)
via the Digitraffic open data API. It covers all Finnish passenger, commuter, and freight trains
with scheduled and actual timetable rows including delay information, for the years {min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}.

**Weather data** is sourced from the [Finnish Meteorological Institute (FMI)](https://www.ilmatieteenlaitos.fi/)
open data service. It contains hourly observations from **{len(ems_stations)} automatic weather stations**
across Finland, including temperature, wind speed, precipitation, snow depth, pressure, and visibility.
    """)
