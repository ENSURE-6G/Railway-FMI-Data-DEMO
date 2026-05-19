# Railway-FMI Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 3-page Streamlit demo app visualising Finnish railway timetable/delay data and FMI meteorological observations for a project meeting.

**Architecture:** Modular Approach B — one Python file per page under `pages/`, shared logic in `utils/` (data_loader, train_utils, weather_utils), all paths and constants in `const.py`. Data files live outside the project folder and are referenced via relative sibling path. Each monthly CSV is loaded on demand and cached with `@st.cache_data`.

**Tech Stack:** Python 3.11, Streamlit, Pandas, Folium, streamlit-folium, Plotly, ast (stdlib), pytest

---

## File Map

| File | Responsibility |
|---|---|
| `environment.yml` | Conda env `venv_rail_fmi_demo` with all deps |
| `const.py` | All paths, patterns, and UI constants |
| `utils/__init__.py` | Empty package marker |
| `utils/data_loader.py` | All CSV I/O, `@st.cache_data`, stop explosion |
| `utils/train_utils.py` | Route filtering, stop sorting |
| `utils/weather_utils.py` | Station timeseries extraction |
| `tests/__init__.py` | Empty package marker |
| `tests/test_train_utils.py` | Unit tests for train_utils |
| `tests/test_weather_utils.py` | Unit tests for weather_utils |
| `Home.py` | Streamlit entry point (redirect to Home page) |
| `pages/1_🏠_Home.py` | Home page: metrics + combined map |
| `pages/2_🚆_Train_Viewer.py` | Route selection, map, timeline chart, raw table |
| `pages/3_🌤️_Weather_Viewer.py` | EMS map selection, 4 charts, raw table |

---

## Task 1: Project Scaffolding + Conda Environment

**Files:**
- Create: `environment.yml`
- Create: `utils/__init__.py`
- Create: `tests/__init__.py`
- Create: `pages/` folder (empty, Streamlit detects it automatically)

- [ ] **Step 1: Create `environment.yml`**

```yaml
name: venv_rail_fmi_demo
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pandas
  - plotly
  - pip
  - pip:
    - streamlit>=1.32
    - folium
    - streamlit-folium
    - pytest
```

- [ ] **Step 2: Create the conda environment**

Run:
```bash
conda env create -f environment.yml
conda activate venv_rail_fmi_demo
```
Expected: environment created with no errors, `streamlit --version` prints a version.

- [ ] **Step 3: Create package markers and folders**

```bash
mkdir pages utils tests
type nul > utils\__init__.py
type nul > tests\__init__.py
```

- [ ] **Step 4: Commit**

```bash
git init
git add environment.yml utils/__init__.py tests/__init__.py
git commit -m "chore: scaffold project structure and conda environment"
```

---

## Task 2: const.py

**Files:**
- Create: `const.py`

- [ ] **Step 1: Create `const.py`**

```python
from pathlib import Path

# Project root is the folder containing this file
_PROJECT_ROOT = Path(__file__).parent

# External data root is a sibling folder at the same level as the project
_DATA_ROOT = _PROJECT_ROOT.parent / "Railway-FMI-Data-CSV-Files-v2"

TRAIN_DATA_PATH = _DATA_ROOT / "train_data"
WEATHER_DATA_PATH = _DATA_ROOT / "weather_data"
METADATA_PATH = _PROJECT_ROOT / "metadata"

AVAILABLE_YEARS: list[int] = [2024, 2025]
AVAILABLE_MONTHS: list[int] = list(range(1, 13))

TRAIN_FILE_PATTERN = "all_trains_data_{year}_{month:02d}.csv"
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.csv"

TRAIN_CATEGORIES = ["Long-distance", "Commuter", "Cargo"]
TRAIN_TYPES = ["IC", "S", "PYO", "HDM", "HL", "T"]

MAP_CENTER = [64.5, 26.0]
MAP_ZOOM = 5
```

- [ ] **Step 2: Verify paths resolve correctly**

Run:
```bash
python -c "from const import TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH; print(TRAIN_DATA_PATH.exists(), WEATHER_DATA_PATH.exists(), METADATA_PATH.exists())"
```
Expected output: `True True True`

- [ ] **Step 3: Commit**

```bash
git add const.py
git commit -m "feat: add const.py with all paths and shared constants"
```

---

## Task 3: utils/data_loader.py

**Files:**
- Create: `utils/data_loader.py`

- [ ] **Step 1: Create `utils/data_loader.py`**

