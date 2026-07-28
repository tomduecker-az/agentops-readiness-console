from __future__ import annotations

from readiness_core.blueprint_builder import _classify_step
from readiness_core.models import AutonomyPosture


_CASES = [
    (
        "Manager submits an access request for an employee, including employee identifier and requested access.",
        AutonomyPosture.ai_assist,
    ),
    (
        "Identity analyst verifies employee identifier, employee email, manager email, role, and employment status against the HR source.",
        AutonomyPosture.ai_assist,
    ),
    (
        "Identity analyst reviews the request for privileged access, sensitive systems, custom permissions, APIs, or security-related access.",
        AutonomyPosture.ai_assist,
    ),
    (
        "Missing, unclear, incomplete, or conflicting intake information is routed back to the manager for clarification.",
        AutonomyPosture.ai_recommend_human_approve,
    ),
    (
        "Application owner reviews and approves or rejects the requested system access.",
        AutonomyPosture.ai_recommend_human_approve,
    ),
    (
        "Security reviewer performs additional review for privileged access, sensitive data, custom roles, or security-related permissions.",
        AutonomyPosture.ai_recommend_human_approve,
    ),
    (
        "IT provisions approved access in the identity provider and target systems.",
        AutonomyPosture.approval_gated_action,
    ),
    (
        "Identity analyst updates ticket status, records provisioned systems, and attaches approval evidence.",
        AutonomyPosture.approval_gated_action,
    ),
    (
        "Access requests approaching the SLA deadline are escalated to the identity team lead.",
        AutonomyPosture.ai_recommend_human_approve,
    ),
    (
        "Weekly access review report is prepared for the security lead and audit evidence is retained.",
        AutonomyPosture.ai_assist,
    ),
]


def main() -> None:
    failures = []

    for step, expected_posture in _CASES:
        result = _classify_step(step)
        actual_posture = result["posture"]

        print(f"{actual_posture.value:32} expected={expected_posture.value:32} {step[:80]}")

        if actual_posture != expected_posture:
            failures.append(
                {
                    "step": step,
                    "expected": expected_posture.value,
                    "actual": actual_posture.value,
                }
            )

    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(
                f"- expected={failure['expected']} actual={failure['actual']} step={failure['step']}"
            )

        raise AssertionError(f"{len(failures)} autonomy classifier checks failed.")

    print("\nPASS")


if __name__ == "__main__":
    main()