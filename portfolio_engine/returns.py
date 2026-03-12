from pypfopt import expected_returns


MIN_EXPECTED_RETURN = 0.02   # 2%
MAX_EXPECTED_RETURN = 0.25   # 25%


def compute_expected_returns(price_data):
    """
    Compute annualized expected returns and clip them to a
    conservative-but-flexible range for MVP realism.
    """
    mu = expected_returns.mean_historical_return(price_data)

    mu = mu.clip(lower=MIN_EXPECTED_RETURN, upper=MAX_EXPECTED_RETURN)

    return mu