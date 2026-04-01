from __future__ import annotations

import json

from ai.prompts.system_prompt import SYSTEM_PROMPT

PROMPT_VERSION = "step1_v1"


def build_ask_portfolio_prompt(
    *,
    question: str,
    ai_context: dict,
    conversation: list[dict] | None = None,
) -> str:
    conversation = conversation or []

    serialized_context = json.dumps(ai_context, ensure_ascii=False, indent=2)
    serialized_conversation = json.dumps(conversation, ensure_ascii=False, indent=2)

    return f"""
{SYSTEM_PROMPT}

Return this exact JSON shape:
{{
  "answer": "string",
  "reasoning_summary": ["string"],
  "watch_for": ["string"],
  "follow_up_suggestions": ["string"]
}}

Prompt version: {PROMPT_VERSION}

Conversation so far:
{serialized_conversation}

User question:
{question}

AI context:
{serialized_context}
""".strip()