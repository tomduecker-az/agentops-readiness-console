import argparse
import json

from fastapi.testclient import TestClient

from app.llm.shadow_analysis import run_llm_shadow_analysis
from app.main import app


def main() -> None:
    args = _parse_args()

    client = TestClient(app)

    print(f"\n1. Creating governed baseline run for workflow: {args.workflow_id}")
    run_response = client.post(
        "/runs",
        json={"workflow_id": args.workflow_id},
    )
    assert run_response.status_code == 200, run_response.text

    run_data = run_response.json()
    run_id = run_data["run_id"]

    print(f"- run_id: {run_id}")

    print("\n2. Running LLM shadow analysis...")
    shadow_result = run_llm_shadow_analysis(
        run_id=run_id,
        workflow_id=args.workflow_id,
    )

    analysis = shadow_result["analysis"]

    print(f"- llm_artifact_id: {shadow_result['artifact_id']}")
    print(f"- workflow_summary: {analysis.get('workflow_summary')}")

    print("\n3. LLM risk observations:")
    for item in analysis.get("risk_observations", []):
        print(
            f"- [{item.get('severity')}] "
            f"{item.get('risk_category')}: {item.get('risk')}"
        )

    print("\n4. LLM implementation recommendations:")
    for item in analysis.get("implementation_recommendations", []):
        print(
            f"- [{item.get('priority')}] "
            f"{item.get('title')} "
            f"(approval_required={item.get('approval_required')})"
        )

    print("\n5. Missing information noted by LLM:")
    for item in analysis.get("missing_information", []):
        print(f"- {item}")

    print("\n6. Grounding notes:")
    for item in analysis.get("grounding_notes", []):
        print(f"- {item}")

    if args.print_json:
        print("\nFull LLM shadow artifact:")
        print(json.dumps(analysis, indent=2))

    print("\nPASS: LLM shadow analysis completed and persisted.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LLM shadow analysis for a workflow packet."
    )
    parser.add_argument(
        "--workflow-id",
        default="access_request_review",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()