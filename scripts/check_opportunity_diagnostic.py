from __future__ import annotations

import argparse
import json
from pathlib import Path

from readiness_core import (
    WorkflowAIOpportunityDiagnostic,
    evaluate_diagnostic_quality,
    quality_passed,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the quality of a Workflow AI Opportunity Diagnostic."
    )
    parser.add_argument("--path", required=True)
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Fail when warnings are present.",
    )

    args = parser.parse_args()

    path = Path(args.path)
    diagnostic = json.loads(path.read_text(encoding="utf-8"))

    WorkflowAIOpportunityDiagnostic.model_validate(diagnostic)

    issues = evaluate_diagnostic_quality(diagnostic)

    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]

    print("Workflow AI Opportunity Diagnostic Quality Check")
    print(f"- path: {path}")
    print(f"- errors: {len(errors)}")
    print(f"- warnings: {len(warnings)}")

    if issues:
        print("\nIssues:")
        for issue in issues:
            print(
                f"- {issue.severity.upper()} | {issue.code} | "
                f"{issue.location} | {issue.message}"
            )

    if not quality_passed(issues):
        raise SystemExit(1)

    if args.warnings_as_errors and warnings:
        raise SystemExit(1)

    print("\nQuality check: PASS")


if __name__ == "__main__":
    main()