from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from workflow_core.packet_v1_parser import parse_workflow_packet_v1

from workflow_core.packet_v1_validator import validate_workflow_packet_v1


DEFAULT_OUTPUT_DIR = "examples/normalized_packets"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a completed Workflow Packet v1 workbook into normalized JSON."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to completed workflow_packet_v1.xlsx workbook.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to examples/normalized_packets/<workbook_stem>_normalized_packet.json",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print normalized packet JSON to stdout.",
    )

    args = parser.parse_args()

    packet_path = Path(args.path)

    validation_result = validate_workflow_packet_v1(packet_path)

    if not validation_result.valid:
        print("Workflow Packet v1 Parse")
        print(f"- source: {packet_path}")
        print("- status: failed validation")
        print(f"- errors: {validation_result.error_count}")
        print(f"- warnings: {validation_result.warning_count}")

        if validation_result.issues:
            print("\nValidation issues:")
            for issue in validation_result.issues:
                print(
                    f"- {issue.severity.upper()} | {issue.code} | "
                    f"{issue.location} | {issue.message}"
                )

        raise SystemExit(1)

    if validation_result.warning_count > 0:
        print("Workflow Packet v1 Validation Warnings")
        for issue in validation_result.issues:
            if issue.severity == "warning":
                print(
                    f"- WARNING | {issue.code} | "
                    f"{issue.location} | {issue.message}"
                )
        print("")

    packet = parse_workflow_packet_v1(
        packet_path,
        validate_before_parse=False,
    )
    packet_json = asdict(packet)

    output_path = Path(args.output) if args.output else _default_output_path(packet_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet_json, indent=2), encoding="utf-8")

    print("Workflow Packet v1 Parse")
    print(f"- source: {packet_path}")
    print(f"- output: {output_path}")
    print(f"- workflow_id: {packet.workflow_id}")
    print(f"- workflow_name: {packet.workflow_name}")
    print(f"- workflow_steps: {len(packet.workflow_steps)}")
    print(f"- policy_controls: {len(packet.policy_controls)}")
    print(f"- data_fields: {len(packet.data_dictionary)}")
    print(f"- sample_records: {len(packet.sample_records)}")
    print(f"- target_systems: {len(packet.target_systems)}")

    if args.print_json:
        print(json.dumps(packet_json, indent=2))


def _default_output_path(packet_path: Path) -> Path:
    return Path(DEFAULT_OUTPUT_DIR) / f"{packet_path.stem}_normalized_packet.json"


if __name__ == "__main__":
    main()