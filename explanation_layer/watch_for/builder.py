from .portfolio_triggers import generate_portfolio_triggers
from .growth_flags import generate_growth_flags
from .simulation_flags import generate_simulation_flags
from .news_watch import generate_news_watch_items
from .formatter import format_watch_for_items


def generate_watch_for(
    weights,
    risk_contributions,
    concentration,
    diversification_ratio,
    portfolio_volatility,
    expected_portfolio_return,
    simulation_loss_probability=None,
    simulation_percentile_5=None,
    simulation_percentile_95=None,
    max_volatility=None,
    max_weight_constraint=0.35,
):

    portfolio_items = generate_portfolio_triggers(
        weights=weights,
        risk_contributions=risk_contributions,
        concentration=concentration,
        diversification_ratio=diversification_ratio,
        portfolio_volatility=portfolio_volatility,
        max_volatility=max_volatility,
        max_weight_constraint=max_weight_constraint,
    )

    growth_items = generate_growth_flags(
        weights=weights,
        risk_contributions=risk_contributions,
        expected_portfolio_return=expected_portfolio_return,
    )

    simulation_items = generate_simulation_flags(
        simulation_loss_probability=simulation_loss_probability,
        simulation_percentile_5=simulation_percentile_5,
        simulation_percentile_95=simulation_percentile_95,
        portfolio_volatility=portfolio_volatility,
        max_volatility=max_volatility,
    )

    news_items = generate_news_watch_items()

    all_items = (
        portfolio_items
        + growth_items
        + simulation_items
        + news_items
    )

    return format_watch_for_items(all_items, max_items=3)