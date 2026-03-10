from pypfopt import risk_models

def compute_covariance_matrix(price_data):
    cov_matrix = risk_models.CovarianceShrinkage(price_data).ledoit_wolf()
    return cov_matrix