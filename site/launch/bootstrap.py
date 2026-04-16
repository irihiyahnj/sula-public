#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


DEFAULT_SOURCE_REPO = "https://github.com/irihiyahnj/sula-public.git"
DEFAULT_SOURCE_REF = "main"
DEFAULT_SOURCE_DIR = Path.home() / ".sula" / "source"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap and launch Sula from the canonical site contract")
    parser.add_argument("--project-root", required=True, help="Path to the target project root")
    parser.add_argument("--source-dir", help="Optional existing local Sula source checkout")
    parser.add_argument("--source-repo", default=DEFAULT_SOURCE_REPO, help="Canonical public Sula source repository URL")
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF, help="Branch or ref to use when cloning Sula from the canonical public repository")
    parser.add_argument("--approve", action="store_true", help="Apply onboarding instead of stopping at the summary")
    parser.add_argument("--accept-suggested", action="store_true", help="Accept suggested onboarding answers automatically")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    return parser.parse_args()


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        capture_output=capture_output,
    )


def local_source_payload(kind: str, root: Path, *, source_repo: str, source_ref: str) -> dict[str, str]:
    return {
        "kind": kind,
        "root": str(root),
        "source_repo": source_repo,
        "source_ref": source_ref,
        "sula_script": str(root / "scripts" / "sula.py"),
    }


def resolve_source(args: argparse.Namespace, project_root: Path) -> dict[str, str]:
    vendored_script = project_root / "scripts" / "sula.py"
    if vendored_script.exists():
        return local_source_payload("vendored-project", project_root, source_repo=args.source_repo, source_ref=args.source_ref)

    if args.source_dir:
        source_root = Path(args.source_dir).expanduser().resolve()
        if not (source_root / "scripts" / "sula.py").exists():
            raise SystemExit(f"Provided source dir does not contain scripts/sula.py: {source_root}")
        return local_source_payload("explicit-source-dir", source_root, source_repo=args.source_repo, source_ref=args.source_ref)

    if shutil.which("git") is None:
        raise SystemExit("git is required to resolve the canonical Sula source automatically")

    source_root = DEFAULT_SOURCE_DIR.expanduser().resolve()
    if not source_root.exists():
        source_root.parent.mkdir(parents=True, exist_ok=True)
        clone = run(["git", "clone", "--branch", args.source_ref, "--depth", "1", args.source_repo, str(source_root)])
        if clone.returncode != 0:
            raise SystemExit(f"Failed to clone Sula source: {clone.stderr.strip()}")
    else:
        fetch = run(["git", "-C", str(source_root), "fetch", "origin", args.source_ref, "--depth", "1"])
        if fetch.returncode != 0:
            raise SystemExit(f"Failed to refresh Sula source: {fetch.stderr.strip()}")
        checkout = run(["git", "-C", str(source_root), "checkout", args.source_ref])
        if checkout.returncode != 0:
            raise SystemExit(f"Failed to checkout Sula ref: {checkout.stderr.strip()}")
        pull = run(["git", "-C", str(source_root), "pull", "--ff-only", "origin", args.source_ref])
        if pull.returncode != 0:
            raise SystemExit(f"Failed to fast-forward Sula source: {pull.stderr.strip()}")

    if not (source_root / "scripts" / "sula.py").exists():
        raise SystemExit(f"Resolved Sula source does not contain scripts/sula.py: {source_root}")
    return local_source_payload("cloned-source", source_root, source_repo=args.source_repo, source_ref=args.source_ref)


def run_sula_json(source: dict[str, str], sula_args: list[str]) -> dict[str, object]:
    command = ["python3", source["sula_script"], *sula_args, "--json"]
    completed = run(command)
    if completed.returncode not in (0, 1):
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or "Sula launcher failed")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Sula returned non-JSON output in JSON mode: {exc}\n{completed.stdout}") from exc
    payload["_exit_code"] = completed.returncode
    return payload


def print_human_section(title: str, body: str) -> None:
    print(title)
    print(body.rstrip())
    print()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists():
        raise SystemExit(f"Project root does not exist: {project_root}")

    source = resolve_source(args, project_root)
    manifest_exists = (project_root / ".sula" / "project.toml").exists()

    if manifest_exists:
        doctor_payload = run_sula_json(source, ["doctor", "--project-root", str(project_root), "--strict"])
        sync_payload = run_sula_json(source, ["sync", "--project-root", str(project_root), "--dry-run"])
        payload = {
            "command": "site-launch",
            "status": "existing-consumer",
            "source": source,
            "project_root": str(project_root),
            "doctor": doctor_payload,
            "sync_preview": sync_payload,
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
            return 0 if doctor_payload.get("_exit_code", 1) == 0 else 1
        print(f"Sula source: {source['root']} [{source['kind']}]")
        print_human_section("Existing consumer review", doctor_payload.get("project", {}).get("name", str(project_root)))
        print_human_section("Doctor", json.dumps(doctor_payload, indent=2, ensure_ascii=True))
        print_human_section("Sync preview", json.dumps(sync_payload, indent=2, ensure_ascii=True))
        return 0 if doctor_payload.get("_exit_code", 1) == 0 else 1

    onboard_args = ["onboard", "--project-root", str(project_root)]
    if args.accept_suggested:
        onboard_args.append("--accept-suggested")
    if args.approve:
        onboard_args.append("--approve")
    onboard_payload = run_sula_json(source, onboard_args)
    payload = {
        "command": "site-launch",
        "status": onboard_payload.get("status", "unknown"),
        "source": source,
        "project_root": str(project_root),
        "onboard": onboard_payload,
    }
    exit_code = int(onboard_payload.get("_exit_code", 0))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return exit_code
    print(f"Sula source: {source['root']} [{source['kind']}]")
    print_human_section("Onboard result", json.dumps(onboard_payload, indent=2, ensure_ascii=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
