import yfinance as yf
import pandas as pd

tickers = [
    "AAPL",   # stock
    "MSFT",   # stock
    "NVDA",   # stock
    "AMZN",   # stock
    "GOOGL",  # stock
    "SPY",    # broad market ETF
    "QQQ",    # tech ETF
    "XLV",    # healthcare ETF
    "AGG",    # bonds ETF
    "GLD",    # gold ETF
    "DBC"     # commodities ETF
]

data = yf.download(tickers, start="2020-01-01")

prices = data["Close"]

print(prices.tail())
