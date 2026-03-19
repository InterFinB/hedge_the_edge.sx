import cvxpy as cp
import numpy as np
import pandas as pd

from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix
from portfolio_engine.config import OPTIMIZER_REGULARIZATION_STRENGTH


WEIGHT_BOUNDS = (0, 0.35)


def compute_max_feasible_return(mu, max_weight=0.35):
    """
    Compute the maximum feasible portfolio return under:
    - long-only weights
    - full investment
    - max weight per asset

    This is done by allocating as much weight as possible to the assets
    with the highest expected returns first.
    """
    sorted_mu = mu.sort_values(ascending=False)

    remaining_weight = 1.0
    max_return = 0.0

    for _, asset_return in sorted_mu.items():
        if remaining_weight <= 0:
            break

        allocation = min(max_weight, remaining_weight)
        max_return += allocation * asset_return
        remaining_weight -= allocation

    return float(max_return)


def optimize_portfolio(target_return, price_data, max_volatility=None):
    """
    Compute a regularized minimum-variance portfolio subject to:
    - target expected return
    - full investment
    - long-only constraints
    - max weight cap
    - optional maximum volatility constraint

    Objective:
        minimize portfolio_variance + lambda * sum_squares(weights)

    Parameters
    ----------
    target_return : float
        Target annual expected return in decimal form.
    price_data : pd.DataFrame
        Historical price data.
    max_volatility : float or None
        Optional maximum annualized portfolio volatility in decimal form.

    Returns
    -------
    dict
        Cleaned portfolio weights as {ticker: weight}.

    Raises
    ------
    ValueError
        If the target return is infeasible under current constraints,
        or if the requested volatility constraint makes the problem infeasible.
    """
    mu = compute_expected_returns(price_data)
    cov_matrix = compute_covariance_matrix(price_data)

    if not isinstance(mu, pd.Series):
        mu = pd.Series(mu, index=price_data.columns, dtype=float)

    if not isinstance(cov_matrix, pd.DataFrame):
        cov_matrix = pd.DataFrame(
            cov_matrix,
            index=price_data.columns,
            columns=price_data.columns,
        )

    assets = list(mu.index)
    n_assets = len(assets)

    max_feasible_return = compute_max_feasible_return(
        mu,
        max_weight=WEIGHT_BOUNDS[1],
    )

    if target_return > max_feasible_return:
        raise ValueError(
            f"Target return {target_return:.2%} is too high. "
            f"The maximum feasible return under the current constraints is {max_feasible_return:.2%}."
        )

    mu_vector = mu.loc[assets].values.astype(float)
    cov_values = cov_matrix.loc[assets, assets].values.astype(float)

    # Numerical cleanup
    cov_values = 0.5 * (cov_values + cov_values.T)

    w = cp.Variable(n_assets)

    portfolio_variance = cp.quad_form(w, cp.psd_wrap(cov_values))
    portfolio_return = mu_vector @ w
    regularization_penalty = cp.sum_squares(w)

    objective = cp.Minimize(
        portfolio_variance
        + OPTIMIZER_REGULARIZATION_STRENGTH * regularization_penalty
    )

    constraints = [
        cp.sum(w) == 1,
        w >= WEIGHT_BOUNDS[0],
        w <= WEIGHT_BOUNDS[1],
        portfolio_return >= target_return,
    ]

    if max_volatility is not None:
        constraints.append(portfolio_variance <= max_volatility ** 2)

    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.SCS)

    if w.value is None:
        if max_volatility is not None:
            raise ValueError(
                f"Target return {target_return:.2%} is not feasible under the requested "
                f"maximum volatility of {max_volatility:.2%}."
            )
        raise ValueError(
            "Portfolio optimization failed under the current constraints."
        )

    weights = np.array(w.value, dtype=float).flatten()

    # Clean tiny numerical noise
    weights[np.abs(weights) < 1e-8] = 0.0

    # Renormalize cautiously in case of tiny solver drift
    weight_sum = weights.sum()
    if abs(weight_sum) > 1e-12:
        weights = weights / weight_sum

    cleaned_weights = {
        asset: round(float(weight), 8)
        for asset, weight in zip(assets, weights)
    }

    return cleaned_weights