```python
import ast
import pandas as pd
import streamlit as st
from const import (
    TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH,
    TRAIN_FILE_PATTERN, WEATHER_FILE_PATTERN, AVAILABLE_YEARS, AVAILABLE_MONTHS,
)

_TRAIN_COLS = ["trainNumber", "departureDate", "trainType", "trainCategory", "cancelled"]


@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    path = TRAIN_DATA_PATH / TRAIN_FILE_PATTERN.format(year=year, month=month)
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        try:
            stops = ast.literal_eval(row["timeTableRows"])
        except (ValueError, SyntaxError):
            continue
        for stop in stops:
            records.append({
                "trainNumber": row["trainNumber"],
                "departureDate": row["departureDate"],
                "trainType": row["trainType"],
                "trainCategory": row["trainCategory"],
                "cancelled": row["cancelled"],
                "stationName": stop.get("stationName"),
                "stationShortCode": stop.get("stationShortCode"),
                "type": stop.get("type"),
                "scheduledTime": stop.get("scheduledTime"),
                "actualTime": stop.get("actualTime"),
                "differenceInMinutes": stop.get("differenceInMinutes"),
                "stop_cancelled": stop.get("cancelled", False),
            })
    return pd.DataFrame(records)


@st.cache_data
def load_weather_data(year: int, month: int) -> pd.DataFrame:
    path = WEATHER_DATA_PATH / WEATHER_FILE_PATTERN.format(year=year, month=month)
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data
def load_train_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_train_stations.csv")


@st.cache_data
def load_ems_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_fmi_ems_stations.csv")


@st.cache_data
def get_total_train_count() -> int:
    """Count unique train numbers across all available monthly files."""
    all_numbers: set = set()
    for year in AVAILABLE_YEARS:
        for month in AVAILABLE_MONTHS:
            path = TRAIN_DATA_PATH / TRAIN_FILE_PATTERN.format(year=year, month=month)
            if path.exists():
                df = pd.read_csv(path, usecols=["trainNumber"])
                all_numbers.update(df["trainNumber"].unique())
    return len(all_numbers)
```

- [ ] **Step 2: Smoke-test the loaders**

Run:
```bash
python -c "
from utils.data_loader import load_train_stations, load_ems_stations
ts = load_train_stations()
ems = load_ems_stations()
print('Train stations:', len(ts), ts.columns.tolist())
print('EMS stations:', len(ems), ems.columns.tolist())
"
```
Expected: prints row counts (563 train stations, ~209 EMS stations) and column lists including `latitude`, `longitude`.

- [ ] **Step 3: Commit**

```bash
git add utils/data_loader.py
git commit -m "feat: add data_loader with cached CSV loading and stop explosion"
```

---

## Task 4: utils/train_utils.py (TDD)

**Files:**
- Create: `utils/train_utils.py`
- Create: `tests/test_train_utils.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_train_utils.py
import pytest
import pandas as pd
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route


@pytest.fixture
def sample_stops():
    return pd.DataFrame([
        # Train 1: HKI -> TPE
        {"trainNumber": 1, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Helsinki asema", "stationShortCode": "HKI", "type": "DEPARTURE",
         "scheduledTime": "2024-01-01T05:00:00.000Z", "actualTime": "2024-01-01T05:02:00.000Z",
         "differenceInMinutes": 2, "stop_cancelled": False},
        {"trainNumber": 1, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Tampere asema", "stationShortCode": "TPE", "type": "ARRIVAL",
         "scheduledTime": "2024-01-01T07:00:00.000Z", "actualTime": "2024-01-01T07:05:00.000Z",
         "differenceInMinutes": 5, "stop_cancelled": False},
        # Train 2: TPE -> HKI (reverse — should NOT match HKI->TPE route)
        {"trainNumber": 2, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Tampere asema", "stationShortCode": "TPE", "type": "DEPARTURE",
         "scheduledTime": "2024-01-01T08:00:00.000Z", "actualTime": None,
         "differenceInMinutes": 0, "stop_cancelled": False},
        {"trainNumber": 2, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Helsinki asema", "stationShortCode": "HKI", "type": "ARRIVAL",
         "scheduledTime": "2024-01-01T10:00:00.000Z", "actualTime": None,
         "differenceInMinutes": 0, "stop_cancelled": False},
    ])


def test_get_unique_stations_returns_sorted_list(sample_stops):
    result = get_unique_stations(sample_stops)
    assert result == ["Helsinki asema", "Tampere asema"]


def test_get_trains_for_route_finds_correct_train(sample_stops):
    result = get_trains_for_route(sample_stops, "Helsinki asema", "Tampere asema")
    assert len(result) == 1
    assert result.iloc[0]["trainNumber"] == 1


def test_get_trains_for_route_excludes_reverse_direction(sample_stops):
    result = get_trains_for_route(sample_stops, "Helsinki asema", "Tampere asema")
    assert 2 not in result["trainNumber"].values


def test_get_train_route_returns_all_stops_sorted(sample_stops):
    result = get_train_route(sample_stops, 1, "2024-01-01")
    assert len(result) == 2
    assert result.iloc[0]["stationName"] == "Helsinki asema"
    assert result.iloc[1]["stationName"] == "Tampere asema"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_train_utils.py -v
```
Expected: `ModuleNotFoundError: No module named 'utils.train_utils'`

