import io

import pandas as pd
import pytest
from utils.data_loader import load_train_data, load_matched_data

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


@pytest.fixture
def patched_loader(flat_parquet, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", flat_parquet)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.parquet")
    load_train_data.clear()
    yield loader
    load_train_data.clear()


@pytest.fixture
def patched_loader_empty(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "TRAIN_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "TRAIN_FILE_PATTERN", "all_trains_data_flat_{year}_{month:02d}.parquet")
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


MATCHED_COLUMNS = [
    "trainNumber", "departureDate", "stationName", "stationShortCode",
    "scheduledTime", "actualTime", "differenceInMinutes",
    "timetableAcceptanceDate",
    "Air temperature", "Wind speed", "Snow depth",
]


@pytest.fixture
def matched_csv(tmp_path):
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
        "closest_ems": ["Helsinki", "Tampere"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
    }
    df = pd.DataFrame(data)
    path = tmp_path / "matched_data_flat_2024_01.csv"
    df.to_csv(path, index=False)
    return tmp_path


@pytest.fixture
def patched_matched_loader(matched_csv, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "MATCHED_DATA_PATH", matched_csv)
    monkeypatch.setattr(loader, "MATCHED_FILE_PATTERN", "matched_data_flat_{year}_{month:02d}.csv")
    load_matched_data.clear()
    yield loader
    load_matched_data.clear()


@pytest.fixture
def patched_matched_loader_empty(tmp_path, monkeypatch):
    import utils.data_loader as loader
    monkeypatch.setattr(loader, "DATA_SOURCE", "local")
    monkeypatch.setattr(loader, "MATCHED_DATA_PATH", tmp_path)
    monkeypatch.setattr(loader, "MATCHED_FILE_PATTERN", "matched_data_flat_{year}_{month:02d}.csv")
    load_matched_data.clear()
    yield loader
    load_matched_data.clear()


def test_load_matched_data_returns_expected_columns(patched_matched_loader):
    df = load_matched_data(2024, 1)
    assert set(MATCHED_COLUMNS).issubset(df.columns)
    assert len(df) == 2


def test_load_matched_data_parses_datetime_columns(patched_matched_loader):
    df = load_matched_data(2024, 1)
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["actualTime"])
    assert pd.api.types.is_datetime64_any_dtype(df["timetableAcceptanceDate"])
    assert pd.api.types.is_datetime64_any_dtype(df["departureDate"])


def test_load_matched_data_missing_file_returns_empty_dataframe(patched_matched_loader_empty):
    df = load_matched_data(2099, 1)
    assert df.empty


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


def _make_weather_csv_bytes():
    data = {
        "timestamp": ["2024-01-01 00:00:00", "2024-01-01 01:00:00"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
        "station_name": ["Helsinki", "Helsinki"],
    }
    buf = io.BytesIO()
    pd.DataFrame(data).to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_load_weather_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_weather_csv_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_weather_data.clear()

    df = loader.load_weather_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="weather_data",
        Key="fmi_weather_observations_2024_01.csv",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    loader.load_weather_data.clear()


def test_load_weather_data_remote_error_returns_empty(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("timeout")

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    monkeypatch.setattr("streamlit.error", lambda msg: None)
    loader.load_weather_data.clear()

    df = loader.load_weather_data(2024, 1)

    assert df.empty

    loader.load_weather_data.clear()


def test_load_train_data_remote_error_returns_empty(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("connection refused")

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    monkeypatch.setattr("streamlit.error", lambda msg: None)
    loader.load_train_data.clear()

    df = loader.load_train_data(2024, 1)

    assert df.empty

    loader.load_train_data.clear()


def _make_matched_csv_bytes():
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
        "closest_ems": ["Helsinki", "Tampere"],
        "Air temperature": [-3.2, -2.8],
        "Wind speed": [4.1, 3.9],
        "Snow depth": [12.0, 11.5],
    }
    buf = io.BytesIO()
    pd.DataFrame(data).to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_load_matched_data_remote_returns_dataframe(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": _make_matched_csv_bytes()}

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    loader.load_matched_data.clear()

    df = loader.load_matched_data(2024, 1)

    mock_client.get_object.assert_called_once_with(
        Bucket="matched_flat_data",
        Key="matched_data_flat_2024_01.csv",
    )
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["scheduledTime"])

    loader.load_matched_data.clear()


def test_load_matched_data_remote_error_returns_empty(monkeypatch):
    from unittest.mock import MagicMock
    import utils.data_loader as loader

    mock_client = MagicMock()
    mock_client.get_object.side_effect = Exception("NoSuchKey")

    monkeypatch.setattr(loader, "DATA_SOURCE", "remote")
    monkeypatch.setattr(loader, "_get_s3_client", lambda: mock_client)
    monkeypatch.setattr("streamlit.error", lambda msg: None)
    loader.load_matched_data.clear()

    df = loader.load_matched_data(2024, 1)

    assert df.empty

    loader.load_matched_data.clear()
