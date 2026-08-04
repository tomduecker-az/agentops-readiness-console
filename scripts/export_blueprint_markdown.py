from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from readiness_core import render_agentic_readiness_blueprint_markdown


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export an Agentic Readiness Blueprint JSON file to Markdown."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")

    args = parser.parse_args()

    input_path = Path(args.input)
    blueprint = json.loads(input_path.read_text(encoding="utf-8"))

    markdown = render_agentic_readiness_blueprint_markdown(blueprint)

    output_path = Path(args.output) if args.output else _default_output_path(blueprint)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print("Markdown blueprint exported")
    print(f"- input: {input_path}")
    print(f"- output: {output_path}")


def _default_output_path(blueprint: dict[str, Any]) -> Path:
    workflow_id = blueprint["workflow_id"]
    run_id = blueprint["run_id"]

    return Path("examples/reports") / f"{workflow_id}_{run_id}_agentic_readiness_blueprint.md"


if __name__ == "__main__":
    main()