from policy_core.catalog import DATA_CLASSIFICATION_CATALOG
from policy_core.exceptions import UnknownDataElementError
from policy_core.models import DataClassificationResult


def classify_data(data_element: str) -> DataClassificationResult:
    normalized_element = data_element.strip().lower()

    policy = DATA_CLASSIFICATION_CATALOG.get(normalized_element)

    if policy is None:
        raise UnknownDataElementError(
            f"Data element '{data_element}' is not defined in the classification catalog."
        )

    return DataClassificationResult(
        data_element=normalized_element,
        sensitivity=policy["sensitivity"],
        allowed_in_model_context=bool(policy["allowed_in_model_context"]),
        requires_redaction=bool(policy["requires_redaction"]),
        rationale=str(policy["rationale"]),
    )