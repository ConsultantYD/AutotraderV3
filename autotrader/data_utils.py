import datetime as dt
from typing import Any

import backtrader as bt
import pandas as pd
import yfinance as yf

from autotrader.constants import ISO_DATETIME_FORMAT
from autotrader.schemas import DataConfig


class Dataset:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __call__(self):
        return self.df

    @classmethod
    def from_config(cls, config: DataConfig):
        start_datetime = dt.datetime.strptime(config.start_date, ISO_DATETIME_FORMAT)
        end_datetime = dt.datetime.strptime(config.end_date, ISO_DATETIME_FORMAT)
        match config.source:
            case "yahoo":
                return cls.from_yahoo(
                    tickers=config.ticker,
                    start=start_datetime,
                    end=end_datetime,
                    interval=config.interval,
                    keepna=False,
                )
            case _:
                raise NotImplementedError(
                    f"Data source '{config.source}' is not supported."
                )

    @classmethod
    def from_yahoo(cls, **kwargs):
        data = yf.download(**kwargs)

        # Sanitize to match standardized format
        data = data.drop(columns=["Adj Close"])  # Drop unused column
        data.columns = data.columns.droplevel(1)  # Drop multi-level column index
        data = data.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

        return cls(df=data)

    def to_backtrader_feed(self):
        return bt.feeds.PandasData(dataname=self.df)


def convert_event_logs_to_tidy(event_logs: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Converts raw data and event logs into tidy datasets for analysis.

    Args:
        data_logs (List[Dict[str, Any]]): A list of data log entries (raw format).
        event_logs (List[Dict[str, Any]]): A list of event log entries (raw format).

    Returns:
        Dict[str, pd.DataFrame]: A dictionary with tidy DataFrames for `data` and `events`.
    """

    # Convert event logs to tidy dataset
    event_records = []
    for event in event_logs:
        event_data = event.model_dump()
        event_data["event_type"] = event.__class__.__name__
        event_records.append(event_data)

    return pd.DataFrame(event_records)
