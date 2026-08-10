from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full Agentic Readiness Blueprint pipeline."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--proposal-path",
        help="Use an existing exported LLM blueprint proposal JSON file. Avoids a new model call.",
    )
    parser.add_argument(
        "--run-llm",
        action="store_true",
        help="Run the LLM Blueprint Advisor to create a new proposal. This may incur model cost.",
    )
    parser.add_argument(
        "--persist-final",
        action="store_true",
        help="Persist the reconciled blueprint as the final agentic_readiness_blueprint artifact.",
    )

    args = parser.parse_args()

    if args.proposal_path and args.run_llm:
        raise SystemExit("Use either --proposal-path or --run-llm, not both.")

    if not args.proposal_path and not args.run_llm:
        raise SystemExit(
            "Cost control: provide --proposal-path to reuse an existing proposal, "
            "or explicitly pass --run-llm to make a new model call."
        )

    workflow_id = args.workflow_id
    run_id = args.run_id

    baseline_path = Path(
        f"examples/blueprints/{workflow_id}_{run_id}_blueprint.json"
    )
    proposal_path = (
        Path(args.proposal_path)
        if args.proposal_path
        else Path(
            f"examples/blueprint_proposals/{workflow_id}_{run_id}_llm_blueprint_proposal.json"
        )
    )
    comparison_path = Path(
        f"examples/blueprint_comparisons/{workflow_id}_{run_id}_blueprint_comparison.json"
    )
    reconciled_path = Path(
        f"examples/reconciled_blueprints/{workflow_id}_{run_id}_reconciled_blueprint.json"
    )

    print("Agentic Readiness Blueprint Pipeline")
    print(f"- workflow_id: {workflow_id}")
    print(f"- run_id: {run_id}")
    print(f"- run_llm: {args.run_llm}")
    print(f"- proposal_path: {proposal_path}")
    print(f"- persist_final: {args.persist_final}")

    print("\n1. Generate deterministic baseline blueprint")
    _run(
        [
            sys.executable,
            "-m",
            "scripts.generate_agentic_readiness_blueprint",
            "--workflow-id",
            workflow_id,
            "--run-id",
            run_id,
            "--skip-persist",
            "--export-json",
            "--skip-audit",
        ]
    )
    _assert_file_exists(baseline_path)

    if args.run_llm:
        print("\n2. Generate new LLM blueprint proposal")
        _run(
            [
                sys.executable,
                "-m",
                "scripts.run_llm_blueprint_advisor",
                "--workflow-id",
                workflow_id,
                "--run-id",
                run_id,
                "--export-json",
            ]
        )
    else:
        print("\n2. Reuse existing LLM blueprint proposal")
        _assert_file_exists(proposal_path)

    _assert_file_exists(proposal_path)

    print("\n3. Validate LLM blueprint proposal")
    _run(
        [
            sys.executable,
            "-m",
            "scripts.check_llm_blueprint_proposal",
            "--path",
            str(proposal_path),
        ]
    )

    print("\n4. Compare baseline and LLM proposal")
    _run(
        [
            sys.executable,
            "-m",
            "scripts.compare_blueprint_outputs",
            "--baseline-path",
            str(baseline_path),
            "--proposal-path",
            str(proposal_path),
            "--export-json",
        ]
    )
    _assert_file_exists(comparison_path)

    print("\n5. Reconcile final blueprint")
    reconcile_command = [
        sys.executable,
        "-m",
        "scripts.reconcile_blueprint_outputs",
        "--baseline-path",
        str(baseline_path),
        "--proposal-path",
        str(proposal_path),
        "--comparison-path",
        str(comparison_path),
        "--export-json",
    ]

    if args.persist_final:
        reconcile_command.append("--persist")

    _run(reconcile_command)
    _assert_file_exists(reconciled_path)

    print("\nPipeline complete")
    print(f"- baseline_path: {baseline_path}")
    print(f"- proposal_path: {proposal_path}")
    print(f"- comparison_path: {comparison_path}")
    print(f"- reconciled_path: {reconciled_path}")
    print(f"- persisted_final: {args.persist_final}")


def _run(command: list[str]) -> None:
    env = os.environ.copy()

    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        if "services/api" not in existing_pythonpath.split(os.pathsep):
            env["PYTHONPATH"] = f"services/api{os.pathsep}{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = "services/api"

    print("+", " ".join(command))

    completed = subprocess.run(
        command,
        env=env,
        check=False,
    )

    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _assert_file_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected file was not created: {path}")


if __name__ == "__main__":
    main()