- [ ] **Step 3: Implement `utils/train_utils.py`**

```python
# utils/train_utils.py
import pandas as pd


def get_unique_stations(stops_df: pd.DataFrame) -> list[str]:
    return sorted(stops_df["stationName"].dropna().unique().tolist())


def get_trains_for_route(
    stops_df: pd.DataFrame, origin: str, destination: str
) -> pd.DataFrame:
    origin_stops = (
        stops_df[stops_df["stationName"] == origin][["trainNumber", "departureDate", "scheduledTime"]]
        .rename(columns={"scheduledTime": "origin_time"})
    )
    dest_stops = (
        stops_df[stops_df["stationName"] == destination][["trainNumber", "departureDate", "scheduledTime"]]
        .rename(columns={"scheduledTime": "dest_time"})
    )
    merged = origin_stops.merge(dest_stops, on=["trainNumber", "departureDate"])
    merged["origin_time"] = pd.to_datetime(merged["origin_time"])
    merged["dest_time"] = pd.to_datetime(merged["dest_time"])
    valid = merged[merged["origin_time"] < merged["dest_time"]].copy()

    train_meta = (
        stops_df[["trainNumber", "departureDate", "trainType", "trainCategory", "cancelled"]]
        .drop_duplicates()
    )
    result = valid.merge(train_meta, on=["trainNumber", "departureDate"])
    return (
        result[["trainNumber", "departureDate", "trainType", "trainCategory", "origin_time", "cancelled"]]
        .sort_values("origin_time")
        .reset_index(drop=True)
    )


def get_train_route(
    stops_df: pd.DataFrame, train_number: int, departure_date: str
) -> pd.DataFrame:
    mask = (stops_df["trainNumber"] == train_number) & (stops_df["departureDate"] == departure_date)
    route = stops_df[mask].copy()
    route["scheduledTime"] = pd.to_datetime(route["scheduledTime"])
    return route.sort_values("scheduledTime").reset_index(drop=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_train_utils.py -v
```
Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add utils/train_utils.py tests/test_train_utils.py
git commit -m "feat: add train_utils with route filtering and stop sorting"
```

---

## Task 5: utils/weather_utils.py (TDD)

**Files:**
- Create: `utils/weather_utils.py`
- Create: `tests/test_weather_utils.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_weather_utils.py
import pytest
import pandas as pd
from utils.weather_utils import get_station_timeseries


@pytest.fixture
def sample_weather():
    return pd.DataFrame([
        {"timestamp": pd.Timestamp("2024-01-01 00:00:00"), "station_name": "Oulu lentoasema",
         "Air temperature": -10.0, "Wind speed": 5.0, "Precipitation amount": 0.0, "Snow depth": 20.0,
         "Wind direction": 270.0, "Gust speed": 8.0},
        {"timestamp": pd.Timestamp("2024-01-01 01:00:00"), "station_name": "Oulu lentoasema",
         "Air temperature": -11.0, "Wind speed": 6.0, "Precipitation amount": 0.1, "Snow depth": 21.0,
         "Wind direction": 280.0, "Gust speed": 9.0},
        {"timestamp": pd.Timestamp("2024-01-01 00:00:00"), "station_name": "Helsinki Kaisaniemi",
         "Air temperature": -3.0, "Wind speed": 3.0, "Precipitation amount": 0.0, "Snow depth": 5.0,
         "Wind direction": 180.0, "Gust speed": 4.0},
    ])


def test_get_station_timeseries_filters_correct_station(sample_weather):
    result = get_station_timeseries(sample_weather, "Oulu lentoasema")
    assert len(result) == 2
    assert all(result["station_name"] == "Oulu lentoasema")


def test_get_station_timeseries_returns_all_columns(sample_weather):
    result = get_station_timeseries(sample_weather, "Oulu lentoasema")
    assert "timestamp" in result.columns
    assert "Air temperature" in result.columns
    assert "Wind speed" in result.columns
    assert "Precipitation amount" in result.columns
    assert "Snow depth" in result.columns


