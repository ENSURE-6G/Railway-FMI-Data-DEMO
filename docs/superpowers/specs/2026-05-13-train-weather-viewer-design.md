# Design Spec: Train & Weather Viewer Page

**Date:** 2026-05-13
**Status:** Approved

## Summary

Add a new Streamlit page, `4_🌦️_Train_Weather_Viewer.py`, that mirrors the existing Train Viewer page exactly but loads from the matched train+weather dataset. The only visible difference is that the raw stop data table exposes all 146 columns (train fields + weather fields) instead of ~28.

## Data Layer

### `const.py` additions

```python
MATCHED_DATA_PATH = _DATA_ROOT / "matched_flat_data"
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"
```

### `data_loader.py` addition

New cached function:

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

Source files: `matched_data_flat_{year}_{month:02d}.csv` in `Railway-FMI-Data-CSV-Files-v2/matched_flat_data/`.

## New Page

**File:** `pages/4_🌦️_Train_Weather_Viewer.py`
**Title:** `🌦️ Train & Weather Viewer`
**Icon:** `🌦️`

### Structure (identical to Train Viewer)

1. Year / month selectors
2. Load matched data via `load_matched_data(year, month)`
3. Empty-data guard + session state key reset on period change
4. Route selection: Origin and Destination selectboxes (same defaults: Helsinki asema → Rovaniemi)
5. "Find Trains" button — uses `get_trains_for_route` from `train_utils`
6. Train selectbox — uses `get_train_route` from `train_utils`
7. Stop trimming between origin and destination (inclusive)
8. **Delay timeline chart** — Plotly scatter+line, same color thresholds (≤5 min green, ≤10 orange, >10 red)
9. **Route map** — Folium, joins station coordinates from `load_train_stations()`, same circle markers and popups
10. **Raw stop data table** — `st.dataframe(route_stops, use_container_width=True, hide_index=True)` — all 146 columns shown as-is

### What reuses existing utilities

- `get_unique_stations`, `get_trains_for_route`, `get_train_route` from `utils/train_utils.py`
- `load_train_stations` from `utils/data_loader.py`
- Constants `AVAILABLE_YEARS`, `AVAILABLE_MONTHS`, `DEFAULT_ORIGIN`, `DEFAULT_DESTINATION` from `const.py`

## What Is Not Changing

- The existing Train Viewer page (`2_🚆_Train_Viewer.py`) is untouched
- No shared rendering utility is introduced
- No additional weather-specific charts beyond what the train viewer already has

## File Checklist

| File | Change |
|------|--------|
| `const.py` | Add `MATCHED_DATA_PATH`, `MATCHED_FILE_PATTERN` |
| `utils/data_loader.py` | Add `load_matched_data()` |
| `pages/4_🌦️_Train_Weather_Viewer.py` | New file, copy of Train Viewer wired to matched data |
