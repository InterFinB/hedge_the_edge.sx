import yfinance as yf
import pandas as pd
import datetime

from portfolio_engine.config import TICKERS, START_DATE


_cached_price_data = None
_cache_timestamp = None


def load_price_data(force_refresh=False):

    global _cached_price_data
    global _cache_timestamp

    if _cached_price_data is not None and not force_refresh:
        return _cached_price_data

    end_date = datetime.datetime.today()

    raw = yf.download(
        TICKERS,
        start=START_DATE,
        end=end_date,
        progress=False,
        auto_adjust=False,
    )

    # ----------------------------
    # SAFE PRICE EXTRACTION
    # ----------------------------

    if isinstance(raw.columns, pd.MultiIndex):

        if "Adj Close" in raw.columns.levels[0]:
            data = raw["Adj Close"]

        elif "Close" in raw.columns.levels[0]:
            data = raw["Close"]

        else:
            raise ValueError("No price column found in Yahoo data")

    else:
        # single ticker case
        if "Adj Close" in raw.columns:
            data = raw[["Adj Close"]]
        elif "Close" in raw.columns:
            data = raw[["Close"]]
        else:
            raise ValueError("No price column found in Yahoo data")

    # ----------------------------
    # CLEAN DATA
    # ----------------------------

    data = data.sort_index()

    data = data.ffill()

    threshold = int(len(data) * 0.8)
    data = data.dropna(axis=1, thresh=threshold)

    data = data.dropna()

    if data.shape[1] < 2:
        raise ValueError(
            "Not enough valid price data after cleaning"
        )

    # ----------------------------

    _cached_price_data = data
    _cache_timestamp = datetime.datetime.now()

    return _cached_price_data