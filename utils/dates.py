import pandas as pd


def to_utc(series):
    return pd.to_datetime(
        series,
        utc=True,
        errors="coerce",
    )
