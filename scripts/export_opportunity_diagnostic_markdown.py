from __future__ import annotations

import argparse
import json
from pathlib import Path

from readiness_core import (
    WorkflowAIOpportunityDiagnostic,
    render_workflow_ai_opportunity_diagnostic_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a Workflow AI Opportunity Diagnostic JSON file to Markdown."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")

    args = parser.parse_args()

    input_path = Path(args.input)
    diagnostic_json = json.loads(input_path.read_text(encoding="utf-8"))

    diagnostic = WorkflowAIOpportunityDiagnostic.model_validate(diagnostic_json)
    markdown = render_workflow_ai_opportunity_diagnostic_markdown(diagnostic)

    output_path = Path(args.output) if args.output else _default_output_path(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print("Workflow AI Opportunity Diagnostic Markdown Export")
    print(f"- input: {input_path}")
    print(f"- output: {output_path}")


def _default_output_path(input_path: Path) -> Path:
    output_dir = Path("examples/reports")
    output_name = input_path.name.replace(
        "_opportunity_diagnostic.json",
        "_opportunity_diagnostic.md",
    )

    if output_name == input_path.name:
        output_name = f"{input_path.stem}.md"

    return output_dir / output_name


if __name__ == "__main__":
    main()