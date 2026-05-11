# tests/test_train_utils.py
import pytest
import pandas as pd
from utils.train_utils import get_unique_stations, get_trains_for_route, get_train_route


@pytest.fixture
def sample_stops():
    return pd.DataFrame([
        # Train 1: HKI -> TPE
        {"trainNumber": 1, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Helsinki asema", "stationShortCode": "HKI", "type": "DEPARTURE",
         "scheduledTime": "2024-01-01T05:00:00.000Z", "actualTime": "2024-01-01T05:02:00.000Z",
         "differenceInMinutes": 2, "stop_cancelled": False},
        {"trainNumber": 1, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Tampere asema", "stationShortCode": "TPE", "type": "ARRIVAL",
         "scheduledTime": "2024-01-01T07:00:00.000Z", "actualTime": "2024-01-01T07:05:00.000Z",
         "differenceInMinutes": 5, "stop_cancelled": False},
        # Train 2: TPE -> HKI (reverse — should NOT match HKI->TPE route)
        {"trainNumber": 2, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Tampere asema", "stationShortCode": "TPE", "type": "DEPARTURE",
         "scheduledTime": "2024-01-01T08:00:00.000Z", "actualTime": None,
         "differenceInMinutes": 0, "stop_cancelled": False},
        {"trainNumber": 2, "departureDate": "2024-01-01", "trainType": "IC",
         "trainCategory": "Long-distance", "cancelled": False,
         "stationName": "Helsinki asema", "stationShortCode": "HKI", "type": "ARRIVAL",
         "scheduledTime": "2024-01-01T10:00:00.000Z", "actualTime": None,
         "differenceInMinutes": 0, "stop_cancelled": False},
    ])


def test_get_unique_stations_returns_sorted_list(sample_stops):
    result = get_unique_stations(sample_stops)
    assert result == ["Helsinki asema", "Tampere asema"]


def test_get_trains_for_route_finds_correct_train(sample_stops):
    result = get_trains_for_route(sample_stops, "Helsinki asema", "Tampere asema")
    assert len(result) == 1
    assert result.iloc[0]["trainNumber"] == 1


def test_get_trains_for_route_excludes_reverse_direction(sample_stops):
    result = get_trains_for_route(sample_stops, "Helsinki asema", "Tampere asema")
    assert 2 not in result["trainNumber"].values


def test_get_train_route_returns_all_stops_sorted(sample_stops):
    result = get_train_route(sample_stops, 1, "2024-01-01")
    assert len(result) == 2
    assert result.iloc[0]["stationName"] == "Helsinki asema"
    assert result.iloc[1]["stationName"] == "Tampere asema"
