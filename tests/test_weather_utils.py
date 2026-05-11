# tests/test_weather_utils.py
import pytest
import pandas as pd
from utils.weather_utils import get_station_timeseries


@pytest.fixture
def sample_weather():
    return pd.DataFrame([
        {"timestamp": pd.Timestamp("2024-01-01 00:00:00"), "station_name": "Oulu lentoasema",
         "Air temperature": -10.0, "Wind speed": 5.0, "Precipitation amount": 0.0, "Snow depth": 20.0,
         "Wind direction": 270.0, "Gust speed": 8.0},
        {"timestamp": pd.Timestamp("2024-01-01 01:00:00"), "station_name": "Oulu lentoasema",
         "Air temperature": -11.0, "Wind speed": 6.0, "Precipitation amount": 0.1, "Snow depth": 21.0,
         "Wind direction": 280.0, "Gust speed": 9.0},
        {"timestamp": pd.Timestamp("2024-01-01 00:00:00"), "station_name": "Helsinki Kaisaniemi",
         "Air temperature": -3.0, "Wind speed": 3.0, "Precipitation amount": 0.0, "Snow depth": 5.0,
         "Wind direction": 180.0, "Gust speed": 4.0},
    ])


def test_get_station_timeseries_filters_correct_station(sample_weather):
    result = get_station_timeseries(sample_weather, "Oulu lentoasema")
    assert len(result) == 2
    assert all(result["station_name"] == "Oulu lentoasema")


def test_get_station_timeseries_returns_all_columns(sample_weather):
    result = get_station_timeseries(sample_weather, "Oulu lentoasema")
    assert "timestamp" in result.columns
    assert "Air temperature" in result.columns
    assert "Wind speed" in result.columns
    assert "Precipitation amount" in result.columns
    assert "Snow depth" in result.columns


def test_get_station_timeseries_empty_for_unknown_station(sample_weather):
    result = get_station_timeseries(sample_weather, "Unknown Station")
    assert len(result) == 0
