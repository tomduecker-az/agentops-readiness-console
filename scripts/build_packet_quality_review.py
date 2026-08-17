from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.packet_quality_review_service import build_packet_quality_review


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build combined packet_quality_review.json from claim graph, deterministic review, and adversarial review."
    )
    parser.add_argument("--claim-graph", required=True)
    parser.add_argument("--deterministic-review", required=True)
    parser.add_argument("--adversarial-review", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    claim_graph = json.loads(Path(args.claim_graph).read_text(encoding="utf-8"))
    deterministic_review = json.loads(
        Path(args.deterministic_review).read_text(encoding="utf-8")
    )
    adversarial_review = json.loads(
        Path(args.adversarial_review).read_text(encoding="utf-8")
    )

    packet_quality_review = build_packet_quality_review(
        packet_claim_graph=claim_graph,
        deterministic_review=deterministic_review,
        adversarial_review=adversarial_review,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet_quality_review, indent=2), encoding="utf-8")

    print(f"Wrote: {output_path}")
    print(f"Total findings: {packet_quality_review['summary']['total_findings']}")
    print(
        "Reconciled critical/high findings:",
        packet_quality_review["summary"]["reconciled_critical_or_high_count"],
    )

    print()
    print("Top reconciled findings:")
    for finding in packet_quality_review["summary"]["top_reconciled_findings"]:
        print(
            f"- {finding.get('finding_id')} | "
            f"{finding.get('source')} | "
            f"{finding.get('severity')} | "
            f"{finding.get('finding_type')} | "
            f"{finding.get('title')}"
        )


if __name__ == "__main__":
    main()
