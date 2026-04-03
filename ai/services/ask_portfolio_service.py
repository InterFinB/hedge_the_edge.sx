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
        return fallback_ask_portfolio_response(question="")

    try:
        prompt = build_ask_portfolio_prompt(
            question=question,
            ai_context=ai_context.model_dump(),
            conversation=[turn.model_dump() for turn in (conversation or [])],
        )

        client = LLMClient()

        raw = client.generate_json(prompt)

        validated = validate_ask_portfolio_response(raw)

        # enforce version
        validated.prompt_version = validated.prompt_version or PROMPT_VERSION

        return validated

    except (LLMClientError, ValueError) as e:
        # safe fallback for ANY LLM issue
        return fallback_ask_portfolio_response(question=question)

    except Exception as e:
        # absolute fallback — never break API
        return AskPortfolioResponse(
            answer="Something went wrong while generating the AI response.",
            reasoning_summary=[
                "The system encountered an unexpected error."
            ],
            watch_for=[
                "Retry the question in a moment.",
                "If the issue persists, check backend logs.",
            ],
            follow_up_suggestions=[
                "What is the main risk?",
                "Explain the allocation",
            ],
            source="fallback",
            prompt_version=PROMPT_VERSION,
        )