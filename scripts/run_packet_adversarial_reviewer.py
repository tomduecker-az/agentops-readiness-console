from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.llm.packet_adversarial_reviewer import generate_packet_adversarial_review


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run LLM adversarial review against packet claim graph and deterministic findings."
    )
    parser.add_argument(
        "--claim-graph",
        required=True,
        help="Path to packet_claim_graph.json",
    )
    parser.add_argument(
        "--deterministic-review",
        required=True,
        help="Path to packet_quality_deterministic_review.json",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write packet_adversarial_review.json",
    )

    args = parser.parse_args()

    claim_graph_path = Path(args.claim_graph)
    deterministic_review_path = Path(args.deterministic_review)
    output_path = Path(args.output)

    claim_graph = json.loads(claim_graph_path.read_text(encoding="utf-8"))
    deterministic_review = json.loads(
        deterministic_review_path.read_text(encoding="utf-8")
    )

    review = generate_packet_adversarial_review(
        packet_claim_graph=claim_graph,
        deterministic_review=deterministic_review,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2), encoding="utf-8")

    print(f"Wrote: {output_path}")
    print(f"Advisory findings: {len(review.get('advisory_findings', []))}")

    print()
    print("Findings:")
    for finding in review.get("advisory_findings", []):
        print(
            f"- {finding.get('finding_id')} | "
            f"{finding.get('severity')} | "
            f"{finding.get('title')}"
        )


if __name__ == "__main__":
    main()
