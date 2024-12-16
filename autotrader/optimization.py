import optuna
import pandas as pd
from autotrader.backtesting import run_coarse_backtest
from autotrader.data_utils import Dataset, convert_event_logs_to_tidy
from autotrader.schemas import BacktestConfig, DataConfig
from autotrader.strategies import BaseStrategy
from optuna.samplers import (
    # CmaEsSampler,
    GPSampler,
    TPESampler,
)


def optimize_strategy_params_on_backtest(
    data_config: DataConfig,
    backtest_config: BacktestConfig,
    strategy_class: BaseStrategy,
    n_trials: int = 200,
    sampler: optuna.samplers.BaseSampler = GPSampler(seed=10),
    optuna_callback: callable = None,
):
    """
    Optimize strategy parameters using Optuna with comprehensive tracking.

    Args:
        data_config (DataConfig): Configuration for data sourcing
        backtest_config (BacktestConfig): Configuration for backtest
        strategy_class (type): Strategy class to optimize
        n_trials (int, optional): Number of trials for optimization. Defaults to 200.
        sampler (optuna.samplers.BaseSampler, optional): Optuna sampler. Defaults to GPSampler.

    Returns:
        Dict[str, Any]: A dictionary containing the Optuna study and additional tracking information
    """

    # Get hyperparameter space for the strategy
    hyperparam_space = strategy_class.get_hyperparam_space()

    # Default to TPESampler if no sampler is provided
    if sampler is None:
        sampler = TPESampler(seed=10, deterministic_objective=True)

    # Create storage for trial details
    trial_details = {
        "params": [],
        "initial_portfolios": [],
        "final_portfolios": [],
        "returns": [],
        "relative_returns": [],
        "sharpe_ratio": [],
        "drawdown": [],
        "sqn": [],
        # "event_logs": [],
        "data_logs": [],
    }

    trial_outputs = []

    def objective(trial):
        # Dynamically create strategy parameters based on hyperparameter space
        strategy_params = {}
        for param_name, param_config in hyperparam_space.items():
            if param_config["type"] == "int":
                strategy_params[param_name] = trial.suggest_int(
                    param_name, param_config["min"], param_config["max"]
                )
            elif param_config["type"] == "float":
                strategy_params[param_name] = trial.suggest_float(
                    param_name, param_config["min"], param_config["max"]
                )
            elif param_config["type"] == "categorical":
                strategy_params[param_name] = trial.suggest_categorical(
                    param_name, param_config["choices"]
                )

        # Running the backtest with suggested parameters
        dataset = Dataset.from_config(data_config)
        output = run_coarse_backtest(
            backtest_config, dataset, strategy_class, strategy_params
        )
        trial_outputs.append(output)
        initial_portfolio = output["portfolio_info"]["initial_portfolio"]
        final_portfolio = output["portfolio_info"]["final_portfolio"]

        # Store trial details
        trial_details["params"].append(strategy_params)
        trial_details["initial_portfolios"].append(initial_portfolio)
        trial_details["final_portfolios"].append(final_portfolio)

        # Store event and data logs if available
        output_strategy = output["output_strategy"]
        # trial_details["event_logs"].append(output_strategy.event_log)
        trial_details["data_logs"].append(output_strategy.data_log)

        # Calculate return
        portfolio_return = final_portfolio - initial_portfolio
        relative_portfolio_return = portfolio_return / initial_portfolio

        trial_details["returns"].append(portfolio_return)
        trial_details["relative_returns"].append(relative_portfolio_return)

        # Add other KPIs
        sharpe_ratio = output["analysis_results"]["sharpe"]["sharperatio"]
        drawdown = output["analysis_results"]["drawdown"]["max"]["drawdown"]
        sqn = output["analysis_results"]["sqn"]["sqn"]
        trial_details["sharpe_ratio"].append(sharpe_ratio)
        trial_details["drawdown"].append(drawdown)
        trial_details["sqn"].append(sqn)

        return final_portfolio - initial_portfolio

    # Create and run the study
    study = optuna.create_study(direction="maximize", sampler=sampler)
    callbacks = [optuna_callback] if optuna_callback is not None else []
    study.optimize(objective, n_trials=n_trials, callbacks=callbacks)

    # Convert logs to DataFrames for easier analysis
    trial_details["data_logs_df"] = [
        pd.DataFrame(data_log) for data_log in trial_details["data_logs"]
    ]
    # trial_details["event_logs_df"] = [
    #    convert_event_logs_to_tidy(event_log)
    #    for event_log in trial_details["event_logs"]
    # ]

    # Create a comprehensive results DataFrame
    results_df = pd.DataFrame(
        {
            "trial_number": range(n_trials),
            "params": trial_details["params"],
            "initial_portfolio": trial_details["initial_portfolios"],
            "final_portfolio": trial_details["final_portfolios"],
            "portfolio_return": trial_details["returns"],
            "relative_portfolio_return": trial_details["relative_returns"],
            # "event_logs": trial_details["event_logs_df"],
        }
    )

    # Return a comprehensive dictionary with all details
    return {
        "study": study,
        "trial_details": trial_details,
        "results_df": results_df,
        "trial_outputs": trial_outputs,
    }
