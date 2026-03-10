from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_engine.data_loader import load_price_data
from portfolio_engine.optimizer import optimize_portfolio
from portfolio_engine.risk import compute_portfolio_volatility, compute_portfolio_return
from portfolio_engine.input_parser import parse_percentage_input
import explanation_layer.explanation

app = FastAPI(title="RM Agent API")


class PortfolioRequest(BaseModel):
    target_return: str
    max_volatility: Optional[str] = None


@app.get("/")
def home():
    return {"message": "RM Agent API is running"}


@app.post("/portfolio")
def generate_portfolio(request: PortfolioRequest):
    try:
        target_return = float(parse_percentage_input(request.target_return))

        price_data = load_price_data()
        weights = optimize_portfolio(target_return, price_data)

        portfolio_volatility = float(compute_portfolio_volatility(weights, price_data))
        portfolio_return = float(compute_portfolio_return(weights, price_data))

        clean_weights = {k: float(v) for k, v in dict(weights).items()}

        feasible = None

        response = {
            "desired_return": f"{target_return:.2%}",
            "expected_portfolio_return": f"{portfolio_return:.2%}",
            "portfolio_volatility": f"{portfolio_volatility:.2%}",
            "weights": clean_weights,
        }

        if request.max_volatility is not None and request.max_volatility.strip() != "":
            max_volatility = float(parse_percentage_input(request.max_volatility))
            feasible = bool(portfolio_volatility <= max_volatility)

            response["max_allowed_volatility"] = f"{max_volatility:.2%}"
            response["feasible"] = feasible
            response["message"] = (
                "This portfolio satisfies the user's downside tolerance."
                if feasible
                else "This portfolio exceeds the user's downside tolerance."
            )
        else:
            response["message"] = "Minimum-risk portfolio for the requested return."

        explanation = explanation_layer.explanation.generate_explanation(
            desired_return=target_return,
            expected_portfolio_return=portfolio_return,
            portfolio_volatility=portfolio_volatility,
            weights=clean_weights,
            feasible=feasible,
            max_weight_constraint=0.35,
        )

        response["explanation"] = explanation

        return response

    except ValueError as e:
        error_message = str(e)

        if "target_return must be lower than the maximum possible return" in error_message:
            raise HTTPException(
                status_code=400,
                detail="The desired return is too high for the current investable universe. Please enter a lower target return."
            )

        raise HTTPException(status_code=400, detail=error_message)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")