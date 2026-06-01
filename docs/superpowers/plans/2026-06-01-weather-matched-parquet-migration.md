# Weather + Matched Data Parquet Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch `load_weather_data()` and `load_matched_data()` to read `.parquet` files from both local filesystem and Allas S3, completing the full parquet migration across all data loaders.

**Architecture:** Same two-step pattern as the train migration: update file patterns in `const.py`, swap `read_csv` → `read_parquet` in `data_loader.py`, update test fixtures and remote helpers in lock-step. The weather loader also drops a manual `pd.to_datetime` post-processing step since parquet preserves dtypes. A pre-existing bucket name bug in the weather remote test is fixed as part of rewriting that test.

**Tech Stack:** Python 3.11, pandas, pyarrow (already added), pytest, boto3

---

## Files Modified

- `const.py` — change `WEATHER_FILE_PATTERN` and `MATCHED_FILE_PATTERN` extensions
- `utils/data_loader.py` — swap `read_csv` → `read_parquet` in `load_weather_data()` and `load_matched_data()`
- `tests/test_data_loader.py` — update weather and matched fixtures and remote helpers to parquet; fix weather bucket name bug

---

### Task 1: Update WEATHER_FILE_PATTERN and MATCHED_FILE_PATTERN in const.py

**Files:**
- Modify: `const.py`

- [ ] **Step 1: Change both file pattern extensions**

In `const.py`, change `WEATHER_FILE_PATTERN` (line 17) from:

```python
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.csv"
```

to:

```python
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.parquet"
```

And change `MATCHED_FILE_PATTERN` (line 19) from:

```python
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"
```

to:

```python
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.parquet"
```

Do NOT touch `TRAIN_FILE_PATTERN` (line 16) — it is already `.parquet`.

- [ ] **Step 2: Commit**

```bash
git add const.py
git commit -m "feat: switch WEATHER_FILE_PATTERN and MATCHED_FILE_PATTERN to .parquet"
```

---

### Task 2: Update load_weather_data() to use read_parquet

**Files:**
- Modify: `utils/data_loader.py:59-78`

- [ ] **Step 1: Replace load_weather_data with parquet version**

Replace the entire `load_weather_data` function (lines 59–78):

```python
@st.cache_data(ttl=3600, max_entries=6)
def load_weather_data(year: int, month: int) -> pd.DataFrame:
    filename = WEATHER_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = WEATHER_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_WEATHER_BUCKET, Key=filename)
            return pd.read_parquet(io.BytesIO(obj["Body"].read()))
        except Exception as e:
            st.error(f"Could not load weather data from Allas: {e}")
            return pd.DataFrame()
```

Key changes: `pd.read_csv(...)` → `pd.read_parquet(...)` in both branches; the two `df["timestamp"] = pd.to_datetime(df["timestamp"])` lines are dropped (parquet stores datetime dtype natively); the intermediate `df` variable is removed.

Do NOT touch `load_train_data` or `load_matched_data`.

- [ ] **Step 2: Commit**

```bash
git add utils/data_loader.py
git commit -m "feat: load_weather_data reads parquet instead of csv"
```

---

### Task 3: Update load_matched_data() to use read_parquet

**Files:**
- Modify: `utils/data_loader.py:81-104`

- [ ] **Step 1: Replace load_matched_data with parquet version**

Replace the entire `load_matched_data` function (lines 81–104):

```python
@st.cache_data(ttl=3600, max_entries=6)
def load_matched_data(year: int, month: int) -> pd.DataFrame:
    filename = MATCHED_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = MATCHED_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_MATCHED_BUCKET, Key=filename)
            return pd.read_parquet(io.BytesIO(obj["Body"].read()))
        except Exception as e:
            st.error(f"Could not load matched data from Allas: {e}")
            return pd.DataFrame()
```

Key changes: `pd.read_csv(...)` → `pd.read_parquet(...)` in both branches; `parse_dates` and `low_memory=False` args dropped.

Do NOT touch `load_train_data` or `load_weather_data`.

- [ ] **Step 2: Commit**

```bash
git add utils/data_loader.py
git commit -m "feat: load_matched_data reads parquet instead of csv"
```

---

### Task 4: Update weather and matched test fixtures and helpers

**Files:**
- Modify: `tests/test_data_loader.py`

This task updates weather and matched fixtures/helpers only. Train fixtures (`flat_parquet`, `patched_loader`, `patched_loader_empty`, `_make_train_parquet_bytes`) are NOT touched.

- [ ] **Step 1: Replace matched_csv fixture with matched_parquet**

Find the `matched_csv` fixture (around line 103) and replace it entirely. Cast datetime columns to `datetime64` before writing so parquet preserves the dtype:

```python
@pytest.fixture
def matched_parquet(tmp_path):
    data = {
        "trainNumber": [1, 1],
        "departureDate": pd.to_datetime(["2024-01-01", "2024-01-01"]),
        "operatorUICCode": [10, 10],
        "operatorShortCode": ["vr", "vr"],
        "trainType": ["IC", "IC"],
        "trainCategory": ["Long-distance", "Long-distance"],
        "commuterLineID": ["", ""],
        "runningCurrently": [False, False],
        "cancelled": [False, False],
        "version": [287293186071, 287293186071],
        "timetableType": ["REGULAR", "REGULAR"],
        "timetableAcceptanceDate": pd.to_datetime(["2023-11-02T05:57:22.000Z", "2023-11-02T05:57:22.000Z"]),
        "stationName": ["Helsinki asema", "Tampere asema"],
        "stationShortCode": ["HKI", "TPE"],
        "stationUICCode": [1, 140],
        "countryCode": ["FI", "FI"],
        "type": ["DEPARTURE", "ARRIVAL"],
        "trainStopping": [True, True],
        "commercialStop": [True, True],
        "commercialTrack": ["9", "4"],
        "stop_cancelled": [False, False],
        "scheduledTime": pd.to_datetime(["2024-01-01T04:57:00.000Z", "2024-01-01T06:57:00.000Z"]),
        "actualTime": pd.to_datetime(["2024-01-01T04:57:21.000Z", "2024-01-01T06:58:00.000Z"]),
        "differenceInMinutes": [0.0, 1.0],
        "causes": ["[]", "[]"],
        "trainReady": ["", ""],
        "closest_ems": ["Helsinki", "Tampere"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
    }
    df = pd.DataFrame(data)
    path = tmp_path / "matched_data_flat_2024_01.parquet"
    df.to_parquet(path, index=False)
    return tmp_path
```

