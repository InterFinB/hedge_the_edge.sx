import streamlit as st
import requests
import pandas as pd
import plotly.express as px

from portfolio_engine.config import TICKER_TO_NAME

API_URL = "http://127.0.0.1:8000/portfolio"

st.set_page_config(page_title="Hedge The Edge", page_icon="📈", layout="wide")

st.title("Hedge The Edge")
st.caption("AI-powered minimum-risk portfolio advisor")

st.markdown(
    """
Enter your target return and, optionally, your maximum tolerated volatility.

The app computes a **minimum-risk portfolio** designed to achieve your requested return,
then explains the result in a readable and educational way.
"""
)


def format_asset_name(ticker: str) -> str:
    name = TICKER_TO_NAME.get(ticker)
    if name:
        return f"{ticker} ({name})"
    return ticker


def set_table_index_from_one(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.index = range(1, len(df) + 1)
    return df


def render_weights_table(title: str, data: dict):
    st.subheader(title)
    if not data:
        st.write("No data available.")
        return

    rows = [
        {"Asset": format_asset_name(k), "Weight": v}
        for k, v in data.items()
    ]
    df = pd.DataFrame(rows)
    df = set_table_index_from_one(df)
    st.table(df)


def render_risk_contributions_table(title: str, contributions: dict, effects: dict):
    st.subheader(title)
    if not contributions:
        st.write("No data available.")
        return

    rows = []
    for ticker, value in contributions.items():
        rows.append(
            {
                "Asset": format_asset_name(ticker),
                "Risk Contribution": value,
                "Effect": effects.get(ticker, "-"),
            }
        )

    df = pd.DataFrame(rows)
    df = set_table_index_from_one(df)
    st.table(df)


def build_weights_df(chart_data: dict) -> pd.DataFrame:
    weights = chart_data.get("weights", {})
    if not weights:
        return pd.DataFrame(columns=["Asset", "Weight", "Weight (%)"])

    df = pd.DataFrame(
        [{"Asset": asset, "Weight": weight} for asset, weight in weights.items()]
    )
    df["Weight (%)"] = df["Weight"] * 100
    df = df.sort_values("Weight (%)", ascending=False).reset_index(drop=True)
    return df


def build_risk_contributions_df(chart_data: dict) -> pd.DataFrame:
    risk_contributions = chart_data.get("risk_contributions", {})
    if not risk_contributions:
        return pd.DataFrame(
            columns=["Ticker", "Asset", "Risk Contribution (%)", "Effect", "Abs Contribution"]
        )

    df = pd.DataFrame(
        [
            {
                "Ticker": asset,
                "Asset": format_asset_name(asset),
                "Risk Contribution (%)": value,
            }
            for asset, value in risk_contributions.items()
        ]
    )

    df["Effect"] = df["Risk Contribution (%)"].apply(
        lambda x: "risk-reducing" if x < 0 else "risk-increasing"
    )
    df["Abs Contribution"] = df["Risk Contribution (%)"].abs()

    df = df.sort_values("Abs Contribution", ascending=True).reset_index(drop=True)
    return df


def render_status_banner(data: dict):
    if "feasible" in data:
        if data["feasible"]:
            st.success(data.get("message", "This portfolio satisfies the downside tolerance."))
        else:
            st.warning(
                data.get(
                    "message",
                    "This portfolio exceeds the requested downside tolerance."
                )
            )
    else:
        st.info(data.get("message", "Minimum-risk portfolio for the requested return."))


def render_summary_metrics(data: dict):
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Desired Return", data.get("desired_return", "-"))
    col2.metric("Expected Return", data.get("expected_portfolio_return", "-"))
    col3.metric("Volatility", data.get("portfolio_volatility", "-"))
    col4.metric("Diversification", str(data.get("diversification_level", "-")).title())

    if "max_allowed_volatility" in data:
        st.caption(f"Maximum allowed volatility: {data['max_allowed_volatility']}")


def render_allocation_chart(weights_df: pd.DataFrame):
    st.subheader("Portfolio Allocation")

    if weights_df.empty:
        st.write("No allocation data available.")
        return

    fig = px.pie(
        weights_df,
        names="Asset",
        values="Weight (%)",
        hole=0.55,
    )

    fig.update_traces(
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>Weight: %{value:.2f}%<extra></extra>",
        sort=False
    )

    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        legend_title_text="Assets",
        uniformtext_minsize=12,
        uniformtext_mode="hide",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk_chart(risk_df: pd.DataFrame):
    st.subheader("Risk Contribution by Asset")

    if risk_df.empty:
        st.write("No risk contribution data available.")
        return

    fig = px.bar(
        risk_df,
        x="Risk Contribution (%)",
        y="Ticker",
        orientation="h",
        color="Effect",
        text="Risk Contribution (%)",
        category_orders={"Effect": ["risk-increasing", "risk-reducing"]},
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Asset: %{customdata[0]}<br>"
            "Risk contribution: %{x:.2f}%<extra></extra>"
        ),
        customdata=risk_df[["Asset"]].values,
    )

    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis_title="Risk Contribution (%)",
        yaxis_title="",
        legend_title_text="Effect",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_diagnostics(data: dict):
    st.subheader("Diagnostics")

    col1, col2 = st.columns(2)

    col1.metric("Diversification Ratio", str(data.get("diversification_ratio", "-")))
    col2.metric("Concentration Index", str(data.get("concentration_index", "-")))

    st.write(f"**Diversification level:** {data.get('diversification_level', '-')}")
    st.write(f"**Concentration level:** {data.get('concentration_level', '-')}")


