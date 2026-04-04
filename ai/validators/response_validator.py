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
    follow_ups = _clean_string_list(payload.get("follow_ups"))

    return AskPortfolioResponse(
      answer=answer.strip(),
      why=why,
      follow_ups=follow_ups,
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
      ],
      follow_ups=[
        "What part of the portfolio would you like to explore next?",
        "Would you like to look at risk, returns, or diversification?",
      ],
      source="fallback",
      prompt_version="step2_v1",
    )