# Train & Weather Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new Streamlit page that mirrors the Train Viewer but loads matched train+weather data, exposing all 146 columns in the raw stop table.

**Architecture:** Three-file change — add two constants to `const.py`, add one cached loader to `data_loader.py`, and create the new page as a near-copy of `2_🚆_Train_Viewer.py`. All existing train utilities (`get_unique_stations`, `get_trains_for_route`, `get_train_route`) are reused unchanged.

**Tech Stack:** Python, Streamlit, pandas, Plotly, Folium, streamlit-folium, pytest

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `const.py` | Modify | Add `MATCHED_DATA_PATH` and `MATCHED_FILE_PATTERN` |
| `utils/data_loader.py` | Modify | Add `load_matched_data(year, month)` cached function |
| `tests/test_data_loader.py` | Modify | Add tests for `load_matched_data` |
| `pages/4_🌦️_Train_Weather_Viewer.py` | Create | New page wired to matched data |

---

## Task 1: Add matched data constants to `const.py`

**Files:**
- Modify: `const.py`

- [ ] **Step 1: Add the two constants**

Open `const.py`. After the `WEATHER_FILE_PATTERN` line, add:

```python
MATCHED_DATA_PATH = _DATA_ROOT / "matched_flat_data"
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"
```

The full bottom of the file should now read:

```python
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.csv"
MATCHED_DATA_PATH = _DATA_ROOT / "matched_flat_data"
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"

TRAIN_CATEGORIES: list[str] = ["Long-distance", "Commuter", "Cargo"]
...
```

- [ ] **Step 2: Verify import works**

Run:
```
python -c "from const import MATCHED_DATA_PATH, MATCHED_FILE_PATTERN; print(MATCHED_DATA_PATH, MATCHED_FILE_PATTERN)"
```

Expected output (path will vary by machine):
```
..\Railway-FMI-Data-CSV-Files-v2\matched_flat_data matched_data_flat_{year}_{month:02d}.csv
```

- [ ] **Step 3: Commit**

```bash
git add const.py
git commit -m "feat: add MATCHED_DATA_PATH and MATCHED_FILE_PATTERN constants"
```

---

## Task 2: Add `load_matched_data` to `data_loader.py` (TDD)

**Files:**
- Modify: `utils/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write the failing tests**

Open `tests/test_data_loader.py`. Add these imports at the top (alongside the existing ones):

```python
from utils.data_loader import load_train_data, load_matched_data
```

Then append the following fixtures and tests at the bottom of the file:

```python
MATCHED_COLUMNS = [
    "trainNumber", "departureDate", "stationName", "stationShortCode",
    "scheduledTime", "actualTime", "differenceInMinutes",
    "timetableAcceptanceDate",
    "Air temperature", "Wind speed", "Snow depth",
]


