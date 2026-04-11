from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest
import json


REPO_ROOT = Path(__file__).resolve().parents[1]
SULA_SCRIPT = REPO_ROOT / "scripts" / "sula.py"


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SULA_SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class SulaCliTests(unittest.TestCase):
    def create_react_erpnext_repo(self, project_root: Path) -> None:
        (project_root / "src" / "api").mkdir(parents=True, exist_ok=True)
        (project_root / "src" / "store").mkdir(parents=True, exist_ok=True)
        (project_root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        (project_root / "src" / "api" / "erpnext.ts").write_text("export const api = true;\n", encoding="utf-8")
        (project_root / "src" / "store" / "useStore.ts").write_text("export const store = true;\n", encoding="utf-8")
        (project_root / "src" / "App.tsx").write_text("export const App = () => null;\n", encoding="utf-8")
        (project_root / ".github" / "workflows" / "deploy.yml").write_text(
            "name: deploy\non: workflow_dispatch\n",
            encoding="utf-8",
        )
        (project_root / "README.md").write_text(
            "# OKOKTOTO\n\nReact frontend over ERPNext.\n",
            encoding="utf-8",
        )
        (project_root / "package.json").write_text(
            json.dumps(
                {
                    "name": "okoktoto-v5",
                    "description": "React frontend over ERPNext",
                    "homepage": "https://example.com/app/",
                    "scripts": {"dev": "vite", "build": "vite build", "typecheck": "tsc --noEmit"},
                    "dependencies": {"react": "^19.0.0", "react-router-dom": "^7.0.0"},
                    "devDependencies": {"typescript": "^5.0.0", "vite": "^6.0.0"},
                }
            ),
            encoding="utf-8",
        )

    def write_valid_status(self, project_root: Path) -> None:
        (project_root / "STATUS.md").write_text(
            """# STATUS

- last updated: 2026-04-11

## Summary

- stable summary

## Health

- status: green
- reason: stable

## Current Focus

- memory rollout

## Blockers

- none

## Recent Decisions

- 2026-04-11: established the initial memory contract

## Next Review

- owner: Codex
- date: 2026-04-18
- trigger: next major delivery
""",
            encoding="utf-8",
        )

    def test_init_creates_manifest_lock_and_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            result = run_cli(
                "init",
                "--project-root",
                str(project_root),
                "--name",
                "Alpha Project",
                "--slug",
                "alpha-project",
                "--description",
                "Alpha description",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project_root / ".sula" / "project.toml").exists())
            self.assertTrue((project_root / ".sula" / "version.lock").exists())
            self.assertTrue((project_root / "CODEX.md").exists())
            self.assertTrue((project_root / "README.md").exists())
            self.assertTrue((project_root / "docs" / "ops" / "project-memory.md").exists())
            self.assertTrue((project_root / "docs" / "ops" / "release-checklist.md").exists())
            self.assertTrue((project_root / "docs" / "runbooks" / "deploy-and-rollback.md").exists())
            self.assertTrue((project_root / "docs" / "change-records" / "_template.md").exists())
            self.assertTrue((project_root / "docs" / "releases" / "_template.md").exists())
            self.assertTrue((project_root / "docs" / "incidents" / "_template.md").exists())

    def test_adopt_reports_plan_before_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_react_erpnext_repo(project_root)

            result = run_cli("adopt", "--project-root", str(project_root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Recommended profile: react-frontend-erpnext", result.stdout)
            self.assertIn("Approval flow:", result.stdout)
            self.assertFalse((project_root / ".sula" / "project.toml").exists())

    def test_adopt_approve_applies_and_validates_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_react_erpnext_repo(project_root)

            result = run_cli("adopt", "--project-root", str(project_root), "--approve")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sula adoption completed", result.stdout)
            self.assertIn("How to use Sula after adoption", result.stdout)
            self.assertTrue((project_root / ".sula" / "project.toml").exists())
            self.assertTrue((project_root / ".sula" / "version.lock").exists())
            self.assertTrue((project_root / "CODEX.md").exists())
            self.assertTrue((project_root / "docs" / "change-records").exists())

    def test_adopt_reports_blocker_when_profile_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "README.md").write_text("# Unknown Project\n\nNo known stack markers.\n", encoding="utf-8")

            result = run_cli("adopt", "--project-root", str(project_root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Blocking issues:", result.stdout)
            self.assertIn("could not determine a Sula profile automatically", result.stdout)

    def test_init_supports_sula_core_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            result = run_cli(
                "init",
                "--project-root",
                str(project_root),
                "--profile",
                "sula-core",
                "--name",
                "Sula Root",
                "--slug",
                "sula-root",
                "--description",
                "Self-managed Sula root",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = (project_root / ".sula" / "project.toml").read_text(encoding="utf-8")
            self.assertIn('profile = "sula-core"', manifest)
            self.assertTrue((project_root / "docs" / "runbooks" / "self-adoption.md").exists())
            self.assertTrue((project_root / "docs" / "architecture" / "system-map.md").exists())

    def test_sync_dry_run_reports_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            managed_file = project_root / "CODEX.md"
            managed_file.write_text("local drift\n", encoding="utf-8")

            result = run_cli("sync", "--project-root", str(project_root), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Managed sync plan", result.stdout)
            self.assertIn("CODEX.md", result.stdout)
            self.assertIn("update", result.stdout)
            self.assertIn("Dry run only", result.stdout)
            self.assertEqual(managed_file.read_text(encoding="utf-8"), "local drift\n")

    def test_sync_updates_managed_files_and_preserves_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            managed_file = project_root / "CODEX.md"
            scaffold_file = project_root / "README.md"
            original_scaffold = scaffold_file.read_text(encoding="utf-8")

            managed_file.write_text("local drift\n", encoding="utf-8")
            scaffold_file.write_text("project-owned readme\n", encoding="utf-8")

            result = run_cli("sync", "--project-root", str(project_root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotEqual(managed_file.read_text(encoding="utf-8"), "local drift\n")
            self.assertEqual(scaffold_file.read_text(encoding="utf-8"), "project-owned readme\n")
            self.assertNotEqual(scaffold_file.read_text(encoding="utf-8"), original_scaffold)

    def test_doctor_reports_drift_and_lock_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            (project_root / "CODEX.md").write_text("local drift\n", encoding="utf-8")
            (project_root / ".sula" / "version.lock").write_text(
                'sula_version = "0.0.0"\nprofile = "react-frontend-erpnext"\n',
                encoding="utf-8",
            )

            result = run_cli("doctor", "--project-root", str(project_root))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Managed files differ from the current Sula render", result.stdout)
            self.assertIn("lockfile sula_version", result.stdout)

    def test_doctor_strict_fails_on_missing_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            result = run_cli("doctor", "--project-root", str(project_root), "--strict")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Warnings:", result.stdout)
            self.assertIn("paths.api_layer", result.stdout)

    def test_record_new_creates_change_record_and_updates_memory_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            self.write_valid_status(project_root)

            result = run_cli(
                "record",
                "new",
                "--project-root",
                str(project_root),
                "--title",
                "Adopt memory contract",
                "--summary",
                "Created the first durable memory record.",
                "--date",
                "2026-04-11",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            record_path = project_root / "docs" / "change-records" / "2026-04-11-adopt-memory-contract.md"
            self.assertTrue(record_path.exists())
            self.assertIn("Adopt memory contract", (project_root / "CHANGE-RECORDS.md").read_text(encoding="utf-8"))
            self.assertIn("Adopt memory contract", (project_root / "STATUS.md").read_text(encoding="utf-8"))

    def test_memory_digest_generates_summary_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            self.write_valid_status(project_root)

            record_result = run_cli(
                "record",
                "new",
                "--project-root",
                str(project_root),
                "--title",
                "Capture memory baseline",
                "--summary",
                "Baseline memory record.",
                "--date",
                "2026-04-11",
            )
            self.assertEqual(record_result.returncode, 0, record_result.stderr)

            digest_result = run_cli("memory", "digest", "--project-root", str(project_root))

            self.assertEqual(digest_result.returncode, 0, digest_result.stderr)
            digest_path = project_root / ".sula" / "memory-digest.md"
            self.assertTrue(digest_path.exists())
            digest = digest_path.read_text(encoding="utf-8")
            self.assertIn("Current State", digest)
            self.assertIn("Capture memory baseline", digest)


if __name__ == "__main__":
    unittest.main()
