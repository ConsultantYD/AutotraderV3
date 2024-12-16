import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from optuna.visualization import (
    plot_contour,
    plot_edf,
    plot_optimization_history,
    plot_parallel_coordinate,
    plot_param_importances,
    plot_rank,
    plot_slice,
    plot_timeline,
)


pio.templates.default = "plotly_white"


def get_optuna_study_figures() -> dict[str, callable]:
    fig_list = {
        "Optimization Performance History": plot_optimization_history,
        "Parameters Importance": plot_param_importances,
        "Parameters Relationship Contour": plot_contour,
        "Parameters Relationship Slice": plot_slice,
        "Parameters Parallel Coordinates": plot_parallel_coordinate,
        "Parameters Relationship Rank": plot_rank,
        "Empirical Distribution Function": plot_edf,
        "Timeline": plot_timeline,
    }
    return fig_list


def plot_trade_events_timeline(event_logs: pd.DataFrame) -> go.Figure:
    """
    Create a comprehensive timeline of trading events with detailed annotations.

    Args:
        event_logs (pd.DataFrame): Tidy dataframe of trading events

    Returns:
        go.Figure: Plotly figure showing trade event timeline
    """
    # Filter and prepare specific event types
    buy_submissions = event_logs[event_logs["event_type"] == "BuyOrderSubmission"]
    buy_executions = event_logs[event_logs["event_type"] == "BuyOrderExecution"]
    sell_submissions = event_logs[event_logs["event_type"] == "SellOrderSubmission"]
    sell_executions = event_logs[event_logs["event_type"] == "SellOrderExecution"]

    # Create figure
    fig = go.Figure()

    # Add buy events
    fig.add_trace(
        go.Scatter(
            x=buy_submissions["timestamp"],
            y=[1] * len(buy_submissions),
            mode="markers",
            name="Buy Submissions",
            marker=dict(
                color="green",
                symbol="triangle-up",
                size=10,
                line=dict(width=2, color="darkgreen"),
            ),
            hovertemplate="Buy Submission<br>Timestamp: %{x}<br>Price: %{customdata[0]:.2f}<extra></extra>",
            customdata=buy_submissions[["ref_price"]].values,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=buy_executions["timestamp"],
            y=[1.1] * len(buy_executions),
            mode="markers",
            name="Buy Executions",
            marker=dict(
                color="lime",
                symbol="circle",
                size=10,
                line=dict(width=2, color="green"),
            ),
            hovertemplate="Buy Execution<br>Timestamp: %{x}<br>Price: %{customdata[0]:.2f}<br>Size: %{customdata[1]}<extra></extra>",
            customdata=buy_executions[["ref_price", "size"]].values,
        )
    )

    # Add sell events
    fig.add_trace(
        go.Scatter(
            x=sell_submissions["timestamp"],
            y=[0.9] * len(sell_submissions),
            mode="markers",
            name="Sell Submissions",
            marker=dict(
                color="red",
                symbol="triangle-down",
                size=10,
                line=dict(width=2, color="darkred"),
            ),
            hovertemplate="Sell Submission<br>Timestamp: %{x}<br>Price: %{customdata[0]:.2f}<extra></extra>",
            customdata=sell_submissions[["ref_price"]].values,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=sell_executions["timestamp"],
            y=[0.8] * len(sell_executions),
            mode="markers",
            name="Sell Executions",
            marker=dict(
                color="salmon",
                symbol="circle",
                size=10,
                line=dict(width=2, color="red"),
            ),
            hovertemplate="Sell Execution<br>Timestamp: %{x}<br>Price: %{customdata[0]:.2f}<br>Size: %{customdata[1]}<extra></extra>",
            customdata=sell_executions[["ref_price", "size"]].values,
        )
    )

    # Customize layout
    fig.update_layout(
        title="Trading Events Timeline",
        xaxis_title="Timestamp",
        yaxis_title="Event Type",
        height=600,
        width=1200,
        legend_title_text="Event Categories",
        yaxis=dict(
            tickmode="array",
            tickvals=[0.8, 1, 1.1],
            ticktext=["Sell Executions", "Buy Submissions", "Buy Executions"],
        ),
    )

    return fig


