def generate_simulation_commentary(
    feasible=None,
    simulation_mean_return=None,
    simulation_median_return=None,
    simulation_loss_probability=None,
    simulation_percentile_5=None,
    simulation_percentile_95=None,
):

    bullets = []

    has_sim = all(
        v is not None
        for v in [
            simulation_mean_return,
            simulation_median_return,
            simulation_loss_probability,
            simulation_percentile_5,
            simulation_percentile_95,
        ]
    )

    if not has_sim:
        return bullets

    # -----------------------------
    # 1 — downside probability
    # -----------------------------

    loss_prob = simulation_loss_probability

    if loss_prob < 0.10:
        bullets.append(
            f"Modeled probability of negative 1-year return is low ({loss_prob:.2%})."
        )
    elif loss_prob < 0.25:
        bullets.append(
            f"Modeled probability of negative 1-year return is moderate ({loss_prob:.2%})."
        )
    else:
        bullets.append(
            f"Modeled probability of negative 1-year return is elevated ({loss_prob:.2%})."
        )

    # -----------------------------
    # 2 — outcome range
    # -----------------------------

    p5 = simulation_percentile_5
    p95 = simulation_percentile_95

    spread = p95 - p5

    bullets.append(
        f"Modeled return range is approximately {p5:.2%} to {p95:.2%}."
    )

    # -----------------------------
    # 3 — range interpretation
    # -----------------------------

    if spread < 0.15:
        bullets.append(
            "Outcome dispersion is relatively tight, suggesting stable risk assumptions."
        )

    elif spread < 0.30:
        bullets.append(
            "Outcome dispersion is moderate, indicating meaningful uncertainty."
        )

    else:
        bullets.append(
            "Outcome dispersion is wide, indicating sensitivity to market conditions."
        )

    # -----------------------------
    # 4 — mean vs median insight
    # -----------------------------

    mean_r = simulation_mean_return
    med_r = simulation_median_return

    if mean_r > med_r + 0.01:
        bullets.append(
            "Mean return is above median, indicating upside-driven scenarios dominate the distribution."
        )

    elif med_r > mean_r + 0.01:
        bullets.append(
            "Median return exceeds mean, indicating downside scenarios have noticeable impact."
        )

    return bullets[:4]