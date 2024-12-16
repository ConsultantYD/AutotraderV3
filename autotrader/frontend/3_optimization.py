import pandas as pd
import uuid
from autotrader.optimization import optimize_strategy_params_on_backtest
from autotrader.schemas import BacktestConfig, DataConfig
from autotrader.strategies import MeanReversionStrategy
from autotrader.visualization_utils import (
    get_optuna_study_figures,
    plot_all_performance_plots,
)
from autotrader.constants import ISO_DATETIME_FORMAT
import datetime as dt
import streamlit as st

st.header("🧬 Strategy Optimization")

if "strategies" not in st.session_state:
    st.session_state.strategies = {}

col00, _ = st.columns(2)

study_name = col00.text_input("**Study Name:** ")


st.write("#### Data & Timeframe")
##########################################################################
# - DATA CONFIGURATION -#
##########################################################################

if "def_ticker_value" not in st.session_state:
    st.session_state.def_ticker_value = "MSFT"

# Create an ss variable as key of dataframe.
if "dfk" not in st.session_state:
    st.session_state.dfk = str(uuid.uuid4())


def execute_cb():
    """Change the dataframe key.

    This is called when the button with execute label
    is clicked. The dataframe key is changed to unselect rows on it.
    """
    st.session_state.dfk = str(uuid.uuid4())


@st.dialog("Available Stocks", width="large")
def show_available_stocks_df():
    stocks_df = pd.read_csv("stock_symbols.csv")
    stocks_df.set_index("SYMBOL", inplace=True)

    industries = stocks_df["INDUSTRY "].unique()
    industries.sort()
    filtered_industries = st.multiselect("Filter Industries", industries)

    # No filters = show nothing
    if not filtered_industries:
        filtered_industries = industries

    filtered_stocks_df = stocks_df[stocks_df["INDUSTRY "].isin(filtered_industries)]

    event = st.dataframe(
        filtered_stocks_df,
        use_container_width=True,
        selection_mode=["single-row"],
        on_select="rerun",
        key=st.session_state.dfk,
    )

    if len(event.selection["rows"]) > 0:
        selected_row = event.selection["rows"][0]
        row = filtered_stocks_df.iloc[selected_row : selected_row + 1, :]
        print(len(event.selection["rows"]), row.index[0])
        st.session_state.def_ticker_value = row.index[0]
        execute_cb()
        st.rerun()


col11, col12, col13 = st.columns(3, vertical_alignment="bottom")

yesterday = (dt.datetime.today() - dt.timedelta(days=1)).date()
seven_days_ago = (dt.datetime.today() - dt.timedelta(days=7)).date()

source = col11.selectbox("Data Source", ["yahoo"])
ticker = col12.text_input(
    "Ticker", value=st.session_state.def_ticker_value, max_chars=10
)
if col13.button("Browse ..."):
    show_available_stocks_df()

col11, col12, col13 = st.columns(3, vertical_alignment="top")

start_date = col11.date_input(
    "Start Date", value=seven_days_ago, max_value=yesterday - dt.timedelta(days=1)
)
end_date = col12.date_input("End Date", value=yesterday, max_value=yesterday)
interval = col13.pills("Interval", ["1m", "5m", "15m", "1h"], default="1m")

start_datetime = dt.datetime.combine(start_date, dt.datetime.min.time())
end_datetime = dt.datetime.combine(end_date, dt.datetime.min.time())

# Configuration
data_config = DataConfig(
    source=source,
    ticker=ticker,
    start_date=start_datetime.strftime(ISO_DATETIME_FORMAT),
    end_date=end_datetime.strftime(ISO_DATETIME_FORMAT),
    interval=interval,
)

##########################################################################
# - BACKTEST CONFIGURATION -#
##########################################################################

st.write("#### Portfolio & Trading")
col31, col32, col33, col34 = st.columns((3, 3, 3, 4))

cash = col31.number_input("Initial Cash", value=100000.0, min_value=1000.0)
commission = col32.number_input("Commission", value=0.0, min_value=0.0, step=0.001)
stake = col33.number_input("Stake", value=1, min_value=1)
strategy = col34.selectbox("Strategy", ["Mean Reversion"])

if (
    st.button("Launch Optimization", type="primary", disabled=study_name == "")
    and study_name != ""
    and study_name not in st.session_state.strategies
):
    st.divider()
    backtest_config = BacktestConfig(
        data_config=data_config, cash=cash, commission=commission, stake=stake
    )

    st.session_state.n_trials = 100
    st.session_state.opt_progress = 0.0
    st.session_state.prog_bar = st.progress(
        st.session_state.opt_progress, text="Starting trials ..."
    )
    st.session_state.best_value = st.empty()

    def progress_callback(study, frozen_trial):
        st.session_state.opt_progress = frozen_trial.number / st.session_state.n_trials
        perc_progress = round(st.session_state.opt_progress * 100, 1)
        st.session_state.prog_bar.progress(
            st.session_state.opt_progress, text=str(perc_progress) + "%"
        )
        st.session_state.best_value.write(
            f"Best trial revenue: :green[{round(study.best_value, 2)}]$"
        )

    # Optimize strategy parameters
    optimization_results = optimize_strategy_params_on_backtest(
        data_config,
        backtest_config,
        MeanReversionStrategy,
        n_trials=st.session_state.n_trials,
        optuna_callback=progress_callback,
    )

    st.session_state.prog_bar.progress(1.0, text="Completed")

    st.session_state.strategies[study_name] = optimization_results
elif study_name in st.session_state.strategies:
    optimization_results = st.session_state.strategies[study_name]

else:
    optimization_results = None

if optimization_results is not None:
    # Unpack results
    study = optimization_results["study"]
    trial_details = optimization_results["trial_details"]
    results_df = optimization_results["results_df"]

    st.write("##### ")
    st.write("##### 📖 Experiments Overview")
    top_trials = results_df.nlargest(len(results_df), "portfolio_return")
    st.dataframe(top_trials[["portfolio_return", "params"]], use_container_width=True)

    st.write("##### 🧪 Detailed Experiment Details")
    # Print best results
    best_params = study.best_params
    best_value = study.best_value
    best_trial = study.best_trial
    print(f"Best parameters: {best_params}")
    print(f"Best portfolio return: {best_value}")

    # Visualize top trial performance
    best_trial_idx = top_trials.index[0]
    portfolio_figures = plot_all_performance_plots(
        event_logs=trial_details["event_logs_df"][best_trial_idx],
        data_logs=trial_details["data_logs_df"][best_trial_idx],
    )
    for fig_name, fig in portfolio_figures.items():
        st.plotly_chart(fig)

    # Visualize Optuna study results
    fig_dict = get_optuna_study_figures()
    for fig_name, fig_maker in fig_dict.items():
        fig = fig_maker(study)
        st.plotly_chart(fig)
