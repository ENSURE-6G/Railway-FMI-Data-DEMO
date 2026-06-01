from pathlib import Path

# Project root is the folder containing this file
_PROJECT_ROOT = Path(__file__).parent

# External data root is a sibling folder at the same level as the project
_DATA_ROOT = _PROJECT_ROOT.parent / "Railway-FMI-Data-CSV-Files-v2"

TRAIN_DATA_PATH = _DATA_ROOT / "train_flat_data"
WEATHER_DATA_PATH = _DATA_ROOT / "weather_with_rolling_windows_data"
METADATA_PATH = _PROJECT_ROOT / "metadata"

AVAILABLE_YEARS: list[int] = list(range(2018, 2026))
AVAILABLE_MONTHS: list[int] = list(range(1, 13))

TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.parquet"
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.parquet"
MATCHED_DATA_PATH = _DATA_ROOT / "matched_flat_data"
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.parquet"

# Data source: "local" loads from filesystem, "remote" fetches from CSC Allas (S3)
DATA_SOURCE: str = "remote"

# Allas S3 configuration — used only when DATA_SOURCE == "remote"
ALLAS_ENDPOINT_URL: str = "https://a3s.fi"
ALLAS_TRAIN_BUCKET: str = "train_flat_data"
ALLAS_WEATHER_BUCKET: str = "weather_data"
ALLAS_MATCHED_BUCKET: str = "matched_flat_data"

TRAIN_CATEGORIES: list[str] = ["Long-distance", "Commuter", "Cargo"]
TRAIN_TYPES: list[str] = ["IC", "S", "PYO", "HDM", "HL", "T"]

MAP_CENTER: list[float] = [64.5, 26.0]
MAP_ZOOM: int = 5

DEFAULT_YEAR: int = 2024
DEFAULT_MONTH: int = 1

DEFAULT_ORIGIN = "Helsinki asema"
DEFAULT_DESTINATION = "Rovaniemi"
