from __future__ import annotations

from ai.schemas import AskPortfolioResponse


def _clean_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def validate_ask_portfolio_response(payload: object) -> AskPortfolioResponse:
    if not isinstance(payload, dict):
        raise ValueError("AI response is not a JSON object.")

    answer = payload.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("AI response is missing a valid 'answer' field.")

    why = _clean_string_list(payload.get("why"))

    return AskPortfolioResponse(
        answer=answer.strip(),
        why=why,
        source="llm",
        prompt_version=payload.get("prompt_version")
        if isinstance(payload.get("prompt_version"), str)
        else None,
    )


def fallback_ask_portfolio_response(question: str) -> AskPortfolioResponse:
    return AskPortfolioResponse(
        answer=(
            "I could not generate a reliable portfolio-specific answer for that question "
            "from the available context."
        ),
        why=[
            "The AI response was unavailable or invalid.",
            "The portfolio data itself is still intact.",
            "Try narrowing the question to one issue like concentration, downside risk, or top holdings.",
        ],
        source="fallback",
        prompt_version="step1_v2",
    )