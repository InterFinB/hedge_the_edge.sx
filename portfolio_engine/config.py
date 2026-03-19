ASSET_UNIVERSE = [
    # Large-cap stocks
    {"ticker": "AAPL", "name": "Apple", "category": "Large-Cap Stocks"},
    {"ticker": "MSFT", "name": "Microsoft", "category": "Large-Cap Stocks"},
    {"ticker": "NVDA", "name": "NVIDIA", "category": "Large-Cap Stocks"},
    {"ticker": "AMZN", "name": "Amazon", "category": "Large-Cap Stocks"},
    {"ticker": "GOOGL", "name": "Alphabet", "category": "Large-Cap Stocks"},
    {"ticker": "META", "name": "Meta", "category": "Large-Cap Stocks"},
    {"ticker": "JPM", "name": "JPMorgan Chase", "category": "Large-Cap Stocks"},
    {"ticker": "XOM", "name": "Exxon Mobil", "category": "Large-Cap Stocks"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "category": "Large-Cap Stocks"},
    {"ticker": "UNH", "name": "UnitedHealth Group", "category": "Large-Cap Stocks"},

    # Broad market and sector ETFs
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust", "category": "Broad Market and Sector ETFs"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "category": "Broad Market and Sector ETFs"},
    {"ticker": "XLV", "name": "Health Care Select Sector SPDR Fund", "category": "Broad Market and Sector ETFs"},
    {"ticker": "XLF", "name": "Financial Select Sector SPDR Fund", "category": "Broad Market and Sector ETFs"},
    {"ticker": "XLE", "name": "Energy Select Sector SPDR Fund", "category": "Broad Market and Sector ETFs"},
    {"ticker": "XLI", "name": "Industrial Select Sector SPDR Fund", "category": "Broad Market and Sector ETFs"},

    # International and style ETFs
    {"ticker": "VEA", "name": "Vanguard FTSE Developed Markets ETF", "category": "International and Style ETFs"},
    {"ticker": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "category": "International and Style ETFs"},
    {"ticker": "IJR", "name": "iShares Core S&P Small-Cap ETF", "category": "International and Style ETFs"},

    # Bonds and alternative assets
    {"ticker": "AGG", "name": "iShares Core U.S. Aggregate Bond ETF", "category": "Bonds and Alternative Assets"},
    {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "category": "Bonds and Alternative Assets"},
    {"ticker": "LQD", "name": "iShares iBoxx $ Investment Grade Corporate Bond ETF", "category": "Bonds and Alternative Assets"},
    {"ticker": "GLD", "name": "SPDR Gold Shares", "category": "Bonds and Alternative Assets"},
    {"ticker": "DBC", "name": "Invesco DB Commodity Index Tracking Fund", "category": "Bonds and Alternative Assets"},
    {"ticker": "VNQ", "name": "Vanguard Real Estate ETF", "category": "Bonds and Alternative Assets"},
]

TICKERS = [asset["ticker"] for asset in ASSET_UNIVERSE]

TICKER_TO_NAME = {asset["ticker"]: asset["name"] for asset in ASSET_UNIVERSE}

TICKER_TO_CATEGORY = {asset["ticker"]: asset["category"] for asset in ASSET_UNIVERSE}

START_DATE = "2020-01-01"

# Expected return model configuration
# Supported methods:
# - "historical"
# - "exponential"
# - "blended"
# - "equilibrium_blended"
EXPECTED_RETURN_METHOD = "equilibrium_blended"

# Existing signal model settings
EXPECTED_RETURN_BLEND_WEIGHT = 0.50
EXPECTED_RETURN_SPAN = 180

# Equilibrium-anchor blend setting
# final_mu = signal_weight * signal_mu + (1 - signal_weight) * anchor_mu
EXPECTED_RETURN_SIGNAL_WEIGHT = 0.50

MIN_EXPECTED_RETURN = 0.02   # 2%
MAX_EXPECTED_RETURN = 0.25   # 25%
BASELINE_EXPECTED_RETURN = 0.08   # 8%

# Deterministic category-based equilibrium anchors
CATEGORY_BASELINE_RETURNS = {
    "Large-Cap Stocks": 0.11,
    "Broad Market and Sector ETFs": 0.10,
    "International and Style ETFs": 0.10,
    "Bonds and Alternative Assets": 0.05,
}

# Optimizer configuration
OPTIMIZER_REGULARIZATION_STRENGTH = 0.05