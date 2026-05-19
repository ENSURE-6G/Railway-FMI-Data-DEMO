# Railway-FMI Demo — Design Spec
**Date:** 2026-05-11  
**Status:** Approved

---

## Overview

A Streamlit multi-page interactive demo for the Train-Weather data project, to be presented at a project meeting. The app visualizes two years (2024–2025) of Finnish railway timetable/delay data and FMI meteorological station observations. The three pages are fully independent — no cross-analysis between train and weather data in this version.

---

## Project Structure

```
Railway-FMI-Data_DEMO/
  Home.py                          ← Streamlit entry point (redirects or shows Home content)
  const.py                         ← all shared constants
  pages/
    1_🏠_Home.py
    2_🚆_Train_Viewer.py
    3_🌤️_Weather_Viewer.py
  utils/
    data_loader.py                 ← all CSV I/O with @st.cache_data
    train_utils.py                 ← route/timetable logic
    weather_utils.py               ← station filtering and chart prep
  metadata/
    metadata_train_stations.csv    ← train station names + lat/lon
    metadata_fmi_ems_stations.csv  ← EMS station names + fmisid + lat/lon
  docs/
    superpowers/specs/
      2026-05-11-railway-fmi-demo-design.md
  environment.yml                  ← conda env: venv_rail_fmi_demo
```

---

## External Data Sources (read-only, not inside the project)

- **Train data:** `Railway-FMI-Data-CSV-Files-v2/train_data/all_trains_data_YYYY_MM.csv`
- **Weather data:** `Railway-FMI-Data-CSV-Files-v2/weather_data/fmi_weather_observations_YYYY_MM.csv`
- **Pre-aggregated delay table:** `Railway-FMI-Data-CSV-Files-v2/delay_table_differenceInMinutes.csv`

Paths are defined in `const.py` — pages never hardcode them.

---

## const.py

Defines all shared constants:

```python
TRAIN_DATA_PATH        # absolute path to train_data/ folder
WEATHER_DATA_PATH      # absolute path to weather_data/ folder
METADATA_PATH          # absolute path to metadata/ folder inside project
AVAILABLE_YEARS        # [2024, 2025]  — extend here as new years arrive
AVAILABLE_MONTHS       # list(range(1, 13))
TRAIN_FILE_PATTERN     # "all_trains_data_{year}_{month:02d}.csv"
WEATHER_FILE_PATTERN   # "fmi_weather_observations_{year}_{month:02d}.csv"
TRAIN_CATEGORIES       # ["Long-distance", "Commuter", "Cargo"]
TRAIN_TYPES            # ["IC", "S", "PYO", "HDM", "HL", "T"]
MAP_CENTER             # [64.5, 26.0]  — center of Finland
MAP_ZOOM               # 5
```

---

## Data Layer — utils/data_loader.py

All functions decorated with `@st.cache_data`. Files are loaded only once per (year, month) combination per session.

| Function | Returns | Notes |
|---|---|---|
| `load_train_data(year, month)` | `pd.DataFrame` | Reads monthly CSV; parses `timeTableRows` with `ast.literal_eval()`, explodes into one row per station stop |
| `load_weather_data(year, month)` | `pd.DataFrame` | Reads monthly CSV as-is |
| `load_train_stations()` | `pd.DataFrame` | Reads `metadata_train_stations.csv`; cached with no TTL |
| `load_ems_stations()` | `pd.DataFrame` | Reads `metadata_fmi_ems_stations.csv`; cached with no TTL |

**Parsed train stops schema** (result of exploding `timeTableRows`):

| Column | Description |
|---|---|
| `trainNumber` | Train identifier |
| `departureDate` | Date of service |
| `trainType` | IC, S, PYO, etc. |
| `trainCategory` | Long-distance / Commuter / Cargo |
| `cancelled` | Train-level cancellation flag |
| `stationName` | Human-readable station name |
| `stationShortCode` | e.g. HKI, PSL |
| `type` | DEPARTURE or ARRIVAL |
| `scheduledTime` | ISO datetime string |
| `actualTime` | ISO datetime string (may be null) |
| `differenceInMinutes` | Signed integer; positive = late |
| `stop_cancelled` | Stop-level cancellation flag |

---

## utils/train_utils.py

