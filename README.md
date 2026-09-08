# 🚆 Predicting Train Delays in Finland

A Streamlit demo app for a **multi-modal data fusion** research project: it combines
**Finnish railway timetable data** with **FMI weather observations** to explore — and
ultimately predict — train delays across the Finnish rail network, 2018–2025.

The app is the *visual front end* of the research. It does not train models; it explores
the source data, shows the delay statistics that motivate the work, and presents the
results of the delay-prediction experiments.

---

## What's in the app

The entry point is `Home.py`. Everything under `pages/` is auto-discovered by Streamlit
and shown in the sidebar, ordered by the number prefix in the filename. (Numbering starts
at 2 because `Home.py` occupies the first slot as the app entry point.)

| Page | What it shows |
|---|---|
| 🏠 **Home** (`Home.py`) | Project goal, the traditional-vs-fusion approach diagrams, headline counts (train stations, EMS weather stations, data coverage), and an interactive Finland map. Click a train station to draw lines to its **5 closest weather stations** — this is the spatial join the fusion model relies on. |
| 📊 **Delay Statistics** | Network-wide delay dashboard: year-over-year comparison, temporal patterns, and a delay-severity breakdown over time. |
| 🔍 **Delay Comparison** | **Delay origin vs. propagation** — compares raw total delay against offset-corrected, station-originated delay, so you can see how much of a delay was *created* at a station vs. *inherited* from upstream. |
| 🌤️ **Weather Viewer** | Pick an FMI weather station on the map, browse its observation time series for a chosen month. |
| 🚆 **Train Viewer** | Pick an origin/destination, list the trains on that route, and map a selected train's stops with delay information. |
| 🌦️ **Train & Weather Viewer** | The fusion view — a train's journey shown alongside the weather observed along its route. |
| 🤖 **AI Results** | Results of the XGBoost delay-prediction experiments at Oulu central station (101,146 observations): experimental setup, the hierarchical weather categorisation scheme, and MAE / RMSE / R² across model iterations. |

---

## Data

Two open data sources, plus a pre-computed join:

