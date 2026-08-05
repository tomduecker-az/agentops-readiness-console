from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from workflow_core.packet_v1_validator import validate_workflow_packet_v1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Workflow Packet v1 Excel workbook."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to workflow_packet_v1.xlsx",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print validation result as JSON.",
    )
    parser.add_argument(
        "--template-mode",
        action="store_true",
        help="Validate workbook structure without requiring completed business responses.",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Exit nonzero when warnings are present.",
    )

    args = parser.parse_args()

    result = validate_workflow_packet_v1(
        Path(args.path),
        validate_required_content=not args.template_mode,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print("Workflow Packet v1 Validation")
        print(f"- mode: {'template' if args.template_mode else 'completed packet'}")
        print(f"- path: {result.path}")
        print(f"- valid: {result.valid}")
        print(f"- errors: {result.error_count}")
        print(f"- warnings: {result.warning_count}")

        if result.issues:
            print("\nIssues:")
            for issue in result.issues:
                print(
                    f"- {issue.severity.upper()} | {issue.code} | "
                    f"{issue.location} | {issue.message}"
                )

    if not result.valid:
        raise SystemExit(1)

    if args.warnings_as_errors and result.warning_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()