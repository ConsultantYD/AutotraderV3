from optimization import optimize_strategy_params_on_backtest
from schemas import BacktestConfig, DataConfig
from strategies import MeanReversionStrategy
from visualization_utils import (
    get_optuna_study_figures,
    plot_all_performance_plots,
)
from autotrader.backtesting import run_coarse_backtest
from autotrader.data_utils import Dataset
from autotrader.visualization_backtesting import plot_backtest_results

# Configuration
data_config = DataConfig(
    source="yahoo",
    ticker="BTC-USD",
    start_date="2024-12-01T00:00:00",
    end_date="2024-12-08T00:00:00",
    interval="1m",
)
backtest_config = BacktestConfig(
    data_config=data_config, cash=1000000.0, commission=0.0, stake=1
)

# ------------------------------------------------------------
# CASE 1: Run single backtest
# ------------------------------------------------------------
dataset = Dataset.from_config(data_config)
strategy_params = {
    "bb_period": 82,
    "devfactor": 1.8398294282578231,
    "stop_loss_pct": 0.14999999999999997,
    "take_profit_pct": 0.15,
}
backtest_output = run_coarse_backtest(
    backtest_config, dataset, MeanReversionStrategy, strategy_params
)

for k, v in backtest_output["analysis_results"].items():
    print(k)
    if isinstance(v, dict):
        for k2, v2 in v.items():
            print()
            print("    ", k2)
            print("    ", v2)
            print("     -------------------")
    else:
        print(v)
    print("*" * 50)
    print("\n")

# ------------------------------------------------------------
# CASE 2: Run multiple backtest with additional strategy parameters
# ------------------------------------------------------------
# Optimize strategy parameters
optimization_results = optimize_strategy_params_on_backtest(
    data_config, backtest_config, MeanReversionStrategy, n_trials=1000
)

# Unpack results
study = optimization_results["study"]
trial_details = optimization_results["trial_details"]
results_df = optimization_results["results_df"]

print("Trial details")
print(trial_details)
print("\nResults DataFrame")
print(results_df)

# Print best results
best_params = study.best_params
best_value = study.best_value
best_trial = study.best_trial
print(f"Best parameters: {best_params}")
print(f"Best portfolio return: {best_value}")

# Optional: Additional analysis
print("\nTrials ordered by portfolio return:")
top_trials = results_df.nlargest(len(results_df), "portfolio_return")
print(top_trials[["portfolio_return", "params"]])

# Visualize top trial performance
best_trial_idx = top_trials.index[0]

# Visualize best trial performance
backtest_output = optimization_results["trial_outputs"][best_trial_idx]
fig = plot_backtest_results(backtest_output, dataset, use_candlestick=False)
fig.show()


# portfolio_figures = plot_all_performance_plots(
#    event_logs=trial_details["event_logs_df"][best_trial_idx],
#    data_logs=trial_details["data_logs_df"][best_trial_idx],
# )
# for fig_name, fig in portfolio_figures.items():
#    fig.show()

# Visualize Optuna study results
# fig_dict = get_optuna_study_figures()
# for fig_name, fig_maker in fig_dict.items():
#    fig = fig_maker(study)
#    fig.show()
