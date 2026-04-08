import numpy as np
import pandas as pd


def simulate_portfolio_annual_returns(
    weights: dict,
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 2000,
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

    aligned_assets = [
        asset
        for asset in weight_series.index
        if asset in expected_returns.index and asset in cov_matrix.index
    ]

    if not aligned_assets:
        raise ValueError("No overlapping assets found between weights and model inputs.")

    weight_vector = weight_series.loc[aligned_assets].values
    mu_vector = expected_returns.loc[aligned_assets].values
    cov_values = cov_matrix.loc[aligned_assets, aligned_assets].values

    rng = np.random.default_rng(random_seed)

    simulated_asset_returns = rng.multivariate_normal(
        mean=mu_vector,
        cov=cov_values,
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

    Returned fields:
      - bin_start: left edge of the bucket, decimal form
      - bin_end: right edge of the bucket, decimal form
      - bin_center: midpoint of the bucket, decimal form
      - frequency: count of simulations in the bucket
      - count: alias of frequency for frontend compatibility
      - label: preformatted display label, e.g. "4.2% to 5.1%"
    """
    if simulated_returns is None or len(simulated_returns) == 0:
        return []

    counts, bin_edges = np.histogram(simulated_returns, bins=n_bins)

    chart_data: list[dict] = []

    for i in range(len(counts)):
        bin_start = float(bin_edges[i])
        bin_end = float(bin_edges[i + 1])
        bin_center = float((bin_start + bin_end) / 2)
        frequency = int(counts[i])

        chart_data.append(
            {
                "bin_start": bin_start,
                "bin_end": bin_end,
                "bin_center": bin_center,
                "frequency": frequency,
                "count": frequency,
                "label": f"{bin_start * 100:.1f}% to {bin_end * 100:.1f}%",
            }
        )

    return chart_data