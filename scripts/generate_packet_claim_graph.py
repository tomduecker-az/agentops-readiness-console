from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.packet_claim_graph import build_packet_claim_graph


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a packet claim graph from a normalized Workflow Packet JSON file."
    )
    parser.add_argument(
        "--normalized-packet",
        required=True,
        help="Path to normalized_packet.json",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write packet_claim_graph.json",
    )
    args = parser.parse_args()

    input_path = Path(args.normalized_packet)
    output_path = Path(args.output)

    packet = json.loads(input_path.read_text(encoding="utf-8"))
    graph = build_packet_claim_graph(packet)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    print(f"Wrote: {output_path}")
    print(f"Claims: {graph['metadata']['claim_count']}")
    print("Claim types:")
    for claim_type, claim_ids in sorted(graph["indexes"]["claims_by_type"].items()):
        print(f"  {claim_type}: {len(claim_ids)}")


if __name__ == "__main__":
    main()