| Function | Returns | Notes |
|---|---|---|
| `get_unique_stations(stops_df)` | `list[str]` | Sorted list of all station names in the loaded month |
| `get_trains_for_route(stops_df, origin, destination)` | `pd.DataFrame` | Trains that stop at origin before destination; returns one row per train with trainNumber, type, category, first scheduled departure, cancelled status |
| `get_train_route(stops_df, train_number, departure_date)` | `pd.DataFrame` | All stops for a specific train, sorted by scheduled time |

---

## utils/weather_utils.py

| Function | Returns | Notes |
|---|---|---|
| `get_station_timeseries(weather_df, station_name)` | `pd.DataFrame` | Filters rows for the selected station; returns timestamp + core columns only (Air temperature, Wind speed, Precipitation amount, Snow depth) |

---

## Pages

### 🏠 Home (`pages/1_🏠_Home.py`)

**Layout (top to bottom):**
1. App title + subtitle describing the dataset
2. Three `st.metric` cards in columns:
   - Total trains tracked (count of unique trainNumbers across available data)
   - Total EMS stations (from metadata, static count)
   - Date range covered ("Jan 2024 – Dec 2025")
3. Full-width `streamlit_folium` map of Finland:
   - Blue circle markers for all train stations (no filtering)
   - Orange circle markers for EMS stations
   - Popups with station name on click
4. "About this dataset" expander with a short description of data sources (Finnish Transport Infrastructure Agency + FMI)

---

### 🚆 Train Viewer (`pages/2_🚆_Train_Viewer.py`)

**Interaction flow:**

1. **Data selection** (top of page): Year dropdown + Month dropdown → triggers `load_train_data(year, month)` via `data_loader`
2. **Route selection**: Two `st.selectbox` dropdowns — Origin and Destination — populated from `get_unique_stations()`. A "🔍 Find Trains" button triggers the search.
3. **Train list**: `st.dataframe` showing matching trains from `get_trains_for_route()` — columns: train number, type, category, scheduled departure time, cancelled flag. A `st.selectbox` below the table lets the user pick a specific train number to view in detail.
4. **Train detail** (shown after selection):
   - **Folium map**: Polyline connecting all stops in geographic order; circle markers at each station; popup shows station name, scheduled time, actual time, delay in minutes.
   - **Plotly timeline chart**: x-axis = scheduled time, y-axis = station name (ordered by stop sequence), points colored by delay severity:
     - Green: < 2 minutes
     - Yellow: 2–10 minutes
     - Red: > 10 minutes
   - **Raw data table**: `st.dataframe` showing all columns for the selected train's stops (full parsed stop schema with no column filtering).

---

### 🌤️ Weather Viewer (`pages/3_🌤️_Weather_Viewer.py`)

**Interaction flow:**

1. **Data selection** (top of page): Year dropdown + Month dropdown → triggers `load_weather_data(year, month)`
2. **Station selection via map**: Full-width `streamlit_folium` map showing all EMS stations as clickable orange markers. The `st_folium()` return value's `last_object_clicked_popup` field captures the selected station name.
3. **Station detail** (shown after a station is clicked):
   - Station name as `st.subheader`
   - 2×2 grid of Plotly line charts (using `st.columns`):
     - Air Temperature (°C)
     - Wind Speed (m/s)
     - Precipitation Amount (mm)
     - Snow Depth (cm)
   - All charts share the same x-axis (timestamps for the selected month)
   - **Raw data table**: `st.dataframe` showing all columns for the selected station's rows for the selected month (no column filtering).

---

## Environment

**Conda environment name:** `venv_rail_fmi_demo`

**Key dependencies (environment.yml):**
- python 3.11
- streamlit
- pandas
- folium
- streamlit-folium
- plotly
- ast (stdlib)

---

## Constraints & Notes

- Data files are outside the project directory — paths in `const.py` must use absolute paths or be configurable.
- No cross-analysis between train and weather data in this version.
- `timeTableRows` parsing is the most expensive step; `@st.cache_data` on `load_train_data` is critical for demo performance.
- EMS stations have no lat/lon in weather CSVs — always join from `metadata_fmi_ems_stations.csv`.
- Adding a new year only requires updating `AVAILABLE_YEARS` in `const.py`.
