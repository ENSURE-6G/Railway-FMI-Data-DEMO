# pages/2_🚆_Train_Viewer.py
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_train_data, load_train_stations
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, DEFAULT_YEAR, DEFAULT_MONTH, DEFAULT_ORIGIN, DEFAULT_DESTINATION

st.set_page_config(page_title="Train Viewer", page_icon="🚆", layout="wide")
st.title("🚆 Train Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=AVAILABLE_YEARS.index(DEFAULT_YEAR))
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=AVAILABLE_MONTHS.index(DEFAULT_MONTH), format_func=lambda m: f"{m:02d}")

with st.spinner("Loading train data..."):
    stops_df = load_train_data(year, month)

if stops_df.empty:
    st.error(f"No train data available for {year}-{month:02d}.")
    st.stop()

# Clear stale search results when the data period changes
data_key = f"{year}-{month}"
if st.session_state.get("data_key") != data_key:
    st.session_state["data_key"] = data_key
    st.session_state.pop("search_done", None)

stations = get_unique_stations(stops_df)

st.divider()

# --- Route selection ---
st.subheader("🔍 Select Route")
col_o, col_d = st.columns(2)
default_origin_idx = stations.index(DEFAULT_ORIGIN) if DEFAULT_ORIGIN in stations else 0
default_dest_idx = stations.index(DEFAULT_DESTINATION) if DEFAULT_DESTINATION in stations else 0
origin = col_o.selectbox("Origin station", stations, index=default_origin_idx, key="widget_origin")
destination = col_d.selectbox("Destination station", stations, index=default_dest_idx, key="widget_destination")

if st.button("🔍 Find Trains", type="primary"):
    st.session_state["search_done"] = True
    st.session_state["saved_origin"] = origin
    st.session_state["saved_destination"] = destination

if st.session_state.get("search_done"):
    origin = st.session_state["saved_origin"]
    destination = st.session_state["saved_destination"]

    if origin == destination:
        st.warning("Origin and destination must be different.")
        st.stop()

    route_df = get_trains_for_route(stops_df, origin, destination)

    if route_df.empty:
        st.info(f"No trains found from **{origin}** to **{destination}** in {year}-{month:02d}.")
        st.stop()

    st.success(f"Found **{len(route_df)}** train(s) from **{origin}** to **{destination}**")

    train_options = [
        f"{row['trainNumber']} — {str(row['departureDate'])[:10]}"
        for _, row in route_df.iterrows()
    ]
    selected_train_str = st.selectbox("Select a train to inspect", train_options)
    selected_train = int(selected_train_str.split(" — ")[0])
    departure_date = route_df.iloc[train_options.index(selected_train_str)]["departureDate"]

    # --- Train detail ---
    route_stops = get_train_route(stops_df, selected_train, departure_date)

    # Trim to stops between origin and destination (inclusive)
    origin_mask = route_stops["stationName"] == origin
    dest_mask = route_stops["stationName"] == destination
    if origin_mask.any() and dest_mask.any():
        origin_idx = route_stops[origin_mask].index[0]
        dest_idx = route_stops[dest_mask].index[0]
        if origin_idx <= dest_idx:
            route_stops = route_stops.loc[origin_idx:dest_idx].reset_index(drop=True)

    st.divider()
    st.subheader(f"Train {selected_train} — {str(departure_date)[:10]}")

    # --- Plotly timeline chart ---
    st.markdown("**Schedule vs Actual Timeline**")
    delay_colors = []
    for d in route_stops["differenceInMinutes"]:
        if pd.isna(d) or d <= 5:
            delay_colors.append("#2ca02c")
        elif d <= 10:
            delay_colors.append("#ff7f0e")
        else:
            delay_colors.append("#d62728")

    sched_labels = pd.to_datetime(route_stops["scheduledTime"]).dt.strftime("%H:%M")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sched_labels,
        y=route_stops["differenceInMinutes"],
        mode="markers+lines",
        name="Delay",
        line=dict(color="#aec7e8"),
        marker=dict(color=delay_colors, size=10),
        text=[
            f"{row['stationName']}<br>Scheduled: {str(row['scheduledTime'])[:16]}<br>Actual: {str(row['actualTime'])[:16]}"
            for _, row in route_stops.iterrows()
        ],
        hovertemplate="%{text}<br>Delay: %{y} min<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.update_layout(
        xaxis_title="Scheduled Time",
        yaxis_title="Delay (minutes)",
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h"),
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Join with station metadata for lat/lon
    train_stations = load_train_stations()
    route_with_coords = route_stops.merge(
        train_stations[["stationShortCode", "latitude", "longitude"]],
        on="stationShortCode",
        how="left",
    )
    coords = route_with_coords.dropna(subset=["latitude", "longitude"])

    # --- Folium route map ---
    st.markdown("**Route Map**")
    if not coords.empty:
        center = [coords["latitude"].mean(), coords["longitude"].mean()]
        m = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")

        polyline_coords = list(zip(coords["latitude"], coords["longitude"]))
        folium.PolyLine(polyline_coords, color="#1f77b4", weight=3, opacity=0.8).add_to(m)

        for _, row in coords.iterrows():
            delay = row["differenceInMinutes"]
            color = "#2ca02c" if pd.isna(delay) or delay <= 5 else "#ff7f0e" if delay <= 10 else "#d62728"
            sched = str(row["scheduledTime"])[:16] if pd.notna(row["scheduledTime"]) else "N/A"
            actual = str(row["actualTime"])[:16] if pd.notna(row["actualTime"]) else "N/A"
            delay_str = f"{int(delay)} min" if pd.notna(delay) else "N/A"
            station_name = row["stationName"]
            popup_html = (
                f"<b>{station_name}</b><br>"
                f"Scheduled: {sched}<br>"
                f"Actual: {actual}<br>"
                f"Delay: {delay_str}"
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=row["stationName"],
            ).add_to(m)

        st_folium(m, use_container_width=True, height=650, returned_objects=[])
    else:
        st.warning("No coordinate data available for this train's stops.")

    # --- Raw data table ---
    st.markdown("**Raw Stop Data**")
    st.dataframe(route_stops, use_container_width=True, hide_index=True)
