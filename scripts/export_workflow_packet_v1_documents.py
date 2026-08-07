from __future__ import annotations

import argparse
import json
from pathlib import Path

from workflow_core.packet_v1_document_exporter import (
    export_workflow_packet_v1_documents,
)
from workflow_core.packet_v1_parser import parse_workflow_packet_v1


DEFAULT_OUTPUT_ROOT = "examples/generated_workflows"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a completed Workflow Packet v1 workbook to workflow document files."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to completed workflow_packet_v1.xlsx workbook.",
    )
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Output root directory. Default: {DEFAULT_OUTPUT_ROOT}",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Exact output directory. Overrides --output-root.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing generated workflow directory.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print export result JSON.",
    )

    args = parser.parse_args()

    packet = parse_workflow_packet_v1(Path(args.path))

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path(args.output_root) / packet.workflow_id
    )

    result = export_workflow_packet_v1_documents(
        packet=packet,
        output_dir=output_dir,
        overwrite=args.overwrite,
    )

    print("Workflow Packet v1 Document Export")
    print(f"- source: {args.path}")
    print(f"- workflow_id: {result['workflow_id']}")
    print(f"- workflow_name: {result['workflow_name']}")
    print(f"- output_dir: {result['output_dir']}")
    print(f"- manifest_path: {result['manifest_path']}")
    print(f"- files_written: {len(result['files_written'])}")

    if args.print_json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()