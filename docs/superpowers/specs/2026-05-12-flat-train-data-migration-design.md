# Flat Train Data Migration Design

**Date:** 2026-05-12
**Status:** Approved

## Summary

Migrate the train data source from the original nested CSV format (one row per train run, with a stringified JSON `timeTableRows` column) to the new pre-flattened CSV format (one row per stop). This eliminates the `ast.literal_eval` parsing loop in `load_train_data`, reducing load time significantly.

## Motivation

The old format required deserializing a Python-stringified list of dicts for every train run on every load. For a full month this means tens of thousands of `ast.literal_eval` calls plus row-by-row Python iteration — the main cause of ~5 minute load times. The new flat format is a direct CSV read with no parsing step.

## Changes

### `const.py`

Two constants updated:

```python
TRAIN_DATA_PATH = _DATA_ROOT / "train_flat_data"
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
```

### `data_loader.py`

`load_train_data` simplified to a single `pd.read_csv` call with `parse_dates` for the timestamp columns. `import ast` removed.

```python
@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    path = TRAIN_DATA_PATH / TRAIN_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(
        path,
        parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
    )
```

The function now returns all 26 columns from the flat CSV. The existing 12 columns the app uses are a subset of these, so no downstream code changes are needed.

## New CSV Schema

The flat CSV has one row per train stop per train run. A full train schedule is identified by `(trainNumber, departureDate)`.

| Column | Type | Notes |
|---|---|---|
| trainNumber | int | |
| departureDate | date | Parsed as datetime |
| operatorUICCode | int | |
| operatorShortCode | str | |
| trainType | str | e.g. IC, S, HDM |
| trainCategory | str | Long-distance, Commuter, Cargo |
| commuterLineID | str | Nullable |
| runningCurrently | bool | |
| cancelled | bool | Train-level cancellation |
| version | int | |
| timetableType | str | REGULAR / ADHOC |
| timetableAcceptanceDate | datetime | Parsed |
| stationName | str | |
| stationShortCode | str | |
| stationUICCode | int | |
| countryCode | str | |
| type | str | DEPARTURE / ARRIVAL |
| trainStopping | bool | |
| commercialStop | bool | |
| commercialTrack | str | |
| stop_cancelled | bool | Stop-level cancellation |
| scheduledTime | datetime | Parsed |
| actualTime | datetime | Parsed, nullable |
| differenceInMinutes | float | Nullable |
| causes | str | Stringified list, not parsed |
| trainReady | str | Stringified dict, nullable |

## No Downstream Changes Required

- `train_utils.py`: `pd.to_datetime()` calls on already-parsed datetime columns become no-ops — safe, no change needed.
- `Train_Viewer.py`: uses the same column names as before — no change needed.
- `Weather_Viewer.py`: unaffected.

## Files Changed

| File | Change |
|---|---|
| `const.py` | Update `TRAIN_DATA_PATH` and `TRAIN_FILE_PATTERN` |
| `utils/data_loader.py` | Simplify `load_train_data`, remove `import ast` |
