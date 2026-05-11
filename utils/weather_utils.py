# utils/weather_utils.py
import pandas as pd


def get_station_timeseries(weather_df: pd.DataFrame, station_name: str) -> pd.DataFrame:
    return weather_df[weather_df["station_name"] == station_name].reset_index(drop=True)
