#!/usr/bin/env python3
"""Sula vector renderer.

Pure function from a folder of typed text fragments to a project view.
Standard library only. See ../../docs/sula-vector-convention.md for the spec.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

CONVENTION_VERSION = "1.0"

TIER_ORDER = ["highest", "invariant", "aesthetic", "discipline", "anti-pattern"]
TIER_TITLES = {
    "highest": "A — Highest rule",
    "invariant": "B — Invariants",
    "aesthetic": "C — Aesthetics",
    "discipline": "D — Implementation discipline",
    "anti-pattern": "E — Anti-patterns",
}


@dataclass
class Fragment:
    id: str
    time: str
    kind: str
    refs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    path: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        if key in {"id", "time", "kind", "refs", "tags", "body", "path"}:
            return getattr(self, key)
        return self.extra.get(key, default)


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    return value


def _parse_inline_list(value: str) -> list[Any]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [_parse_scalar(item) for item in inner.split(",")]


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        tail = text.find("\n---", 4)
        if tail == -1 or text[tail:].strip() != "---":
            return {}, text
        end = tail
        body = ""
    else:
        body = text[end + 5 :]
    raw = text[4:end]

    out: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list_key is not None:
            out[current_list_key].append(_parse_scalar(line[4:]))
            continue
        if ":" not in line:
            current_list_key = None
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            out[key] = []
            current_list_key = key
        elif value.startswith("[") and value.endswith("]"):
            out[key] = _parse_inline_list(value)
            current_list_key = None
        else:
            out[key] = _parse_scalar(value)
            current_list_key = None
    return out, body.strip()


def _fragment_from_meta(
    meta: dict[str, Any], body: str, path: Path
) -> Fragment | None:
    fid = meta.get("id")
    time = meta.get("time")
    kind = meta.get("kind")
    if not fid or not time or not kind:
        return None
    refs = meta.get("refs") or []
    tags = meta.get("tags") or []
    extra = {
        k: v
        for k, v in meta.items()
        if k not in {"id", "time", "kind", "refs", "tags"}
    }
    return Fragment(
        id=str(fid),
        time=str(time),
        kind=str(kind),
        refs=[str(x) for x in refs],
        tags=[str(x) for x in tags],
        extra=extra,
        body=body,
        path=str(path),
    )


def load_fragments(folder: Path) -> list[Fragment]:
    out: list[Fragment] = []
    for path in sorted(folder.rglob("*.md")):
        if path.name in {"AGENTS.md", "README.md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, body = _parse_frontmatter(text)
        frag = _fragment_from_meta(meta, body, path)
        if frag is not None:
            out.append(frag)
    out.sort(key=lambda f: f.time)
    return out


def _matches(
    f: Fragment,
    *,
    kind: str | None = None,
    since: str | None = None,
    until: str | None = None,
    tag: str | None = None,
    ref: str | None = None,
    thread: str | None = None,
    family: str | None = None,
) -> bool:
    if kind and f.kind != kind:
        return False
    if since and f.time < since:
        return False
    if until and f.time > until:
        return False
    if tag and tag not in f.tags:
        return False
    if ref and ref not in f.refs:
        return False
    if thread and f.get("thread_id") != thread:
        return False
    if family and f.get("family_key") != family:
        return False
    return True


def filter_fragments(frags: Iterable[Fragment], **q: Any) -> list[Fragment]:
    return [f for f in frags if _matches(f, **q)]


def _summarize(f: Fragment, max_chars: int = 200) -> str:
    first = f.body.strip().split("\n", 1)[0] if f.body else ""
    return first[:max_chars]


def _to_dict(f: Fragment) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": f.id,
        "time": f.time,
        "kind": f.kind,
        "refs": f.refs,
        "tags": f.tags,
    }
    base.update(f.extra)
    base["summary"] = _summarize(f)
    base["path"] = f.path
    return base


def _is_satisfied(intent: Fragment, frags: list[Fragment]) -> bool:
    back_refs = [f for f in frags if intent.id in f.refs]
    if intent.kind == "goal":
        return any(
            f.kind == "verification-fact" and f.get("passed") in {True, "true"}
            for f in back_refs
        )
    if "done_when" in intent.extra:
        return any(f.kind in {"fact", "verification-fact"} for f in back_refs)
    return False


def _pinned_threads(frags: list[Fragment]) -> list[dict[str, Any]]:
    threads: dict[str, list[Fragment]] = {}
    pinned_ids: set[str] = set()
    for f in frags:
        tid = f.get("thread_id")
        if not tid:
            continue
        threads.setdefault(str(tid), []).append(f)
        if f.get("pinned") in {True, "true"}:
            pinned_ids.add(str(tid))
    out = []
    for tid in sorted(pinned_ids):
        items = sorted(threads[tid], key=lambda f: f.time)
        last = items[-1]
        out.append(
            {
                "thread_id": tid,
                "last_turn_time": last.time,
                "last_turn_summary": _summarize(last),
                "turn_count": len(items),
            }
        )
    return out


def view_list(frags: list[Fragment]) -> list[dict[str, Any]]:
    return [_to_dict(f) for f in frags]


def view_digest(frags: list[Fragment], n: int = 10) -> dict[str, Any]:
    decisions = [f for f in frags if f.kind == "decision"][-n:]
    open_intents = [
        f
        for f in frags
        if f.kind in {"intent", "goal"} and not _is_satisfied(f, frags)
    ][-n:]
    recent = frags[-n:]
    return {
        "decisions": [_to_dict(f) for f in decisions],
        "open_intents": [_to_dict(f) for f in open_intents],
        "recent": [_to_dict(f) for f in recent],
        "pinned_threads": _pinned_threads(frags),
    }


def view_progress(frags: list[Fragment]) -> list[dict[str, Any]]:
    intents = [
        f
        for f in frags
        if f.kind in {"intent", "goal"} and "done_when" in f.extra
    ]
    out = []
    for it in intents:
        evidence = [
            f
            for f in frags
            if it.id in f.refs and f.kind in {"fact", "verification-fact"}
        ]
        out.append(
            {
                "intent": _to_dict(it),
                "evidence": [_to_dict(f) for f in evidence],
                "met": _is_satisfied(it, frags),
            }
        )
    return out


def view_thread(frags: list[Fragment], thread_id: str) -> list[dict[str, Any]]:
    return [_to_dict(f) for f in frags if f.get("thread_id") == thread_id]


def view_family(frags: list[Fragment], family_key: str) -> dict[str, Any]:
    members = [f for f in frags if f.get("family_key") == family_key]
    by_role: dict[str, Fragment] = {}
    for f in members:
        role = str(f.get("artifact_role", "default"))
        if role not in by_role or f.time > by_role[role].time:
            by_role[role] = f
    return {
        "family_key": family_key,
        "members": [_to_dict(f) for f in members],
        "latest_by_role": {r: _to_dict(f) for r, f in by_role.items()},
    }


def view_goals(frags: list[Fragment]) -> list[dict[str, Any]]:
    goals = [f for f in frags if f.kind == "goal"]
    out = []
    for g in goals:
        verifications = [
            f for f in frags if g.id in f.refs and f.kind == "verification-fact"
        ]
        out.append(
            {
                "goal": _to_dict(g),
                "verifications": [_to_dict(f) for f in verifications],
                "met": _is_satisfied(g, frags),
            }
        )
    return out


def view_principles(frags: list[Fragment]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {tier: [] for tier in TIER_ORDER}
    for f in frags:
        if f.kind != "principle":
            continue
        tier = str(f.get("tier", "")).strip()
        if tier in grouped:
            entry = _to_dict(f)
            entry["body"] = f.body
            grouped[tier].append(entry)
    return grouped


def view_changes_summary(frags: list[Fragment]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    fragment_entries: list[dict[str, Any]] = []
    for f in frags:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
        entry: dict[str, Any] = {
            "id": f.id,
            "time": f.time,
            "kind": f.kind,
            "summary": _summarize(f, max_chars=120),
            "refs": list(f.refs),
        }
        if f.kind == "verification-fact":
            entry["passed"] = f.get("passed") in {True, "true"}
        fragment_entries.append(entry)
    return {
        "total": len(frags),
        "by_kind": dict(sorted(by_kind.items(), key=lambda x: (-x[1], x[0]))),
        "fragments": fragment_entries,
    }


def render_changes_summary_line(summary: dict[str, Any]) -> str:
    if summary["total"] == 0:
        return "[sula] no changes"
    parts = ", ".join(f"{n} {k}" for k, n in summary["by_kind"].items())
    return f"[sula] +{summary['total']} ({parts})"


def render_changes_summary_block(frags: list[Fragment]) -> str:
    if not frags:
        return "[sula] no changes"
    width = max((len(f.kind) for f in frags), default=4)
    width = max(width, len("verification-fact"))
    lines = [f"[sula] +{len(frags)} this turn:"]
    for f in frags:
        marker = "+"
        summary = _summarize(f, max_chars=120)
        if f.kind == "verification-fact":
            passed = f.get("passed") in {True, "true"}
            marker = "✓" if passed else "✗"
            target = f.refs[0] if f.refs else ""
            short_target = target.split("--", 1)[-1] if "--" in target else target
            status = "PASS" if passed else "FAIL"
            summary = f"{status}  {short_target}"
        lines.append(f"  {marker} {f.kind.ljust(width)}  {summary}")
    return "\n".join(lines)


def render_principles_block(frags: list[Fragment]) -> str:
    grouped = view_principles(frags)
    if not any(grouped.values()):
        return (
            "## Principles in force\n\n"
            "(no principle fragments found in this vector — copy "
            "tools/sula_vector/principles/*.md into fragments/)\n"
        )
    lines: list[str] = ["## Principles in force", ""]
    for tier in TIER_ORDER:
        items = grouped[tier]
        if not items:
            continue
        lines.append(f"### Tier {TIER_TITLES[tier]}")
        lines.append("")
        for p in items:
            body = (p.get("body") or "").strip()
            if body:
                lines.append(body)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_for_agent(
    frags: list[Fragment], project_name: str = "", n: int = 10
) -> str:
    non_principle = [f for f in frags if f.kind != "principle"]
    digest = view_digest(non_principle, n=n)
    lines: list[str] = []
    header = f"# {project_name} (Sula vector)" if project_name else "# Project context (Sula vector)"
    lines.append(header)
    lines.append("")
    lines.append(f"Convention: v{CONVENTION_VERSION}")
    latest = non_principle[-1].time if non_principle else "n/a"
    lines.append(f"Fragments: {len(non_principle)} activity, {len(frags) - len(non_principle)} principle, latest activity at {latest}")
    lines.append("")

    lines.append(render_principles_block(frags).rstrip())
    lines.append("")

    if digest["pinned_threads"]:
        lines.append("## Pinned threads (last turn)")
        for t in digest["pinned_threads"]:
            lines.append(
                f"- {t['thread_id']} [{t['last_turn_time']}]: {t['last_turn_summary']}"
            )
        lines.append("")

    lines.append("## Recent decisions")
    if not digest["decisions"]:
        lines.append("- (none)")
    for d in digest["decisions"]:
        lines.append(f"- [{d['time']}] {d['id']}: {d['summary']}")
    lines.append("")

    lines.append("## Open intents and goals")
    if not digest["open_intents"]:
        lines.append("- (none)")
    for i in digest["open_intents"]:
        lines.append(f"- [{i['time']}] {i['kind']} {i['id']}: {i['summary']}")
    lines.append("")

    lines.append("## Recent activity")
    if not digest["recent"]:
        lines.append("- (none)")
    for r in digest["recent"]:
        lines.append(f"- [{r['time']}] {r['kind']}: {r['summary']}")
    lines.append("")

    lines.append("## How to act")
    lines.append("Append one new fragment per change. Never edit past fragments.")
    lines.append(
        "Filename: <ISO-8601-time-Z>--<short-slug>.md. Required frontmatter: id, time, kind."
    )
    return "\n".join(lines).rstrip() + "\n"


def _format_human(view: str, result: Any, out: Any) -> None:
    if view == "digest":
        for section in ("pinned_threads", "decisions", "open_intents", "recent"):
            out.write(f"## {section}\n")
            items = result.get(section, [])
            if not items:
                out.write("(none)\n\n")
                continue
            for it in items:
                if section == "pinned_threads":
                    out.write(
                        f"- {it['thread_id']} [{it['last_turn_time']}]: "
                        f"{it['last_turn_summary']}\n"
                    )
                else:
                    out.write(
                        f"- [{it['time']}] {it.get('kind','?')} "
                        f"{it.get('id','')}: {it.get('summary','')}\n"
                    )
            out.write("\n")
        return
    if view == "progress":
        for row in result:
            it = row["intent"]
            mark = "✓" if row["met"] else "·"
            out.write(
                f"{mark} [{it['time']}] {it['kind']} {it['id']}: "
                f"{it.get('summary','')}\n"
            )
            for ev in row["evidence"]:
                out.write(
                    f"    └ [{ev['time']}] {ev['kind']}: {ev.get('summary','')}\n"
                )
        return
    if view == "goals":
        for row in result:
            g = row["goal"]
            mark = "✓" if row["met"] else "·"
            out.write(f"{mark} {g['id']}: {g.get('summary','')}\n")
            for v in row["verifications"]:
                passed = v.get("passed") in {True, "true"}
                out.write(
                    f"    {'PASS' if passed else 'FAIL'} [{v['time']}]: "
                    f"{v.get('summary','')}\n"
                )
        return
    if view == "family":
        out.write(f"family: {result['family_key']}\n")
        for role, item in result["latest_by_role"].items():
            out.write(
                f"  {role}: [{item['time']}] {item['id']} -> "
                f"{item.get('pointer','-')}\n"
            )
        return
    for it in result:
        out.write(
            f"[{it['time']}] {it.get('kind','?')} {it.get('id','')}: "
            f"{it.get('summary','')}\n"
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a Sula vector folder.")
    p.add_argument("folder", help="path to a folder containing fragments/")
    p.add_argument(
        "--view",
        default="digest",
        choices=["digest", "list", "progress", "thread", "family", "goals", "principles", "changes-summary"],
    )
    p.add_argument("--kind")
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--tag")
    p.add_argument("--ref")
    p.add_argument("--thread")
    p.add_argument("--family")
    p.add_argument("--for-agent", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--project-name", default="")
    args = p.parse_args(argv)

    root = Path(args.folder)
    fragments_dir = root / "fragments" if (root / "fragments").is_dir() else root
    if not fragments_dir.exists():
        print(f"folder not found: {fragments_dir}", file=sys.stderr)
        return 2

    frags = load_fragments(fragments_dir)
    filtered = filter_fragments(
        frags,
        kind=args.kind,
        since=args.since,
        until=args.until,
        tag=args.tag,
        ref=args.ref,
        thread=args.thread,
        family=args.family,
    )

    if args.for_agent:
        sys.stdout.write(render_for_agent(filtered, args.project_name))
        return 0

    if args.view == "digest":
        result: Any = view_digest(filtered)
    elif args.view == "list":
        result = view_list(filtered)
    elif args.view == "progress":
        result = view_progress(filtered)
    elif args.view == "thread":
        if not args.thread:
            print("--thread is required for view=thread", file=sys.stderr)
            return 2
        result = view_thread(filtered, args.thread)
    elif args.view == "family":
        if not args.family:
            print("--family is required for view=family", file=sys.stderr)
            return 2
        result = view_family(filtered, args.family)
    elif args.view == "goals":
        result = view_goals(filtered)
    elif args.view == "principles":
        if args.json:
            json.dump(view_principles(filtered), sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            sys.stdout.write(render_principles_block(filtered))
        return 0
    elif args.view == "changes-summary":
        activity = [f for f in filtered if f.kind != "principle"]
        if args.json:
            json.dump(view_changes_summary(activity), sys.stdout, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            sys.stdout.write(render_changes_summary_block(activity) + "\n")
        return 0
    else:
        result = view_list(filtered)

    if args.json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        _format_human(args.view, result, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