- [ ] **Step 2: Update patched_matched_loader**

Find `patched_matched_loader` and replace:

```python
@pytest.fixture
def patched_matched_loader(matched_parquet, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "MATCHED_DATA_PATH", matched_parquet)
    monkeypatch.setattr(loader, "MATCHED_FILE_PATTERN", "matched_data_flat_{year}_{month:02d}.parquet")
    load_matched_data.clear()
    yield loader
    load_matched_data.clear()
```

- [ ] **Step 3: Update patched_matched_loader_empty**

Find `patched_matched_loader_empty` and replace:

```python
@pytest.fixture
def patched_matched_loader_empty(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "MATCHED_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "MATCHED_FILE_PATTERN", "matched_data_flat_{year}_{month:02d}.parquet")
    load_matched_data.clear()
    yield loader
    load_matched_data.clear()
```

- [ ] **Step 4: Replace _make_weather_csv_bytes with _make_weather_parquet_bytes**

Find `_make_weather_csv_bytes` (around line 299) and replace entirely:

```python
def _make_weather_parquet_bytes():
    data = {
        "timestamp": pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 01:00:00"]),
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
        "station_name": ["Helsinki", "Helsinki"],
    }
    buf = io.BytesIO()
    pd.DataFrame(data).to_parquet(buf, index=False)
    buf.seek(0)
    return buf
```

- [ ] **Step 5: Update test_load_weather_data_remote_returns_dataframe**

Find `test_load_weather_data_remote_returns_dataframe` and replace. This also fixes the pre-existing bucket name bug (`"weather_data"` → `"weather_with_rolling_windows_data"`):

```python
def test_load_weather_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_weather_parquet_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_weather_data.clear()

    df = loader.load_weather_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="weather_with_rolling_windows_data",
        Key="fmi_weather_observations_2024_01.parquet",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    loader.load_weather_data.clear()
```

- [ ] **Step 6: Replace _make_matched_csv_bytes with _make_matched_parquet_bytes**

Find `_make_matched_csv_bytes` (around line 374) and replace entirely:

```python
def _make_matched_parquet_bytes():
    data = {
        "trainNumber": [1, 1],
        "departureDate": pd.to_datetime(["2024-01-01", "2024-01-01"]),
        "operatorUICCode": [10, 10],
        "operatorShortCode": ["vr", "vr"],
        "trainType": ["IC", "IC"],
        "trainCategory": ["Long-distance", "Long-distance"],
        "commuterLineID": ["", ""],
        "runningCurrently": [False, False],
        "cancelled": [False, False],
        "version": [287293186071, 287293186071],
        "timetableType": ["REGULAR", "REGULAR"],
        "timetableAcceptanceDate": pd.to_datetime(["2023-11-02T05:57:22.000Z", "2023-11-02T05:57:22.000Z"]),
        "stationName": ["Helsinki asema", "Tampere asema"],
        "stationShortCode": ["HKI", "TPE"],
        "stationUICCode": [1, 140],
        "countryCode": ["FI", "FI"],
        "type": ["DEPARTURE", "ARRIVAL"],
        "trainStopping": [True, True],
        "commercialStop": [True, True],
        "commercialTrack": ["9", "4"],
        "stop_cancelled": [False, False],
        "scheduledTime": pd.to_datetime(["2024-01-01T04:57:00.000Z", "2024-01-01T06:57:00.000Z"]),
        "actualTime": pd.to_datetime(["2024-01-01T04:57:21.000Z", "2024-01-01T06:58:00.000Z"]),
        "differenceInMinutes": [0.0, 1.0],
        "causes": ["[]", "[]"],
        "trainReady": ["", ""],
        "closest_ems": ["Helsinki", "Tampere"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
    }
    buf = io.BytesIO()
    pd.DataFrame(data).to_parquet(buf, index=False)
    buf.seek(0)
    return buf
```

- [ ] **Step 7: Update test_load_matched_data_remote_returns_dataframe**

Find `test_load_matched_data_remote_returns_dataframe` and replace:

```python
def test_load_matched_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_matched_parquet_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_matched_data.clear()

    df = loader.load_matched_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="matched_flat_data",
        Key="matched_data_flat_2024_01.parquet",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])

    loader.load_matched_data.clear()
```

- [ ] **Step 8: Run weather and matched tests**

```bash
pytest tests/test_data_loader.py -v -k "weather or matched"
```

Expected: all weather and matched tests pass (including the previously failing `test_load_weather_data_remote_returns_dataframe`).

- [ ] **Step 9: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass with no failures.

- [ ] **Step 10: Commit**

```bash
git add tests/test_data_loader.py
git commit -m "test: update weather and matched fixtures and helpers to use parquet"
```
