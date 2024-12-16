import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_backtest_results(results, dataset, use_candlestick=False):
    """
    Produce a Plotly figure with three vertical subplots:
      1. Top subplot (row=1): Bar chart of trade PnL upon close.
      2. Middle subplot (row=2): Waterfall chart of cumulative PnL over time.
      3. Bottom subplot (row=3): Either a candlestick chart of OHLC or a line chart of close prices.
         - If line chart, no linear interpolation between days (each day is a separate trace).

    Args:
        results (dict): The dictionary returned by run_coarse_backtest.
        dataset (Dataset): The dataset object containing the price DataFrame.
        use_candlestick (bool): If True, plot a candlestick chart. Otherwise, plot a line chart.
    """
    trades = results["analysis_results"]["trades_list"]
    if not trades:
        raise ValueError("No trades found in the results.")

    # Sort trades by close time to ensure chronological order
    trades = sorted(trades, key=lambda t: t["close_datetime"])

    # Extract open, close datetimes, and pnls in sorted order
    open_datetimes = [t["open_datetime"].replace(tzinfo=None) for t in trades]
    close_datetimes = [t["close_datetime"].replace(tzinfo=None) for t in trades]
    pnls = [t["pnl"] for t in trades]

    df = dataset.df.copy().sort_index()
    # Ensure DataFrame index is timezone naive if needed
    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)

    # Helper function to get closest price for a given datetime
    def get_closest_price(dt):
        if dt in df.index:
            return df.loc[dt, "close"]
        pos = df.index.get_indexer([dt], method="nearest")
        idx = pos[0]
        return df.iloc[idx]["close"]

    # Get open/close prices of trades
    open_prices = [get_closest_price(dt) for dt in open_datetimes]
    close_prices = [get_closest_price(dt) for dt in close_datetimes]

    # Separate trades into winners and losers
    positive_mask = [p >= 0 for p in pnls]
    negative_mask = [p < 0 for p in pnls]

    positive_x = [close_datetimes[i] for i, val in enumerate(positive_mask) if val]
    positive_y = [pnls[i] for i, val in enumerate(positive_mask) if val]

    negative_x = [close_datetimes[i] for i, val in enumerate(negative_mask) if val]
    negative_y = [pnls[i] for i, val in enumerate(negative_mask) if val]

    # Create subplots with the new order:
    # Row 1: Waterfall chart (cumulative PnL)
    # Row 2: Trade PnL bars
    # Row 3: Price chart
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.15, 0.15, 0.7],
        vertical_spacing=0.01,
    )

    # Middle subplot (Row 1): Waterfall cumulative PnL
    fig.add_trace(
        go.Waterfall(
            x=close_datetimes,
            y=pnls,
            measure=["relative"] * len(pnls),
            name="Cumulative Cashflow",
            increasing={"marker": {"color": "green"}},
            decreasing={"marker": {"color": "red"}},
            totals={"marker": {"color": "blue"}},
            # Make line grey
            connector={"line": {"color": "gray"}},
        ),
        row=1,
        col=1,
    )

    # Row 2: Trade PnL as markers
    fig.add_trace(
        go.Scatter(
            x=positive_x,
            y=positive_y,
            mode="markers",
            name="Profitable Trades",
            marker=dict(
                symbol="circle",
                color="green",
                size=8,
                # line=dict(width=0.5, color="black"),
            ),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=negative_x,
            y=negative_y,
            mode="markers",
            name="Losing Trades",
            marker=dict(
                symbol="circle",
                color="red",
                size=8,
                # line=dict(width=0.5, color="black"),
            ),
        ),
        row=2,
        col=1,
    )

    # Add vertical lines ("lollipop" sticks) for each point
    # Note: We use xref='x2', yref='y2' to reference the second subplot's axes.
    for px, py in zip(positive_x, positive_y):
        fig.add_shape(
            type="line",
            x0=px,
            x1=px,
            y0=0,
            y1=py,
            line=dict(color="green", width=2),
            xref="x2",
            yref="y2",
        )

    for nx, ny in zip(negative_x, negative_y):
        fig.add_shape(
            type="line",
            x0=nx,
            x1=nx,
            y0=0,
            y1=ny,
            line=dict(color="red", width=2),
            xref="x2",
            yref="y2",
        )

    # Bottom subplot (Row 3): Price chart
    if use_candlestick:
        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(df.columns):
            raise ValueError(
                "DataFrame must contain 'open', 'high', 'low', 'close' for candlestick plot."
            )
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="OHLC",
            ),
            row=3,
            col=1,
        )
    else:
        # Plot each day as a separate trace to avoid continuous line across days
        df["date"] = df.index.date
        for d, day_df in df.groupby("date"):
            fig.add_trace(
                go.Scatter(
                    x=day_df.index,
                    y=day_df["close"],
                    mode="lines+markers",
                    line_color="black",
                    name="Close Price",
                    # Make markers small
                    marker=dict(size=2),
                    connectgaps=False,
                    showlegend=False,  # Avoid repeating legend entries
                ),
                row=3,
                col=1,
            )

    # Add trade open/close markers on the price chart (bottom subplot)
    fig.add_trace(
        go.Scatter(
            x=open_datetimes,
            y=open_prices,
            mode="markers",
            name="Trade Open",
            marker_symbol="triangle-up",
            marker_color="green",
            marker_size=15,
        ),
        row=3,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=close_datetimes,
            y=close_prices,
            mode="markers",
            name="Trade Close",
            marker_symbol="triangle-down",
            marker_color="red",
            marker_size=15,
        ),
        row=3,
        col=1,
    )

    # Update layout for a clean white background figure
    fig.update_layout(
        template="plotly_white",
        # title="Backtest Results",
        # legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="right", x=1),
        # margin=dict(l=50, r=50, t=50, b=50),
    )

    # Update axes labels
    fig.update_yaxes(title_text="Cumulative PnL", row=1, col=1)
    fig.update_yaxes(title_text="Trades PnL", row=2, col=1)
    fig.update_yaxes(title_text="Price", row=3, col=1)

    # Make grid lines visible
    fig.update_xaxes(zeroline=True)
    fig.update_yaxes(showgrid=True, row=1, col=1)
    fig.update_yaxes(showgrid=False, row=2, col=1)

    fig.update_xaxes(showgrid=False, row=3, col=1)
    fig.update_yaxes(showgrid=False, row=3, col=1)

    return fig
