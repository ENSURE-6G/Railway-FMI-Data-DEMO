# pages/2_🚆_Train_Viewer.py
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_train_data, load_train_stations
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS

st.set_page_config(page_title="Train Viewer", page_icon="🚆", layout="wide")
st.title("🚆 Train Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=0)
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=0, format_func=lambda m: f"{m:02d}")

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
origin = col_o.selectbox("Origin station", stations, key="widget_origin")
destination = col_d.selectbox("Destination station", stations, key="widget_destination")

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

    # Display train list
    display_df = route_df.copy()
    display_df["origin_time"] = display_df["origin_time"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(
        display_df.rename(columns={
            "trainNumber": "Train #", "trainType": "Type",
            "trainCategory": "Category", "origin_time": "Departure",
            "cancelled": "Cancelled", "departureDate": "Date",
        }),
        use_container_width=True,
        hide_index=True,
    )

    train_options = route_df["trainNumber"].astype(str).tolist()
    selected_train_str = st.selectbox("Select a train to inspect", train_options)
    selected_train = int(selected_train_str)
    departure_date = route_df[route_df["trainNumber"] == selected_train]["departureDate"].iloc[0]

    # --- Train detail ---
    route_stops = get_train_route(stops_df, selected_train, departure_date)

    st.divider()
    st.subheader(f"Train {selected_train} — {departure_date}")

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
            color = "#2ca02c" if pd.isna(delay) or delay < 2 else "#ff7f0e" if delay <= 10 else "#d62728"
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

        st_folium(m, use_container_width=True, height=450, returned_objects=[])
    else:
        st.warning("No coordinate data available for this train's stops.")

    # --- Plotly timeline chart ---
    st.markdown("**Schedule vs Actual Timeline**")
    delay_colors = []
    for d in route_stops["differenceInMinutes"]:
        if pd.isna(d) or d < 2:
            delay_colors.append("#2ca02c")
        elif d <= 10:
            delay_colors.append("#ff7f0e")
        else:
            delay_colors.append("#d62728")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=route_stops["scheduledTime"],
        y=route_stops["stationName"],
        mode="markers+lines",
        name="Scheduled",
        line=dict(color="#aec7e8", dash="dot"),
        marker=dict(color=delay_colors, size=10),
        text=[
            f"Delay: {int(d)} min" if pd.notna(d) else "No data"
            for d in route_stops["differenceInMinutes"]
        ],
        hovertemplate="%{y}<br>%{x}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Scheduled Time",
        yaxis_title="Station",
        height=max(300, len(route_stops) * 28),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Raw data table ---
    st.markdown("**Raw Stop Data**")
    st.dataframe(route_stops, use_container_width=True, hide_index=True)