def test_get_station_timeseries_empty_for_unknown_station(sample_weather):
    result = get_station_timeseries(sample_weather, "Unknown Station")
    assert len(result) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_weather_utils.py -v
```
Expected: `ModuleNotFoundError: No module named 'utils.weather_utils'`

- [ ] **Step 3: Implement `utils/weather_utils.py`**

```python
# utils/weather_utils.py
import pandas as pd


def get_station_timeseries(weather_df: pd.DataFrame, station_name: str) -> pd.DataFrame:
    return weather_df[weather_df["station_name"] == station_name].reset_index(drop=True)
```

- [ ] **Step 4: Run all tests to verify they pass**

Run:
```bash
pytest tests/ -v
```
Expected: all tests PASSED (4 train_utils + 3 weather_utils = 7 total).

- [ ] **Step 5: Commit**

```bash
git add utils/weather_utils.py tests/test_weather_utils.py
git commit -m "feat: add weather_utils with station timeseries extraction"
```

---

## Task 6: Home.py + pages/1_🏠_Home.py

**Files:**
- Create: `Home.py`
- Create: `pages/1_🏠_Home.py`

- [ ] **Step 1: Create `Home.py` (Streamlit entry point)**

```python
# Home.py
import streamlit as st

st.set_page_config(
    page_title="Railway & Weather Demo",
    page_icon="🚆",
    layout="wide",
)

st.switch_page("pages/1_🏠_Home.py")
```

- [ ] **Step 2: Create `pages/1_🏠_Home.py`**

```python
# pages/1_🏠_Home.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.data_loader import load_train_stations, load_ems_stations, get_total_train_count
from const import MAP_CENTER, MAP_ZOOM, AVAILABLE_YEARS

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

st.title("🚆 Railway & Weather Data Explorer")
st.caption("Finnish railway timetable and FMI meteorological observations — 2024–2025")

# --- Metrics ---
train_stations = load_train_stations()
ems_stations = load_ems_stations()
total_trains = get_total_train_count()

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
    st.markdown("""
**Train data** is sourced from the [Finnish Transport Infrastructure Agency (Väylävirasto)](https://www.digitraffic.fi/)
via the Digitraffic open data API. It covers all Finnish passenger, commuter, and freight trains
with scheduled and actual timetable rows including delay information, for the years 2024–2025.

**Weather data** is sourced from the [Finnish Meteorological Institute (FMI)](https://www.ilmatieteenlaitos.fi/)
open data service. It contains hourly observations from **""" + str(len(ems_stations)) + """ automatic weather stations**
across Finland, including temperature, wind speed, precipitation, snow depth, pressure, and visibility.
    """)
```

- [ ] **Step 3: Run the app and verify the Home page**

Run:
```bash
streamlit run Home.py
```
Expected: browser opens, Home page shows 3 metric cards and a map of Finland with blue (train) and orange (EMS) markers. Clicking a marker shows its name in a popup.

- [ ] **Step 4: Commit**

```bash
git add Home.py "pages/1_🏠_Home.py"
git commit -m "feat: add Home page with metrics, combined station map, and dataset info"
```

---

## Task 7: pages/2_🚆_Train_Viewer.py

**Files:**
- Create: `pages/2_🚆_Train_Viewer.py`

- [ ] **Step 1: Create `pages/2_🚆_Train_Viewer.py`**

```python
# pages/2_🚆_Train_Viewer.py
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_train_data, load_train_stations
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, MAP_CENTER, MAP_ZOOM

st.set_page_config(page_title="Train Viewer", page_icon="🚆", layout="wide")
st.title("🚆 Train Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=0)
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=0, format_func=lambda m: f"{m:02d}")

with st.spinner("Loading train data..."):
    stops_df = load_train_data(year, month)

stations = get_unique_stations(stops_df)

st.divider()

# --- Route selection ---
st.subheader("🔍 Select Route")
col_o, col_d = st.columns(2)
origin = col_o.selectbox("Origin station", stations, key="origin")
destination = col_d.selectbox("Destination station", stations, key="destination")

if st.button("🔍 Find Trains", type="primary"):
    st.session_state["search_done"] = True
    st.session_state["origin"] = origin
    st.session_state["destination"] = destination

