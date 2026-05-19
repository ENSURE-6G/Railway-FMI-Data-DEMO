# Streamlit Community Cloud Deployment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the Railway & Weather Data Explorer to Streamlit Community Cloud with credentials injected via `st.secrets`, viewer access restricted to invited emails, and no secrets in the repository.

**Architecture:** `_get_s3_client()` in `data_loader.py` is updated to check `st.secrets` first and fall back to `os.environ` (`.env`). A gitignored `.streamlit/secrets.toml` holds credentials for local dev. On Streamlit Cloud, credentials are entered in the dashboard secrets panel and injected as `st.secrets` at runtime.

**Tech Stack:** Python, Streamlit, boto3, GitHub, Streamlit Community Cloud

---

## File Map

| File | Action | What changes |
|---|---|---|
| `utils/data_loader.py` | Modify | `_get_s3_client()` checks `st.secrets` before `os.environ` |
| `tests/test_data_loader.py` | Modify | Update existing credential test + add `st.secrets` path test |
| `.streamlit/secrets.toml` | Create (gitignored) | Local dev credentials |

---

### Task 1: Update `_get_s3_client()` to check `st.secrets` first

**Files:**
- Modify: `utils/data_loader.py:19-34`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write the failing tests**

Add these two tests to `tests/test_data_loader.py` (after the existing `test_get_s3_client_uses_env_credentials`):

```python
def test_get_s3_client_uses_st_secrets(monkeypatch):
    import streamlit as st
    import utils.data_loader as loader

    monkeypatch.setattr(st, "secrets", {
        "ALLAS_ACCESS_KEY_ID": "secrets-key",
        "ALLAS_SECRET_ACCESS_KEY": "secrets-secret",
    })
    loader._get_s3_client.clear()

    client = loader._get_s3_client()

    assert client.meta.endpoint_url == "https://a3s.fi"

    loader._get_s3_client.clear()


def test_get_s3_client_falls_back_to_env_when_no_secrets_toml(monkeypatch):
    import streamlit as st
    import utils.data_loader as loader

    class _NoSecrets:
        def __getitem__(self, key):
            raise FileNotFoundError("No secrets.toml")

    monkeypatch.setattr(st, "secrets", _NoSecrets())
    monkeypatch.setenv("ALLAS_ACCESS_KEY_ID", "env-key")
    monkeypatch.setenv("ALLAS_SECRET_ACCESS_KEY", "env-secret")
    loader._get_s3_client.clear()

    client = loader._get_s3_client()

    assert client.meta.endpoint_url == "https://a3s.fi"

    loader._get_s3_client.clear()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_data_loader.py::test_get_s3_client_uses_st_secrets tests/test_data_loader.py::test_get_s3_client_falls_back_to_env_when_no_secrets_toml -v
```

Expected: FAIL — current `_get_s3_client` doesn't check `st.secrets`.

- [ ] **Step 3: Replace `_get_s3_client()` in `utils/data_loader.py`**

Replace lines 19–34 with:

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

- [ ] **Step 4: Update the existing env-credentials test to explicitly mock `st.secrets` as absent**

Find `test_get_s3_client_uses_env_credentials` in `tests/test_data_loader.py` and replace it with:

```python
def test_get_s3_client_uses_env_credentials(monkeypatch):
    import streamlit as st
    import utils.data_loader as loader

    class _NoSecrets:
        def __getitem__(self, key):
            raise FileNotFoundError("No secrets.toml")

    monkeypatch.setattr(st, "secrets", _NoSecrets())
    monkeypatch.setenv("ALLAS_ACCESS_KEY_ID", "test-key-id")
    monkeypatch.setenv("ALLAS_SECRET_ACCESS_KEY", "test-secret")
    loader._get_s3_client.clear()

    client = loader._get_s3_client()

    assert client.meta.endpoint_url == "https://a3s.fi"

    loader._get_s3_client.clear()
```

- [ ] **Step 5: Run new tests to confirm they pass**

```bash
pytest tests/test_data_loader.py::test_get_s3_client_uses_st_secrets tests/test_data_loader.py::test_get_s3_client_falls_back_to_env_when_no_secrets_toml tests/test_data_loader.py::test_get_s3_client_uses_env_credentials -v
```

Expected: all 3 PASS.

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all 22 tests pass.

