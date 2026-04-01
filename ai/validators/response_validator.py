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

    return AskPortfolioResponse(
        answer=answer.strip(),
        reasoning_summary=_clean_string_list(payload.get("reasoning_summary")),
        watch_for=_clean_string_list(payload.get("watch_for")),
        follow_up_suggestions=_clean_string_list(payload.get("follow_up_suggestions")),
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
        reasoning_summary=[
            "The AI response was unavailable or invalid.",
            "The portfolio data itself is still intact.",
        ],
        watch_for=[
            "Try asking about one aspect at a time, such as concentration, downside risk, or top holdings."
        ],
        follow_up_suggestions=[
            "Why is the largest position so large?",
            "What does the simulation downside mean here?",
            "Is this portfolio concentrated or diversified?",
        ],
        source="fallback",
        prompt_version="step1_v1",
    )