import datetime as dt
from typing import Any

from autotrader.schemas import BaseSchema


class Event(BaseSchema):
    timestamp: dt.datetime

    # Return class name, datetime as isoformat, and print all attributes (except datetime) with their names
    def __str__(self):
        attributes = ", ".join(
            f"{key}={value}"
            for key, value in self.model_dump().items()
            if key != "timestamp"
        )
        attributes = ", ".join(sorted(attributes.split(", ")))
        return (
            f"{self.__class__.__name__}(t={self.timestamp.isoformat()}, {attributes})"
        )


class Action(Event):
    justification: None | Any = None


class NoAction(Action): ...


class Order(Action):
    submission_id: int
    size: int
    ref_price: float


class BuyOrderSubmission(Order): ...


class SellOrderSubmission(Order): ...


class BuyOrderExecution(Order): ...


class SellOrderExecution(Order): ...


class BuyOrderRejection(Event):
    submission_id: int
    justification: None | Any = None


class SellOrderRejection(Event):
    submission_id: int
    justification: None | Any = None
