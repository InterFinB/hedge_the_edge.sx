from .summary import generate_portfolio_summary
from .risk import generate_risk_commentary
from .simulation import generate_simulation_commentary
from .watch_for import generate_watch_for
from .takeaways import generate_takeaways
from .vocabulary import generate_vocabulary


def generate_explanation_bullets(
    desired_return,
    expected_portfolio_return,
    portfolio_volatility,
    weights,
    risk_contributions,
    diversification_ratio,
    concentration,
    feasible=None,
    max_weight_constraint=0.35,
    simulation_mean_return=None,
    simulation_median_return=None,
    simulation_loss_probability=None,
    simulation_percentile_5=None,
    simulation_percentile_95=None,
):
    sections = []

    summary = generate_portfolio_summary(
        desired_return=desired_return,
        expected_portfolio_return=expected_portfolio_return,
        portfolio_volatility=portfolio_volatility,
        weights=weights,
        diversification_ratio=diversification_ratio,
        concentration=concentration,
        max_weight_constraint=max_weight_constraint,
    )

    risk = generate_risk_commentary(
        weights=weights,
        risk_contributions=risk_contributions,
    )

    simulation = generate_simulation_commentary(
        feasible=feasible,
        simulation_mean_return=simulation_mean_return,
        simulation_median_return=simulation_median_return,
        simulation_loss_probability=simulation_loss_probability,
        simulation_percentile_5=simulation_percentile_5,
        simulation_percentile_95=simulation_percentile_95,
    )

    watch_for = generate_watch_for(
        weights=weights,
        risk_contributions=risk_contributions,
        max_weight_constraint=max_weight_constraint,
    )

    takeaways = generate_takeaways(
        concentration=concentration,
        diversification_ratio=diversification_ratio,
        risk_contributions=risk_contributions,
        simulation_loss_probability=simulation_loss_probability,
    )

    used_terms = set()
    if summary or risk or simulation or watch_for or takeaways:
        used_terms.update(["Risk", "Diversification", "Concentration", "Risk contribution"])
    if simulation:
        used_terms.add("Modeled range of outcomes")
    if feasible is not None:
        used_terms.add("Downside limit")

    vocabulary = generate_vocabulary(sorted(used_terms))

    if summary:
        sections.append("Portfolio Summary")
        sections.extend(summary)

    if risk:
        sections.append("Risk Commentary")
        sections.extend(risk)

    if simulation:
        sections.append("Simulation Commentary")
        sections.extend(simulation)

    if watch_for:
        sections.append("Watch For")
        sections.extend(watch_for)

    if takeaways:
        sections.append("Takeaways")
        sections.extend(takeaways)

    if vocabulary:
        sections.append("Vocabulary")
        sections.extend(vocabulary)

    return sections