# Weather + Matched Data Parquet Migration — Design Spec

**Date:** 2026-06-01  
**Scope:** Weather Viewer and Train-Weather Viewer (`load_weather_data`, `load_matched_data`). Train loader is untouched.

## Context

The `weather_with_rolling_windows_data` and `matched_flat_data` buckets on Allas S3, and their corresponding local folders, are fully migrated to Parquet. The train data loader was already migrated (2026-06-01). This spec describes the same minimal change applied to the two remaining loaders.

A pre-existing bug in `test_load_weather_data_remote_returns_dataframe` — asserting `Bucket="weather_data"` instead of the correct `"weather_with_rolling_windows_data"` — is fixed as part of this work since the test is being rewritten anyway.

## Changes

### `const.py`

Change `WEATHER_FILE_PATTERN` from:

```python
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.csv"
```

to:

```python
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.parquet"
```

Change `MATCHED_FILE_PATTERN` from:

```python
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"
```

to:

```python
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.parquet"
```

No other constants are modified.

### `utils/data_loader.py` — `load_weather_data()`

Replace `pd.read_csv(...)` with `pd.read_parquet(...)` in both branches. Drop the manual `df["timestamp"] = pd.to_datetime(df["timestamp"])` line — parquet preserves the datetime dtype natively.

- **Local branch:** `pd.read_csv(path)` + manual timestamp parse → `pd.read_parquet(path)`
- **Remote branch:** `pd.read_csv(io.BytesIO(...))` + manual timestamp parse → `pd.read_parquet(io.BytesIO(...))`

### `utils/data_loader.py` — `load_matched_data()`

Replace `pd.read_csv(...)` with `pd.read_parquet(...)` in both branches. Drop `parse_dates` and `low_memory=False`.

- **Local branch:** `pd.read_csv(path, parse_dates=[...], low_memory=False)` → `pd.read_parquet(path)`
- **Remote branch:** `pd.read_csv(io.BytesIO(...), parse_dates=[...], low_memory=False)` → `pd.read_parquet(io.BytesIO(...))`

All other aspects of both functions are unchanged: signatures, `@st.cache_data` decorators, error handling, return types.

### `tests/test_data_loader.py` — weather and matched fixtures/helpers

Five items updated:

1. **`matched_csv` fixture → `matched_parquet`**: write a `.parquet` file. Cast `departureDate`, `scheduledTime`, `actualTime`, `timetableAcceptanceDate` to `datetime64` via `pd.to_datetime()` before writing.

2. **`patched_matched_loader`**: update dependency from `matched_csv` to `matched_parquet`; update monkeypatched `MATCHED_FILE_PATTERN` to `.parquet`.

3. **`patched_matched_loader_empty`**: update monkeypatched `MATCHED_FILE_PATTERN` to `.parquet`.

4. **`_make_weather_csv_bytes` → `_make_weather_parquet_bytes`**: cast `timestamp` column via `pd.to_datetime()`, serialize with `to_parquet`. Update `test_load_weather_data_remote_returns_dataframe` to use the new helper, assert `Key="fmi_weather_observations_2024_01.parquet"`, and fix the bucket assertion to `Bucket="weather_with_rolling_windows_data"`.

5. **`_make_matched_csv_bytes` → `_make_matched_parquet_bytes`**: cast datetime columns via `pd.to_datetime()`, serialize with `to_parquet`. Update `test_load_matched_data_remote_returns_dataframe` to use the new helper and assert `Key="matched_data_flat_2024_01.parquet"`.

## Out of Scope

- `load_train_data` — unchanged (already migrated)
- `pages/3_🌤️_Weather_Viewer.py` — unchanged (DataFrame schema identical)
- `pages/4_🌦️_Train_Weather_Viewer.py` — unchanged (DataFrame schema identical)
- `utils/weather_utils.py`, `utils/train_utils.py` — unchanged
- Train test fixtures — unchanged
