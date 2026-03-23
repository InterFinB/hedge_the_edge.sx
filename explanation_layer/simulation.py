def generate_simulation_commentary(
    feasible=None,
    simulation_mean_return=None,
    simulation_median_return=None,
    simulation_loss_probability=None,
    simulation_percentile_5=None,
    simulation_percentile_95=None,
):
    bullets = []

    if feasible is True:
        bullets.append("This portfolio stays within the downside limit.")
    elif feasible is False:
        bullets.append("This portfolio goes beyond the downside limit.")

    has_simulation = all(
        value is not None
        for value in [
            simulation_mean_return,
            simulation_median_return,
            simulation_loss_probability,
            simulation_percentile_5,
            simulation_percentile_95,
        ]
    )

    if not has_simulation:
        return bullets

    bullets.append(
        f"Modeled chance of a negative 1-year return: {simulation_loss_probability:.2%}."
    )

    bullets.append(
        f"Modeled range of outcomes: about {simulation_percentile_5:.2%} in weaker scenarios to {simulation_percentile_95:.2%} in stronger ones."
    )

    spread = simulation_percentile_95 - simulation_percentile_5
    if spread > 0.30:
        bullets.append("The range of outcomes is wide, so uncertainty remains important.")
    elif spread > 0.15:
        bullets.append("The range of outcomes is moderate.")
    else:
        bullets.append("The range of outcomes is relatively tight.")

    return bullets[:4]