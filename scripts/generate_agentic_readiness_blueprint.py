from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.services.blueprint_service import generate_agentic_readiness_blueprint


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an Agentic Readiness Blueprint for a completed workflow analysis run."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--skip-persist", action="store_true")
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip audit event writes. Use for local/no-persistence runs.",
    )
    parser.add_argument("--export-json", action="store_true")

    args = parser.parse_args()

    print("1. Generating Agentic Readiness Blueprint...")
    print(f"- workflow_id: {args.workflow_id}")
    print(f"- run_id: {args.run_id}")

    result = generate_agentic_readiness_blueprint(
        workflow_id=args.workflow_id,
        run_id=args.run_id,
        persist=not args.skip_persist,
        audit_enabled=not args.skip_audit,
    )

    blueprint = result["blueprint"]

    print("\n2. Blueprint generated")
    print(f"- artifact_id: {result['artifact_id']}")
    print(f"- recommendation: {blueprint['executive_summary']['recommendation']}")
    print(f"- autonomy_rows: {len(blueprint['step_level_autonomy_matrix'])}")
    print(f"- tool_capabilities: {len(blueprint['tooling_blueprint'])}")
    print(f"- approval_gates: {len(blueprint['human_approval_gates'])}")
    print(f"- roadmap_items: {len(blueprint['implementation_roadmap'])}")

    overall_score = _get_overall_score(blueprint)
    if overall_score is not None:
        print(f"- overall_readiness_score: {overall_score}/100")

    if args.export_json:
        output_path = _write_json_export(
            workflow_id=args.workflow_id,
            run_id=args.run_id,
            blueprint=blueprint,
        )
        print(f"- json_export_path: {output_path}")

    if args.print_json:
        print("\nFull Agentic Readiness Blueprint:")
        print(json.dumps(blueprint, indent=2))


def _get_overall_score(blueprint: dict[str, Any]) -> int | None:
    for score in blueprint.get("readiness_scorecard", []):
        if score.get("dimension") == "overall_readiness":
            return score.get("score")

    return None


def _write_json_export(
    *,
    workflow_id: str,
    run_id: str,
    blueprint: dict[str, Any],
) -> Path:
    output_dir = Path("examples/blueprints")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{workflow_id}_{run_id}_blueprint.json"
    output_path.write_text(
        json.dumps(blueprint, indent=2),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    main()