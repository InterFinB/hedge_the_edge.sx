Hedge The Edge AI

AI-powered portfolio optimization agent that constructs minimum-risk portfolios for a desired return and explains the allocation decisions in plain financial language.

The system combines quantitative portfolio optimization with an AI-style explanation layer to make investment decisions transparent and educational.

Core Idea

The user specifies:

desired portfolio return

optional downside volatility tolerance

The system then:

analyzes market data

estimates expected returns and asset covariances

computes the minimum-risk portfolio

explains why each asset appears in the allocation

System Architecture
User Input
    ↓
FastAPI API Layer
    ↓
Portfolio Engine (Quantitative Optimization)
    ↓
Explanation Layer (Financial Interpretation)
    ↓
JSON Response

Key Features

• Mean-variance portfolio optimization (Markowitz framework)

• Minimum-risk portfolio construction for a target return

• Downside tolerance feasibility check

• Asset allocation constraints (max weight per asset)

• Financial explanation layer describing:

asset roles (defensive / growth / diversifiers)

diversification logic

constraint effects

zero-weight asset reasoning

• REST API for integration with chatbots, web apps, or AI agents

Technology Stack

Backend

Python

FastAPI

NumPy

Pandas

PyPortfolioOpt

yfinance

Architecture

Modular quant engine

Separate explanation layer

API delivery layer

Project Structure

RM_Agent/
│
├── api/
│   └── server.py              # FastAPI application
│
├── portfolio_engine/
│   ├── optimizer.py           # Portfolio optimization
│   ├── risk.py                # Risk metrics
│   ├── returns.py             # Expected return estimation
│   ├── covariance.py          # Covariance matrix estimation
│   ├── data_loader.py         # Market data ingestion
│   └── input_parser.py        # User input normalization
│
├── explanation_layer/
│   └── explanation.py         # Portfolio explanation logic
│
├── scripts/
│   ├── fetch_data.py
│   └── test_optimizer.py
│
└── requirements.txt

How the Portfolio Is Constructed

The system solves a constrained mean-variance optimization problem:

Minimize portfolio volatility subject to:

target expected return

full investment constraint

maximum asset weight constraint

The optimizer identifies the most efficient asset mix that achieves the requested return.

Running the Project
1. Clone the repository
git clone https://github.com/InterFinB/hedge_the_edge.ai.git
2. Create a virtual environment
python -m venv venv

Activate:

Windows

venv\Scripts\activate

Mac/Linux

source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Run the API
uvicorn api.server:app --reload
5. Open API documentation
http://127.0.0.1:8000/docs

You can test the portfolio engine directly from this interface.

Example Request
{
  "target_return": "10%",
  "max_volatility": "15%"
}

Example Response
{
  "desired_return": "10.00%",
  "expected_portfolio_return": "10.00%",
  "portfolio_volatility": "9.08%",
  "weights": {...},
  "explanation": "To achieve the requested return..."
}

Future Improvements

Planned upgrades include:

• Monte Carlo portfolio risk simulation
• Black-Litterman return estimation
• Larger investable asset universe
• LLM-powered explanation refinement
• Web and chatbot interface

Vision

The goal of Hedge The Edge AI is to build an AI financial advisor that combines:

rigorous quantitative portfolio construction

transparent decision explanations

conversational user interaction

to improve financial literacy and portfolio decision making.
