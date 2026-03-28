📊 Hedge the Edge

Hedge the Edge is a portfolio optimization web application that generates minimum-risk portfolios for a target return, enriched with diagnostics, simulations, and AI-powered explanations.

It combines quantitative portfolio construction with intuitive, structured insights — designed for users who want both rigor and understanding.

🚀 Features
🧠 Portfolio Optimization
Mean-variance optimization with constraints
Target return + optional volatility cap
Regularization for stability
Category and weight constraints
📈 Diagnostics
Risk contributions (who drives volatility)
Diversification ratio
Concentration metrics
Active / meaningful positions
🎲 Simulation
Monte Carlo simulation of annual returns
Distribution visualization
Key statistics:
Mean / Median
Loss probability
5th / 95th percentiles
💬 Explanation Layer
Portfolio summary
Risk commentary
Simulation interpretation
“Watch for” and “Takeaways”
Financial vocabulary section
🌐 Web App
Clean Next.js frontend
Interactive charts (Recharts)
Structured UI blocks
Real-time API integration
🏗️ Architecture
hedge_the_edge/
│
├── api/                     # FastAPI backend
│   └── server.py
│
├── portfolio_engine/        # Core quant engine
│   ├── optimizer.py
│   ├── data_loader.py
│   ├── returns.py
│   ├── covariance.py
│   ├── risk.py
│   ├── diagnostics.py
│   ├── simulation.py
│   └── config.py
│
├── explanation_layer/       # Explanation generation
│   └── explanation.py
│
├── hedge-the-edge-web/      # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── services/
│   └── types/
│
├── scripts/                 # Optional utilities
│
├── requirements.txt
└── README.md
⚙️ How It Works
Market data is loaded
Yahoo Finance via yfinance
Cached with fallback logic
Portfolio is optimized
Target return constraint
Optional volatility constraint
Category + weight bounds
Diagnostics are computed
Risk decomposition
Concentration
Diversification
Simulation is run
Monte Carlo returns
Distribution + summary stats
Explanation is generated
Structured narrative
Actionable insights
Frontend displays everything
Charts + tables + explanation tabs
🛠️ Setup
1. Clone the repo
git clone https://github.com/InterFinB/hedge_the_edge.sx
cd hedge_the_edge.sx
2. Backend (FastAPI)
pip install -r requirements.txt
uvicorn api.server:app --reload

Backend runs at:

http://127.0.0.1:8000
3. Frontend (Next.js)
cd hedge-the-edge-web
npm install
npm run dev

Create .env.local:

NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000

Frontend runs at:

http://localhost:3000
🔌 API Endpoints
POST /portfolio

Generate portfolio:

{
  "target_return": 0.10,
  "max_volatility": 0.15
}

Response includes:

weights
diagnostics
simulation
explanation
market_data (cache status, warnings)
GET /cache-status

Returns:

cache validity
timestamp
asset count
POST /refresh-data

Forces market data refresh.

⚠️ Data Notes
Uses Yahoo Finance (yfinance)
Includes:
retry logic
caching
fallback to stale data
Some tickers may be:
temporarily unavailable
dropped during cleaning
🧩 Future Improvements
Replace live Yahoo calls with stored data
Add dynamic portfolio monitoring (“agent layer”)
Improve explanation personalization
Add user profiles / saved portfolios
Expand asset universe
📌 Status
✅ MVP complete
✅ Web app deployed
✅ Robust data handling
🔜 Moving toward intelligent portfolio agent
🧠 Philosophy

Hedge the Edge is built on a simple idea:

A good portfolio is not just optimized — it is understood.
