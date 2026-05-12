import pandas as pd
import pytest
from utils.data_loader import load_train_data

FLAT_COLUMNS = [
    "trainNumber", "departureDate", "operatorUICCode", "operatorShortCode",
    "trainType", "trainCategory", "commuterLineID", "runningCurrently",
    "cancelled", "version", "timetableType", "timetableAcceptanceDate",
    "stationName", "stationShortCode", "stationUICCode", "countryCode",
    "type", "trainStopping", "commercialStop", "commercialTrack",
    "stop_cancelled", "scheduledTime", "actualTime", "differenceInMinutes",
    "causes", "trainReady",
]


@pytest.fixture
def flat_csv(tmp_path):
    data = {
        "trainNumber": [1, 1],
        "departureDate": ["2024-01-01", "2024-01-01"],
        "operatorUICCode": [10, 10],
        "operatorShortCode": ["vr", "vr"],
        "trainType": ["IC", "IC"],
        "trainCategory": ["Long-distance", "Long-distance"],
        "commuterLineID": ["", ""],
        "runningCurrently": [False, False],
        "cancelled": [False, False],
        "version": [287293186071, 287293186071],
        "timetableType": ["REGULAR", "REGULAR"],
        "timetableAcceptanceDate": ["2023-11-02T05:57:22.000Z", "2023-11-02T05:57:22.000Z"],
        "stationName": ["Helsinki asema", "Tampere asema"],
        "stationShortCode": ["HKI", "TPE"],
        "stationUICCode": [1, 140],
        "countryCode": ["FI", "FI"],
        "type": ["DEPARTURE", "ARRIVAL"],
        "trainStopping": [True, True],
        "commercialStop": [True, True],
        "commercialTrack": ["9", "4"],
        "stop_cancelled": [False, False],
        "scheduledTime": ["2024-01-01T04:57:00.000Z", "2024-01-01T06:57:00.000Z"],
        "actualTime": ["2024-01-01T04:57:21.000Z", "2024-01-01T06:58:00.000Z"],
        "differenceInMinutes": [0.0, 1.0],
        "causes": ["[]", "[]"],
        "trainReady": ["", ""],
    }
    df = pd.DataFrame(data)
    path = tmp_path / "all_trains_data_flat_2024_01.csv"
    df.to_csv(path, index=False)
    return tmp_path


@pytest.fixture
def patched_loader(flat_csv, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", flat_csv)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.csv")
    load_train_data.clear()
    yield loader
    load_train_data.clear()


@pytest.fixture
def patched_loader_empty(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.csv")
    load_train_data.clear()
    yield loader
    load_train_data.clear()


def test_load_train_data_returns_all_flat_columns(patched_loader):
    df = load_train_data(2024, 1)
    assert set(FLAT_COLUMNS).issubset(df.columns)
    assert len(df) == 2


def test_load_train_data_parses_datetime_columns(patched_loader):
    df = load_train_data(2024, 1)
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["actualTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["timetableAcceptanceDate"])
    assert pd.api.types.is_datetime64_any_dtype(df["departureDate"])


def test_load_train_data_missing_file_returns_empty_dataframe(patched_loader_empty):
    df = load_train_data(2099, 1)
    assert df.empty
