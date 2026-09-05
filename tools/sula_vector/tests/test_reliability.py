"""Behavioral invariants for immutable writing, evidence and project handoffs."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
from append import append_fragment, publish
from capture import CaptureError, capture_graph, fold_witnessed, hash_file, scan_tree, tree_digest
from render import (Fragment, focus_ids, judgment_gap, load_fragments, load_report,
                    render_for_agent, verification_status, view_doctor, view_goals,
                    witnessed_paths)


def skill(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), TOOLS / "skills" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sula-reliability-")).resolve()
        self.frags = self.root / "fragments"
        self.frags.mkdir()

    def tearDown(self):
        shutil.rmtree(self.root)

    def add(self, kind, body="context", **fields):
        return append_fragment(self.frags, kind, {"kind": kind, **fields}, body).stem

    def run_tool(self, name, *args):
        return subprocess.run([sys.executable, str(TOOLS / name), *args], capture_output=True, text=True)

    def capture(self):
        result = self.run_tool("skills/witness.py", "--project-root", str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def render(self, *args):
        result = self.run_tool("render.py", str(self.root), *args, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)


class TestImmutablePublication(ProjectCase):
    def test_concurrent_appends_preserve_every_body_and_old_bytes(self):
        original = append_fragment(self.frags, "same", {"kind": "fact"}, "original")
        old = original.read_bytes()
        def write(n):
            return append_fragment(self.frags, "same", {"kind": "fact"}, f"body-{n}", stamp="2026-09-05T00:00:00Z")
        with ThreadPoolExecutor(max_workers=8) as pool:
            paths = list(pool.map(write, range(40)))
        self.assertEqual(len(set(paths)), 40)
        self.assertEqual({f.body for f in load_fragments(self.frags)}, {"original", *(f"body-{n}" for n in range(40))})
        self.assertEqual(original.read_bytes(), old)
        self.assertTrue(view_doctor(*load_report(self.frags))["ok"])

    def test_publish_collision_never_replaces_content(self):
        target = self.frags / "reserved.md"
        self.assertTrue(publish(target, "first"))
        self.assertFalse(publish(target, "second"))
        self.assertEqual(target.read_text(), "first")

    def test_failed_publication_leaves_no_partial_fragment(self):
        with patch("append.os.link", side_effect=OSError("unsupported")):
            with self.assertRaises(OSError):
                append_fragment(self.frags, "x", {"kind": "fact"}, "body")
        self.assertEqual(list(self.frags.iterdir()), [])

    def test_same_second_verification_results_both_survive(self):
        gid = self.add("goal", verifier_ref="shell: true")
        verifier = skill("verifier-shell")
        with patch.object(verifier, "now_iso", return_value="2026-09-05T00:00:00Z"):
            one = verifier.write_verification_fact(self.frags, gid, "false", False, "first")
            two = verifier.write_verification_fact(self.frags, gid, "true", True, "second")
        self.assertNotEqual(one, two)
        self.assertIn("first", one.read_text())
        self.assertIn("second", two.read_text())

    def test_structured_values_round_trip_without_header_injection(self):
        text = 'A\nkind: goal\nsummary: "overwritten"'
        self.add("decision", summary=text, governs=['path,with comma', 'path\nwith newline'])
        f = load_fragments(self.frags)[0]
        self.assertEqual(f.kind, "decision")
        self.assertEqual(f.get("summary"), text)
        self.assertEqual(f.id_list("governs"), ['path,with comma', 'path\nwith newline'])

    def test_fractional_time_sorts_after_whole_second(self):
        append_fragment(self.frags, "a", {"kind": "fact"}, "later", stamp="2026-09-05T00:00:00.000001Z")
        append_fragment(self.frags, "z", {"kind": "fact"}, "earlier", stamp="2026-09-05T00:00:00Z")
        self.assertEqual([f.body for f in load_fragments(self.frags)], ["earlier", "later"])


class TestEvidenceRelations(ProjectCase):
    def test_missing_explanation_cannot_clear_gap(self):
        wid = self.add("witness", files_changed=1, explained_by=["missing"])
        frags, problems = load_report(self.frags)
        self.assertEqual([f.id for f in judgment_gap(frags)], [wid])
        self.assertIn("dangling-ref", view_doctor(frags, problems)["by_code"])

    def test_evidence_cannot_impersonate_a_judgment(self):
        wid = self.add("witness", files_changed=1)
        self.add("fact", explains=[wid])
        report = view_doctor(*load_report(self.frags))
        self.assertIn("invalid-explanation", report["by_code"])
        self.assertIn("unexplained-change", report["by_code"])

    def test_note_rejects_symbolic_explanation_and_wrong_lane(self):
        wid = self.add("witness", files_changed=1)
        for args in [("--kind", "decision", "--explains", "family:missing"),
                     ("--kind", "fact", "--explains", wid)]:
            result = self.run_tool("note.py", str(self.root), *args, "why")
            self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(len(load_fragments(self.frags)), 1)

    def test_relationship_repair_is_append_only(self):
        wid = self.add("witness", files_changed=1)
        bad = self.add("fact", explains=[wid])
        self.add("correction", supersedes=[bad], explains=[wid])
        self.assertTrue(view_doctor(*load_report(self.frags))["ok"])

    def test_revised_decision_still_explains_its_historical_change(self):
        wid = self.add("witness", files_changed=1)
        old = self.add("decision", "why it changed then", explains=[wid])
        self.add("correction", "choose a different direction now", supersedes=[old])
        self.assertEqual(judgment_gap(load_fragments(self.frags)), [])


class TestProjectionConsistency(ProjectCase):
    def test_display_filters_preserve_goal_status(self):
        gid = self.add("goal", verifier_ref="shell:true", tags=["delivery"], done_when="exit zero")
        self.add("verification-fact", refs=[gid], passed=True)
        for selectors in [(), ("--kind", "goal"), ("--lane", "direction"), ("--tag", "delivery")]:
            rows = self.render("--view", "goals", *selectors)
            self.assertEqual([(r["goal"]["id"], r["met"]) for r in rows], [(gid, True)])

    def test_filtered_judgment_does_not_resurrect_superseded_rule(self):
        old = self.add("decision", "old", tags=["old"])
        self.add("correction", "new", supersedes=[old])
        rows = self.render("--view", "effective", "--kind", "decision")
        self.assertEqual(rows["in_force"], [])
        self.assertEqual(rows["retired"][0]["id"], old)

    def test_filtered_witness_keeps_its_explanation(self):
        wid = self.add("witness", files_changed=1)
        self.add("decision", explains=[wid])
        self.assertEqual(self.render("--view", "unexplained", "--kind", "witness"), [])

    def test_until_is_historical_while_since_is_display_only(self):
        goal = append_fragment(self.frags, "goal", {"kind": "goal", "verifier_ref": "shell:true"}, "goal", stamp="2026-01-01T00:00:00Z")
        append_fragment(self.frags, "verification", {"kind": "verification-fact", "refs": [goal.stem], "passed": True}, "pass", stamp="2026-02-01T00:00:00Z")
        self.assertFalse(self.render("--view", "goals", "--until", "2026-01-02T00:00:00Z")[0]["met"])
        self.assertTrue(self.render("--view", "goals", "--since", "2026-01-01T00:00:00Z")[0]["met"])


class TestContentCapture(ProjectCase):
    def test_whitespace_paths_round_trip_and_decay(self):
        from render import view_decay
        path = self.root / ' \tquoted" name.txt'
        path.write_text("one")
        self.add("decision", "subject", governs=[path.name])
        self.capture()
        self.assertIn("no change", self.capture().stdout)
        path.unlink()
        self.add("decision", "remove subject")
        self.capture()
        self.assertEqual(view_decay(load_fragments(self.frags))[0]["gone"], [path.name])

    def test_large_same_size_edit_is_observed(self):
        path = self.root / "master.mp4"
        with path.open("wb") as handle:
            handle.truncate(50 * 1024 * 1024 + 1)
        self.capture()
        with path.open("r+b") as handle:
            handle.seek(25 * 1024 * 1024)
            handle.write(b"new")
        self.add("decision", "replace master")
        self.capture()
        frags = load_fragments(self.frags)
        witnesses = [f for f in frags if f.kind == "witness"]
        self.assertEqual(witnesses[-1].get("files_changed"), "1")
        self.assertEqual(witnesses[-1].get("hash_method"), "sha256")
        self.assertTrue(view_doctor(frags, [])["ok"])
        self.assertIn("no change", self.capture().stdout)

    def test_unreadable_file_cannot_be_reported_unchanged(self):
        path = self.root / "asset"
        path.write_bytes(b"a")
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            with self.assertRaises(CaptureError):
                hash_file(path)

    def test_empty_project_still_has_a_capture_boundary(self):
        self.capture()
        self.assertEqual(len([f for f in load_fragments(self.frags) if f.kind == "witness"]), 1)

    def test_concurrent_capture_branches_block_until_reconciled(self):
        base = self.add("witness", baseline=True, capture_format="2")
        self.add("witness", capture_format="2", capture_parents=[base], baseline=True)
        self.add("witness", capture_format="2", capture_parents=[base], baseline=True)
        self.assertIn("capture-fork", view_doctor(*load_report(self.frags))["by_code"])
        blocked = self.run_tool("skills/witness.py", "--project-root", str(self.root))
        self.assertEqual(blocked.returncode, 2)
        reconciled = self.run_tool("skills/witness.py", "--project-root", str(self.root), "--reconcile")
        self.assertEqual(reconciled.returncode, 0, reconciled.stderr)
        self.assertTrue(view_doctor(*load_report(self.frags))["ok"])

    def test_missing_capture_ancestor_blocks(self):
        self.add("witness", capture_format="2", capture_parents=["missing"], baseline=True)
        self.assertIn("capture-ancestry", view_doctor(*load_report(self.frags))["by_code"])

    def test_capture_ancestry_outvotes_clock_skew(self):
        base = append_fragment(self.frags, "witness", {"kind": "witness", "capture_format": "2"}, "+ a 1 " + json.dumps("x"), stamp="2026-09-05T01:00:00Z")
        append_fragment(self.frags, "witness", {"kind": "witness", "capture_format": "2", "capture_parents": [base.stem]}, "~ b 1 " + json.dumps("x"), stamp="2026-09-05T00:00:00Z")
        tree, count = fold_witnessed(load_fragments(self.frags))
        self.assertEqual(tree["x"], ("b", 1))
        self.assertEqual(count, 2)

    def test_explicit_parent_wins_over_legacy_clock_order(self):
        base = append_fragment(self.frags, "witness", {"kind": "witness"}, "+ a 1 x", stamp="2026-09-05T10:00:00Z")
        child = append_fragment(self.frags, "witness", {"kind": "witness", "capture_format": "2", "capture_parents": [base.stem]}, "~ b 1 " + json.dumps("x"), stamp="2026-09-05T09:59:00Z")
        ordered, heads, errors = capture_graph(load_fragments(self.frags))
        self.assertEqual([f.id for f in ordered], [base.stem, child.stem])
        self.assertEqual(errors, [])
        self.assertEqual(len(heads), 1)
        tree, count = fold_witnessed(load_fragments(self.frags))
        self.assertEqual(tree["x"], ("b", 1))
        self.assertEqual(count, 2)

    def test_legacy_quote_filename_survives_new_reader(self):
        base = append_fragment(self.frags, "witness", {"kind": "witness"}, '~ a 1 "file.txt"', stamp="2026-09-05T10:00:00Z")
        append_fragment(self.frags, "witness", {"kind": "witness", "capture_format": "2", "capture_parents": [base.stem]}, "+ b 1 " + json.dumps("x"), stamp="2026-09-05T10:01:00Z")
        tree, count = fold_witnessed(load_fragments(self.frags))
        self.assertIn('"file.txt"', tree)
        present, removed = witnessed_paths(load_fragments(self.frags))
        self.assertEqual(present, {"x", '"file.txt"'})
        self.assertEqual(count, 2)

    def test_json_quoted_filename_decodes_in_new_records(self):
        quoted = json.dumps('say "hi".txt', ensure_ascii=False)
        append_fragment(self.frags, "witness", {"kind": "witness", "capture_format": "2"}, "+ a 1 " + json.dumps("x") + "\n~ b 1 " + quoted, stamp="2026-09-05T10:00:00Z")
        tree, count = fold_witnessed(load_fragments(self.frags))
        self.assertIn('say "hi".txt', tree)
        present, removed = witnessed_paths(load_fragments(self.frags))
        self.assertEqual(present, {"x", 'say "hi".txt'})
        self.assertEqual(count, 1)

    def test_malformed_json_path_raises_capture_error(self):
        append_fragment(self.frags, "witness", {"kind": "witness", "capture_format": "2"}, '+ b 1 "unclosed', stamp="2026-09-05T10:00:00Z")
        with self.assertRaises(CaptureError):
            fold_witnessed(load_fragments(self.frags))


class TestVersionedVerification(ProjectCase):
    def test_conflicting_simultaneous_results_do_not_select_an_arbitrary_pass(self):
        gid = self.add("goal", verifier_ref="shell: true")
        for passed in (True, False):
            append_fragment(self.frags, "verification", {"kind": "verification-fact", "refs": [gid], "passed": passed},
                            "result", stamp="2026-09-05T00:00:00Z")
        self.assertFalse(view_goals(load_fragments(self.frags))[0]["met"])

    def test_note_supports_explicit_multiple_inputs(self):
        result = self.run_tool("note.py", str(self.root), "--kind", "goal", "--verifier", "shell: true",
                               "--verify-path", "delivery", "--verify-path", "checks.py", "verify")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(load_fragments(self.frags)[0].id_list("verification_paths"), ["delivery", "checks.py"])

    def verify(self):
        result = self.run_tool("skills/verifier-shell.py", "--project-root", str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_old_pass_becomes_stale_when_content_changes(self):
        path = self.root / "contract.txt"
        path.write_text("v1")
        self.add("goal", verifier_ref="shell: true")
        self.verify()
        self.assertTrue(view_goals(load_fragments(self.frags))[0]["met"])
        path.write_text("v2")
        self.add("decision", "change terms")
        self.capture()
        frags = load_fragments(self.frags)
        vf = next(f for f in frags if f.kind == "verification-fact")
        self.assertEqual(verification_status(vf, frags), "stale")
        self.assertFalse(view_goals(frags)[0]["met"])
        self.verify()
        self.assertTrue(view_goals(load_fragments(self.frags))[0]["met"])

    def test_scoped_pass_survives_unrelated_file_changes(self):
        (self.root / "contract.txt").write_text("v1")
        (self.root / "notes.txt").write_text("v1")
        self.add("goal", verifier_ref="shell: true", verification_paths=["contract.txt"])
        self.verify()
        (self.root / "notes.txt").write_text("v2")
        self.add("decision", "notes only")
        self.capture()
        self.assertTrue(view_goals(load_fragments(self.frags))[0]["met"])

    def test_verifier_that_changes_its_inputs_fails(self):
        (self.root / "x").write_text("before")
        self.add("goal", verifier_ref="shell: printf after > x")
        result = self.run_tool("skills/verifier-shell.py", "--project-root", str(self.root))
        self.assertEqual(result.returncode, 1)
        vf = next(f for f in load_fragments(self.frags) if f.kind == "verification-fact")
        self.assertFalse(vf.get("passed"))

    def test_finish_captures_unexplained_changes_before_checking(self):
        (self.root / "x").write_text("before")
        self.capture()
        (self.root / "x").write_text("after")
        result = self.run_tool("skills/finish.py", "--project-root", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("unexplained-change", result.stdout)


class TestFocusedHandoff(ProjectCase):
    def test_bulk_capture_does_not_pull_unrelated_judgments_into_focus(self):
        unrelated = self.add("decision", "office stationery")
        relevant = self.add("decision", "contract approved")
        self.add("witness", "+ hash 1 contract.txt", explained_by=[unrelated, relevant], files_added=1)
        chosen = focus_ids(load_fragments(self.frags), "contract")
        self.assertIn(relevant, chosen)
        self.assertNotIn(unrelated, chosen)

    def test_review_condition_is_recorded_time_based_and_does_not_retire(self):
        from render import review_conditions
        f = Fragment("rule", "2026-01-01T00:00:00Z", "decision", extra={"review_after": "2026-02-01"})
        self.assertEqual(review_conditions([f]), [])
        clock = Fragment("observed", "2026-02-02T00:00:00Z", "fact")
        self.assertEqual([x.id for x in review_conditions([f, clock])], ["rule"])
        self.assertIn("rule", render_for_agent([f, clock]))

    def test_focus_retains_global_rules_open_work_and_evidence(self):
        principle = self.add("principle", "always keep evidence")
        global_rule = self.add("decision", "do not publish without review", scope="global")
        evidence = self.add("fact", "source contract approved")
        relevant = self.add("decision", "monthly contract cadence", refs=[evidence])
        unrelated = self.add("decision", "old office stationery choice")
        goal = self.add("goal", "unfinished billing", verifier_ref="shell: false")
        gap = self.add("witness", files_changed=1)
        frags = load_fragments(self.frags)
        chosen = focus_ids(frags, "contract")
        self.assertTrue({principle, global_rule, relevant, evidence, goal, gap} <= chosen)
        self.assertNotIn(unrelated, chosen)
        text = render_for_agent(frags, selected_ids=chosen)
        self.assertIn("unfinished billing", text)
        self.assertIn("Unexplained change", text)
        self.assertNotIn("old office stationery choice", text)
        self.assertEqual(text, render_for_agent(frags, selected_ids=chosen))


if __name__ == "__main__":
    unittest.main()
