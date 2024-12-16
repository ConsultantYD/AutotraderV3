from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Any

import backtrader as bt
from autotrader.data_utils import Dataset
from autotrader.schemas import BacktestConfig

import matplotlib.pyplot as plt


class TradesListAnalyzer(bt.Analyzer):
    def __init__(self):
        self.trades = []

    def notify_trade(self, trade):
        if trade.isclosed:
            # Extract open and close events from the trade history
            open_event = None
            close_event = None

            for evt in trade.history:
                # evt = (event_name, bar, size, price, value, pnl, pnlcomm)
                if evt[0] == "OPEN":
                    open_event = evt
                elif evt[0] == "CLOSE":
                    close_event = evt

            # Convert numeric datetimes to Python datetime objects
            open_dt = (
                trade.data.num2date(trade.dtopen) if trade.dtopen is not None else None
            )
            close_dt = (
                trade.data.num2date(trade.dtclose)
                if trade.dtclose is not None
                else None
            )

            # Append the detailed trade info as a dict
            self.trades.append(
                {
                    "open_datetime": open_dt,
                    "close_datetime": close_dt,
                    "pnl": trade.pnl,
                }
            )

    def get_analysis(self):
        return self.trades


def run_coarse_backtest(
    backtest_config: BacktestConfig,
    dataset: Dataset,
    strategy_class: type[bt.Strategy],
    strategy_params: dict = None,
) -> dict[str, Any]:
    """
    Run a backtest with the specified strategy and configuration.

    By default, this function also adds several analyzers to provide a richer
    set of metrics.

    Args:
        strategy_class (type[bt.Strategy]): The strategy class to backtest
        data_config (DataConfig): Configuration for data sourcing
        backtest_config (BacktestConfig): Configuration for the backtest
        strategy_params (dict, optional): Additional strategy parameters

    Returns:
        The output strategy after backtest
    """
    # Initialize cerebro and define internal components
    cerebro = bt.Cerebro()
    data_feed = dataset.to_backtrader_feed()
    cerebro.adddata(data_feed)

    # Configure strategy with additional parameters if provided
    if strategy_params:
        cerebro.addstrategy(strategy_class, **strategy_params)
    else:
        cerebro.addstrategy(strategy_class)

    # Set broker parameters
    cerebro.broker.setcommission(commission=backtest_config.commission)
    cerebro.broker.setcash(backtest_config.cash)
    cerebro.addsizer(bt.sizers.FixedSize, stake=backtest_config.stake)

    # Add Backtrader analyzers
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        _name="sharpe",
        timeframe=bt.TimeFrame.Days,
        annualize=True,
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
    cerebro.addanalyzer(bt.analyzers.Transactions, _name="transactions")
    cerebro.addanalyzer(bt.analyzers.PositionsValue, _name="positionsvalue")
    cerebro.addanalyzer(TradesListAnalyzer, _name="trades_list")

    # Run the backtest
    initial_portfolio = cerebro.broker.getvalue()
    strategies = cerebro.run()
    output_strategy = strategies[0]
    final_portfolio = cerebro.broker.getvalue()

    # Extract analyzer data
    analyzers = output_strategy.analyzers
    analysis_results = {
        "sharpe": analyzers.sharpe.get_analysis(),
        "drawdown": analyzers.drawdown.get_analysis(),
        "returns": analyzers.returns.get_analysis(),
        "trades_summary": analyzers.trades.get_analysis(),
        "sqn": analyzers.sqn.get_analysis(),
        "timereturn": analyzers.timereturn.get_analysis(),
        "transactions": analyzers.transactions.get_analysis(),
        "positionsvalue": analyzers.positionsvalue.get_analysis(),
        "trades_list": analyzers.trades_list.get_analysis(),
    }

    # Create portfolio information dictionary
    portfolio_info = {
        "initial_portfolio": initial_portfolio,
        "final_portfolio": final_portfolio,
    }

    # Create output dictionary
    output = {
        "output_strategy": output_strategy,
        "portfolio_info": portfolio_info,
        "analysis_results": analysis_results,
    }

    return output
