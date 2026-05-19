# Streamlit Community Cloud Deployment — Design Spec

**Date:** 2026-05-19  
**Status:** Approved

## Overview

Deploy the Railway & Weather Data Explorer to Streamlit Community Cloud using a public GitHub repository. The deployed app always loads data from CSC Allas (remote mode). Access is restricted to invited viewers via Streamlit Cloud's email-based authentication. Credentials are never stored in the repository.

## Architecture

Streamlit Community Cloud pulls code from a public GitHub repository and runs `Home.py` as the entry point. S3 credentials are stored in Streamlit Cloud's secrets manager and injected as `st.secrets` at runtime. Locally, credentials are read from `.streamlit/secrets.toml` (gitignored) or `.env`, in that order.

## Changes Required

### `utils/data_loader.py` — `_get_s3_client()`

Replace the current credential lookup with a `st.secrets`-first approach:

```python
@st.cache_resource
def _get_s3_client():
    import boto3
    try:
        key = st.secrets["ALLAS_ACCESS_KEY_ID"]
        secret = st.secrets["ALLAS_SECRET_ACCESS_KEY"]
    except (KeyError, FileNotFoundError):
        key = os.environ.get("ALLAS_ACCESS_KEY_ID")
        secret = os.environ.get("ALLAS_SECRET_ACCESS_KEY")
    if not key or not secret:
        raise RuntimeError(
            "ALLAS_ACCESS_KEY_ID and ALLAS_SECRET_ACCESS_KEY must be set in "
            ".streamlit/secrets.toml (local) or Streamlit Cloud secrets (deployed)."
        )
    return boto3.client(
        "s3",
        endpoint_url=ALLAS_ENDPOINT_URL,
        aws_access_key_id=key,
        aws_secret_access_key=secret,
    )
```

`FileNotFoundError` is caught because `st.secrets` raises it when no `secrets.toml` exists locally. This makes the fallback to `os.environ` (`.env` via `load_dotenv()`) work correctly in both environments.

### `.streamlit/secrets.toml` — New file (gitignored)

Create for local development:

```toml
ALLAS_ACCESS_KEY_ID = "your_access_key_id_here"
ALLAS_SECRET_ACCESS_KEY = "your_secret_access_key_here"
```

This file is already covered by `.gitignore` line 15 (`.streamlit/secrets.toml`). It must never be committed.

### `const.py` — No change

`DATA_SOURCE = "remote"` stays hardcoded. The deployed app is always remote. Local dev can change this manually when needed.

### `requirements.txt` — No change

All required packages are already listed.

## GitHub Repository Setup

1. Create a new **public** repository on GitHub
2. Add the remote: `git remote add origin <repo-url>`
3. Push: `git push -u origin master`

Files safe to be public:
- `const.py` — contains bucket names and endpoint URL (not secrets)
- `.env.example` — contains only placeholder values
- All source code

Files that must never be pushed (already gitignored):
- `.env`
- `.streamlit/secrets.toml`

## Streamlit Community Cloud Deployment

1. Go to `share.streamlit.io` and sign in with GitHub
2. Click **New app**
3. Select: repo, branch (`master`), main file (`Home.py`)
4. Open **Advanced settings → Secrets** and enter:
   ```
   ALLAS_ACCESS_KEY_ID = "..."
   ALLAS_SECRET_ACCESS_KEY = "..."
   ```
5. Click **Deploy**

## Viewer Authentication

In Streamlit Cloud dashboard → app **Settings → Sharing**:
- Set access to **Only specific people can view this app**
- Invite viewers by email address

Invited users must log in with the invited email via Google or GitHub OAuth. No code changes required — this is managed entirely in the dashboard.

## Security Properties After Deployment

| Risk | Mitigation |
|---|---|
| Credentials in repo | `secrets.toml` and `.env` are gitignored; secrets entered via dashboard only |
| Public code exposes bucket names | Bucket names are not secrets — access requires S3 credentials |
| Unrestricted app access | Viewer authentication via email invite |
| Unlimited Allas fetches | Streamlit `@st.cache_data` caches results per session — each file fetched once |
| Leaked keys from chat history | Keys shared in this session should be rotated via `allas-conf -m S3` on Puhti/Mahti |

## Files Changed

| File | Action |
|---|---|
| `utils/data_loader.py` | Modify `_get_s3_client()` to check `st.secrets` before `os.environ` |
| `.streamlit/secrets.toml` | Create (gitignored) — local dev credentials |