def plot_price_with_trade_annotations(
    data_logs: pd.DataFrame, event_logs: pd.DataFrame
) -> go.Figure:
    """
    Create a price chart with trade annotations.

    Args:
        data_logs (pd.DataFrame): Dataframe with price and volume data
        event_logs (pd.DataFrame): Dataframe with trading events

    Returns:
        go.Figure: Plotly figure showing price with trade markers
    """
    # Create candlestick chart
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=data_logs["timestamp"],
                open=data_logs["open"],
                high=data_logs["high"],
                low=data_logs["low"],
                close=data_logs["close"],
                name="Price",
            )
        ]
    )

    # Filter buy and sell events
    buy_executions = event_logs[event_logs["event_type"] == "BuyOrderExecution"]
    sell_executions = event_logs[event_logs["event_type"] == "SellOrderExecution"]

    # Add buy markers
    fig.add_trace(
        go.Scatter(
            x=buy_executions["timestamp"],
            y=buy_executions["ref_price"],
            mode="markers",
            name="Buy Trades",
            marker=dict(
                color="green",
                symbol="triangle-up",
                size=10,
                line=dict(width=2, color="darkgreen"),
            ),
            hovertemplate="Buy Trade<br>Timestamp: %{x}<br>Price: %{y:.2f}<br>Size: %{customdata}<extra></extra>",
            customdata=buy_executions["size"],
        )
    )

    # Add sell markers
    fig.add_trace(
        go.Scatter(
            x=sell_executions["timestamp"],
            y=sell_executions["ref_price"],
            mode="markers",
            name="Sell Trades",
            marker=dict(
                color="red",
                symbol="triangle-down",
                size=10,
                line=dict(width=2, color="darkred"),
            ),
            hovertemplate="Sell Trade<br>Timestamp: %{x}<br>Price: %{y:.2f}<br>Size: %{customdata}<extra></extra>",
            customdata=sell_executions["size"],
        )
    )

    # Customize layout
    fig.update_layout(
        title="Price Chart with Trade Executions",
        xaxis_title="Timestamp",
        yaxis_title="Price",
        height=800,
        width=1400,
        legend_title_text="Price and Trades",
    )

    return fig


def plot_trade_events_timeline_new(event_logs: pd.DataFrame) -> go.Figure:
    """
    Create a comprehensive timeline of trading events.
    Args:
        event_logs (pd.DataFrame): A dataframe containing event logs with timestamps and event descriptions.
    Returns:
        go.Figure: Plotly figure object.
    """
    new_event_logs = event_logs.copy()[event_logs["event_type"] != "NoAction"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=new_event_logs["timestamp"],
            y=new_event_logs["event_type"],
            mode="markers",
            marker=dict(size=10),
            text=new_event_logs["justification"],
            name="Event",
        )
    )
    fig.update_layout(
        title="Event Timeline",
        xaxis_title="Timestamp",
        yaxis_title="Event Type",
        hovermode="closest",
        showlegend=True,
    )
    return fig


def plot_data_distribution(data_logs: pd.DataFrame) -> go.Figure:
    """
    Visualize the distribution of key numerical fields in the data logs.
    Args:
        data_logs (pd.DataFrame): A dataframe containing data logs with numerical fields.
    Returns:
        go.Figure: Plotly figure object.
    """
    sanitized_data_logs = data_logs.copy()[["open", "high", "low", "close"]]
    fig = go.Figure()
    for column in sanitized_data_logs.select_dtypes(include=["number"]).columns:
        fig.add_trace(go.Box(y=data_logs[column], name=column, boxmean="sd"))
    fig.update_layout(
        title="Data Distribution",
        yaxis_title="Values",
        xaxis_title="Metrics",
        showlegend=False,
    )
    return fig


def plot_all_performance_plots(
    data_logs: pd.DataFrame,
    event_logs: pd.DataFrame,
) -> dict[str, go.Figure]:
    """
    Generate a dictionary of performance plots for the given data and event logs.
    Args:
        data_logs (pd.DataFrame): A dataframe containing data logs.
        event_logs (pd.DataFrame): A dataframe containing event logs.
        initial_portfolio (float): The initial portfolio value.
        final_portfolio (float): The final portfolio value.
    Returns:
        dict: A dictionary of Plotly figures.
    """
    # Generate performance plots
    trade_events_timeline = plot_trade_events_timeline(event_logs)
    price_with_trade_annotations = plot_price_with_trade_annotations(
        data_logs, event_logs
    )
    trade_events_timeline_new = plot_trade_events_timeline_new(event_logs)
    data_distribution = plot_data_distribution(data_logs)

    # Create a dictionary of performance plots
    performance_plots = {
        "Trade Events Timeline": trade_events_timeline,
        "Price with Trade Annotations": price_with_trade_annotations,
        "Trade Events Timeline New": trade_events_timeline_new,
        "Data Distribution": data_distribution,
    }

    return performance_plots
