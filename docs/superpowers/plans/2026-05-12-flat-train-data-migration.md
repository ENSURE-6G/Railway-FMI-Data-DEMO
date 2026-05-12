# Flat Train Data Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the nested-CSV + `ast.literal_eval` loader with a direct read of the pre-flattened CSV files, eliminating the slow parsing loop.

**Architecture:** Two constants in `const.py` are updated to point at the new subfolder and filename pattern. `load_train_data` in `data_loader.py` is reduced to a single `pd.read_csv` call with `parse_dates`. No downstream code changes are needed because the flat CSV is a superset of what the old loader returned.

**Tech Stack:** Python, pandas, pytest, streamlit (`st.cache_data`)

---

## File Map

| File | Action | What changes |
|---|---|---|
| `const.py` | Modify | `TRAIN_DATA_PATH` subfolder, `TRAIN_FILE_PATTERN` filename |
| `utils/data_loader.py` | Modify | Simplify `load_train_data`; remove `import ast` |
| `tests/test_data_loader.py` | Create | Tests for new `load_train_data` behaviour |

---

### Task 1: Write failing tests for `load_train_data`

**Files:**
- Create: `tests/test_data_loader.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_data_loader.py
import pandas as pd
import pytest
from utils.data_loader import load_train_data

FLAT_COLUMNS = [
    "trainNumber", "departureDate", "operatorUICCode", "operatorShortCode",
    "trainType", "trainCategory", "commuterLineID", "runningCurrently",
    "cancelled", "version", "timetableType", "timetableAcceptanceDate",
    "stationName", "stationShortCode", "stationUICCode", "countryCode",
    "type", "trainStopping", "commercialStop", "commercialTrack",
    "stop_cancelled", "scheduledTime", "actualTime", "differenceInMinutes",
    "causes", "trainReady",
]


@pytest.fixture
def flat_csv(tmp_path):
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
    }
    df = pd.DataFrame(data)
    path = tmp_path / "all_trains_data_flat_2024_01.csv"
    df.to_csv(path, index=False)
    return tmp_path


def test_load_train_data_returns_all_flat_columns(flat_csv, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", flat_csv)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.csv")
    load_train_data.clear()
    df = load_train_data(2024, 1)
    assert set(FLAT_COLUMNS).issubset(df.columns)
    assert len(df) == 2


def test_load_train_data_parses_datetime_columns(flat_csv, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", flat_csv)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.csv")
    load_train_data.clear()
    df = load_train_data(2024, 1)
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["actualTime"])


def test_load_train_data_missing_file_returns_empty_dataframe(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.csv")
    load_train_data.clear()
    df = load_train_data(2099, 1)
    assert df.empty
```

- [ ] **Step 2: Run tests — verify they fail**

```
cd "D:\OneDrive - University of Oulu and Oamk\Railway-FMI-Data_DEMO"
conda activate railway-fmi-demo
pytest tests/test_data_loader.py -v
```

Expected: `test_load_train_data_returns_all_flat_columns` FAILS (old loader returns only 12 columns), `test_load_train_data_parses_datetime_columns` FAILS (old loader returns strings). The missing-file test may pass already — that is fine.

---

### Task 2: Update `const.py`

**Files:**
- Modify: `const.py`

- [ ] **Step 1: Update the two train constants**

In `const.py`, change lines 9 and 16:

```python
# Before:
TRAIN_DATA_PATH = _DATA_ROOT / "train_data"
TRAIN_FILE_PATTERN = "all_trains_data_{year}_{month:02d}.csv"

# After:
TRAIN_DATA_PATH = _DATA_ROOT / "train_flat_data"
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
```

No other lines in `const.py` change.

- [ ] **Step 2: Commit**

```bash
git add const.py
git commit -m "feat: point train data path to flat CSV subfolder"
```

---

### Task 3: Simplify `load_train_data`

**Files:**
- Modify: `utils/data_loader.py`

- [ ] **Step 1: Replace the function and remove `import ast`**

Full updated `utils/data_loader.py`:

```python
import pandas as pd
import streamlit as st
from const import (
    TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH,
    TRAIN_FILE_PATTERN, WEATHER_FILE_PATTERN,
)


@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    path = TRAIN_DATA_PATH / TRAIN_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(
        path,
        parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
    )


@st.cache_data
def load_weather_data(year: int, month: int) -> pd.DataFrame:
    path = WEATHER_DATA_PATH / WEATHER_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data
def load_train_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_train_stations.csv")


@st.cache_data
def load_ems_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_fmi_ems_stations.csv")
```

- [ ] **Step 2: Run all tests — verify they all pass**

```
pytest tests/ -v
```

Expected output: all tests pass, including the three new `test_data_loader` tests.

- [ ] **Step 3: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: replace ast.literal_eval loop with direct flat CSV read"
```
