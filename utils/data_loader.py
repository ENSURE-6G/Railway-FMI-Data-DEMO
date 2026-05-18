import io
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from const import (
    TRAIN_DATA_PATH, WEATHER_DATA_PATH, METADATA_PATH,
    TRAIN_FILE_PATTERN, WEATHER_FILE_PATTERN,
    MATCHED_DATA_PATH, MATCHED_FILE_PATTERN,
    DATA_SOURCE,
    ALLAS_ENDPOINT_URL, ALLAS_TRAIN_BUCKET, ALLAS_WEATHER_BUCKET, ALLAS_MATCHED_BUCKET,
)

load_dotenv()


@st.cache_resource
def _get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=ALLAS_ENDPOINT_URL,
        aws_access_key_id=os.environ["ALLAS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["ALLAS_SECRET_ACCESS_KEY"],
    )


@st.cache_data
def load_train_data(year: int, month: int) -> pd.DataFrame:
    filename = TRAIN_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = TRAIN_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(
            path,
            parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
            low_memory=False,
        )
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_TRAIN_BUCKET, Key=filename)
            return pd.read_csv(
                io.BytesIO(obj["Body"].read()),
                parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
                low_memory=False,
            )
        except Exception as e:
            st.error(f"Could not load train data from Allas: {e}")
            return pd.DataFrame()


@st.cache_data
def load_weather_data(year: int, month: int) -> pd.DataFrame:
    filename = WEATHER_FILE_PATTERN.format(year=year, month=month)
    if DATA_SOURCE == "local":
        path = WEATHER_DATA_PATH / filename
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    else:
        try:
            client = _get_s3_client()
            obj = client.get_object(Bucket=ALLAS_WEATHER_BUCKET, Key=filename)
            df = pd.read_csv(io.BytesIO(obj["Body"].read()))
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
        except Exception as e:
            st.error(f"Could not load weather data from Allas: {e}")
            return pd.DataFrame()


@st.cache_data
def load_matched_data(year: int, month: int) -> pd.DataFrame:
    path = MATCHED_DATA_PATH / MATCHED_FILE_PATTERN.format(year=year, month=month)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(
        path,
        parse_dates=["scheduledTime", "actualTime", "departureDate", "timetableAcceptanceDate"],
        low_memory=False,
    )


@st.cache_data
def load_train_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_train_stations.csv")


@st.cache_data
def load_ems_stations() -> pd.DataFrame:
    return pd.read_csv(METADATA_PATH / "metadata_fmi_ems_stations.csv")
