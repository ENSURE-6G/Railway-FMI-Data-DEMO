# Allas Remote Storage Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `DATA_SOURCE` flag to `const.py` that switches all three CSV loaders between local filesystem and CSC Allas S3 object storage, with no changes to any page or UI file.

**Architecture:** A single `DATA_SOURCE: str` constant in `const.py` (values `"local"` or `"remote"`) controls branching inside each `load_*` function in `data_loader.py`. A shared `_get_s3_client()` helper (cached with `@st.cache_resource`) creates a boto3 client pointed at `https://a3s.fi`. Credentials are loaded from a `.env` file via `python-dotenv`.

**Tech Stack:** Python, boto3, python-dotenv, pytest, Streamlit, pandas

---

## File Map

| File | Action | What changes |
|---|---|---|
| `requirements.txt` | Create | boto3, python-dotenv |
| `const.py` | Modify | `DATA_SOURCE` flag + 4 Allas constants |
| `utils/data_loader.py` | Modify | `load_dotenv()`, `_get_s3_client()`, remote branch in 3 loaders |
| `tests/test_data_loader.py` | Modify | Remote-path tests for all 3 loaders + error handling |
| `.env.example` | Create | Template showing required env var names |

---

### Task 1: Create `requirements.txt` and install dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create `requirements.txt`**

```text
streamlit
pandas
boto3
python-dotenv
folium
streamlit-folium
```

(Add any other packages already in your conda env that pages import — the list above covers the data layer.)

- [ ] **Step 2: Install the new packages**

```bash
pip install boto3 python-dotenv
```

Expected: both packages install without errors.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add requirements.txt with boto3 and python-dotenv"
```

---

### Task 2: Update `const.py` with `DATA_SOURCE` flag and Allas constants

**Files:**
- Modify: `const.py`

- [ ] **Step 1: Add the flag and Allas constants to `const.py`**

Open `const.py` and add the following block after the existing path constants (after the `MATCHED_FILE_PATTERN` line):

```python
# Data source: "local" loads from filesystem, "remote" fetches from CSC Allas (S3)
DATA_SOURCE: str = "local"

# Allas S3 configuration — used only when DATA_SOURCE == "remote"
ALLAS_ENDPOINT_URL: str = "https://a3s.fi"
ALLAS_TRAIN_BUCKET: str = "train_flat_data"
ALLAS_WEATHER_BUCKET: str = "weather_data"
ALLAS_MATCHED_BUCKET: str = "matched_flat_Data"
```

The full updated `const.py` should look like this:

```python
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent
_DATA_ROOT = _PROJECT_ROOT.parent / "Railway-FMI-Data-CSV-Files-v2"

TRAIN_DATA_PATH = _DATA_ROOT / "train_flat_data"
WEATHER_DATA_PATH = _DATA_ROOT / "weather_data"
METADATA_PATH = _PROJECT_ROOT / "metadata"

AVAILABLE_YEARS: list[int] = [2024, 2025]
AVAILABLE_MONTHS: list[int] = list(range(1, 13))

TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.csv"
MATCHED_DATA_PATH = _DATA_ROOT / "matched_flat_data"
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"

# Data source: "local" loads from filesystem, "remote" fetches from CSC Allas (S3)
DATA_SOURCE: str = "local"

# Allas S3 configuration — used only when DATA_SOURCE == "remote"
ALLAS_ENDPOINT_URL: str = "https://a3s.fi"
ALLAS_TRAIN_BUCKET: str = "train_flat_data"
ALLAS_WEATHER_BUCKET: str = "weather_data"
ALLAS_MATCHED_BUCKET: str = "matched_flat_Data"

TRAIN_CATEGORIES: list[str] = ["Long-distance", "Commuter", "Cargo"]
TRAIN_TYPES: list[str] = ["IC", "S", "PYO", "HDM", "HL", "T"]

MAP_CENTER: list[float] = [64.5, 26.0]
MAP_ZOOM: int = 5

