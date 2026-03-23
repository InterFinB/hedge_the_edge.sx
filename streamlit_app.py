import streamlit as st
import requests
import pandas as pd
import plotly.express as px

from portfolio_engine.config import TICKER_TO_NAME, TICKER_TO_CATEGORY

API_URL = "http://127.0.0.1:8000/portfolio"

st.set_page_config(page_title="Hedge The Edge", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }
    .sub-text {
        color: #6b7280;
        margin-bottom: 1.2rem;
    }
    .section-card {
        background: #ffffff;
        padding: 1.1rem 1.2rem;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 8px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.12rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .bullet-item {
        margin-bottom: 0.4rem;
        color: #111827;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">Hedge The Edge</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-text">AI-powered minimum-risk portfolio advisor</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
Enter your target return and, optionally, your maximum tolerated volatility.

The app builds a **minimum-risk portfolio** for that target and explains the result in a clean, readable way.
"""
)


def format_asset_name(ticker: str) -> str:
    name = TICKER_TO_NAME.get(ticker)
    return f"{ticker} ({name})" if name else ticker


def get_asset_category(ticker: str) -> str:
    return TICKER_TO_CATEGORY.get(ticker, "Other")


def set_table_index_from_one(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.index = range(1, len(df) + 1)
    return df


def format_percent_value(value, decimals=2) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return str(value)


def render_card(title: str, render_fn):
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
        render_fn()
        st.markdown("</div>", unsafe_allow_html=True)


def render_weights_table(title: str, data: dict):
    def content():
        if not data:
            st.write("No data available.")
            return

        rows = []
        for ticker, value in data.items():
            rows.append(
                {
                    "Asset": format_asset_name(ticker),
                    "Weight": format_percent_value(value),
                }
            )

        df = pd.DataFrame(rows)
        df = set_table_index_from_one(df)
        st.dataframe(df, use_container_width=True, hide_index=False)

    render_card(title, content)


def render_risk_contributions_table(title: str, contributions: dict, effects: dict):
    def content():
        if not contributions:
            st.write("No data available.")
            return

        rows = []
        for ticker, value in contributions.items():
            rows.append(
                {
                    "Asset": format_asset_name(ticker),
                    "Risk Contribution": format_percent_value(value),
                    "Effect": effects.get(ticker, "-"),
                }
            )

        df = pd.DataFrame(rows)
        df = set_table_index_from_one(df)
        st.dataframe(df, use_container_width=True, hide_index=False)

    render_card(title, content)


def render_category_exposure_table(title: str, category_df: pd.DataFrame):
    def content():
        if category_df.empty:
            st.write("No data available.")
            return

        df = category_df.copy()
        df["Weight"] = df["Weight (%)"].map(lambda x: f"{x:.2f}%")
        df = df[["Category", "Weight"]]
        df = set_table_index_from_one(df)
        st.dataframe(df, use_container_width=True, hide_index=False)

    render_card(title, content)


def build_weights_df(chart_data: dict) -> pd.DataFrame:
    weights = chart_data.get("weights", {})
    if not weights:
        return pd.DataFrame(columns=["Ticker", "Asset", "Category", "Weight", "Weight (%)"])

    df = pd.DataFrame(
        [
            {
                "Ticker": asset,
                "Asset": format_asset_name(asset),
                "Category": get_asset_category(asset),
                "Weight": weight,
            }
            for asset, weight in weights.items()
        ]
    )
    df["Weight (%)"] = df["Weight"] * 100
    df = df.sort_values("Weight (%)", ascending=False).reset_index(drop=True)
    return df


def build_category_exposure_df(weights_df: pd.DataFrame) -> pd.DataFrame:
    if weights_df.empty:
        return pd.DataFrame(columns=["Category", "Weight (%)"])

    df = (
        weights_df.groupby("Category", as_index=False)["Weight (%)"]
        .sum()
        .sort_values("Weight (%)", ascending=False)
        .reset_index(drop=True)
    )
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
        lambda x: "Risk-reducing" if x < 0 else "Risk-increasing"
    )
    df["Abs Contribution"] = df["Risk Contribution (%)"].abs()
    df = df.sort_values("Abs Contribution", ascending=True).reset_index(drop=True)
    return df


def build_simulation_distribution_df(chart_data: dict) -> pd.DataFrame:
    distribution = chart_data.get("simulation_distribution", [])
    if not distribution:
        return pd.DataFrame(columns=["Return (%)", "Frequency"])

    df = pd.DataFrame(distribution)
    df["Return (%)"] = df["bin_center"] * 100
    df["Frequency"] = df["frequency"]
    return df[["Return (%)", "Frequency"]]


def render_status_banner(data: dict):
    if "feasible" in data:
        if data["feasible"]:
            st.success(data.get("message", "This portfolio stays within the downside limit."))
        else:
            st.warning(data.get("message", "This portfolio goes beyond the downside limit."))
    else:
        st.info(data.get("message", "Minimum-risk portfolio for the requested return."))


def render_summary_metrics(data: dict):
    st.subheader("Portfolio Snapshot")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Target Return", data.get("desired_return", "-"))
    col2.metric("Expected Return", data.get("expected_portfolio_return", "-"))
    col3.metric("Risk (Vol)", data.get("portfolio_volatility", "-"))
    col4.metric("Diversification", str(data.get("diversification_level", "-")).title())

    if "max_allowed_volatility" in data:
        st.caption(f"Maximum allowed volatility: {data['max_allowed_volatility']}")


def render_allocation_chart(weights_df: pd.DataFrame):
    def content():
        if weights_df.empty:
            st.write("No allocation data available.")
            return

        fig = px.pie(
            weights_df,
            names="Ticker",
            values="Weight (%)",
            hole=0.58,
        )

        fig.update_traces(
            textinfo="none",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Asset: %{customdata[0]}<br>"
                "Category: %{customdata[1]}<br>"
                "Weight: %{value:.2f}%<extra></extra>"
            ),
            customdata=weights_df[["Asset", "Category"]].values,
            sort=False,
        )

        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            legend_title_text="Assets",
        )

        st.plotly_chart(fig, use_container_width=True)

    render_card("Portfolio Allocation", content)


def render_category_exposure_chart(category_df: pd.DataFrame):
    def content():
        if category_df.empty:
            st.write("No category exposure data available.")
            return

        fig = px.pie(
            category_df,
            names="Category",
            values="Weight (%)",
            hole=0.58,
        )

        fig.update_traces(
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>Weight: %{value:.2f}%<extra></extra>",
            sort=False,
        )

        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            legend_title_text="Categories",
        )

        st.plotly_chart(fig, use_container_width=True)

    render_card("Category Exposure", content)


def render_risk_chart(risk_df: pd.DataFrame):
    def content():
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
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Risk Contribution (%)",
            yaxis_title="",
            legend_title_text="Effect",
        )

        st.plotly_chart(fig, use_container_width=True)

    render_card("Risk Contribution by Asset", content)


def render_diagnostics(data: dict):
    def content():
        col1, col2 = st.columns(2)
        col1.metric("Diversification Ratio", str(data.get("diversification_ratio", "-")))
        col2.metric("Concentration Index", str(data.get("concentration_index", "-")))

        st.caption(f"Diversification level: {data.get('diversification_level', '-')}")
        st.caption(f"Concentration level: {data.get('concentration_level', '-')}")

    render_card("Diagnostics", content)


def render_simulation_summary(data: dict):
    simulation = data.get("simulation", {})
    if not simulation:
        return

    def content():
        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Mean", simulation.get("mean_return", "-"))
        col2.metric("Median", simulation.get("median_return", "-"))
        col3.metric("Loss Chance", simulation.get("loss_probability", "-"))
        col4.metric("5th %ile", simulation.get("percentile_5", "-"))
        col5.metric("95th %ile", simulation.get("percentile_95", "-"))

        st.caption("These simulated outcomes are model-based scenarios, not forecasts.")

    render_card("Simulation Summary", content)


def render_simulation_distribution_chart(simulation_df: pd.DataFrame):
    def content():
        if simulation_df.empty:
            st.write("No simulation distribution data available.")
            return

        fig = px.bar(
            simulation_df,
            x="Return (%)",
            y="Frequency",
        )

        fig.update_traces(
            hovertemplate=(
                "Return bin center: %{x:.2f}%<br>"
                "Frequency: %{y}<extra></extra>"
            )
        )

        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Simulated 1-Year Return (%)",
            yaxis_title="Frequency",
        )

        st.plotly_chart(fig, use_container_width=True)

    render_card("Simulated Return Distribution", content)


def split_explanation_sections(bullets):
    sections = {}
    current_section = None

    known_headers = {
        "Portfolio Summary",
        "Risk Commentary",
        "Simulation Commentary",
        "Watch For",
        "Takeaways",
        "Vocabulary",
    }

    for item in bullets:
        if item in known_headers:
            current_section = item
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(item)

    return sections


def render_explanation(data: dict):
    bullets = data.get("explanation_bullets", [])
    if not bullets:
        return

    sections = split_explanation_sections(bullets)
    if not sections:
        return

    st.subheader("Explanation")

    preferred_order = [
        "Portfolio Summary",
        "Risk Commentary",
        "Simulation Commentary",
        "Watch For",
        "Takeaways",
        "Vocabulary",
    ]

    for section_name in preferred_order:
        items = sections.get(section_name, [])
        if not items:
            continue

        def content(section_items=items):
            for bullet in section_items:
                st.markdown(
                    f"<div class='bullet-item'>• {bullet}</div>",
                    unsafe_allow_html=True
                )

        render_card(section_name, content)


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
                category_df = build_category_exposure_df(weights_df)
                risk_df = build_risk_contributions_df(chart_data)
                simulation_df = build_simulation_distribution_df(chart_data)

                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    render_allocation_chart(weights_df)
                with chart_col2:
                    render_risk_chart(risk_df)

                category_col1, category_col2 = st.columns(2)
                with category_col1:
                    render_category_exposure_chart(category_df)
                with category_col2:
                    render_category_exposure_table("Category Exposure Table", category_df)

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
                render_simulation_summary(data)
                render_simulation_distribution_chart(simulation_df)
                render_explanation(data)

                with st.expander("Important assumptions"):
                    st.markdown(
                        """
- The portfolio is optimized to achieve the requested return with minimum modeled volatility.
- The optimization is long-only.
- The maximum asset weight constraint is 35%.
- Expected returns are based on historical estimates and clipped for realism.
- Covariance estimation uses Ledoit-Wolf shrinkage.
- Monte Carlo results are model-based simulations, not forecasts.
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
                "Could not connect to the FastAPI backend. Make sure the API is running at http://127.0.0.1:8000"
            )
        except requests.exceptions.Timeout:
            st.error("The request timed out. Please try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.divider()
st.caption("Run the backend first with: uvicorn api.server:app --reload")
st.caption("Run this frontend with: python -m streamlit run streamlit_app.py")