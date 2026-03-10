from pypfopt import EfficientFrontier
from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix

def optimize_portfolio(target_return, price_data):
    mu = compute_expected_returns(price_data)
    cov_matrix = compute_covariance_matrix(price_data)

    max_possible_return = mu.max()

    if target_return > max_possible_return:
        raise ValueError(
            f"Target return {target_return:.2%} is too high. "
            f"The maximum estimated return in the current universe is {max_possible_return:.2%}."
        )

    ef = EfficientFrontier(mu, cov_matrix, weight_bounds=(0, 0.35))
    ef.efficient_return(target_return=target_return)

    cleaned_weights = ef.clean_weights()
    return cleaned_weights