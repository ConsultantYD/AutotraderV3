import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from autotrader.constants import ISO_DATETIME_FORMAT


class BaseSchema(BaseModel):
    ConfigDict(validate_assignment=True, populate_by_name=True)


class DataConfig(BaseSchema):
    source: Literal["yahoo"]
    ticker: str
    start_date: str
    end_date: str
    interval: Literal["1m", "5m", "15m", "30m", "1h", "1d"]

    @field_validator("start_date", "end_date", mode="before")
    def check_value(cls, value: str) -> str:
        # Validate start_date and end_date are datetime-compatible
        try:
            # Attempt to parse the date string
            dt.datetime.strptime(value, ISO_DATETIME_FORMAT)
        except ValueError as e:
            err_msg = f"Date '{value}' is not in the correct format."
            raise ValueError(err_msg) from e
        return value


class BacktestConfig(BaseSchema):
    data_config: DataConfig
    cash: float = 10000.0
    commission: float = 0.0
    stake: int = 1
