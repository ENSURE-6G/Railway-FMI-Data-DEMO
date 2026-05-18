# Allas Remote Storage Integration — Design Spec

**Date:** 2026-05-18  
**Status:** Approved

## Overview

Add a `DATA_SOURCE` flag to `const.py` that switches the app between loading CSV files from the local filesystem and fetching them from CSC Allas object storage (S3-compatible). No pages or UI change — only the data loaders are affected.

## Architecture

Single flag in `const.py` controls all three data types (train, weather, matched). Each loader function in `data_loader.py` branches on this flag. Remote access uses boto3 pointed at the CSC Allas S3 endpoint (`https://a3s.fi`). Credentials come from environment variables loaded via `python-dotenv`.

## `const.py` Changes

```python
# Data source flag: "local" uses local filesystem, "remote" uses CSC Allas (S3)
DATA_SOURCE: str = "local"  # switch to "remote" to use Allas

# Allas S3 configuration (used only when DATA_SOURCE == "remote")
ALLAS_ENDPOINT_URL = "https://a3s.fi"
ALLAS_TRAIN_BUCKET = "train_flat_data"
ALLAS_WEATHER_BUCKET = "weather_data"
ALLAS_MATCHED_BUCKET = "matched_flat_Data"
```

## `data_loader.py` Changes

### S3 client helper

```python
@st.cache_resource
def _get_s3_client():
    import boto3, os
    return boto3.client(
        "s3",
        endpoint_url=ALLAS_ENDPOINT_URL,
        aws_access_key_id=os.environ["ALLAS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["ALLAS_SECRET_ACCESS_KEY"],
    )
```

Cached with `@st.cache_resource` so the client is created once per session. Raises `KeyError` at startup if credentials are missing from the environment, which Streamlit surfaces as an error.

### Loader pattern

Each of the three `load_*` functions (`load_train_data`, `load_weather_data`, `load_matched_data`) follows this pattern:

```python
@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    filename = TRAIN_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = TRAIN_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path, parse_dates=[...], low_memory=False)
    else:
        try:
            import io
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_TRAIN_BUCKET, Key=filename)
            return pd.read_csv(io.BytesIO(obj["Body"].read()), parse_dates=[...], low_memory=False)
        except Exception as e:
            st.error(f"Could not load train data from Allas: {e}")
            return pd.DataFrame()
```

On remote fetch failure, `st.error()` is shown and an empty DataFrame is returned — consistent with the existing local "file not found" behavior.

`load_train_stations()` and `load_ems_stations()` are metadata files stored locally and are **not** affected by this flag.

### Credential loading

Add at the top of `data_loader.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## `.env` File (gitignored)

```
ALLAS_ACCESS_KEY_ID=your_key_here
ALLAS_SECRET_ACCESS_KEY=your_secret_here
```

Add `.env` to `.gitignore` if not already present.

## Dependencies

Add to `requirements.txt`:
- `boto3`
- `python-dotenv`

## One-Time Credential Setup

CSC Allas S3 credentials are generated via the Pouta web UI (`pouta.csc.fi`):

1. Log in → **Project → API Access → EC2 Credentials**
2. Copy the **Access Key** and **Secret Key** into `.env`

Alternatively, on Puhti/Mahti: run `allas-conf --mode s3cmd` to generate keys stored in `~/.s3cfg`.

## Error Handling

| Scenario | Behavior |
|---|---|
| Local file not found | Return empty DataFrame (existing behavior) |
| Remote file not found (NoSuchKey) | `st.error()` + return empty DataFrame |
| Credential missing from env | `KeyError` raised at client creation → Streamlit error |
| Network/connection failure | `st.error()` + return empty DataFrame |

## Files Changed

- `const.py` — add `DATA_SOURCE` flag and Allas bucket constants
- `utils/data_loader.py` — add `_get_s3_client()`, add remote branch to 3 loaders, add `load_dotenv()`
- `requirements.txt` — add `boto3`, `python-dotenv`
- `.env` (new, gitignored) — S3 credentials
- `.gitignore` — ensure `.env` is listed

## Out of Scope

- Streamlit Cloud / secrets.toml deployment (can be added later)
- Caching files locally after remote fetch
- Swift protocol access
- Uploading or writing data to Allas
