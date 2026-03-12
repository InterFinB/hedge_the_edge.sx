import yfinance as yf
from datetime import datetime, timedelta
from portfolio_engine.config import TICKERS, START_DATE

# In-memory cache
_cached_price_data = None
_cache_timestamp = None

# Cache duration
CACHE_DURATION = timedelta(hours=1)


def load_price_data(force_refresh=False):
    global _cached_price_data, _cache_timestamp

    now = datetime.now()

    # Use cached data if it exists and is still fresh
    if (
        not force_refresh
        and _cached_price_data is not None
        and _cache_timestamp is not None
        and now - _cache_timestamp < CACHE_DURATION
    ):
        return _cached_price_data

    # Otherwise, fetch fresh data
    data = yf.download(TICKERS, start=START_DATE)["Close"]

    _cached_price_data = data
    _cache_timestamp = now

    return _cached_price_data