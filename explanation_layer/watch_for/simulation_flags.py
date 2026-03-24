def generate_simulation_flags(
    simulation_loss_probability,
    simulation_percentile_5,
    simulation_percentile_95,
    portfolio_volatility,
    max_volatility=None,
):

    items = []

    if simulation_loss_probability is None:
        return items

    # -------------------------
    # loss probability
    # -------------------------

    if simulation_loss_probability > 0.25:

        items.append(
            {
                "kind": "loss_probability",
                "asset": None,
                "priority": 95,
                "message": (
                    "Watch loss probability: the modeled probability of negative return is elevated. "
                    "If volatility increases, recompute the portfolio."
                ),
            }
        )

    # -------------------------
    # dispersion
    # -------------------------

    if (
        simulation_percentile_5 is not None
        and simulation_percentile_95 is not None
    ):

        spread = simulation_percentile_95 - simulation_percentile_5

        if spread > 0.30:

            items.append(
                {
                    "kind": "dispersion",
                    "asset": None,
                    "priority": 80,
                    "message": (
                        "Watch dispersion: the simulated return distribution is wide, "
                        "indicating high uncertainty of outcomes."
                    ),
                }
            )

    # -------------------------
    # volatility limit
    # -------------------------

    if max_volatility is not None and max_volatility > 0:

        if portfolio_volatility >= 0.9 * max_volatility:

            items.append(
                {
                    "kind": "volatility_limit",
                    "asset": None,
                    "priority": 100,
                    "message": (
                        "Watch volatility: portfolio volatility is close to the downside limit. "
                        "If volatility rises further, reduce higher-volatility allocations."
                    ),
                }
            )

    return items