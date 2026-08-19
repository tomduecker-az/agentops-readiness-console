from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FriendlyRunError:
    category: str
    title: str
    message: str
    suggested_action: str
    technical_detail: str


def classify_run_error(error: BaseException | str) -> FriendlyRunError:
    technical_detail = _technical_detail(error)
    normalized = technical_detail.lower()

    if "openai_api_key" in normalized or "api key" in normalized and "not configured" in normalized:
        return FriendlyRunError(
            category="model_configuration",
            title="AI model configuration is incomplete",
            message="The assessment could not start because the OpenAI API key is not configured.",
            suggested_action="Configure the API key and retry the assessment.",
            technical_detail=technical_detail,
        )

    if "model_not_found" in normalized or "does not exist" in normalized and "model" in normalized:
        return FriendlyRunError(
            category="model_configuration",
            title="AI model configuration error",
            message="The selected AI model could not be found.",
            suggested_action="Check the configured model name and retry the assessment.",
            technical_detail=technical_detail,
        )

    if "reasoning.effort" in normalized or "unsupported parameter" in normalized:
        return FriendlyRunError(
            category="model_configuration",
            title="AI model setting is not supported",
            message=(
                "The selected model does not support one of the configured reasoning settings."
            ),
            suggested_action=(
                "Use a reasoning-capable model, or remove reasoning-effort settings for this model."
            ),
            technical_detail=technical_detail,
        )

    if "executive_brief" in normalized or "model response was not valid json" in normalized:
        return FriendlyRunError(
            category="report_generation",
            title="Client report could not be generated",
            message=(
                "The model response did not include all required report fields or was not valid JSON."
            ),
            suggested_action=(
                "Retry with a stronger report-generation model or review the generated analysis artifacts."
            ),
            technical_detail=technical_detail,
        )

    if "missing local llm workflow analysis artifact" in normalized:
        return FriendlyRunError(
            category="missing_artifact",
            title="LLM workflow analysis is required",
            message=(
                "This assessment does not have an LLM workflow analysis artifact yet."
            ),
            suggested_action=(
                "Run fresh LLM workflow analysis before generating downstream assessment artifacts."
            ),
            technical_detail=technical_detail,
        )

    if "unsupported evaluation_profile_id" in normalized or "no llm shadow evaluation profile" in normalized:
        return FriendlyRunError(
            category="evaluation_profile",
            title="Evaluation profile is not configured",
            message=(
                "The selected evaluation profile is not available for this assessment."
            ),
            suggested_action=(
                "Use the default evaluation profile or configure a supported profile before retrying."
            ),
            technical_detail=technical_detail,
        )

    if "workflow packet" in normalized and ("invalid" in normalized or "validation" in normalized):
        return FriendlyRunError(
            category="workbook_validation",
            title="Workflow packet could not be validated",
            message=(
                "The uploaded workbook did not pass workflow packet validation."
            ),
            suggested_action=(
                "Review the workbook template requirements, correct the packet, and upload it again."
            ),
            technical_detail=technical_detail,
        )

    if "calledprocesserror" in normalized or "returned non-zero exit status" in normalized:
        return FriendlyRunError(
            category="pipeline_step_failed",
            title="Assessment step failed",
            message=(
                "One assessment step stopped before the full pipeline completed."
            ),
            suggested_action=(
                "Review the technical details locally, correct the issue, and retry the failed step."
            ),
            technical_detail=technical_detail,
        )

    return FriendlyRunError(
        category="unexpected_error",
        title="Assessment failed",
        message="The assessment stopped before completion.",
        suggested_action="Review the technical details locally and retry after correcting the issue.",
        technical_detail=technical_detail,
    )


def friendly_error_details(error: BaseException | str) -> dict[str, str]:
    friendly = classify_run_error(error)
    return {
        "category": friendly.category,
        "title": friendly.title,
        "message": friendly.message,
        "suggested_action": friendly.suggested_action,
        "technical_detail": friendly.technical_detail,
    }


def _technical_detail(error: BaseException | str) -> str:
    if isinstance(error, BaseException):
        return f"{type(error).__name__}: {error}"
    return str(error)