def render_explanation(data: dict):
    bullets = data.get("explanation_bullets", [])
    if bullets:
        st.subheader("Explanation")
        for bullet in bullets:
            st.markdown(f"- {bullet}")


with st.form("portfolio_form"):
    left, right = st.columns(2)

    with left:
        target_return = st.text_input(
            "Desired return",
            placeholder="Examples: 10%, 0.10, 10"
        )

    with right:
        max_volatility = st.text_input(
            "Maximum tolerated volatility (optional)",
            placeholder="Examples: 15%, 0.15, 15"
        )

    submitted = st.form_submit_button("Generate portfolio")


if submitted:
    if not target_return.strip():
        st.error("Please enter a desired return.")
    else:
        payload = {"target_return": target_return.strip()}

        if max_volatility.strip():
            payload["max_volatility"] = max_volatility.strip()

        try:
            with st.spinner("Generating portfolio..."):
                response = requests.post(API_URL, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()

                render_status_banner(data)
                render_summary_metrics(data)

                chart_data = data.get("chart_data", {})
                weights_df = build_weights_df(chart_data)
                risk_df = build_risk_contributions_df(chart_data)

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    render_allocation_chart(weights_df)

                with chart_col2:
                    render_risk_chart(risk_df)

                table_col1, table_col2 = st.columns(2)

                with table_col1:
                    render_weights_table("Portfolio Weights", data.get("weights_percent", {}))

                with table_col2:
                    render_risk_contributions_table(
                        "Risk Contributions",
                        data.get("risk_contributions", {}),
                        data.get("risk_effects", {}),
                    )

                render_diagnostics(data)
                render_explanation(data)

                with st.expander("Important assumptions"):
                    st.markdown(
                        """
- The portfolio is optimized to achieve the requested return with minimum modeled volatility.
- The optimization is long-only.
- The maximum asset weight constraint is 35%.
- Expected returns are based on historical estimates and are clipped for realism.
- Covariance estimation uses Ledoit-Wolf shrinkage.
- This tool is educational and does not constitute personal financial advice.
"""
                    )

            else:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                st.error(f"Backend error: {detail}")

        except requests.exceptions.ConnectionError:
            st.error(
                "Could not connect to the FastAPI backend. Make sure the API is running at "
                "http://127.0.0.1:8000"
            )
        except requests.exceptions.Timeout:
            st.error("The request timed out. Please try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.divider()
st.caption("Run the backend first with: uvicorn api.server:app --reload")
st.caption("Run this frontend with: python -m streamlit run streamlit_app.py")