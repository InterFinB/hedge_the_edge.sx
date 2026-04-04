from __future__ import annotations

from ai.prompts.ask_portfolio_prompt import (
    PROMPT_VERSION,
    build_ask_portfolio_prompt,
)
from ai.schemas import AIContext, AskPortfolioResponse, ConversationTurn
from ai.services.llm_client import LLMClient, LLMClientError
from ai.validators.response_validator import (
    fallback_ask_portfolio_response,
    validate_ask_portfolio_response,
)


def ask_portfolio_question(
    *,
    question: str,
    ai_context: AIContext,
    conversation: list[ConversationTurn] | None = None,
) -> AskPortfolioResponse:
    question = (question or "").strip()

    if not question:
        return AskPortfolioResponse(
            answer="Please ask a question about the portfolio.",
            why=[
                "The request was empty, so there was nothing specific to analyze."
            ],
            source="fallback",
            prompt_version=PROMPT_VERSION,
        )

    try:
        prompt = build_ask_portfolio_prompt(
            question=question,
            ai_context=ai_context.model_dump(),
            conversation=[turn.model_dump() for turn in (conversation or [])],
        )

        client = LLMClient()
        raw = client.generate_json(prompt)

        validated = validate_ask_portfolio_response(raw)
        validated.prompt_version = validated.prompt_version or PROMPT_VERSION

        return validated

    except (LLMClientError, ValueError):
        fallback = fallback_ask_portfolio_response(question=question)
        fallback.prompt_version = fallback.prompt_version or PROMPT_VERSION
        return fallback

    except Exception:
        return AskPortfolioResponse(
            answer="Something went wrong while generating the AI response.",
            why=[
                "The system encountered an unexpected error.",
                "Try asking again in a moment.",
            ],
            source="fallback",
            prompt_version=PROMPT_VERSION,
        )