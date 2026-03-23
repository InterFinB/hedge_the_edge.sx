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
    """
    Generate readable bullet-point explanations for the portfolio recommendation.
    """

    bullets = []

    active_assets = {k: v for k, v in weights.items() if v > 0.001}
    zero_weight_assets = [k for k, v in weights.items() if v <= 0.001]

    sorted_assets = sorted(active_assets.items(), key=lambda x: x[1], reverse=True)
    top_assets = sorted_assets[:3]

    sorted_risk = sorted(risk_contributions.items(), key=lambda x: x[1], reverse=True)
    top_risk_assets = [asset for asset, contrib in sorted_risk if contrib > 0][:3]
    negative_risk_assets = [asset for asset, contrib in risk_contributions.items() if contrib < 0]

    bullets.append(
        f"Requested return: {desired_return:.2%}. "
        f"Estimated portfolio return: {expected_portfolio_return:.2%}. "
        f"Estimated portfolio volatility: {portfolio_volatility:.2%}."
    )

    if top_assets:
        top_alloc_text = ", ".join(
            [f"{asset} ({weight:.1%})" for asset, weight in top_assets]
        )
        bullets.append(
            f"Top allocations: {top_alloc_text}. These assets offered the most efficient "
            f"return-risk tradeoff under the optimization constraints."
        )

    defensive_assets = []
    growth_assets = []
    diversifiers = []
    defensive_equity = []
    cyclical_assets = []

    for asset in active_assets.keys():
        if asset in ["AGG", "TLT", "LQD"]:
            defensive_assets.append(asset)

        elif asset in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "QQQ", "SPY", "IJR", "VWO"]:
            growth_assets.append(asset)

        elif asset in ["GLD", "DBC", "VEA", "VNQ", "XLV", "XLF", "XLE", "XLI"]:
            diversifiers.append(asset)

        if asset in ["JNJ", "UNH", "XLV"]:
            defensive_equity.append(asset)

        if asset in ["XOM", "XLE", "DBC"]:
            cyclical_assets.append(asset)

    if defensive_assets:
        bullets.append(
            f"Defensive exposure: {', '.join(defensive_assets)}. These assets help reduce overall volatility."
        )

    if defensive_equity:
        bullets.append(
            f"Defensive equity exposure: {', '.join(defensive_equity)}. These assets can support returns while usually being less volatile than high-growth equities."
        )

    if diversifiers:
        bullets.append(
            f"Diversification support: {', '.join(diversifiers)}. These assets add exposure to different market drivers."
        )

    if growth_assets:
        bullets.append(
            f"Growth exposure: {', '.join(growth_assets)}. These assets help the portfolio reach the return target."
        )

    if cyclical_assets:
        bullets.append(
            f"Cyclical / inflation-sensitive exposure: {', '.join(cyclical_assets)}. These assets can behave differently from bonds or defensive equities and improve diversification."
        )

    if top_risk_assets:
        bullets.append(
            f"Main risk contributors: {', '.join(top_risk_assets)}. These assets account for the largest share of portfolio risk."
        )

    if negative_risk_assets:
        bullets.append(
            f"Negative risk contributors: {', '.join(negative_risk_assets)}. A negative contribution means these assets help offset the risk of the rest of the portfolio because of their covariance structure. In practice, they act as hedges and reduce total portfolio volatility."
        )

    if diversification_ratio < 1.2:
        div_comment = "This suggests relatively weak diversification."
    elif diversification_ratio <= 1.5:
        div_comment = "This suggests moderate diversification."
    else:
        div_comment = "This suggests strong diversification."

    bullets.append(
        f"Diversification ratio: {diversification_ratio:.2f}. Typical interpretation: below 1.2 is low, 1.2 to 1.5 is moderate, and above 1.5 is strong. {div_comment}"
    )

    if concentration < 0.15:
        conc_comment = "This suggests low concentration."
    elif concentration <= 0.25:
        conc_comment = "This suggests moderate concentration."
    else:
        conc_comment = "This suggests high concentration."

    bullets.append(
        f"Concentration index: {concentration:.3f}. Typical interpretation: below 0.15 is low concentration, 0.15 to 0.25 is moderate, and above 0.25 is high. {conc_comment}"
    )

    capped_assets = [
        asset for asset, weight in active_assets.items()
        if abs(weight - max_weight_constraint) < 0.001
    ]
    if capped_assets:
        bullets.append(
            f"Constraint effect: the maximum weight cap of {max_weight_constraint:.0%} was binding for "
            f"{', '.join(capped_assets)}."
        )

    if zero_weight_assets:
        preview = ", ".join(zero_weight_assets[:5])
        bullets.append(
            f"Excluded or near-zero-weight assets: {preview}. These assets did not improve the portfolio enough under current estimates."
        )

    if feasible is True:
        bullets.append(
            "Risk tolerance check: the portfolio satisfies the user's downside tolerance."
        )
    elif feasible is False:
        bullets.append(
            "Risk tolerance check: the portfolio exceeds the user's downside tolerance."
        )

    # Monte Carlo interpretation
    if (
        simulation_mean_return is not None
        and simulation_median_return is not None
        and simulation_loss_probability is not None
        and simulation_percentile_5 is not None
        and simulation_percentile_95 is not None
    ):
        bullets.append(
            f"Monte Carlo simulation summary: the mean simulated 1-year return is {simulation_mean_return:.2%}, "
            f"the median is {simulation_median_return:.2%}, and the estimated probability of a negative 1-year return is {simulation_loss_probability:.2%}."
        )

        bullets.append(
            f"Monte Carlo range: in a weaker outcome scenario, the 5th percentile simulated return is {simulation_percentile_5:.2%}; "
            f"in a stronger scenario, the 95th percentile simulated return is {simulation_percentile_95:.2%}."
        )

        if simulation_loss_probability < 0.10:
            mc_comment = "This suggests relatively limited modeled downside over a 1-year horizon."
        elif simulation_loss_probability <= 0.25:
            mc_comment = "This suggests a meaningful but still moderate modeled chance of loss over a 1-year horizon."
        else:
            mc_comment = "This suggests a materially elevated modeled chance of loss over a 1-year horizon."

        bullets.append(
            f"Monte Carlo interpretation: {mc_comment}"
        )

        spread = simulation_percentile_95 - simulation_percentile_5
        if spread < 0.15:
            spread_comment = "The simulated range is relatively tight, which suggests outcomes are comparatively stable under the model assumptions."
        elif spread <= 0.30:
            spread_comment = "The simulated range is moderate, which suggests a noticeable but not extreme spread of possible outcomes."
        else:
            spread_comment = "The simulated range is wide, which suggests outcomes are sensitive to market conditions and uncertainty remains significant."

        bullets.append(
            f"Monte Carlo dispersion: the gap between the 5th and 95th percentile outcomes is {spread:.2%}. {spread_comment}"
        )

    return bullets