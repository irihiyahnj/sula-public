#!/usr/bin/env python3
"""Reproducible code/document/media-sized handoffs, not a user time-savings study."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
from append import append_fragment
from migrate import install_tooling


def run(root: Path, tool: str, *args: str, expected: int = 0) -> str:
    result = subprocess.run([sys.executable, str(root / "tools/sula_vector" / tool), *args],
                            cwd=root, capture_output=True, text=True)
    if result.returncode != expected:
        raise AssertionError(f"{tool}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def scenario(parent: Path, name: str, rel: str, size: int) -> dict:
    root = parent / name
    fragments = root / "fragments"
    fragments.mkdir(parents=True)
    install_tooling(root, TOOLS)
    asset = root / rel
    asset.parent.mkdir(parents=True, exist_ok=True)
    with asset.open("wb") as handle:
        handle.write(b"approved = True\n" if asset.suffix == ".py" else b"approved\n")
        if size:
            handle.truncate(size)

    def add(kind: str, body: str, **fields) -> str:
        return append_fragment(fragments, kind, {"kind": kind, **fields}, body).stem

    add("principle", "GLOBAL: retain source evidence.")
    add("decision", "GLOBAL: release only after approval.", scope="global")
    source = add("fact", "SOURCE: approval received for the current delivery.")
    add("decision", "RATIONALE: keep this delivery version because it matches the approved source.",
        refs=[source], tags=["delivery"], governs=[rel])
    for index in range(30):
        add("decision", f"Unrelated historical topic {index}: " + "office convention and rationale " * 5)
    check = f"from pathlib import Path; assert Path({rel!r}).open('rb').read(8) == b'approved'"
    if asset.suffix == ".py":
        check = f"import runpy; assert runpy.run_path({rel!r})['approved'] is True"
    goal = add("goal", "Validate the delivery version.", done_when="approved bytes match",
               verifier_ref="shell: " + shlex.quote(sys.executable) + " -c " + shlex.quote(check),
               verification_paths=[rel], tags=["delivery"])
    run(root, "skills/verifier-shell.py", "--project-root", str(root))
    full = run(root, "render.py", ".", "--for-agent")
    focused = run(root, "render.py", ".", "--for-agent", "--focus", "delivery")
    for marker in ("GLOBAL:", "RATIONALE:", "SOURCE:"):
        if marker not in focused:
            raise AssertionError(f"{name}: focus dropped {marker}")
    if len(focused.encode()) >= len(full.encode()):
        raise AssertionError(f"{name}: task focus did not reduce this fixture's reading cost")
    rows = json.loads(run(root, "render.py", ".", "--view", "goals", "--kind", "goal", "--json"))
    if not next(row for row in rows if row["goal"]["id"] == goal)["met"]:
        raise AssertionError("filtered goal lost its verification")

    copy = parent / f"{name}-received"
    shutil.copytree(root, copy)
    received = run(copy, "render.py", ".", "--for-agent", "--focus", "delivery")
    if focused != received:
        raise AssertionError("handoff changed rendered context")
    run(copy, "skills/auto-update-from-canonical.py", "--help")
    before_size = (copy / rel).stat().st_size
    with (copy / rel).open("r+b") as handle:
        handle.write(b"rejected")
    append_fragment(copy / "fragments", "decision", {"kind": "decision"}, "Change the delivered bytes to exercise stale verification.")
    run(copy, "skills/witness.py", "--project-root", str(copy))
    rows = json.loads(run(copy, "render.py", ".", "--view", "goals", "--json"))
    row = next(row for row in rows if row["goal"]["id"] == goal)
    if row["met"] or "stale" not in row["verification_states"].values():
        raise AssertionError("same-size replacement reused the old approval")
    run(copy, "skills/finish.py", "--project-root", str(copy))
    return {
        "scenario": name, "fixture": rel, "asset_bytes": before_size,
        "full_context_bytes": len(full.encode()), "focused_context_bytes": len(focused.encode()),
        "reading_bytes_reduction_percent": round(100 * (1 - len(focused.encode()) / len(full.encode())), 1),
        "rationale_source_and_global_rules_retained": True,
        "copied_project_boot_byte_stable": True, "copied_updater_starts_without_canonical_imports": True,
        "filtered_goal_stays_verified": True, "same_size_edit_invalidates_old_pass": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="sula-handoff-") as temp:
        root = Path(temp)
        rows = [scenario(root, *case) for case in [
            ("code-project", "src/rule.py", 0),
            ("document-project", "delivery/terms.txt", 0),
            ("media-sized-project", "delivery/master.bin", 50 * 1024 * 1024 + 1),
        ]]
    report = {"method": "controlled fixtures copied between local directories",
              "limitations": "No real-user timing, codec QA, remote-device or sync-provider test; byte counts are not token counts.",
              "scenarios": rows, "passed": True}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