- **Train data** — [Finnish Transport Infrastructure Agency (Väylävirasto)](https://www.digitraffic.fi/)
  via the Digitraffic API. Passenger, commuter, and cargo trains with scheduled and actual
  timetable rows, including `differenceInMinutes` per stop.
- **Weather data** — [Finnish Meteorological Institute (FMI)](https://www.ilmatieteenlaitos.fi/)
  open data. Hourly observations from ~200 automatic weather stations (EMS): temperature,
  wind speed, precipitation, snow depth, pressure, visibility.
- **Matched data** — train stops already joined to nearby weather observations. This is what
  the fusion pages and the model consume.

Monthly Parquet files, one per month per dataset:

```
all_trains_data_flat_{year}_{month:02d}.parquet
fmi_weather_observations_{year}_{month:02d}.parquet
matched_data_flat_{year}_{month:02d}.parquet
```

Small, static files live **in the repo** and need no configuration:

- `metadata/` — train station and EMS station coordinates, plus `metadata_top5_closest_ems.csv`
  (the precomputed station-to-weather-station proximity table used by the Home map).
- `statistics/` — pre-aggregated daily delay tables that power the Delay Statistics and
  Delay Comparison pages. These are why those two pages load instantly and work offline.
- `assets/` — diagrams and model-metric plots.

### Where the monthly data comes from

`const.py` has a single switch:

```python
DATA_SOURCE: str = "remote"   # "remote" = CSC Allas (S3) · "local" = filesystem
```

- **`"remote"` (default)** — files are streamed from [CSC Allas](https://docs.csc.fi/data/Allas/)
  object storage over the S3 API (`https://a3s.fi`), from the buckets `train_flat_data`,
  `weather_data`, and `matched_flat_data`. **Requires credentials** (see below).
- **`"local"`** — files are read from a sibling folder next to the project:

  ```
  <parent>/Railway-FMI-Data-CSV-Files-v2/
    train_flat_data/
    weather_with_rolling_windows_data/
    matched_flat_data/
  ```

  No credentials needed, but you must have the data locally. If a month's file is missing,
  the loader returns an empty DataFrame rather than raising.

Loads are cached with `@st.cache_data(ttl=3600, max_entries=6)`, so re-selecting a month
you have already viewed is instant; the cache holds about six months at a time.

---

## Running it

### 1. Environment

The project uses a conda environment defined in `local/environment.yml` (Python 3.11):

```bash
conda env create -f local/environment.yml
conda activate venv_rail_fmi_demo
```

Prefer pip/venv? `requirements.txt` lists the runtime dependencies (add `pytest` to run the
tests):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt pytest
```

### 2. Credentials (only for `DATA_SOURCE = "remote"`)

Create `.streamlit/secrets.toml` — it is gitignored, so it never leaves your machine:

```toml
ALLAS_ACCESS_KEY_ID = "your_access_key_id"
ALLAS_SECRET_ACCESS_KEY = "your_secret_access_key"
```

Environment variables (or a `.env` file — see `.env.example`) work as a fallback if
`secrets.toml` is absent. Generate the keys at **pouta.csc.fi → Project → API Access →
EC2 Credentials**.

If you set `DATA_SOURCE = "local"` you can skip this step entirely. Note that the Home,
Delay Statistics, and Delay Comparison pages need no credentials either way — only the
month-by-month viewer pages hit Allas.

### 3. Launch

```bash
streamlit run Home.py
```

Streamlit opens <http://localhost:8501>. Use the sidebar to move between pages.

### 4. Tests

```bash
python -m pytest -q
```

22 tests covering the data loaders and the train/weather helper functions. They use
synthetic DataFrames and mocks, so they run without data files or credentials.

---

## Project layout

```
Home.py                  # entry point — project intro + station map
const.py                 # ALL paths, patterns, defaults, and the DATA_SOURCE switch
requirements.txt
upload_to_allas.py       # one-off admin script: push local parquet files to Allas buckets

pages/                   # Streamlit multipage app (sidebar order = filename prefix)
  2_📊_Delay_Statistics.py
  3_🔍_Delay_Comparison.py
  4_🌤️_Weather_Viewer.py
  5_🚆_Train_Viewer.py
  6_🌦️_Train_Weather_Viewer.py
  7_🤖_AI_Results.py

utils/
  data_loader.py         # cached loaders; local-vs-Allas branching lives here
  train_utils.py         # route filtering, stop ordering
  weather_utils.py       # per-station time series extraction

metadata/                # station coordinates + top-5 closest EMS lookup (in repo)
statistics/              # pre-aggregated delay tables (in repo)
assets/                  # diagrams and model metric plots
tests/                   # pytest suite
local/environment.yml    # conda environment spec
.streamlit/secrets.toml  # Allas credentials (gitignored — create your own)
```

---

## Making changes

A few things worth knowing before you edit:

- **`const.py` is the config surface.** Paths, file-name patterns, available years/months,
  map center and zoom, default route, train categories — all there. Changing the year range
  is a one-line edit to `AVAILABLE_YEARS`.
- **Add a page** by dropping a `N_emoji_Name.py` file into `pages/`. The number sets sidebar
  order; renumbering existing files is how you reorder them.
- **New data source or bucket?** `utils/data_loader.py` is the only file that touches the
  filesystem or S3. Keep it that way — pages should call loaders, never read files directly.
- **Do not commit secrets.** `.streamlit/secrets.toml` and `.env` are gitignored; keep it so.

---

## Deployment

The app runs on Streamlit Cloud as-is: point it at `Home.py`, keep `DATA_SOURCE = "remote"`,
and paste the two Allas keys into the app's **Secrets** panel (same TOML format as
`.streamlit/secrets.toml`). No other configuration is required — the repo carries its own
metadata, statistics, and assets.
