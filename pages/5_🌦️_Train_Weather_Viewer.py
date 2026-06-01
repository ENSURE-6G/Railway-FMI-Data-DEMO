# pages/4_🌦️_Train_Weather_Viewer.py
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_matched_data, load_train_stations, load_ems_stations
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, DEFAULT_YEAR, DEFAULT_MONTH, DEFAULT_ORIGIN, DEFAULT_DESTINATION

st.set_page_config(page_title="Train & Weather Viewer", page_icon="🌦️", layout="wide")
st.title("🌦️ Train & Weather Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=AVAILABLE_YEARS.index(DEFAULT_YEAR))
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=AVAILABLE_MONTHS.index(DEFAULT_MONTH), format_func=lambda m: f"{m:02d}")

with st.spinner("Loading matched train & weather data..."):
    stops_df = load_matched_data(year, month)

if stops_df.empty:
    st.error(f"No matched data available for {year}-{month:02d}.")
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

    offset_colors = [
        "#d62728" if pd.notna(d) and d > 5 else "#f4a261"
        for d in route_stops["differenceInMinutes_eachStation_offset"]
    ]

    sched_labels = pd.to_datetime(route_stops["scheduledTime"]).dt.strftime("%H:%M")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sched_labels,
        y=route_stops["differenceInMinutes"],
        mode="markers+lines",
        name="Delay (cumulative)",
        line=dict(color="#aec7e8"),
        marker=dict(color=delay_colors, size=10),
        text=[
            f"{row['stationName']}<br>Scheduled: {str(row['scheduledTime'])[:16]}<br>Actual: {str(row['actualTime'])[:16]}"
            for _, row in route_stops.iterrows()
        ],
        hovertemplate="%{text}<br>Delay: %{y} min<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=sched_labels,
        y=route_stops["differenceInMinutes_eachStation_offset"],
        mode="markers+lines",
        name="Delay change per station",
        line=dict(color="#f4a261", dash="dash"),
        marker=dict(symbol="diamond", color=offset_colors, size=8),
        text=[row["stationName"] for _, row in route_stops.iterrows()],
        hovertemplate="%{text}<br>Change: %{y} min<extra></extra>",
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
    st.plotly_chart(fig, width="stretch")

    # Join with station metadata for lat/lon
    train_stations = load_train_stations()
    route_with_coords = route_stops.merge(
        train_stations[["stationShortCode", "latitude", "longitude"]],
        on="stationShortCode",
        how="left",
    )
    coords = route_with_coords.dropna(subset=["latitude", "longitude"])

    # Build closest-EMS lookup from EMS metadata
    ems_stations = load_ems_stations()
    ems_lookup = ems_stations.set_index("station_name")[["latitude", "longitude"]].to_dict("index")

    # --- Folium route map ---
    st.markdown("**Route Map**")
    if not coords.empty:
        center = [coords["latitude"].mean(), coords["longitude"].mean()]
        m = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")

        polyline_coords = list(zip(coords["latitude"], coords["longitude"]))
        folium.PolyLine(polyline_coords, color="#1f77b4", weight=3, opacity=0.8).add_to(m)

        # Draw closest EMS per train station (deduplicated)
        seen_ems = set()
        for _, row in coords.drop_duplicates(subset="stationShortCode").iterrows():
            ems_name = row.get("closest_ems")
            if pd.isna(ems_name) or ems_name not in ems_lookup:
                continue
            ems_coords = ems_lookup[ems_name]
            ems_lat, ems_lng = ems_coords["latitude"], ems_coords["longitude"]
            folium.PolyLine(
                [[row["latitude"], row["longitude"]], [ems_lat, ems_lng]],
                color="#888888",
                weight=1.5,
                opacity=0.7,
                dash_array="6 4",
                tooltip=ems_name,
            ).add_to(m)
            if ems_name not in seen_ems:
                folium.CircleMarker(
                    location=[ems_lat, ems_lng],
                    radius=5,
                    color="#888888",
                    fill=True,
                    fill_color="#bbbbbb",
                    fill_opacity=0.8,
                    tooltip=ems_name,
                    popup=folium.Popup(f"<b>{ems_name}</b>", max_width=200),
                ).add_to(m)
                seen_ems.add(ems_name)

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

        st_folium(m, width='stretch', height=850, returned_objects=[])
    else:
        st.warning("No coordinate data available for this train's stops.")

    # --- Weather grid ---
    st.divider()
    st.markdown("**Weather along the route**")

    # One weather observation per station (ARRIVAL and DEPARTURE share the same matched weather)
    weather_stops = route_stops.drop_duplicates(subset="stationShortCode", keep="first").reset_index(drop=True)
    weather_x = pd.to_datetime(weather_stops["scheduledTime"]).dt.strftime("%H:%M")
    weather_station_names = weather_stops["stationName"].tolist()

    _H = 260
    _M = dict(l=10, r=10, t=35, b=70)
    _LEGEND = dict(orientation="h", y=-0.38, font=dict(size=10))
    _XTICK = dict(tickangle=-45, tickfont=dict(size=9))

    def _weather_fig(title, traces, y_label):
        f = go.Figure()
        for name, col, color in traces:
            if col in weather_stops.columns:
                f.add_trace(go.Scatter(
                    x=weather_x,
                    y=weather_stops[col],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=color),
                    marker=dict(size=5),
                    text=weather_station_names,
                    hovertemplate=f"%{{text}}<br>{name}: %{{y}}<extra></extra>",
                ))
        f.update_layout(
            title=dict(text=title, font=dict(size=13)),
            height=_H,
            margin=_M,
            yaxis_title=y_label,
            legend=_LEGEND,
            xaxis=_XTICK,
        )
        return f

    weather_groups = [
        ("Temperature (°C)",        [("Air temp",   "Air temperature",       "#e76f51"),
                                      ("Dew point",  "Dew-point temperature", "#457b9d")], "°C"),
        ("Wind (m/s)",              [("Speed",       "Wind speed",            "#2a9d8f"),
                                      ("Gust",        "Gust speed",            "#e9c46a")], "m/s"),
        ("Wind direction (°)",      [("Direction",   "Wind direction",        "#8ecae6")], "°"),
        ("Relative humidity (%)",   [("Humidity",    "Relative humidity",     "#4cc9f0")], "%"),
        ("Precipitation",           [("Amount (mm)", "Precipitation amount",  "#0077b6"),
                                      ("Intensity (mm/h)", "Precipitation intensity", "#90e0ef")], "mm / mm·h⁻¹"),
        ("Snow depth (cm)",         [("Snow depth",  "Snow depth",            "#adb5bd")], "cm"),
        ("Pressure (hPa)",          [("Pressure",    "Pressure (msl)",        "#6a4c93")], "hPa"),
        ("Horizontal visibility (m)",[("Visibility", "Horizontal visibility", "#52b788")], "m"),
        ("Cloud amount (okta)",     [("Cloud",       "Cloud amount",          "#778da9")], "okta"),
    ]

    cols = st.columns(3)
    for i, (title, traces, y_label) in enumerate(weather_groups):
        if i > 0 and i % 3 == 0:
            cols = st.columns(3)
        with cols[i % 3]:
            st.plotly_chart(_weather_fig(title, traces, y_label), width="stretch")

    # --- Rolling weather grid ---
    st.divider()
    st.markdown("**Weather rolling windows along the route**")

    _WINDOW_DASH = {"12h": "dash", "24h": "dot", "72h": "dashdot"}
    _STAT_COLOR  = {"max": "#d62728", "min": "#1f77b4", "mean": "#ff7f0e"}

    rolling_features = [
        ("Air temperature",        "°C",    "#e76f51", ["12h","24h","72h"], ["max","min","mean"]),
        ("Wind speed",             "m/s",   "#2a9d8f", ["12h","24h","72h"], ["max","min","mean"]),
        ("Relative humidity",      "%",     "#4cc9f0", ["12h","24h","72h"], ["max","min","mean"]),
        ("Precipitation amount",   "mm",    "#0077b6", ["12h","24h","72h"], ["mean"]),
        ("Precipitation intensity","mm/h",  "#90e0ef", ["12h","24h","72h"], ["max","min","mean"]),
        ("Snow depth",             "cm",    "#adb5bd", ["12h","24h","72h"], ["max","min","mean"]),
        ("Pressure (msl)",         "hPa",   "#6a4c93", ["12h","24h","72h"], ["max","min","mean"]),
        ("Horizontal visibility",  "m",     "#52b788", ["12h","24h","72h"], ["max","min","mean"]),
        ("Cloud amount",           "okta",  "#778da9", ["12h","24h","72h"], ["max","min","mean"]),
    ]

    def _rolling_fig(feature, unit, inst_color, windows, stats):
        f = go.Figure()
        if feature in weather_stops.columns:
            f.add_trace(go.Scatter(
                x=weather_x,
                y=weather_stops[feature],
                mode="lines+markers",
                name="Instant",
                line=dict(color=inst_color, width=2),
                marker=dict(size=5),
                text=weather_station_names,
                hovertemplate="%{text}<br>Instant: %{y}<extra></extra>",
            ))
        for window in windows:
            for stat in stats:
                col = f"{feature} ({window} {stat})"
                if col in weather_stops.columns:
                    f.add_trace(go.Scatter(
                        x=weather_x,
                        y=weather_stops[col],
                        mode="lines",
                        name=f"{window} {stat}",
                        line=dict(color=_STAT_COLOR[stat], dash=_WINDOW_DASH[window], width=1),
                        text=weather_station_names,
                        hovertemplate=f"%{{text}}<br>{window} {stat}: %{{y}}<extra></extra>",
                    ))
        f.update_layout(
            title=dict(text=f"{feature} ({unit})", font=dict(size=13)),
            height=300,
            margin=dict(l=10, r=10, t=35, b=80),
            yaxis_title=unit,
            legend=dict(orientation="h", y=-0.55, font=dict(size=9)),
            xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        )
        return f

    cols = st.columns(3)
    for i, (feature, unit, inst_color, windows, stats) in enumerate(rolling_features):
        if i > 0 and i % 3 == 0:
            cols = st.columns(3)
        with cols[i % 3]:
            st.plotly_chart(_rolling_fig(feature, unit, inst_color, windows, stats), width="stretch")

    # --- Raw data table ---
    st.divider()
    st.markdown("**Raw Stop Data**")
    st.dataframe(route_stops, width="stretch", hide_index=True)
