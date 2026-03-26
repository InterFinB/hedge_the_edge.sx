import cvxpy as cp
import numpy as np
import pandas as pd

from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix
from portfolio_engine.config import (
    OPTIMIZER_REGULARIZATION_STRENGTH,
    MIN_WEIGHT_BOUND,
    MAX_WEIGHT_BOUND,
    MAX_STOCK_CATEGORY_WEIGHT,
    TICKER_TO_CATEGORY,
    STOCK_CATEGORIES,
)

WEIGHT_BOUNDS = (MIN_WEIGHT_BOUND, MAX_WEIGHT_BOUND)

# Practical minimum meaningful portfolio weight:
# assets below this threshold are pruned after optimization.
MIN_MEANINGFUL_WEIGHT = 0.015


def compute_max_feasible_return(
    mu: pd.Series,
    max_weight: float = MAX_WEIGHT_BOUND,
    max_stock_category_weight: float = MAX_STOCK_CATEGORY_WEIGHT,
) -> float:
    if not isinstance(mu, pd.Series):
        raise ValueError("mu must be a pandas Series.")

    sorted_mu = mu.sort_values(ascending=False)

    remaining_weight = 1.0
    remaining_stock_capacity = max_stock_category_weight
    max_return = 0.0

    for ticker, asset_return in sorted_mu.items():
        if remaining_weight <= 0:
            break

        category = TICKER_TO_CATEGORY.get(ticker, "")
        is_stock_like = category in STOCK_CATEGORIES

        asset_capacity = min(max_weight, remaining_weight)

        if is_stock_like:
            if remaining_stock_capacity <= 0:
                continue
            asset_capacity = min(asset_capacity, remaining_stock_capacity)

        if asset_capacity <= 0:
            continue

        max_return += asset_capacity * float(asset_return)
        remaining_weight -= asset_capacity

        if is_stock_like:
            remaining_stock_capacity -= asset_capacity

    return float(max_return)


def _solve_portfolio_problem(
    mu: pd.Series,
    cov: pd.DataFrame,
    target_return: float | None = None,
    max_volatility: float | None = None,
) -> dict:
    assets = list(mu.index)
    n_assets = len(assets)

    if n_assets < 2:
        raise ValueError("Optimization universe must contain at least 2 assets.")

    mu_vector = mu.values.astype(float)
    cov_values = cov.values.astype(float)
    cov_values = 0.5 * (cov_values + cov_values.T)

    w = cp.Variable(n_assets)

    portfolio_variance = cp.quad_form(w, cp.psd_wrap(cov_values))
    regularization_penalty = cp.sum_squares(w)

    constraints = [
        cp.sum(w) == 1,
        w >= WEIGHT_BOUNDS[0],
        w <= WEIGHT_BOUNDS[1],
    ]

    if target_return is not None:
        constraints.append(mu_vector @ w >= target_return)

    stock_indices = [
        i
        for i, asset in enumerate(assets)
        if TICKER_TO_CATEGORY.get(asset, "") in STOCK_CATEGORIES
    ]

    if stock_indices:
        constraints.append(cp.sum(w[stock_indices]) <= MAX_STOCK_CATEGORY_WEIGHT)

    if max_volatility is not None:
        constraints.append(portfolio_variance <= max_volatility**2)

    objective = cp.Minimize(
        portfolio_variance + OPTIMIZER_REGULARIZATION_STRENGTH * regularization_penalty
    )

    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.SCS, verbose=False)

    if w.value is None:
        raise ValueError("Optimization failed under the current constraints.")

    weights = np.array(w.value, dtype=float).flatten()
    weights[np.abs(weights) < 1e-8] = 0.0

    weight_sum = weights.sum()
    if abs(weight_sum) > 1e-12:
        weights = weights / weight_sum

    return {
        asset: float(weight)
        for asset, weight in zip(assets, weights)
    }


def _prune_and_renormalize(
    weights_dict: dict[str, float],
    min_meaningful_weight: float = MIN_MEANINGFUL_WEIGHT,
) -> dict[str, float]:
    pruned = {
        asset: weight
        for asset, weight in weights_dict.items()
        if weight >= min_meaningful_weight
    }

    if not pruned:
        largest_asset = max(weights_dict, key=weights_dict.get)
        pruned = {largest_asset: weights_dict[largest_asset]}

    total = sum(pruned.values())
    if total <= 1e-12:
        raise ValueError("All portfolio weights were removed during pruning.")

    normalized = {
        asset: weight / total
        for asset, weight in pruned.items()
    }

    return normalized


def _round_weights(weights_dict: dict[str, float]) -> dict[str, float]:
    return {
        asset: round(float(weight), 8)
        for asset, weight in weights_dict.items()
    }


def compute_max_feasible_return_for_subset(
    mu: pd.Series,
    assets: list[str],
    max_weight: float = MAX_WEIGHT_BOUND,
    max_stock_category_weight: float = MAX_STOCK_CATEGORY_WEIGHT,
) -> float:
    mu_subset = mu.loc[assets]
    return compute_max_feasible_return(
        mu=mu_subset,
        max_weight=max_weight,
        max_stock_category_weight=max_stock_category_weight,
    )


