import json
from typing import Any
from openai import OpenAI
from app.core.config import get_settings
from datetime import datetime, timezone
from pathlib import Path
import os

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

def _usage_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_usage(response: Any) -> dict[str, Any]:
    usage = _usage_get(response, "usage", {}) or {}

    input_tokens = _usage_get(usage, "input_tokens", 0) or _usage_get(usage, "prompt_tokens", 0) or 0
    output_tokens = _usage_get(usage, "output_tokens", 0) or _usage_get(usage, "completion_tokens", 0) or 0
    total_tokens = _usage_get(usage, "total_tokens", 0) or (input_tokens + output_tokens)

    input_details = (
        _usage_get(usage, "input_tokens_details", None)
        or _usage_get(usage, "prompt_tokens_details", None)
        or {}
    )
    cached_input_tokens = _usage_get(input_details, "cached_tokens", 0) or 0

    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _write_llm_usage_log(
    *,
    stage: str,
    model: str,
    response: Any | None = None,
    error: Exception | None = None,
) -> None:
    usage_log_path = os.getenv("AGENTOPS_LLM_USAGE_LOG_PATH")
    if not usage_log_path:
        return

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "model": model,
        "success": error is None,
    }

    if response is not None:
        record.update(_extract_usage(response))
        response_id = _usage_get(response, "id", None)
        if response_id:
            record["response_id"] = response_id

    if error is not None:
        record["error_type"] = type(error).__name__
        record["error_message"] = str(error)

    path = Path(usage_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

def generate_structured_analysis(
    system_instructions: str,
    user_prompt: str,
    json_schema: dict[str, Any],
    schema_name: str = "llm_workflow_analysis",
    strict: bool = False,
    stage: str = "unlabeled",
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

    try:
        response = client.responses.create(**request_args)
    except Exception as exc:
        _write_llm_usage_log(stage=stage, model=model, error=exc)
        raise

    _write_llm_usage_log(stage=stage, model=model, response=response)

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            f"Model response was not valid JSON: {response.output_text[:500]}"
        ) from exc
