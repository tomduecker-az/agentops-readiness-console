from workflow_core import list_registered_workflows, read_document


def main() -> None:
    workflows = list_registered_workflows()

    print(f"Registered workflows: {len(workflows)}")

    for workflow in workflows:
        print(f"- {workflow.workflow_id}: {workflow.display_name}")
        print(f"  packet_path: {workflow.packet_path}")
        print(f"  documents: {len(workflow.documents)}")

        narrative = read_document(
            workflow_id=workflow.workflow_id,
            document_id="process_narrative",
        )

        first_line = next(
            (
                line.strip()
                for line in narrative.content.splitlines()
                if line.strip() and not line.startswith("#")
            ),
            "No narrative content found.",
        )

        print(f"  narrative: {first_line}")


if __name__ == "__main__":
    main()