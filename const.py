from pathlib import Path

# Project root is the folder containing this file
_PROJECT_ROOT = Path(__file__).parent

# External data root is a sibling folder at the same level as the project
_DATA_ROOT = _PROJECT_ROOT.parent / "Railway-FMI-Data-CSV-Files-v2"

TRAIN_DATA_PATH = _DATA_ROOT / "train_flat_data"
WEATHER_DATA_PATH = _DATA_ROOT / "weather_data"
METADATA_PATH = _PROJECT_ROOT / "metadata"

AVAILABLE_YEARS: list[int] = [2024, 2025]
AVAILABLE_MONTHS: list[int] = list(range(1, 13))

TRAIN_FILE_PATTERN = "all_trains_data_flat_{year}_{month:02d}.csv"
WEATHER_FILE_PATTERN = "fmi_weather_observations_{year}_{month:02d}.csv"
MATCHED_DATA_PATH = _DATA_ROOT / "matched_flat_data"
MATCHED_FILE_PATTERN = "matched_data_flat_{year}_{month:02d}.csv"

TRAIN_CATEGORIES: list[str] = ["Long-distance", "Commuter", "Cargo"]
TRAIN_TYPES: list[str] = ["IC", "S", "PYO", "HDM", "HL", "T"]

MAP_CENTER: list[float] = [64.5, 26.0]
MAP_ZOOM: int = 5

DEFAULT_ORIGIN = "Helsinki asema"
DEFAULT_DESTINATION = "Rovaniemi"
