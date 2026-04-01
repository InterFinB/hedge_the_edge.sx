from __future__ import annotations

import json
import os

from openai import OpenAI


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMClientError("OPENAI_API_KEY is not configured.")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def generate_json(self, prompt: str) -> dict:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                temperature=0.2,
                max_output_tokens=700,
            )
            text = response.output_text.strip()
            return json.loads(text)
        except Exception as exc:
            raise LLMClientError(f"LLM request failed: {exc}") from exc