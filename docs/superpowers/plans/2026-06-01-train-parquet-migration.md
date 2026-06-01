# Train Data Parquet Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch `load_train_data()` to read `.parquet` files from both local filesystem and Allas S3, scoped to the Train Viewer only.

**Architecture:** Two-line change in `const.py` (pattern extension) and a `read_csv` → `read_parquet` swap in `data_loader.py`. Tests are updated in lock-step: local fixture writes parquet, remote helper serializes to parquet. Weather and matched loaders are not touched.

**Tech Stack:** Python 3.11, pandas, pyarrow (new dependency), pytest, boto3

---

## Files Modified

- `const.py` — change `TRAIN_FILE_PATTERN` extension
- `utils/data_loader.py` — swap `read_csv` → `read_parquet` in `load_train_data()`
- `requirements.txt` — add `pyarrow`
- `local/environment.yml` — add `pyarrow` under pip dependencies
- `tests/test_data_loader.py` — update train fixtures and remote helper to parquet

---

### Task 1: Add pyarrow dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `local/environment.yml`

- [ ] **Step 1: Add pyarrow to requirements.txt**

Open `requirements.txt`. Add `pyarrow` after `pandas`:

```
streamlit
pandas
pyarrow
plotly
boto3
python-dotenv
folium
streamlit-folium
```

- [ ] **Step 2: Add pyarrow to local/environment.yml**

Open `local/environment.yml`. Add `pyarrow` under pip:

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
    - boto3
    - python-dotenv
    - pyarrow
```

- [ ] **Step 3: Verify pyarrow is importable in the current environment**

Run:
```bash
python -c "import pyarrow; print(pyarrow.__version__)"
```
Expected: prints a version string (e.g. `16.x.x`). If it fails, install it: `pip install pyarrow`.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt local/environment.yml
git commit -m "chore: add pyarrow dependency for parquet support"
```

---

### Task 2: Update TRAIN_FILE_PATTERN in const.py

**Files:**
- Modify: `const.py:16`

- [ ] **Step 1: Change the file pattern extension**

In `const.py`, change line 16 from:

```python
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
```

to:

```python
TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.parquet"
```

- [ ] **Step 2: Commit**

```bash
git add const.py
git commit -m "feat: switch TRAIN_FILE_PATTERN to .parquet extension"
```

---

### Task 3: Update load_train_data() to use read_parquet

**Files:**
- Modify: `utils/data_loader.py:42-64`

- [ ] **Step 1: Swap read_csv for read_parquet in both branches**

Replace the entire `load_train_data` function in `utils/data_loader.py`:

```python
@st.cache_data(ttl=3600, max_entries=6)
def load_train_data(year: int, month: int) -> pd.DataFrame:
    filename = TRAIN_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = TRAIN_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_TRAIN_BUCKET, Key=filename)
            return pd.read_parquet(io.BytesIO(obj["Body"].read()))
        except Exception as e:
            st.error(f"Could not load train data from Allas: {e}")
            return pd.DataFrame()
```

Note: `parse_dates` and `low_memory` are dropped — parquet stores dtypes natively.

- [ ] **Step 2: Commit**

```bash
git add utils/data_loader.py
git commit -m "feat: load_train_data reads parquet instead of csv"
```

---

### Task 4: Update train fixtures and helpers in tests

**Files:**
- Modify: `tests/test_data_loader.py`

This task updates the train-specific fixtures and the remote helper. Weather and matched fixtures/tests are not touched.

- [ ] **Step 1: Update the flat_csv fixture to write parquet**

Find the `flat_csv` fixture (currently around line 18) and replace it entirely with `flat_parquet`. The key difference: datetime columns must be cast to `datetime64` before writing so parquet preserves the dtype.

```python
@pytest.fixture
def flat_parquet(tmp_path):
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
    }
    df = pd.DataFrame(data)
    path = tmp_path / "all_trains_data_flat_2024_01.parquet"
    df.to_parquet(path, index=False)
    return tmp_path
```

- [ ] **Step 2: Update patched_loader to use flat_parquet and .parquet pattern**

Find `patched_loader` and replace:

```python
@pytest.fixture
def patched_loader(flat_parquet, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", flat_parquet)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.parquet")
    load_train_data.clear()
    yield loader
    load_train_data.clear()
```

- [ ] **Step 3: Update patched_loader_empty to use .parquet pattern**

Find `patched_loader_empty` and replace:

```python
@pytest.fixture
def patched_loader_empty(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.parquet")
    load_train_data.clear()
    yield loader
    load_train_data.clear()
```

- [ ] **Step 4: Replace _make_train_csv_bytes with _make_train_parquet_bytes**

Find `_make_train_csv_bytes` (around line 241) and replace entirely:

```python
def _make_train_parquet_bytes():
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
    }
    buf = io.BytesIO()
    pd.DataFrame(data).to_parquet(buf, index=False)
    buf.seek(0)
    return buf
```

- [ ] **Step 5: Update test_load_train_data_remote_returns_dataframe**

Find `test_load_train_data_remote_returns_dataframe` and replace:

```python
def test_load_train_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_train_parquet_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_train_data.clear()

    df = loader.load_train_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="train_flat_data",
        Key="all_trains_data_flat_2024_01.parquet",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])

    loader.load_train_data.clear()
```

- [ ] **Step 6: Run all train-related tests**

```bash
pytest tests/test_data_loader.py -v -k "train"
```

Expected: all train tests pass. Weather and matched tests are not run here.

- [ ] **Step 7: Run full test suite to confirm no regressions**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add tests/test_data_loader.py
git commit -m "test: update train fixtures and remote helper to use parquet"
```
