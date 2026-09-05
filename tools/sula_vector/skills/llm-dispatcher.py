#!/usr/bin/env python3
"""llm-dispatcher skill: route intents to a configured executor command.

Reads fragments where kind in {intent, cadence-tick} and `executor_command`
is set. For each such fragment that has not already produced a kind:turn
referencing it, runs the executor command in the project root, pipes the
fragment body to stdin, captures stdout/stderr, and appends a kind:turn
fragment with refs back to the source intent.

The executor command is anything that reads stdin and writes stdout: a
Claude/Codex/Gemini CLI wrapper, a curl call to an OpenAI/DeepSeek API, a
local model binary, a shell script. Sula does not care which.

Environment variables passed to the executor:
  SULA_PROJECT_ROOT     absolute path to the project
  SULA_INTENT_ID        the source intent's id
  SULA_INTENT_KIND      'intent' or 'cadence-tick'
  SULA_INTENT_TAGS      comma-joined tags

Idempotent: running twice without new intents appends nothing.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from append import append_fragment, utc_now
from render import load_fragments  # type: ignore

DEFAULT_TIMEOUT_SECONDS = 600
OUTPUT_TRUNCATE = 8000


def now_iso() -> str:
    return utc_now()


def already_dispatched(intent_id: str, frags: list) -> bool:
    return any(f.kind == "turn" and intent_id in f.refs for f in frags)


def dispatch(
    command: str,
    body: str,
    cwd: Path,
    env: dict[str, str],
    timeout: int,
) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            input=body,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, **env},
        )
    except subprocess.TimeoutExpired:
        return False, f"executor timed out after {timeout}s"
    output = (result.stdout + result.stderr).strip()
    if len(output) > OUTPUT_TRUNCATE:
        output = output[:OUTPUT_TRUNCATE] + "\n…(truncated)"
    return result.returncode == 0, output


def write_turn(
    fragments_dir: Path,
    intent_id: str,
    command: str,
    success: bool,
    output: str,
) -> Path:
    status = "ok" if success else "error"
    return append_fragment(fragments_dir, f"turn-dispatch-{intent_id[:60]}", {
        "kind": "turn", "refs": [intent_id], "executor_status": status,
        "tags": ["skill", "llm-dispatcher"],
    }, f"Executor command: `{command}`\nStatus: {status}\n\n```\n{output}\n```", stamp=now_iso())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Dispatch intents with executor_command to a shell executor."
    )
    p.add_argument("--project-root", required=True)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="List dispatchable intents without executing.",
    )
    args = p.parse_args(argv)

    root = Path(args.project_root).resolve()
    fragments_dir = root / "fragments"
    if not fragments_dir.is_dir():
        print(f"no fragments/ in {root}", file=sys.stderr)
        return 2

    frags = load_fragments(fragments_dir)
    candidates = [
        f
        for f in frags
        if f.kind in {"intent", "cadence-tick"}
        and isinstance(f.get("executor_command"), str)
        and not already_dispatched(f.id, frags)
    ]

    if not candidates:
        print("no intents with executor_command pending dispatch")
        return 0

    dispatched = 0
    failed = 0

    for intent in candidates:
        command = str(intent.get("executor_command", "")).strip()
        if not command:
            continue
        env = {
            "SULA_PROJECT_ROOT": str(root),
            "SULA_INTENT_ID": intent.id,
            "SULA_INTENT_KIND": intent.kind,
            "SULA_INTENT_TAGS": ",".join(intent.tags),
        }
        print(f"[llm-dispatcher] {intent.id} -> `{command}`")
        if args.dry_run:
            continue
        success, output = dispatch(command, intent.body, root, env, args.timeout)
        target = write_turn(fragments_dir, intent.id, command, success, output)
        result_tag = "OK" if success else "ERR"
        print(f"[llm-dispatcher] -> {result_tag}  {target.name}")
        if success:
            dispatched += 1
        else:
            failed += 1

    print(f"[llm-dispatcher] dispatched={dispatched} failed={failed} (dry-run={args.dry_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
