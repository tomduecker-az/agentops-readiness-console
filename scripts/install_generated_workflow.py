from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


DEFAULT_WORKFLOW_ROOT = "data/workflows"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install a generated workflow folder into data/workflows safely."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Generated workflow folder, such as examples/generated_workflows/access_request_review.",
    )
    parser.add_argument(
        "--workflow-id",
        required=True,
        help="Workflow ID to install under data/workflows/<workflow-id>.",
    )
    parser.add_argument(
        "--workflow-root",
        default=DEFAULT_WORKFLOW_ROOT,
        help=f"Workflow root directory. Default: {DEFAULT_WORKFLOW_ROOT}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing installed workflow folder.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print install result as JSON.",
    )

    args = parser.parse_args()

    source_dir = Path(args.source)
    workflow_root = Path(args.workflow_root)
    workflow_id = _validate_workflow_id(args.workflow_id)
    destination_dir = workflow_root / workflow_id

    result = install_generated_workflow(
        source_dir=source_dir,
        destination_dir=destination_dir,
        workflow_id=workflow_id,
        overwrite=args.overwrite,
    )

    print("Generated Workflow Install")
    print(f"- source: {result['source_dir']}")
    print(f"- destination: {result['destination_dir']}")
    print(f"- workflow_id: {result['workflow_id']}")
    print(f"- files_copied: {result['files_copied']}")
    print(f"- manifest_path: {result['manifest_path']}")

    if args.print_json:
        print(json.dumps(result, indent=2))


def install_generated_workflow(
    *,
    source_dir: Path,
    destination_dir: Path,
    workflow_id: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    destination_dir = destination_dir.resolve()

    _validate_source_dir(source_dir)
    _validate_destination_dir(destination_dir)

    source_manifest_path = source_dir / "workflow_manifest.json"
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))

    _validate_manifest_files(source_dir, manifest)

    if destination_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"Destination workflow already exists: {destination_dir}. "
                "Use --overwrite to replace it."
            )

        shutil.rmtree(destination_dir)

    destination_dir.mkdir(parents=True, exist_ok=True)

    files_copied = 0

    for source_file in sorted(source_dir.iterdir()):
        if not source_file.is_file():
            continue

        destination_file = destination_dir / source_file.name
        shutil.copy2(source_file, destination_file)
        files_copied += 1

    destination_manifest_path = destination_dir / "workflow_manifest.json"
    installed_manifest = _build_installed_manifest(
        manifest=manifest,
        workflow_id=workflow_id,
        source_dir=source_dir,
        destination_dir=destination_dir,
    )
    destination_manifest_path.write_text(
        json.dumps(installed_manifest, indent=2),
        encoding="utf-8",
    )

    return {
        "source_dir": str(source_dir),
        "destination_dir": str(destination_dir),
        "workflow_id": workflow_id,
        "files_copied": files_copied,
        "manifest_path": str(destination_manifest_path),
    }


def _build_installed_manifest(
    *,
    manifest: dict[str, Any],
    workflow_id: str,
    source_dir: Path,
    destination_dir: Path,
) -> dict[str, Any]:
    installed_manifest = dict(manifest)

    original_workflow_id = installed_manifest.get("workflow_id")
    installed_manifest["workflow_id"] = workflow_id
    installed_manifest["packet_path"] = _repo_relative_path(destination_dir)

    metadata = dict(installed_manifest.get("metadata") or {})
    metadata["installed_from"] = {
        "source_dir": str(source_dir),
        "original_workflow_id": original_workflow_id,
        "install_type": "generated_workflow",
    }
    installed_manifest["metadata"] = metadata

    source = dict(metadata.get("source") or {})
    source["installed_workflow_id"] = workflow_id
    source["original_workflow_id"] = original_workflow_id
    metadata["source"] = source
    installed_manifest["metadata"] = metadata

    return installed_manifest


def _validate_source_dir(source_dir: Path) -> None:
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")

    manifest_path = source_dir / "workflow_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Source directory is missing workflow_manifest.json: {source_dir}"
        )


def _validate_manifest_files(
    source_dir: Path,
    manifest: dict[str, Any],
) -> None:
    documents = manifest.get("documents")

    if not isinstance(documents, list) or not documents:
        raise ValueError("workflow_manifest.json must contain a non-empty documents list.")

    missing_files: list[str] = []

    for document in documents:
        if not isinstance(document, dict):
            raise ValueError("Each manifest document entry must be an object.")

        relative_path = document.get("relative_path") or document.get("file_path")

        if not relative_path:
            raise ValueError("Each manifest document entry must include relative_path.")

        candidate = source_dir / str(relative_path)

        if not candidate.exists():
            missing_files.append(str(relative_path))

    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(
            f"Manifest references files that do not exist in source directory: {missing}"
        )


def _validate_destination_dir(destination_dir: Path) -> None:
    workflow_root = Path(DEFAULT_WORKFLOW_ROOT).resolve()

    try:
        destination_dir.relative_to(workflow_root)
    except ValueError as exc:
        raise ValueError(
            f"Destination must be inside {workflow_root}. Got: {destination_dir}"
        ) from exc


def _validate_workflow_id(workflow_id: str) -> str:
    cleaned = workflow_id.strip()

    if not cleaned:
        raise ValueError("workflow_id is required.")

    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")

    if any(character not in allowed for character in cleaned):
        raise ValueError(
            "workflow_id may only contain lowercase letters, numbers, underscores, and hyphens."
        )

    return cleaned

def _repo_relative_path(path: Path) -> str:
    resolved_path = path.resolve()
    repo_root = Path.cwd().resolve()

    try:
        return resolved_path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(resolved_path)

if __name__ == "__main__":
    main()