DEFAULT_ORIGIN = "Helsinki asema"
DEFAULT_DESTINATION = "Rovaniemi"
```

- [ ] **Step 2: Run existing tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: all existing tests pass.

- [ ] **Step 3: Commit**

```bash
git add const.py
git commit -m "feat: add DATA_SOURCE flag and Allas bucket constants to const.py"
```

---

### Task 3: Add `load_dotenv()` and `_get_s3_client()` to `data_loader.py`

**Files:**
- Modify: `utils/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_data_loader.py`:

```python
def test_get_s3_client_uses_env_credentials(monkeypatch):
    import os
    monkeypatch.setenv("ALLAS_ACCESS_KEY_ID", "test-key-id")
    monkeypatch.setenv("ALLAS_SECRET_ACCESS_KEY", "test-secret")

    import utils.data_loader as loader
    loader._get_s3_client.clear()

    client = loader._get_s3_client()

    meta = client.meta
    assert meta.endpoint_url == "https://a3s.fi"

    loader._get_s3_client.clear()
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
pytest tests/test_data_loader.py::test_get_s3_client_uses_env_credentials -v
```

Expected: FAIL — `AttributeError: module 'utils.data_loader' has no attribute '_get_s3_client'`

- [ ] **Step 3: Implement `load_dotenv()` and `_get_s3_client()` in `data_loader.py`**

Replace the top of `utils/data_loader.py` with:

```python
import io
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from const import (
    TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH,
    TRAIN_FILE_PATTERN, WEATHER_FILE_PATTERN,
    MATCHED_DATA_PATH, MATCHED_FILE_PATTERN,
    DATA_SOURCE,
    ALLAS_ENDPOINT_URL, ALLAS_TRAIN_BUCKET, ALLAS_WEATHER_BUCKET, ALLAS_MATCHED_BUCKET,
)

load_dotenv()


@st.cache_resource
def _get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=ALLAS_ENDPOINT_URL,
        aws_access_key_id=os.environ["ALLAS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["ALLAS_SECRET_ACCESS_KEY"],
    )
```

Leave the existing `load_*` functions unchanged for now.

- [ ] **Step 4: Run the test to confirm it passes**

```bash
pytest tests/test_data_loader.py::test_get_s3_client_uses_env_credentials -v
```

Expected: PASS

- [ ] **Step 5: Run all tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: add load_dotenv and _get_s3_client to data_loader"
```

---

### Task 4: Remote branch for `load_train_data()`

**Files:**
- Modify: `utils/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/test_data_loader.py`:

```python
def _make_train_csv_bytes():
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
    buf = io.BytesIO()
    pd.DataFrame(data).to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_load_train_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_train_csv_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_train_data.clear()

    df = loader.load_train_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="train_flat_data",
        Key="all_trains_data_flat_2024_01.csv",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])

    loader.load_train_data.clear()


def test_load_train_data_remote_error_returns_empty(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("connection refused")

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    monkeypatch.setattr("streamlit.error", lambda msg: None)
    loader.load_train_data.clear()

    df = loader.load_train_data(2024, 1)

    assert df.empty

    loader.load_train_data.clear()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_data_loader.py::test_load_train_data_remote_returns_dataframe tests/test_data_loader.py::test_load_train_data_remote_error_returns_empty -v
```

Expected: FAIL — remote branch does not exist yet.

- [ ] **Step 3: Add the remote branch to `load_train_data()`**

Replace the existing `load_train_data` function in `utils/data_loader.py`:

```python
@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    filename = TRAIN_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = TRAIN_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(
            path,
            parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
            low_memory=False,
        )
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_TRAIN_BUCKET, Key=filename)
            return pd.read_csv(
                io.BytesIO(obj["Body"].read()),
                parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
                low_memory=False,
            )
        except Exception as e:
            st.error(f"Could not load train data from Allas: {e}")
            return pd.DataFrame()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_data_loader.py::test_load_train_data_remote_returns_dataframe tests/test_data_loader.py::test_load_train_data_remote_error_returns_empty -v
```

