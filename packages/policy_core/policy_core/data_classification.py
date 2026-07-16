from policy_core.catalog import DATA_CLASSIFICATION_CATALOG
from policy_core.models import DataClassificationResult, DataSensitivity


def classify_data(data_element: str) -> DataClassificationResult:
    normalized_element = data_element.strip().lower()

    policy = DATA_CLASSIFICATION_CATALOG.get(normalized_element)

    if policy is not None:
        return DataClassificationResult(
            data_element=normalized_element,
            sensitivity=policy["sensitivity"],
            allowed_in_model_context=bool(policy["allowed_in_model_context"]),
            requires_redaction=bool(policy["requires_redaction"]),
            rationale=str(policy["rationale"]),
        )

    return _classify_unknown_data_element(normalized_element)


def _classify_unknown_data_element(data_element: str) -> DataClassificationResult:
    pii_terms = [
        "customer",
        "client",
        "name",
        "email",
        "phone",
        "address",
        "ssn",
        "tax_id",
        "account",
        "identifier",
    ]

    financial_terms = [
        "amount",
        "payment",
        "balance",
        "price",
        "cost",
        "revenue",
        "invoice",
        "charge",
        "refund",
    ]

    free_text_terms = [
        "notes",
        "comment",
        "comments",
        "description",
        "memo",
        "message",
        "reason",
    ]

    operational_terms = [
        "status",
        "type",
        "date",
        "role",
        "days",
        "queue",
        "step",
        "priority",
    ]

    if any(term in data_element for term in pii_terms):
        return DataClassificationResult(
            data_element=data_element,
            sensitivity=DataSensitivity.pii,
            allowed_in_model_context=False,
            requires_redaction=True,
            rationale=(
                "Field name matched a conservative PII heuristic. Treat as blocked "
                "from model context until reviewed."
            ),
        )

    if any(term in data_element for term in financial_terms):
        return DataClassificationResult(
            data_element=data_element,
            sensitivity=DataSensitivity.financial_internal,
            allowed_in_model_context=True,
            requires_redaction=False,
            rationale=(
                "Field name matched a financial-data heuristic. Treat as internal "
                "financial data."
            ),
        )

    if any(term in data_element for term in free_text_terms):
        return DataClassificationResult(
            data_element=data_element,
            sensitivity=DataSensitivity.internal,
            allowed_in_model_context=True,
            requires_redaction=True,
            rationale=(
                "Field name matched a free-text heuristic. Free-text fields may contain "
                "sensitive information and should be reviewed or redacted."
            ),
        )

    if any(term in data_element for term in operational_terms):
        return DataClassificationResult(
            data_element=data_element,
            sensitivity=DataSensitivity.internal,
            allowed_in_model_context=True,
            requires_redaction=False,
            rationale=(
                "Field name matched an operational metadata heuristic. Treat as internal "
                "workflow data."
            ),
        )

    return DataClassificationResult(
        data_element=data_element,
        sensitivity=DataSensitivity.confidential,
        allowed_in_model_context=False,
        requires_redaction=True,
        rationale=(
            "Field is not defined in the policy catalog and did not match a known "
            "heuristic. Defaulting to confidential and requiring review."
        ),
    )