if st.session_state.get("search_done"):
    origin = st.session_state["origin"]
    destination = st.session_state["destination"]

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
            popup_html = (
                f"<b>{row['stationName']}</b><br>"
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
```

Note: Add `import pandas as pd` at the top of the file — it's needed for `pd.isna()`.

- [ ] **Step 2: Fix the missing import (add `import pandas as pd` at top)**

The full file header should be:
```python
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_train_data, load_train_stations
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, MAP_CENTER, MAP_ZOOM
```

- [ ] **Step 3: Run the app and test the Train Viewer**

Run:
```bash
streamlit run Home.py
```
Navigate to "Train Viewer". Select a year/month, pick an origin and destination, click "Find Trains". Select a train from the results. Verify: route map appears with coloured markers, timeline chart shows stops in order, raw table shows all stop columns.

- [ ] **Step 4: Commit**

```bash
git add "pages/2_🚆_Train_Viewer.py"
git commit -m "feat: add Train Viewer with route search, map, delay timeline, and raw table"
```

---

## Task 8: pages/3_🌤️_Weather_Viewer.py

**Files:**
- Create: `pages/3_🌤️_Weather_Viewer.py`

- [ ] **Step 1: Create `pages/3_🌤️_Weather_Viewer.py`**

```python
# pages/3_🌤️_Weather_Viewer.py
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_weather_data, load_ems_stations
from utils.weather_utils import get_station_timeseries
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, MAP_CENTER, MAP_ZOOM

st.set_page_config(page_title="Weather Viewer", page_icon="🌤️", layout="wide")
st.title("🌤️ Weather Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=0)
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=0, format_func=lambda m: f"{m:02d}")

with st.spinner("Loading weather data..."):
    weather_df = load_weather_data(year, month)

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

map_result = st_folium(m, use_container_width=True, height=450, returned_objects=["last_object_clicked_popup"])

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
            use_container_width=True,
        )
    with row1_col2:
        st.plotly_chart(
            make_line_chart(ts_df, "Wind speed", "Wind Speed", "m/s"),
            use_container_width=True,
        )
    with row2_col1:
        st.plotly_chart(
            make_line_chart(ts_df, "Precipitation amount", "Precipitation Amount", "mm"),
            use_container_width=True,
        )
    with row2_col2:
        st.plotly_chart(
            make_line_chart(ts_df, "Snow depth", "Snow Depth", "cm"),
            use_container_width=True,
        )

    # --- Raw data table ---
    st.markdown("**Raw Station Data**")
    st.dataframe(ts_df, use_container_width=True, hide_index=True)
else:
    st.info("Click a station on the map or select one from the dropdown to see its data.")
```

- [ ] **Step 2: Run the app and test the Weather Viewer**

Run:
```bash
streamlit run Home.py
```
Navigate to "Weather Viewer". Select a year/month. Click an orange marker on the map — the station name should appear as a header and 4 charts should render below. Verify the raw data table appears with all weather columns.

- [ ] **Step 3: Run all tests one final time**

Run:
```bash
pytest tests/ -v
```
Expected: 7 tests PASSED, 0 failures.

- [ ] **Step 4: Final commit**

```bash
git add "pages/3_🌤️_Weather_Viewer.py"
git commit -m "feat: add Weather Viewer with EMS map selection, 4 charts, and raw table"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|---|---|
| `const.py` with all paths and constants | Task 2 |
| `environment.yml`, conda env `venv_rail_fmi_demo` | Task 1 |
| `data_loader.py` with `@st.cache_data` | Task 3 |
| Stop explosion from `timeTableRows` | Task 3 |
| `train_utils.py` with 3 functions | Task 4 |
| `weather_utils.py` with `get_station_timeseries` | Task 5 |
| Home: 3 metric cards | Task 6 |
| Home: combined Folium map, all train + EMS stations | Task 6 |
| Home: About expander | Task 6 |
| Train Viewer: year/month selector | Task 7 |
| Train Viewer: origin/destination dropdowns + Find button | Task 7 |
| Train Viewer: train list table + selectbox | Task 7 |
| Train Viewer: Folium route map with delay-coloured markers | Task 7 |
| Train Viewer: Plotly delay timeline chart | Task 7 |
| Train Viewer: raw stop data table (all columns) | Task 7 |
| Weather Viewer: year/month selector | Task 8 |
| Weather Viewer: EMS map click for station selection | Task 8 |
| Weather Viewer: 2×2 Plotly chart grid | Task 8 |
| Weather Viewer: raw station data table (all columns) | Task 8 |
| Adding new year = update `AVAILABLE_YEARS` only | Task 2 |

**No placeholders, no TODOs, no missing code blocks.**  
**Type/name consistency:** `get_train_route` called consistently across tasks 4 and 7. `get_station_timeseries` consistent across tasks 5 and 8. `load_train_stations` consistent across tasks 3 and 7.
