from __future__ import annotations

import json

from ai.prompts.system_prompt import SYSTEM_PROMPT

PROMPT_VERSION = "step1_v2"


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

You are answering questions about a generated investment portfolio.

Write like a strong portfolio assistant:
- be clear, direct, and specific
- sound conversational, not robotic
- do not produce section headers like "Reasoning summary", "Watch for", or "Follow-up ideas"
- do not repeat raw JSON field names
- stay grounded in the provided portfolio context
- do not invent metrics, holdings, or exposures that are not present
- when uncertainty exists, say so plainly
- prefer decisive wording when the context supports it

Return this exact JSON shape:
{{
  "answer": "string",
  "why": ["string"]
}}

Rules for the JSON:
- "answer" must be the main user-facing response in natural prose
- "why" must be a short list of brief supporting reasons
- keep "why" compact and useful
- do not include markdown code fences
- do not return any keys other than "answer" and "why"

Prompt version: {PROMPT_VERSION}

Conversation so far:
{serialized_conversation}

User question:
{question}

AI context:
{serialized_context}
""".strip()