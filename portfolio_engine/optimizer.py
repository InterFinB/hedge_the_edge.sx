from pypfopt import EfficientFrontier
from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix


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


def optimize_portfolio(target_return, price_data):
    mu = compute_expected_returns(price_data)
    cov_matrix = compute_covariance_matrix(price_data)

    max_feasible_return = compute_max_feasible_return(
        mu,
        max_weight=WEIGHT_BOUNDS[1]
    )

    if target_return > max_feasible_return:
        raise ValueError(
            f"Target return {target_return:.2%} is too high. "
            f"The maximum feasible return under the current constraints is {max_feasible_return:.2%}."
        )

    ef = EfficientFrontier(mu, cov_matrix, weight_bounds=WEIGHT_BOUNDS)
    ef.efficient_return(target_return=target_return)

    cleaned_weights = ef.clean_weights()
    return cleaned_weights