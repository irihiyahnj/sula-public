#!/usr/bin/env python3
"""verifier-shell skill: run shell commands as goal verifiers.

Reads fragments where kind=goal and verifier_ref starts with `shell:`.
For any such goal not yet satisfied, runs the shell command in the
project root and appends a kind: verification-fact fragment with
passed: true/false and the command output.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from append import append_fragment, utc_now
from render import _is_satisfied, load_fragments
from capture import CaptureError, ignore_patterns, scan_tree, select_tree, tree_digest

DEFAULT_TIMEOUT_SECONDS = 600
OUTPUT_TRUNCATE = 4000


def now_iso() -> str:
    return utc_now()


def run_command(command: str, cwd: Path, timeout: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"verifier timed out after {timeout}s"
    output = (result.stdout + result.stderr).strip()
    if len(output) > OUTPUT_TRUNCATE:
        output = output[:OUTPUT_TRUNCATE] + "\n…(truncated)"
    return result.returncode == 0, output


def write_verification_fact(
    fragments_dir: Path, goal_id: str, command: str, passed: bool, output: str,
    *, digest: str = "", scope: list[str] | None = None,
) -> Path:
    return append_fragment(fragments_dir, f"verification-fact-shell-{goal_id[:60]}", {
        "kind": "verification-fact", "refs": [goal_id], "passed": passed,
        "tags": ["skill", "verifier-shell"], "verified_tree_digest": digest,
        "verification_scope": scope or [], "verified_command": command,
    }, f"shell verifier: `{command}`\n\n```\n{output}\n```", stamp=now_iso())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Run shell-command verifiers for Sula vector goals."
    )
    p.add_argument("--project-root", required=True)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="List goals that would be evaluated without running commands.",
    )
    args = p.parse_args(argv)

    root = Path(args.project_root).resolve()
    fragments_dir = root / "fragments"
    if not fragments_dir.is_dir():
        print(f"no fragments/ in {root}", file=sys.stderr)
        return 2

    witness = Path(__file__).with_name("witness.py")
    if not args.dry_run:
        captured = subprocess.run([sys.executable, str(witness), "--project-root", str(root)], capture_output=True, text=True)
        if captured.returncode:
            print(captured.stderr, file=sys.stderr)
            return captured.returncode
    frags = load_fragments(fragments_dir)
    candidates = [
        f
        for f in frags
        if f.kind == "goal"
        and isinstance(f.get("verifier_ref"), str)
        and str(f.get("verifier_ref", "")).startswith("shell:")
        and not _is_satisfied(f, frags)
    ]

    if not candidates:
        print("no shell-verified goals to evaluate")
        return 0

    failed = False
    for goal in candidates:
        verifier_ref = str(goal.get("verifier_ref", ""))
        command = verifier_ref[len("shell:") :].strip()
        if not command:
            continue
        print(f"[verifier-shell] {goal.id}: {command}")
        if args.dry_run:
            continue
        scope = goal.id_list("verification_paths")
        patterns = ignore_patterns(frags, [])
        try:
            before = select_tree(scan_tree(root, patterns), scope)
            missing = [p for p in scope if not select_tree(before, [p])]
            if missing:
                raise CaptureError("verification inputs missing or excluded: " + ", ".join(missing))
            passed, output = run_command(command, root, args.timeout)
            after = select_tree(scan_tree(root, patterns), scope)
            if before != after:
                passed = False
                output += "\nVerification inputs changed during the command; result is not valid for a stable version."
            digest = tree_digest(after)
        except CaptureError as exc:
            passed, output, digest = False, str(exc), ""
        captured = subprocess.run([sys.executable, str(witness), "--project-root", str(root)], capture_output=True, text=True)
        if captured.returncode:
            passed = False
            output += "\nCapture failed: " + captured.stderr
        target = write_verification_fact(
            fragments_dir, goal.id, command, passed, output, digest=digest, scope=scope
        )
        failed |= not passed
        status = "PASS" if passed else "FAIL"
        print(f"[verifier-shell] -> {status}  {target.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
