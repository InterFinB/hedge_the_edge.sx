from .utils import classify_loss_probability, classify_dispersion


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

    loss_prob = simulation_loss_probability
    loss_level = classify_loss_probability(loss_prob)

    if loss_level == "low":
        bullets.append(
            f"Modeled probability of a negative 1-year return is low ({loss_prob:.2%})."
        )
    elif loss_level == "moderate":
        bullets.append(
            f"Modeled probability of a negative 1-year return is moderate ({loss_prob:.2%})."
        )
    else:
        bullets.append(
            f"Modeled probability of a negative 1-year return is elevated ({loss_prob:.2%})."
        )

    p5 = simulation_percentile_5
    p95 = simulation_percentile_95
    spread = p95 - p5

    bullets.append(
        f"Modeled return range is approximately {p5:.2%} to {p95:.2%}."
    )

    dispersion = classify_dispersion(p5, p95)
    if dispersion == "tight":
        bullets.append(
            "Outcome dispersion is relatively tight, suggesting more stable simulated outcomes."
        )
    elif dispersion == "moderate":
        bullets.append(
            "Outcome dispersion is moderate, indicating meaningful uncertainty around the central case."
        )
    else:
        bullets.append(
            "Outcome dispersion is wide, indicating a broad range of possible outcomes under the simulation assumptions."
        )

    mean_r = simulation_mean_return
    med_r = simulation_median_return

    if mean_r > med_r + 0.01:
        bullets.append(
            "Mean return is above median, which suggests the distribution is supported by stronger upside scenarios."
        )
    elif med_r > mean_r + 0.01:
        bullets.append(
            "Median return is above mean, which suggests weaker downside outcomes pull down the average."
        )

    return bullets[:4]