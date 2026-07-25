#!/usr/bin/env python3
"""Install runtime capture for a Sula vector.

Capture must not depend on an agent remembering to write things down. This
installs whatever mechanical trigger the project's substrate already offers:

- git repository  -> .git/hooks/post-commit  (witness every commit)
- Kiro workspace  -> .kiro/hooks/*.kiro.hook (witness at the end of every turn)
- plain folder / Drive -> prints the one cron line to paste

Idempotent. Existing non-Sula hooks are never overwritten; the Sula call is
appended to them instead.

    python3 tools/sula_vector/hooks/install.py --project-root .
"""

from __future__ import annotations

import argparse
import json
import stat
from pathlib import Path

MARKER = "# sula-vector witness"

POST_COMMIT = f"""#!/bin/sh
{MARKER}
python3 "$(git rev-parse --show-toplevel)/tools/sula_vector/skills/witness.py" \\
  --project-root "$(git rev-parse --show-toplevel)" >/dev/null 2>&1 || true
"""

KIRO_HOOK = {
    "name": "Sula witness",
    "version": "1.0.0",
    "description": "Append mechanical evidence of what changed at the end of every turn.",
    "when": {"type": "agentStop"},
    "then": {
        "type": "runCommand",
        "command": "python3 tools/sula_vector/skills/witness.py --project-root .",
    },
}

CRON_LINE = (
    "*/30 * * * * cd {root} && "
    "python3 tools/sula_vector/skills/witness.py --project-root . >/dev/null 2>&1"
)


def install_git_hook(root: Path) -> str:
    hooks_dir = root / ".git" / "hooks"
    if not hooks_dir.is_dir():
        return "skipped: not a git repository"
    target = hooks_dir / "post-commit"
    if target.exists():
        text = target.read_text(encoding="utf-8")
        if MARKER in text:
            return "already installed: .git/hooks/post-commit"
        body = POST_COMMIT.split("\n", 1)[1]
        target.write_text(text.rstrip() + "\n\n" + body, encoding="utf-8")
        result = "appended to existing .git/hooks/post-commit"
    else:
        target.write_text(POST_COMMIT, encoding="utf-8")
        result = "installed: .git/hooks/post-commit"
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return result


def install_kiro_hook(root: Path) -> str:
    hooks_dir = root / ".kiro" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / "sula-witness.kiro.hook"
    payload = json.dumps(KIRO_HOOK, indent=2, ensure_ascii=False) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") == payload:
        return "already installed: .kiro/hooks/sula-witness.kiro.hook"
    target.write_text(payload, encoding="utf-8")
    return "installed: .kiro/hooks/sula-witness.kiro.hook"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Install mechanical capture triggers.")
    p.add_argument("--project-root", required=True)
    p.add_argument("--skip-git", action="store_true")
    p.add_argument("--skip-kiro", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.project_root).resolve()
    if not (root / "fragments").is_dir():
        print(f"no fragments/ in {root}")
        return 2

    print(f"[sula] installing capture for {root}")
    if not args.skip_git:
        print(f"  git   {install_git_hook(root)}")
    if not args.skip_kiro:
        print(f"  kiro  {install_kiro_hook(root)}")
    if not (root / ".git").exists():
        print("  folder / Drive substrate — schedule witness yourself:")
        print(f"    {CRON_LINE.format(root=root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
