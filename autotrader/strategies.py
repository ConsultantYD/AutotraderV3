from __future__ import absolute_import, division, print_function, unicode_literals

import uuid

import backtrader as bt
from autotrader.events import (
    BuyOrderExecution,
    BuyOrderRejection,
    BuyOrderSubmission,
    NoAction,
    SellOrderExecution,
    SellOrderRejection,
    SellOrderSubmission,
)


class BaseStrategy(bt.Strategy):
    def __init__(self):
        self.data_log = []  # To store data logs
        self.event_log = []  # To store events
        self.dataclose = self.datas[0].close
        self.order = None
        self.current_submission_id = None  # Track submission IDs

    @classmethod
    def get_hyperparam_space(cls):
        """
        Define the hyperparameter optimization space for the strategy.

        Returns:
            dict: A dictionary of hyperparameters with their optimization ranges.
                  Each hyperparameter should have a type (int, float, categorical)
                  and optimization bounds or choices.

        Example return format:
        {
            'bb_period': {'type': 'int', 'min': 10, 'max': 50},
            'devfactor': {'type': 'float', 'min': 1.0, 'max': 3.0},
        }
        """
        raise NotImplementedError(
            "Subclasses must implement the get_hyperparam_space method."
        )

    def log(self, txt, dt=None):
        """Log messages with timestamps."""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def notify_order(self, order):
        """Handle order notifications and track submission IDs."""
        order_submission_time = self.datas[0].datetime.datetime(0)

        if not hasattr(order, "submission_id"):
            order.submission_id = (
                self.current_submission_id
            )  # Use the current_submission_id

        if order.status == order.Completed:
            execution_time = self.datas[0].datetime.datetime(0)
            if order.isbuy():
                self.event_log.append(
                    BuyOrderExecution(
                        timestamp=execution_time,
                        submission_id=order.submission_id,
                        ref_price=order.executed.price,
                        size=order.executed.size,
                    )
                )
            elif order.issell():
                self.event_log.append(
                    SellOrderExecution(
                        timestamp=execution_time,
                        submission_id=order.submission_id,
                        ref_price=order.executed.price,
                        size=order.executed.size,
                    )
                )
                # Reset the submission_id only after sell execution
                self.current_submission_id = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            justification = (
                "Order rejected due to insufficient margin."
                if order.status == order.Margin
                else "Order canceled."
            )
            if order.isbuy():
                self.event_log.append(
                    BuyOrderRejection(
                        timestamp=order_submission_time,
                        submission_id=order.submission_id,
                        justification=justification,
                    )
                )
            elif order.issell():
                self.event_log.append(
                    SellOrderRejection(
                        timestamp=order_submission_time,
                        submission_id=order.submission_id,
                        justification=justification,
                    )
                )

        self.order = None

    def next(self):
        """Core strategy logic. Calls buy/sell condition handlers and logs data."""
        self.data_log.append(
            {
                "timestamp": self.datas[0].datetime.datetime(0),
                "open": self.datas[0].open[0],
                "high": self.datas[0].high[0],
                "low": self.datas[0].low[0],
                "close": self.datas[0].close[0],
                "volume": self.datas[0].volume[0],
            }
        )

        if self.order:
            return

        # Call the child class methods for buy/sell conditions
        buy_signal, buy_justification = self.should_buy()
        sell_signal, sell_justification = self.should_sell()

        if not self.position and buy_signal:
            self.current_submission_id = (
                uuid.uuid4().int
            )  # Generate submission_id for BuyOrderSubmission
            self.order = self.buy()
            self.order.submission_id = self.current_submission_id
            self.event_log.append(
                BuyOrderSubmission(
                    timestamp=self.datas[0].datetime.datetime(0),
                    submission_id=self.current_submission_id,
                    size=self.order.created.size,
                    ref_price=self.dataclose[0],
                    justification=buy_justification,
                )
            )
        elif self.position and sell_signal:
            if self.current_submission_id is None:
                raise ValueError("Submission ID is missing for SellOrderSubmission.")

            self.order = self.sell()
            self.order.submission_id = self.current_submission_id
            self.event_log.append(
                SellOrderSubmission(
                    timestamp=self.datas[0].datetime.datetime(0),
                    submission_id=self.current_submission_id,
                    size=self.order.created.size,
                    ref_price=self.dataclose[0],
                    justification=sell_justification,
                )
            )
        else:
            # Log NoAction if no conditions are met
            self.event_log.append(
                NoAction(timestamp=self.datas[0].datetime.datetime(0))
            )

    def should_buy(self):
        """Child classes should override to define buy logic. Returns (bool, justification)."""
        raise NotImplementedError(
            "Please implement the buy condition in the child class."
        )

    def should_sell(self):
        """Child classes should override to define sell logic. Returns (bool, justification)."""
        raise NotImplementedError(
            "Please implement the sell condition in the child class."
        )


class DemoStrategy(BaseStrategy):
    def should_buy(self):
        """Define the buy condition: price above SMA."""
        return self.dataclose[0] > self.sma[0], None

    def should_sell(self):
        """Define the sell condition: price below SMA."""
        return self.dataclose[0] < self.sma[0], None


class MeanReversionStrategy(BaseStrategy):
    params = (
        ("bb_period", 20),  # Bollinger Bands period
        ("devfactor", 2.0),  # Standard deviation factor
        ("stop_loss_pct", 0.01),  # Stop-loss percentage (1%)
        ("take_profit_pct", 0.02),  # Take-profit percentage (2%)
    )

    def __init__(self):
        super().__init__()
        self.bb = bt.indicators.BollingerBands(
            period=self.params.bb_period, devfactor=self.params.devfactor
        )
        self.entry_price = None

    @classmethod
    def get_hyperparam_space(cls):
        return {
            "bb_period": {"type": "int", "min": 1, "max": 500},
            "devfactor": {"type": "float", "min": 1, "max": 4.0},
            "stop_loss_pct": {"type": "float", "min": 0.0001, "max": 0.15},
            "take_profit_pct": {"type": "float", "min": 0.0001, "max": 0.15},
        }

    def should_buy(self):
        """Buy when the price crosses below the lower Bollinger Band."""
        if self.dataclose[0] < self.bb.lines.bot[0]:
            justification = f"Price {self.dataclose[0]:.2f} below lower BB {self.bb.lines.bot[0]:.2f}"
            return True, justification
        return False, None

    def should_sell(self):
        """Sell when the price crosses above the upper Bollinger Band or hit stop-loss/take-profit."""
        if self.dataclose[0] > self.bb.lines.top[0]:
            justification = f"Price {self.dataclose[0]:.2f} above upper BB {self.bb.lines.top[0]:.2f}"
            return True, justification

        # Stop-loss condition
        if self.entry_price and self.dataclose[0] <= self.entry_price * (
            1 - self.params.stop_loss_pct
        ):
            justification = f"Price {self.dataclose[0]:.2f} hit stop-loss at {self.entry_price * (1 - self.params.stop_loss_pct):.2f}"
            return True, justification

        # Take-profit condition
        if self.entry_price and self.dataclose[0] >= self.entry_price * (
            1 + self.params.take_profit_pct
        ):
            justification = f"Price {self.dataclose[0]:.2f} hit take-profit at {self.entry_price * (1 + self.params.take_profit_pct):.2f}"
            return True, justification

        return False, None

    def notify_order(self, order):
        super().notify_order(order)

        # Track entry price on a completed buy order
        if order.status == order.Completed and order.isbuy():
            self.entry_price = order.executed.price

        # Reset entry price on a completed sell order
        if order.status == order.Completed and order.issell():
            self.entry_price = None