Expected: PASS

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: add remote branch to load_train_data"
```

---

### Task 5: Remote branch for `load_weather_data()`

**Files:**
- Modify: `utils/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/test_data_loader.py`:

```python
def _make_weather_csv_bytes():
    data = {
        "timestamp": ["2024-01-01 00:00:00", "2024-01-01 01:00:00"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
        "station_name": ["Helsinki", "Helsinki"],
    }
    buf = io.BytesIO()
    pd.DataFrame(data).to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_load_weather_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_weather_csv_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_weather_data.clear()

    df = loader.load_weather_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="weather_data",
        Key="fmi_weather_observations_2024_01.csv",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    loader.load_weather_data.clear()


def test_load_weather_data_remote_error_returns_empty(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("timeout")

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    monkeypatch.setattr("streamlit.error", lambda msg: None)
    loader.load_weather_data.clear()

    df = loader.load_weather_data(2024, 1)

    assert df.empty

    loader.load_weather_data.clear()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_data_loader.py::test_load_weather_data_remote_returns_dataframe tests/test_data_loader.py::test_load_weather_data_remote_error_returns_empty -v
```

Expected: FAIL

- [ ] **Step 3: Add the remote branch to `load_weather_data()`**

Replace the existing `load_weather_data` function in `utils/data_loader.py`:

```python
@st.cache_data
def load_weather_data(year: int, month: int) -> pd.DataFrame:
    filename = WEATHER_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = WEATHER_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_WEATHER_BUCKET, Key=filename)
            df = pd.read_csv(io.BytesIO(obj["Body"].read()))
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
        except Exception as e:
            st.error(f"Could not load weather data from Allas: {e}")
            return pd.DataFrame()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_data_loader.py::test_load_weather_data_remote_returns_dataframe tests/test_data_loader.py::test_load_weather_data_remote_error_returns_empty -v
```

Expected: PASS

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: add remote branch to load_weather_data"
```

---

### Task 6: Remote branch for `load_matched_data()`

**Files:**
- Modify: `utils/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/test_data_loader.py`:

```python
def _make_matched_csv_bytes():
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
    buf = io.BytesIO()
    pd.DataFrame(data).to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_load_matched_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_matched_csv_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_matched_data.clear()

    df = loader.load_matched_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="matched_flat_Data",
        Key="matched_data_flat_2024_01.csv",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])

    loader.load_matched_data.clear()


def test_load_matched_data_remote_error_returns_empty(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    monkeypatch.setattr("streamlit.error", lambda msg: None)
    loader.load_matched_data.clear()

    df = loader.load_matched_data(2024, 1)

    assert df.empty

    loader.load_matched_data.clear()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_data_loader.py::test_load_matched_data_remote_returns_dataframe tests/test_data_loader.py::test_load_matched_data_remote_error_returns_empty -v
```

Expected: FAIL

- [ ] **Step 3: Add the remote branch to `load_matched_data()`**

Replace the existing `load_matched_data` function in `utils/data_loader.py`:

```python
@st.cache_data
def load_matched_data(year: int, month: int) -> pd.DataFrame:
    filename = MATCHED_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = MATCHED_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(
            path,
            parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
            low_memory=False,
        )
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_MATCHED_BUCKET, Key=filename)
            return pd.read_csv(
                io.BytesIO(obj["Body"].read()),
                parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
                low_memory=False,
            )
        except Exception as e:
            st.error(f"Could not load matched data from Allas: {e}")
            return pd.DataFrame()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_data_loader.py::test_load_matched_data_remote_returns_dataframe tests/test_data_loader.py::test_load_matched_data_remote_error_returns_empty -v
```

Expected: PASS

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: add remote branch to load_matched_data"
```

---

### Task 7: Create `.env.example`

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Create `.env.example`**

```text
# CSC Allas S3 credentials
# Generate at: pouta.csc.fi → Project → API Access → EC2 Credentials
ALLAS_ACCESS_KEY_ID=your_access_key_id_here
ALLAS_SECRET_ACCESS_KEY=your_secret_access_key_here
```

- [ ] **Step 2: Confirm `.env` is in `.gitignore`**

```bash
grep "^\.env$" .gitignore
```

Expected: `.env` — if the line is not found, add `.env` to `.gitignore`.

- [ ] **Step 3: Run full test suite one final time**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add .env.example
git commit -m "chore: add .env.example with Allas credential template"
```

---

## Using Remote Mode

Once S3 credentials are obtained (see spec for steps):

1. Copy `.env.example` to `.env` and fill in your keys
2. In `const.py`, change `DATA_SOURCE = "local"` to `DATA_SOURCE = "remote"`
3. Run the app — all three loaders will fetch from Allas

To switch back to local, revert `DATA_SOURCE = "local"`.
