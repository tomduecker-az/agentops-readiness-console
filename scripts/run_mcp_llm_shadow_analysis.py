import argparse
import json

from fastapi.testclient import TestClient

from app.llm.mcp_shadow_agent import run_mcp_llm_shadow_analysis
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

    print("\n2. Running MCP-enabled LLM shadow analysis...")
    shadow_result = run_mcp_llm_shadow_analysis(
        run_id=run_id,
        workflow_id=args.workflow_id,
    )

    analysis = shadow_result["analysis"]
    metadata = analysis.get("metadata", {})

    print(f"- llm_artifact_id: {shadow_result['artifact_id']}")
    print(f"- analysis_mode: {metadata.get('analysis_mode')}")
    print(f"- model: {metadata.get('model')}")
    print(f"- reasoning_effort: {metadata.get('reasoning_effort')}")
    print(f"- tool_call_count: {metadata.get('tool_call_count')}")
    print(f"- workflow_summary: {analysis.get('workflow_summary')}")

    print("\n3. Tool trace:")
    for item in metadata.get("tool_trace", []):
        print(
            f"- {item.get('status')}: "
            f"{item.get('mcp_tool_name')} "
            f"args={item.get('arguments')}"
        )

    print("\n4. Risk observations:")
    for item in analysis.get("risk_observations", []):
        print(
            f"- [{item.get('severity')}] "
            f"{item.get('risk_category')}: {item.get('risk')}"
        )

    print("\n5. Missing information:")
    for item in analysis.get("missing_information", []):
        print(f"- {item}")

    if args.print_json:
        print("\nFull MCP LLM shadow artifact:")
        print(json.dumps(analysis, indent=2))

    print("\nPASS: MCP-enabled LLM shadow analysis completed and persisted.")
    print(f"\nEvaluate with:")
    print(
        "PYTHONPATH=services/api python -m scripts.evaluate_llm_shadow_analysis "
        f"--workflow-id {args.workflow_id} --run-id {run_id} --print-json"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MCP-enabled LLM shadow analysis for a workflow packet."
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