@pytest.fixture
def matched_csv(tmp_path):
    data = {
        "trainNumber": [1, 1],
        "departureDate": ["2024-01-01", "2024-01-01"],
        "operatorUICCode": [10, 10],
        "operatorShortCode": ["vr", "vr"],
        "trainType": ["IC", "IC"],
        "trainCategory": ["Long-distance", "Long-distance"],
        "commuterLineID": ["", ""],
        "runningCurrently": [False, False],
        "cancelled": [False, False],
        "version": [287293186071, 287293186071],
        "timetableType": ["REGULAR", "REGULAR"],
        "timetableAcceptanceDate": ["2023-11-02T05:57:22.000Z", "2023-11-02T05:57:22.000Z"],
        "stationName": ["Helsinki asema", "Tampere asema"],
        "stationShortCode": ["HKI", "TPE"],
        "stationUICCode": [1, 140],
        "countryCode": ["FI", "FI"],
        "type": ["DEPARTURE", "ARRIVAL"],
        "trainStopping": [True, True],
        "commercialStop": [True, True],
        "commercialTrack": ["9", "4"],
        "stop_cancelled": [False, False],
        "scheduledTime": ["2024-01-01T04:57:00.000Z", "2024-01-01T06:57:00.000Z"],
        "actualTime": ["2024-01-01T04:57:21.000Z", "2024-01-01T06:58:00.000Z"],
        "differenceInMinutes": [0.0, 1.0],
        "causes": ["[]", "[]"],
        "trainReady": ["", ""],
        "closest_ems": ["Helsinki", "Tampere"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
    }
    df = pd.DataFrame(data)
    path = tmp_path / "matched_data_flat_2024_01.csv"
    df.to_csv(path, index=False)
    return tmp_path


@pytest.fixture
def patched_matched_loader(matched_csv, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "MATCHED_DATA_PATH", matched_csv)
    monkeypatch.setattr(loader, "MATCHED_FILE_PATTERN", "matched_data_flat_{year}_{month:02d}.csv")
    load_matched_data.clear()
    yield loader
    load_matched_data.clear()


@pytest.fixture
def patched_matched_loader_empty(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "MATCHED_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "MATCHED_FILE_PATTERN", "matched_data_flat_{year}_{month:02d}.csv")
    load_matched_data.clear()
    yield loader
    load_matched_data.clear()


def test_load_matched_data_returns_expected_columns(patched_matched_loader):
    df = load_matched_data(2024, 1)
    assert set(MATCHED_COLUMNS).issubset(df.columns)
    assert len(df) == 2


def test_load_matched_data_parses_datetime_columns(patched_matched_loader):
    df = load_matched_data(2024, 1)
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["actualTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["timetableAcceptanceDate"])
    assert pd.api.types.is_datetime64_any_dtype(df["departureDate"])


def test_load_matched_data_missing_file_returns_empty_dataframe(patched_matched_loader_empty):
    df = load_matched_data(2099, 1)
    assert df.empty
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_data_loader.py::test_load_matched_data_returns_expected_columns -v
```

Expected: `FAILED` with `ImportError: cannot import name 'load_matched_data'`

- [ ] **Step 3: Implement `load_matched_data` in `data_loader.py`**

Open `utils/data_loader.py`. Add the import for the new constants at the top (update the existing import):

```python
from const import (
    TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH,
    TRAIN_FILE_PATTERN, WEATHER_FILE_PATTERN,
    MATCHED_DATA_PATH, MATCHED_FILE_PATTERN,
)
```

Then append the new function after `load_weather_data`:

```python
@st.cache_data
def load_matched_data(year: int, month: int) -> pd.DataFrame:
    path = MATCHED_DATA_PATH / MATCHED_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(
        path,
        parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
    )
```

- [ ] **Step 4: Run all three new tests**

```
pytest tests/test_data_loader.py -k "matched" -v
```

Expected:
```
PASSED tests/test_data_loader.py::test_load_matched_data_returns_expected_columns
PASSED tests/test_data_loader.py::test_load_matched_data_parses_datetime_columns
PASSED tests/test_data_loader.py::test_load_matched_data_missing_file_returns_empty_dataframe
```

- [ ] **Step 5: Run full test suite to check no regressions**

```
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: add load_matched_data loader with tests"
```

---

## Task 3: Create the Train & Weather Viewer page

**Files:**
- Create: `pages/4_🌦️_Train_Weather_Viewer.py`

- [ ] **Step 1: Create the page file**

Create `pages/4_🌦️_Train_Weather_Viewer.py` with the following content:

```python
# pages/4_🌦️_Train_Weather_Viewer.py
import pandas as pd
import streamlit as st
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
from utils.data_loader import load_matched_data, load_train_stations
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route
from const import AVAILABLE_YEARS, AVAILABLE_MONTHS, DEFAULT_ORIGIN, DEFAULT_DESTINATION

st.set_page_config(page_title="Train & Weather Viewer", page_icon="🌦️", layout="wide")
st.title("🌦️ Train & Weather Viewer")

# --- Data selection ---
col_y, col_m = st.columns(2)
year = col_y.selectbox("Year", AVAILABLE_YEARS, index=0)
month = col_m.selectbox("Month", AVAILABLE_MONTHS, index=0, format_func=lambda m: f"{m:02d}")

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
```

- [ ] **Step 2: Verify the page is discoverable by Streamlit**

Run:
```
python -c "import importlib.util; spec = importlib.util.spec_from_file_location('page', 'pages/4_🌦️_Train_Weather_Viewer.py'); print('OK' if spec else 'FAIL')"
```

Expected: `OK`

- [ ] **Step 3: Run full test suite to confirm nothing broke**

```
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add "pages/4_🌦️_Train_Weather_Viewer.py"
git commit -m "feat: add Train & Weather Viewer page"
```

---

## Self-Review Checklist

- [x] `const.py` constants covered in Task 1
- [x] `load_matched_data` covered with TDD in Task 2 (3 tests: columns, datetime parsing, missing file)
- [x] New page created in Task 3 with all 10 structural elements from the spec
- [x] No "TBD" or incomplete steps
- [x] `load_matched_data` name consistent across data_loader.py, test file, and page import
- [x] `MATCHED_DATA_PATH` / `MATCHED_FILE_PATTERN` names consistent across const.py, data_loader.py import, and test monkeypatches
- [x] `load_train_stations` still imported from `data_loader` (not matched loader) — correct per spec
