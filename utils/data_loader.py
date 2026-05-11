import ast
import pandas as pd
import streamlit as st
from const import (
    TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH,
    TRAIN_FILE_PATTERN, WEATHER_FILE_PATTERN,
)


@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    path = TRAIN_DATA_PATH / TRAIN_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        try:
            stops = ast.literal_eval(row["timeTableRows"])
        except (ValueError, SyntaxError):
            continue
        for stop in stops:
            records.append({
                "trainNumber": row["trainNumber"],
                "departureDate": row["departureDate"],
                "trainType": row["trainType"],
                "trainCategory": row["trainCategory"],
                "cancelled": row["cancelled"],
                "stationName": stop.get("stationName"),
                "stationShortCode": stop.get("stationShortCode"),
                "type": stop.get("type"),
                "scheduledTime": stop.get("scheduledTime"),
                "actualTime": stop.get("actualTime"),
                "differenceInMinutes": stop.get("differenceInMinutes"),
                "stop_cancelled": stop.get("cancelled", False),
            })
    return pd.DataFrame(records)


@st.cache_data
def load_weather_data(year: int, month: int) -> pd.DataFrame:
    path = WEATHER_DATA_PATH / WEATHER_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data
def load_train_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_train_stations.csv")


@st.cache_data
def load_ems_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_fmi_ems_stations.csv")
