"""Sula Vector v1.0 test suite (stdlib unittest only).

Covers:
- frontmatter parser (required/optional fields, lists, booleans, malformed)
- fragment loading (skip invalid, sort by time)
- views (digest, list, progress, family, thread, goals, principles, changes-summary)
- render --for-agent (principles prepended, byte-stable, principle-free recent activity)
- migrate.py (idempotence, kind assignment for change-records, releases, events)
- verifier-shell skill (closes goals, idempotent)
- scheduler skill (fires when due, silent when not)
- llm-dispatcher skill (echoes via cat executor, idempotent)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from render import (  # type: ignore  # noqa: E402
    CONVENTION_VERSION,
    Fragment,
    _parse_frontmatter,
    filter_fragments,
    load_fragments,
    render_changes_summary_block,
    render_for_agent,
    render_principles_block,
    view_changes_summary,
    view_digest,
    view_family,
    view_goals,
    view_list,
    view_principles,
    view_progress,
    view_thread,
)


def _make_root() -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp(prefix="sula-test-"))
    frags = root / "fragments"
    frags.mkdir()
    return root, frags


def _write(
    frags_dir: Path,
    *,
    time: str,
    slug: str,
    kind: str,
    body: str = "",
    refs: list[str] | None = None,
    tags: list[str] | None = None,
    extras: dict[str, object] | None = None,
) -> str:
    safe = time.replace(":", "-")
    fid = f"{safe}--{slug}"
    fm = ["---", f"id: {fid}", f"time: {time}", f"kind: {kind}"]
    if refs:
        fm.append(f"refs: [{', '.join(refs)}]")
    if tags:
        fm.append(f"tags: [{', '.join(tags)}]")
    if extras:
        for k, v in extras.items():
            fm.append(f"{k}: {v}")
    fm.append("---")
    (frags_dir / f"{fid}.md").write_text(
        "\n".join(fm) + "\n" + body + "\n", encoding="utf-8"
    )
    return fid


class TestFrontmatterParser(unittest.TestCase):
    def test_required_fields(self):
        text = "---\nid: a\ntime: 2026-05-23T00:00:00Z\nkind: decision\n---\nbody"
        meta, body = _parse_frontmatter(text)
        self.assertEqual(meta["id"], "a")
        self.assertEqual(meta["time"], "2026-05-23T00:00:00Z")
        self.assertEqual(meta["kind"], "decision")
        self.assertEqual(body, "body")

    def test_inline_list(self):
        text = "---\nid: x\ntime: 2026-05-23T00:00:00Z\nkind: x\nrefs: [a, b, c]\n---\n"
        meta, _ = _parse_frontmatter(text)
        self.assertEqual(meta["refs"], ["a", "b", "c"])

    def test_quoted_value(self):
        text = '---\nid: x\ntime: t\nkind: "decision"\n---\nbody'
        meta, _ = _parse_frontmatter(text)
        self.assertEqual(meta["kind"], "decision")

    def test_booleans(self):
        text = "---\nid: x\ntime: t\nkind: x\npinned: true\npassed: false\n---\nbody"
        meta, _ = _parse_frontmatter(text)
        self.assertTrue(meta["pinned"])
        self.assertFalse(meta["passed"])

    def test_no_frontmatter(self):
        meta, body = _parse_frontmatter("just text")
        self.assertEqual(meta, {})
        self.assertEqual(body, "just text")

    def test_unterminated_frontmatter(self):
        text = "---\nid: x\ntime: t\nkind: x\nno closing"
        meta, _ = _parse_frontmatter(text)
        self.assertEqual(meta, {})

    def test_empty_block_list(self):
        text = "---\nid: x\ntime: t\nkind: x\nrefs:\n  - one\n  - two\n---\nbody"
        meta, _ = _parse_frontmatter(text)
        self.assertEqual(meta["refs"], ["one", "two"])


class TestFragmentLoading(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_skip_no_frontmatter(self):
        (self.frags / "junk.md").write_text("just text", encoding="utf-8")
        self.assertEqual(load_fragments(self.frags), [])

    def test_skip_missing_required(self):
        (self.frags / "broken.md").write_text("---\nid: x\n---\nbody", encoding="utf-8")
        self.assertEqual(load_fragments(self.frags), [])

    def test_loads_valid(self):
        _write(self.frags, time="2026-05-23T00:00:00Z", slug="d", kind="decision")
        loaded = load_fragments(self.frags)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].kind, "decision")

    def test_orders_by_time(self):
        _write(self.frags, time="2026-05-23T02:00:00Z", slug="b", kind="fact", body="B")
        _write(self.frags, time="2026-05-23T01:00:00Z", slug="a", kind="fact", body="A")
        loaded = load_fragments(self.frags)
        self.assertEqual([f.body for f in loaded], ["A", "B"])

    def test_recursive_load(self):
        sub = self.frags / "sub"
        sub.mkdir()
        _write(sub, time="2026-05-23T00:00:00Z", slug="d", kind="decision")
        self.assertEqual(len(load_fragments(self.frags)), 1)


class TestViews(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()
        # one decision, one fact, one open goal, one closed intent
        _write(self.frags, time="2026-05-01T00:00:00Z", slug="d1", kind="decision", body="D1")
        _write(self.frags, time="2026-05-02T00:00:00Z", slug="f1", kind="fact", body="F1")
        _write(
            self.frags,
            time="2026-05-03T00:00:00Z",
            slug="g1",
            kind="goal",
            body="G1",
            extras={"done_when": "x", "verifier_ref": "shell:true"},
        )
        intent_id = _write(
            self.frags,
            time="2026-05-04T00:00:00Z",
            slug="i1",
            kind="intent",
            body="I1",
            extras={"done_when": "y"},
        )
        _write(
            self.frags,
            time="2026-05-05T00:00:00Z",
            slug="vf1",
            kind="verification-fact",
            body="vf",
            refs=[intent_id],
            extras={"passed": "true"},
        )

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_digest_separates_decisions_intents_recent(self):
        d = view_digest(load_fragments(self.frags))
        self.assertEqual(len(d["decisions"]), 1)
        # only the goal stays open; intent was satisfied
        self.assertEqual(len(d["open_intents"]), 1)
        self.assertIn("g1", d["open_intents"][0]["id"])

    def test_progress_joins_verification(self):
        rows = view_progress(load_fragments(self.frags))
        # only intents/goals with done_when count
        self.assertEqual(len(rows), 2)
        met = [r for r in rows if r["met"]]
        self.assertEqual(len(met), 1)
        self.assertIn("i1", met[0]["intent"]["id"])

    def test_goals_view(self):
        rows = view_goals(load_fragments(self.frags))
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["met"])

    def test_changes_summary_counts(self):
        s = view_changes_summary(load_fragments(self.frags))
        self.assertEqual(s["total"], 5)
        self.assertEqual(s["by_kind"]["decision"], 1)
        self.assertEqual(s["by_kind"]["verification-fact"], 1)
        self.assertEqual(len(s["fragments"]), 5)

    def test_changes_summary_block_silent_on_empty(self):
        self.assertEqual(render_changes_summary_block([]), "[sula] no changes")

    def test_changes_summary_block_marks_pass(self):
        block = render_changes_summary_block(load_fragments(self.frags))
        self.assertIn("[sula] +5 this turn:", block)
        self.assertIn("✓ verification-fact", block)


class TestThreadAndFamily(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()
        _write(self.frags, time="2026-05-01T00:00:00Z", slug="t1", kind="turn",
               extras={"thread_id": "alpha"})
        _write(self.frags, time="2026-05-02T00:00:00Z", slug="t2", kind="turn",
               extras={"thread_id": "alpha"})
        _write(self.frags, time="2026-05-03T00:00:00Z", slug="a1", kind="artifact",
               extras={"family_key": "X", "artifact_role": "workspace-source", "pointer": "src/x.md"})
        _write(self.frags, time="2026-05-04T00:00:00Z", slug="a2", kind="artifact",
               extras={"family_key": "X", "artifact_role": "exported-derivative", "pointer": "exports/x.docx"})

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_thread_view(self):
        rows = view_thread(load_fragments(self.frags), "alpha")
        self.assertEqual(len(rows), 2)

    def test_family_latest_by_role(self):
        v = view_family(load_fragments(self.frags), "X")
        self.assertEqual(set(v["latest_by_role"].keys()),
                         {"workspace-source", "exported-derivative"})


class TestForAgentRender(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()
        _write(
            self.frags,
            time="2026-05-23T04:50:00Z",
            slug="principle-tier-A",
            kind="principle",
            body="Highest rule body.",
            extras={"tier": "highest"},
        )
        _write(self.frags, time="2026-05-22T00:00:00Z", slug="d1", kind="decision", body="D1")

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_principles_prepended(self):
        out = render_for_agent(load_fragments(self.frags), project_name="T")
        # principle text appears before recent activity
        self.assertIn("Principles in force", out)
        self.assertLess(out.index("Highest rule body."), out.index("Recent activity"))

    def test_principles_excluded_from_activity(self):
        out = render_for_agent(load_fragments(self.frags))
        # principle fragment must not appear under Recent activity bullets
        ra = out.split("## Recent activity", 1)[1]
        self.assertNotIn("principle", ra)

    def test_byte_stable(self):
        a = render_for_agent(load_fragments(self.frags))
        b = render_for_agent(load_fragments(self.frags))
        self.assertEqual(a, b)


class TestMigrateIdempotence(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sula-test-mig-"))
        # Build a synthetic legacy Sula project layout
        (self.root / "docs" / "change-records").mkdir(parents=True)
        (self.root / "docs" / "releases").mkdir(parents=True)
        sula = self.root / ".sula"
        (sula / "events").mkdir(parents=True)
        (sula / "artifacts").mkdir(parents=True)
        (self.root / "docs" / "change-records" / "2026-05-01-foo.md").write_text(
            "# Foo\n\nBody.\n", encoding="utf-8"
        )
        (self.root / "docs" / "releases" / "2026-05-02-release-x.md").write_text(
            "# Release X\n", encoding="utf-8"
        )
        (self.root / "STATUS.md").write_text("# STATUS\nbody\n", encoding="utf-8")
        (sula / "project.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
        (sula / "events" / "log.jsonl").write_text(
            '{"timestamp":"2026-05-01T00:00:00Z","event_type":"record.change","summary":"X"}\n'
            '{"timestamp":"2026-05-01T00:00:00Z","event_type":"record.change","summary":"X"}\n'  # dup
            '{"timestamp":"2026-05-01T00:00:01Z","event_type":"sync.applied","summary":"noise"}\n',
            encoding="utf-8",
        )
        (sula / "artifacts" / "catalog.json").write_text(
            json.dumps({"artifacts": [{"id": "a1", "title": "A1", "kind": "report"}]}),
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.root)

    def _run_migrate(self):
        result = subprocess.run(
            [
                "python3",
                str(TOOLS / "migrate.py"),
                "--project-root",
                str(self.root),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_first_run_produces_expected_kinds(self):
        self._run_migrate()
        frags = load_fragments(self.root / "fragments")
        kinds = {f.kind for f in frags}
        self.assertIn("decision", kinds)  # change-record + manifest + migration-decision
        self.assertIn("release", kinds)
        self.assertIn("snapshot", kinds)  # STATUS.md
        self.assertIn("artifact", kinds)
        self.assertIn("event", kinds)

    def test_second_run_is_noop(self):
        self._run_migrate()
        before = sorted(p.name for p in (self.root / "fragments").glob("*.md"))
        self._run_migrate()
        after = sorted(p.name for p in (self.root / "fragments").glob("*.md"))
        self.assertEqual(before, after)

    def test_event_dedup(self):
        self._run_migrate()
        events = [
            f
            for f in load_fragments(self.root / "fragments")
            if f.kind == "event"
        ]
        # Two duplicate record.change events in source must collapse to one
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].get("event_type"), "record.change")

    def test_legacy_dirs_untouched(self):
        self._run_migrate()
        self.assertTrue((self.root / ".sula").is_dir())
        self.assertTrue((self.root / "STATUS.md").exists())
        self.assertTrue(
            (self.root / "docs" / "change-records" / "2026-05-01-foo.md").exists()
        )


class TestVerifierShellSkill(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()

    def tearDown(self):
        shutil.rmtree(self.root)

    def _run(self):
        result = subprocess.run(
            [
                "python3",
                str(TOOLS / "skills" / "verifier-shell.py"),
                "--project-root",
                str(self.root),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_closes_goal_with_passing_command(self):
        gid = _write(
            self.frags,
            time="2026-05-23T00:00:00Z",
            slug="goal-true",
            kind="goal",
            body="must run true",
            extras={"done_when": "true exits 0", "verifier_ref": "shell:true"},
        )
        self._run()
        verified = [
            f
            for f in load_fragments(self.frags)
            if f.kind == "verification-fact" and gid in f.refs
        ]
        self.assertEqual(len(verified), 1)
        self.assertIn(verified[0].get("passed"), {True, "true"})

    def test_idempotent_on_satisfied_goal(self):
        _write(
            self.frags,
            time="2026-05-23T00:00:00Z",
            slug="goal-true2",
            kind="goal",
            extras={"done_when": "true", "verifier_ref": "shell:true"},
        )
        self._run()
        before = len(list(self.frags.glob("*.md")))
        self._run()
        after = len(list(self.frags.glob("*.md")))
        self.assertEqual(before, after)


class TestSchedulerSkill(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()

    def tearDown(self):
        shutil.rmtree(self.root)

    def _run(self):
        result = subprocess.run(
            [
                "python3",
                str(TOOLS / "skills" / "scheduler.py"),
                "--project-root",
                str(self.root),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_fires_overdue_intent(self):
        past = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        _write(
            self.frags,
            time=past,
            slug="intent-overdue",
            kind="intent",
            body="heartbeat",
            extras={"cadence": "every-1m"},
        )
        self._run()
        ticks = [f for f in load_fragments(self.frags) if f.kind == "cadence-tick"]
        self.assertEqual(len(ticks), 1)

    def test_skips_recent_intent(self):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write(
            self.frags,
            time=now,
            slug="intent-fresh",
            kind="intent",
            body="heartbeat",
            extras={"cadence": "every-10m"},
        )
        self._run()
        ticks = [f for f in load_fragments(self.frags) if f.kind == "cadence-tick"]
        self.assertEqual(len(ticks), 0)


class TestLLMDispatcherSkill(unittest.TestCase):
    def setUp(self):
        self.root, self.frags = _make_root()

    def tearDown(self):
        shutil.rmtree(self.root)

    def _run(self):
        result = subprocess.run(
            [
                "python3",
                str(TOOLS / "skills" / "llm-dispatcher.py"),
                "--project-root",
                str(self.root),
                "--timeout",
                "30",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_dispatches_with_cat_executor(self):
        iid = _write(
            self.frags,
            time="2026-05-23T00:00:00Z",
            slug="intent-cat",
            kind="intent",
            body="hello world via cat",
            extras={"executor_command": "cat"},
        )
        self._run()
        turns = [
            f
            for f in load_fragments(self.frags)
            if f.kind == "turn" and iid in f.refs
        ]
        self.assertEqual(len(turns), 1)
        self.assertIn("hello world via cat", turns[0].body)

    def test_idempotent(self):
        _write(
            self.frags,
            time="2026-05-23T00:00:00Z",
            slug="intent-cat2",
            kind="intent",
            body="x",
            extras={"executor_command": "cat"},
        )
        self._run()
        before = len(list(self.frags.glob("*.md")))
        self._run()
        after = len(list(self.frags.glob("*.md")))
        self.assertEqual(before, after)


class TestConventionVersion(unittest.TestCase):
    def test_version_is_one_zero(self):
        self.assertEqual(CONVENTION_VERSION, "1.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
