import yfinance as yf
from portfolio_engine.config import TICKERS, START_DATE

def load_price_data():
    data = yf.download(TICKERS, start=START_DATE)["Close"]
    return data