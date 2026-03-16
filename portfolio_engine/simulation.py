import numpy as np
import pandas as pd

from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix


def simulate_portfolio_annual_returns(
    weights: dict,
    price_data: pd.DataFrame,
    n_simulations: int = 5000,
    random_seed: int = 42,
) -> np.ndarray:
    """
    Simulate 1-year portfolio returns using a multivariate normal model.

    Returns a NumPy array of simulated annual portfolio returns in decimal form.
    Example:
        0.10 -> +10%
        -0.08 -> -8%
    """
    if not weights:
        raise ValueError("Weights dictionary is empty.")

    weight_series = pd.Series(weights, dtype=float)

    expected_returns = compute_expected_returns(price_data)
    covariance_matrix = compute_covariance_matrix(price_data)

    aligned_assets = [
        asset
        for asset in weight_series.index
        if asset in expected_returns.index and asset in covariance_matrix.index
    ]

    if not aligned_assets:
        raise ValueError("No overlapping assets found between weights and market data.")

    weight_vector = weight_series.loc[aligned_assets].values
    mu_vector = expected_returns.loc[aligned_assets].values
    cov_matrix = covariance_matrix.loc[aligned_assets, aligned_assets].values

    rng = np.random.default_rng(random_seed)

    simulated_asset_returns = rng.multivariate_normal(
        mean=mu_vector,
        cov=cov_matrix,
        size=n_simulations,
    )

    simulated_portfolio_returns = simulated_asset_returns @ weight_vector

    return simulated_portfolio_returns


def summarize_simulation_results(simulated_returns: np.ndarray) -> dict:
    """
    Summarize Monte Carlo simulation results.
    """
    if simulated_returns is None or len(simulated_returns) == 0:
        raise ValueError("Simulated returns array is empty.")

    mean_return = float(np.mean(simulated_returns))
    median_return = float(np.median(simulated_returns))
    loss_probability = float(np.mean(simulated_returns < 0))
    percentile_5 = float(np.percentile(simulated_returns, 5))
    percentile_95 = float(np.percentile(simulated_returns, 95))

    return {
        "mean_return": mean_return,
        "median_return": median_return,
        "loss_probability": loss_probability,
        "percentile_5": percentile_5,
        "percentile_95": percentile_95,
    }


def prepare_simulation_chart_data(
    simulated_returns: np.ndarray,
    n_bins: int = 40,
) -> list[dict]:
    """
    Convert simulated returns into histogram-style chart data for the frontend.
    """
    if simulated_returns is None or len(simulated_returns) == 0:
        return []

    counts, bin_edges = np.histogram(simulated_returns, bins=n_bins)

    chart_data = []
    for i in range(len(counts)):
        bin_center = float((bin_edges[i] + bin_edges[i + 1]) / 2)
        frequency = int(counts[i])

        chart_data.append(
            {
                "bin_center": bin_center,
                "frequency": frequency,
            }
        )

    return chart_data