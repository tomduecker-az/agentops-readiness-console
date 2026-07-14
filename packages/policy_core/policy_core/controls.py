from policy_core.catalog import CONTROL_CATALOG
from policy_core.models import RequiredControlsResult


def get_required_controls(workflow_step: str) -> RequiredControlsResult:
    normalized_step = workflow_step.strip().lower()

    controls = CONTROL_CATALOG.get(normalized_step, [])

    return RequiredControlsResult(
        workflow_step=normalized_step,
        controls=controls,
    )