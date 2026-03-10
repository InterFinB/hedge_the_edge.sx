from pypfopt import expected_returns

def compute_expected_returns(price_data):
    mu = expected_returns.mean_historical_return(price_data)
    return mu