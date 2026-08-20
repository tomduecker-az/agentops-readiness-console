import json
from typing import Any

from openai import OpenAI

from app.core.config import get_settings


class LLMProviderError(RuntimeError):
    pass


def _supports_reasoning_effort(model: str) -> bool:
    normalized = model.lower().strip()
    return (
        normalized.startswith("gpt-5")
        or normalized.startswith("o1")
        or normalized.startswith("o3")
        or normalized.startswith("o4")
    )


def generate_structured_analysis(
    system_instructions: str,
    user_prompt: str,
    json_schema: dict[str, Any],
    schema_name: str = "llm_workflow_analysis",
    strict: bool = False,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.openai_api_key:
        raise LLMProviderError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=settings.openai_api_key)

    model = settings.openai_model.strip() or "gpt-5.6-sol"
    reasoning_effort = getattr(settings, "openai_reasoning_effort", "").strip()

    request_args: dict[str, Any] = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": system_instructions,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": json_schema,
                "strict": strict,
            }
        },
    }

    if _supports_reasoning_effort(model):
        request_args["reasoning"] = {
            "effort": reasoning_effort or "high",
        }

    response = client.responses.create(**request_args)

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            f"Model response was not valid JSON: {response.output_text[:500]}"
        ) from exc