def optimize_min_variance_portfolio(
    price_data: pd.DataFrame,
    expected_returns: pd.Series | None = None,
    cov_matrix: pd.DataFrame | None = None,
    asset_subset: list[str] | None = None,
) -> dict:
    mu = expected_returns if expected_returns is not None else compute_expected_returns(price_data)
    cov = cov_matrix if cov_matrix is not None else compute_covariance_matrix(price_data)

    if not isinstance(mu, pd.Series):
        mu = pd.Series(mu, index=price_data.columns, dtype=float)

    if not isinstance(cov, pd.DataFrame):
        cov = pd.DataFrame(
            cov,
            index=price_data.columns,
            columns=price_data.columns,
        )

    assets = list(mu.index)

    if asset_subset is not None:
        assets = [asset for asset in asset_subset if asset in mu.index and asset in cov.index]

    if len(assets) < 2:
        raise ValueError("Optimization universe must contain at least 2 assets.")

    mu = mu.loc[assets]
    cov = cov.loc[assets, assets]

    raw_weights = _solve_portfolio_problem(
        mu=mu,
        cov=cov,
        target_return=None,
        max_volatility=None,
    )

    pruned_weights = _prune_and_renormalize(raw_weights, MIN_MEANINGFUL_WEIGHT)
    surviving_assets = list(pruned_weights.keys())

    if len(surviving_assets) < 2:
        return _round_weights(pruned_weights)

    mu_refined = mu.loc[surviving_assets]
    cov_refined = cov.loc[surviving_assets, surviving_assets]

    refined_weights = _solve_portfolio_problem(
        mu=mu_refined,
        cov=cov_refined,
        target_return=None,
        max_volatility=None,
    )

    refined_pruned = _prune_and_renormalize(refined_weights, MIN_MEANINGFUL_WEIGHT)
    return _round_weights(refined_pruned)


def optimize_portfolio(
    target_return: float,
    price_data: pd.DataFrame,
    max_volatility: float | None = None,
    expected_returns: pd.Series | None = None,
    cov_matrix: pd.DataFrame | None = None,
    asset_subset: list[str] | None = None,
) -> dict:
    mu = expected_returns if expected_returns is not None else compute_expected_returns(price_data)
    cov = cov_matrix if cov_matrix is not None else compute_covariance_matrix(price_data)

    if not isinstance(mu, pd.Series):
        mu = pd.Series(mu, index=price_data.columns, dtype=float)

    if not isinstance(cov, pd.DataFrame):
        cov = pd.DataFrame(
            cov,
            index=price_data.columns,
            columns=price_data.columns,
        )

    assets = list(mu.index)

    if asset_subset is not None:
        assets = [asset for asset in asset_subset if asset in mu.index and asset in cov.index]

    if len(assets) < 2:
        raise ValueError("Optimization universe must contain at least 2 assets.")

    mu = mu.loc[assets]
    cov = cov.loc[assets, assets]

    max_feasible_return = compute_max_feasible_return(
        mu=mu,
        max_weight=WEIGHT_BOUNDS[1],
        max_stock_category_weight=MAX_STOCK_CATEGORY_WEIGHT,
    )

    if target_return > max_feasible_return:
        raise ValueError(
            f"Target return {target_return:.2%} is too high. "
            f"The maximum feasible return under the current constraints is {max_feasible_return:.2%}."
        )

    try:
        raw_weights = _solve_portfolio_problem(
            mu=mu,
            cov=cov,
            target_return=target_return,
            max_volatility=max_volatility,
        )
    except ValueError:
        if max_volatility is not None:
            raise ValueError(
                f"Target return {target_return:.2%} is not feasible under the requested "
                f"maximum volatility of {max_volatility:.2%}."
            )
        raise ValueError("Portfolio optimization failed under the current constraints.")

    pruned_weights = _prune_and_renormalize(raw_weights, MIN_MEANINGFUL_WEIGHT)
    surviving_assets = list(pruned_weights.keys())

    if len(surviving_assets) < 2:
        return _round_weights(pruned_weights)

    mu_refined = mu.loc[surviving_assets]
    cov_refined = cov.loc[surviving_assets, surviving_assets]

    refined_max_feasible_return = compute_max_feasible_return_for_subset(
        mu=mu_refined,
        assets=surviving_assets,
        max_weight=WEIGHT_BOUNDS[1],
        max_stock_category_weight=MAX_STOCK_CATEGORY_WEIGHT,
    )

    if target_return > refined_max_feasible_return:
        return _round_weights(pruned_weights)

    try:
        refined_weights = _solve_portfolio_problem(
            mu=mu_refined,
            cov=cov_refined,
            target_return=target_return,
            max_volatility=max_volatility,
        )

        refined_pruned = _prune_and_renormalize(refined_weights, MIN_MEANINGFUL_WEIGHT)
        return _round_weights(refined_pruned)

    except ValueError:
        return _round_weights(pruned_weights)