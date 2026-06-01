# Train Data Parquet Migration — Design Spec

**Date:** 2026-06-01  
**Scope:** Train Viewer only (`load_train_data`). Weather and matched loaders are untouched.

## Context

The `train_flat_data` bucket on Allas S3 and the local `train_flat_data` folder have been fully migrated from CSV to Parquet files. The application still references `.csv` filenames and reads with `pd.read_csv`. This spec describes the minimal changes to make the Train Viewer consume parquet files from both sources.

## Changes

### `const.py`

Change `TRAIN_FILE_PATTERN` from:

```python
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
```

to:

```python
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.parquet"
```

No other constants are modified. `WEATHER_FILE_PATTERN`, `MATCHED_FILE_PATTERN`, bucket names, and all paths remain unchanged.

### `utils/data_loader.py` — `load_train_data()`

Replace `pd.read_csv(...)` with `pd.read_parquet(...)` in both the local and remote branches.

- **Local branch:** `pd.read_csv(path, parse_dates=[...], low_memory=False)` → `pd.read_parquet(path)`
- **Remote branch:** `pd.read_csv(io.BytesIO(...), parse_dates=[...], low_memory=False)` → `pd.read_parquet(io.BytesIO(...))`

The `parse_dates` and `low_memory` arguments are dropped entirely — parquet stores column dtypes natively (datetimes are preserved as-is), so no post-load parsing is needed.

All other aspects of `load_train_data` are unchanged: function signature, `@st.cache_data` decorator, error handling, return type (`pd.DataFrame`).

### `tests/test_data_loader.py` — train-related fixtures and helpers

Four items need updating to match the new format:

1. **`flat_csv` fixture** — write a `.parquet` file instead of `.csv`. The `departureDate`, `scheduledTime`, `actualTime`, and `timetableAcceptanceDate` columns must be cast to `datetime64` before writing so parquet preserves the dtype (instead of relying on `parse_dates`). Rename the fixture to `flat_parquet` and update the file path to `all_trains_data_flat_2024_01.parquet`.

2. **`patched_loader` fixture** — update the monkeypatched `TRAIN_FILE_PATTERN` to `"all_trains_data_flat_{year}_{month:02d}.parquet"`. Update the fixture dependency from `flat_csv` to `flat_parquet`.

3. **`patched_loader_empty` fixture** — update the monkeypatched `TRAIN_FILE_PATTERN` to `"all_trains_data_flat_{year}_{month:02d}.parquet"`.

4. **`_make_train_csv_bytes` helper** — rename to `_make_train_parquet_bytes`. Cast datetime columns to `datetime64` before writing, serialize with `df.to_parquet(buf, index=False)` instead of `df.to_csv`. The `test_load_train_data_remote_returns_dataframe` test must update its `Key` assertion to `"all_trains_data_flat_2024_01.parquet"` and use this new helper.

Tests not affected: weather tests, matched tests, S3 client tests, error-returns-empty tests.

## Out of Scope

- `load_weather_data` — unchanged
- `load_matched_data` — unchanged
- `pages/2_🚆_Train_Viewer.py` — unchanged (DataFrame schema is identical)
- `utils/train_utils.py` — unchanged
- Any other page or utility

## Dependencies

`pyarrow` or `fastparquet` must be available in the environment for `pd.read_parquet` to work. `pyarrow` is the standard choice and is likely already installed (it is a common pandas dependency). Confirm it is listed in `environment.yml` / `requirements.txt`.
