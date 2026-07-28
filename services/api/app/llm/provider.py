import json
from typing import Any

from openai import OpenAI

from app.core.config import get_settings


class LLMProviderError(RuntimeError):
    pass


def generate_structured_analysis(
    system_instructions: str,
    user_prompt: str,
    json_schema: dict[str, Any],
    schema_name: str = "llm_workflow_analysis",
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.openai_api_key:
        raise LLMProviderError("OPENAI_API_KEY is not configured.")
    
    client = OpenAI(api_key=settings.openai_api_key)

    model = settings.openai_model.strip() or "gpt-5.6-sol"
    reasoning_effort = settings.openai_reasoning_effort.strip() or "high"

    response = client.responses.create(
        model=model,
        reasoning={
            "effort": reasoning_effort,
        },
        input=[
            {
                "role": "system",
                "content": system_instructions,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": json_schema,
                "strict": False,
            }
        },
    )

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            f"Model response was not valid JSON: {response.output_text[:500]}"
        ) from exc