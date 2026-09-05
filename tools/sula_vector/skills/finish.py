#!/usr/bin/env python3
"""Host completion check: capture, validate, then check that observed files stayed stable."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture import CaptureError, fold_witnessed, ignore_patterns, scan_tree, tree_digest
from render import load_report, render_doctor_block, view_doctor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("witness.py")),
                             "--project-root", str(root)], capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode:
        return result.returncode
    frags, problems = load_report(root / "fragments")
    report = view_doctor(frags, problems)
    sys.stdout.write(render_doctor_block(report))
    if not report["ok"]:
        return 1
    try:
        recorded, _ = fold_witnessed(frags)
        current = scan_tree(root, ignore_patterns(frags, []))
        if current != recorded:
            print("[sula] files changed after capture; run finish again", file=sys.stderr)
            return 1
    except CaptureError as exc:
        print(f"[sula] incomplete observation: {exc}", file=sys.stderr)
        return 1
    print(f"[sula] completion check OK — observed sha256 tree {tree_digest(current)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
