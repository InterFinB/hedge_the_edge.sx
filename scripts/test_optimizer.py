import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_engine.data_loader import load_price_data
from portfolio_engine.optimizer import optimize_portfolio
from portfolio_engine.risk import compute_portfolio_volatility, compute_portfolio_return
from portfolio_engine.input_parser import get_valid_percentage_input

# User inputs
target_return = get_valid_percentage_input(
    "Enter your desired return (e.g. 0.10, 10, or 10%): ",
    min_value=0,
    max_value=1
)

max_volatility = get_valid_percentage_input(
    "Enter your maximum tolerated volatility (e.g. 0.15, 15, or 15%): ",
    min_value=0,
    max_value=1
)

price_data = load_price_data()

try:
    weights = optimize_portfolio(target_return, price_data)

    portfolio_volatility = compute_portfolio_volatility(weights, price_data)
    portfolio_return = compute_portfolio_return(weights, price_data)

    print("\nDesired return:")
    print(f"{target_return:.2%}")

    print("\nExpected portfolio return:")
    print(f"{portfolio_return:.2%}")

    print("\nOptimal portfolio weights:")
    print(weights)

    print("\nPortfolio volatility:")
    print(f"{portfolio_volatility:.2%}")

    if portfolio_volatility <= max_volatility:
        print("\nThis portfolio satisfies the user's downside tolerance.")
    else:
        print("\nThis portfolio exceeds the user's downside tolerance.")

except ValueError as e:
    print("\nUnable to build a portfolio for this request.")

    error_message = str(e)

    if "target_return must be lower than the maximum possible return" in error_message:
        print("The desired return is too high for the current investable universe.")
        print("Please enter a lower target return.")
    else:
        print(error_message)