# utils/train_utils.py
import pandas as pd


def get_unique_stations(stops_df: pd.DataFrame) -> list[str]:
    return sorted(stops_df["stationName"].dropna().unique().tolist())


def get_trains_for_route(
    stops_df: pd.DataFrame, origin: str, destination: str
) -> pd.DataFrame:
    origin_stops = (
        stops_df[stops_df["stationName"] == origin][["trainNumber", "departureDate", "scheduledTime"]]
        .rename(columns={"scheduledTime": "origin_time"})
    )
    dest_stops = (
        stops_df[stops_df["stationName"] == destination][["trainNumber", "departureDate", "scheduledTime"]]
        .rename(columns={"scheduledTime": "dest_time"})
    )
    merged = origin_stops.merge(dest_stops, on=["trainNumber", "departureDate"])
    valid = merged[merged["origin_time"] < merged["dest_time"]].copy()

    train_meta = (
        stops_df[["trainNumber", "departureDate", "trainType", "trainCategory", "cancelled"]]
        .drop_duplicates()
    )
    result = valid.merge(train_meta, on=["trainNumber", "departureDate"])
    return (
        result[["trainNumber", "departureDate", "trainType", "trainCategory", "origin_time", "cancelled"]]
        .sort_values("origin_time")
        .reset_index(drop=True)
    )


def get_train_route(
    stops_df: pd.DataFrame, train_number: int, departure_date: str | pd.Timestamp
) -> pd.DataFrame:
    mask = (stops_df["trainNumber"] == train_number) & (stops_df["departureDate"] == departure_date)
    route = stops_df[mask].copy()
    return route.sort_values("scheduledTime").reset_index(drop=True)