- [ ] **Step 7: Commit**

```bash
git add utils/data_loader.py tests/test_data_loader.py
git commit -m "feat: check st.secrets before os.environ in _get_s3_client"
```

---

### Task 2: Create `.streamlit/secrets.toml` for local development

**Files:**
- Create: `.streamlit/secrets.toml` (gitignored — do NOT commit)

- [ ] **Step 1: Verify `.streamlit/secrets.toml` is gitignored**

```bash
grep "secrets.toml" .gitignore
```

Expected: `.streamlit/secrets.toml` — already present on line 15.

- [ ] **Step 2: Create the `.streamlit/` directory and `secrets.toml`**

Create the file `.streamlit/secrets.toml` with your actual Allas credentials:

```toml
ALLAS_ACCESS_KEY_ID = "your_access_key_id_here"
ALLAS_SECRET_ACCESS_KEY = "your_secret_access_key_here"
```

Replace the placeholder values with the real keys from your `.env` file.

- [ ] **Step 3: Verify the file is not tracked by git**

```bash
git status
```

Expected: `.streamlit/secrets.toml` does NOT appear in the output (it is gitignored).

- [ ] **Step 4: Run the app locally to confirm `st.secrets` path works**

```bash
streamlit run Home.py
```

Select any year/month on a data page. Data should load from Allas without errors. If you see "Could not load ... from Allas", the credentials in `secrets.toml` are wrong.

---

### Task 3: Create GitHub repository and push

No code changes. Manual steps only.

- [ ] **Step 1: Create a new public repository on GitHub**

Go to `github.com` → **New repository**:
- Name: `Railway-FMI-Data-DEMO` (or your preferred name)
- Visibility: **Public**
- Do NOT initialise with README, .gitignore, or licence (the repo already has these)

- [ ] **Step 2: Add the GitHub remote**

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
```

Replace `<your-username>` and `<repo-name>` with your actual values.

- [ ] **Step 3: Verify no secrets are staged**

```bash
git status
```

Confirm that `.env` and `.streamlit/secrets.toml` are NOT listed. If either appears, stop — do not push until they are removed from tracking.

- [ ] **Step 4: Push to GitHub**

```bash
git push -u origin master
```

Expected: all commits pushed, branch `master` tracked on `origin`.

- [ ] **Step 5: Confirm on GitHub**

Open the repo on GitHub. Verify:
- `const.py` is visible (bucket names are public — this is fine)
- `.env` is **not** present
- `.streamlit/` directory is **not** present

---

### Task 4: Deploy on Streamlit Community Cloud

No code changes. Manual steps only.

- [ ] **Step 1: Sign in to Streamlit Community Cloud**

Go to `share.streamlit.io` and sign in with your GitHub account.

- [ ] **Step 2: Create a new app**

Click **New app** and fill in:
- **Repository:** `<your-username>/<repo-name>`
- **Branch:** `master`
- **Main file path:** `Home.py`

- [ ] **Step 3: Add secrets before deploying**

Click **Advanced settings → Secrets** and paste:

```toml
ALLAS_ACCESS_KEY_ID = "your_access_key_id_here"
ALLAS_SECRET_ACCESS_KEY = "your_secret_access_key_here"
```

Replace placeholders with the real keys. Click **Save**.

- [ ] **Step 4: Deploy**

Click **Deploy!** and wait for the build to complete (typically 2–3 minutes). The build log will show package installation from `requirements.txt`.

Expected: app loads at `https://<your-app>.streamlit.app` and data loads from Allas.

- [ ] **Step 5: Restrict viewer access**

In the Streamlit Cloud dashboard, click your app → **Settings → Sharing**:
- Set to **Only specific people can view this app**
- Add the email addresses of allowed viewers

Invited viewers will authenticate via Google or GitHub OAuth using the invited email.

---

## Security checklist before going live

- [ ] `.env` not in git history: `git log --all --full-history -- .env` returns nothing
- [ ] `.streamlit/secrets.toml` not in git history: `git log --all --full-history -- .streamlit/secrets.toml` returns nothing
- [ ] Credentials posted in this session rotated: run `allas-conf -m S3` on Puhti/Mahti and update `.env`, `secrets.toml`, and Streamlit Cloud secrets with the new keys
- [ ] Viewer access restricted to invited emails in Streamlit Cloud dashboard
