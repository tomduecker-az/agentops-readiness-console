from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.packet_quality_rules import run_packet_quality_rules


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic packet quality rules against packet_claim_graph.json."
    )
    parser.add_argument(
        "--claim-graph",
        required=True,
        help="Path to packet_claim_graph.json",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write packet_quality_deterministic_review.json",
    )
    args = parser.parse_args()

    input_path = Path(args.claim_graph)
    output_path = Path(args.output)

    graph = json.loads(input_path.read_text(encoding="utf-8"))
    review = run_packet_quality_rules(graph)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2), encoding="utf-8")

    print(f"Wrote: {output_path}")
    print(f"Findings: {review['summary']['finding_count']}")
    print("By severity:")
    for severity, count in sorted(review["summary"]["by_severity"].items()):
        print(f"  {severity}: {count}")
    print("By rule:")
    for rule_id, count in sorted(review["summary"]["by_rule_id"].items()):
        print(f"  {rule_id}: {count}")


if __name__ == "__main__":
    main()
