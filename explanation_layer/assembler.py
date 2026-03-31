from .summary import generate_portfolio_summary
from .risk import generate_risk_commentary
from .simulation import generate_simulation_commentary
from .takeaways import generate_takeaways
from .vocabulary import generate_vocabulary


def generate_explanation(
    desired_return,
    expected_portfolio_return,
    portfolio_volatility,
    weights,
    risk_contributions,
    diversification_ratio,
    concentration,
    feasible=None,
    max_volatility=None,
    max_weight_constraint=0.35,
    simulation_mean_return=None,
    simulation_median_return=None,
    simulation_loss_probability=None,
    simulation_percentile_5=None,
    simulation_percentile_95=None,
):
    portfolio_summary = generate_portfolio_summary(
        desired_return=desired_return,
        expected_portfolio_return=expected_portfolio_return,
        portfolio_volatility=portfolio_volatility,
        weights=weights,
        diversification_ratio=diversification_ratio,
        concentration=concentration,
        max_weight_constraint=max_weight_constraint,
    )

    risk_commentary = generate_risk_commentary(
        weights=weights,
        risk_contributions=risk_contributions,
    )

    simulation_commentary = generate_simulation_commentary(
        feasible=feasible,
        simulation_mean_return=simulation_mean_return,
        simulation_median_return=simulation_median_return,
        simulation_loss_probability=simulation_loss_probability,
        simulation_percentile_5=simulation_percentile_5,
        simulation_percentile_95=simulation_percentile_95,
    )

    watch_for = []

    takeaways = generate_takeaways(
        concentration=concentration,
        diversification_ratio=diversification_ratio,
        risk_contributions=risk_contributions,
        simulation_loss_probability=simulation_loss_probability,
        portfolio_volatility=portfolio_volatility,
        desired_return=desired_return,
    )

    used_terms = set()

    if portfolio_summary:
        used_terms.update({
            "Expected return",
            "Volatility",
            "Allocation",
            "Diversification",
            "Diversification ratio",
            "Concentration",
        })

    if risk_commentary:
        used_terms.update({
            "Risk contribution",
            "Correlation",
        })

    if simulation_commentary:
        used_terms.update({
            "Monte Carlo simulation",
            "Modeled range of outcomes",
            "Dispersion",
            "Loss probability",
            "Percentile",
        })

    if feasible is not None:
        used_terms.add("Downside limit")

    if any(
        "constraint" in bullet.lower()
        for bullet in (
            portfolio_summary
            + risk_commentary
        )
    ):
        used_terms.update({
            "Weight constraint",
            "Constraint",
        })

    vocabulary = generate_vocabulary(sorted(used_terms))

    return {
        "portfolio_summary": portfolio_summary,
        "risk_commentary": risk_commentary,
        "simulation_commentary": simulation_commentary,
        "watch_for": watch_for,
        "takeaways": takeaways,
        "vocabulary": vocabulary,
    }