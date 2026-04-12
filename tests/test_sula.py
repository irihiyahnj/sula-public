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


def run_cli_input(input_text: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SULA_SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


class SulaCliTests(unittest.TestCase):
    def create_generic_project(self, project_root: Path) -> None:
        (project_root / "docs").mkdir(parents=True, exist_ok=True)
        (project_root / "README.md").write_text(
            "# Field Ops\n\nContract review and staffing coordination project.\n",
            encoding="utf-8",
        )
        (project_root / "docs" / "notes.md").write_text("Initial notes.\n", encoding="utf-8")
        (project_root / "docs" / "project-map.md").write_text(
            """# Project Map

## Tasks

- Review supplier onboarding contract
- Finalize staffing shortlist

## Decisions

- 2026-04-10: Use Sula as the durable project kernel

## Risks

- Contract redlines are still pending legal review

## People

- Alice Chen

## Agreements

- Master Services Agreement with Supplier Northwind

## Milestones

- 2026-04-20: Send final contract package
""",
            encoding="utf-8",
        )

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

    def test_adopt_falls_back_to_generic_project_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli("adopt", "--project-root", str(project_root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Recommended profile: generic-project", result.stdout)
            self.assertIn("defaulted to `generic-project`", result.stdout)
            self.assertNotIn("Blocking issues:", result.stdout)

    def test_adopt_json_reports_detected_workflow_and_storage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--workflow-pack",
                "video-production",
                "--storage-provider",
                "google-drive",
                "--storage-sync-mode",
                "local-sync",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "report")
            self.assertEqual(payload["report"]["project"]["profile"], "generic-project")
            self.assertEqual(payload["report"]["project"]["default_agent"], "Codex")
            self.assertEqual(payload["report"]["manifest"]["workflow"]["pack"], "video-production")
            self.assertEqual(payload["report"]["manifest"]["storage"]["provider"], "google-drive")
            self.assertEqual(payload["report"]["project_root"], str(project_root.resolve()))

    def test_onboard_json_returns_questions_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli("onboard", "--project-root", str(project_root), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "onboard")
            self.assertEqual(payload["status"], "questions")
            question_ids = {item["id"] for item in payload["questions"]}
            self.assertIn("workflow_pack", question_ids)
            self.assertIn("storage_provider", question_ids)
            self.assertEqual(payload["summary"]["workflow"]["pack"], "client-service")
            self.assertEqual(payload["summary"]["storage"]["provider"], "local-fs")
            self.assertTrue(payload["summary"]["what_you_get"])

    def test_onboard_accept_suggested_approve_applies_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli(
                "onboard",
                "--project-root",
                str(project_root),
                "--accept-suggested",
                "--approve",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "onboard")
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["summary"]["workflow"]["pack"], "client-service")
            self.assertTrue((project_root / ".sula" / "project.toml").exists())

    def test_onboard_interactive_uses_defaults_and_waits_for_apply_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli_input(
                "\n\n\n\n\n\n\nn\n",
                "onboard",
                "--project-root",
                str(project_root),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sula onboarding questions:", result.stdout)
            self.assertIn("What you will get:", result.stdout)
            self.assertIn("Sula was not applied.", result.stdout)
            self.assertFalse((project_root / ".sula" / "project.toml").exists())

    def test_adopt_approve_supports_non_git_generic_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli("adopt", "--project-root", str(project_root), "--approve")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project_root / ".sula" / "project.toml").exists())
            self.assertTrue((project_root / ".sula" / "kernel.toml").exists())
            self.assertTrue((project_root / ".sula" / "adapters" / "catalog.json").exists())
            self.assertTrue((project_root / ".sula" / "adapters" / "bundles.json").exists())
            self.assertTrue((project_root / ".sula" / "objects" / "catalog.json").exists())
            self.assertTrue((project_root / ".sula" / "sources" / "registry.json").exists())
            self.assertTrue((project_root / ".sula" / "cache" / "kernel.db").exists())
            manifest = (project_root / ".sula" / "project.toml").read_text(encoding="utf-8")
            self.assertIn('profile = "generic-project"', manifest)
            self.assertIn('primary_branch = "n/a"', manifest)
            self.assertTrue((project_root / "docs" / "runbooks" / "project-operations.md").exists())

    def test_adopt_approve_json_emits_single_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli("adopt", "--project-root", str(project_root), "--approve", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "adopt")
            self.assertEqual(payload["status"], "ok")
            self.assertTrue((project_root / ".sula" / "project.toml").exists())
            adapter_catalog = json.loads((project_root / ".sula" / "adapters" / "catalog.json").read_text(encoding="utf-8"))
            adapter_ids = {item["id"] for item in adapter_catalog["adapters"]}
            self.assertIn("generic-project", adapter_ids)
            self.assertIn("docs", adapter_ids)
            self.assertIn("memory", adapter_ids)
            bundle_catalog = json.loads((project_root / ".sula" / "adapters" / "bundles.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle_catalog["bundles"][0]["profile"], "generic-project")
            registry = json.loads((project_root / ".sula" / "sources" / "registry.json").read_text(encoding="utf-8"))
            paths = {item["path"] for item in registry}
            self.assertIn("README.md", paths)
            self.assertIn("docs/notes.md", paths)
            discovered = [item for item in registry if item.get("discovered")]
            self.assertTrue(discovered)
            readme_entry = next(item for item in registry if item["path"] == "README.md")
            self.assertIn("generic-project", readme_entry["adapters"])
            self.assertIn("docs", readme_entry["adapters"])
            query_cache = json.loads((project_root / ".sula" / "cache" / "query-index.json").read_text(encoding="utf-8"))
            self.assertTrue(query_cache["documents"])
            index_catalog = json.loads((project_root / ".sula" / "indexes" / "catalog.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(index_catalog["counts"]["discovered_sources"], 2)
            self.assertGreaterEqual(index_catalog["counts"]["source_adapter_links"], 2)
            self.assertGreaterEqual(index_catalog["counts"]["objects"], 3)
            sqlite_indexes = {item["name"] for item in index_catalog["indexes"]}
            self.assertIn("sqlite-cache", sqlite_indexes)

    def test_adopt_with_google_drive_storage_adds_google_drive_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--workflow-pack",
                "video-production",
                "--storage-provider",
                "google-drive",
                "--storage-sync-mode",
                "local-sync",
                "--storage-provider-root-url",
                "https://drive.google.com/drive/folders/example",
                "--approve",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = (project_root / ".sula" / "project.toml").read_text(encoding="utf-8")
            self.assertIn('[storage]', manifest)
            self.assertIn('provider = "google-drive"', manifest)
            adapter_catalog = json.loads((project_root / ".sula" / "adapters" / "catalog.json").read_text(encoding="utf-8"))
            adapter_ids = {item["id"] for item in adapter_catalog["adapters"]}
            self.assertIn("google-drive", adapter_ids)

    def test_query_returns_matching_object_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli("query", "--project-root", str(project_root), "--q", "contract", "--kind", "document")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sula query results", result.stdout)
            self.assertIn("README.md", result.stdout)

    def test_query_supports_filters_and_timeline_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli(
                "query",
                "--project-root",
                str(project_root),
                "--q",
                "contract",
                "--kind",
                "agreement",
                "--adapter",
                "docs",
                "--path-prefix",
                "docs/",
                "--timeline",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["results"])
            self.assertEqual(payload["results"][0]["kind"], "agreement")
            self.assertTrue(payload["results"][0]["path"].startswith("docs/"))

    def test_query_dedupes_same_path_kind_title_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli(
                "query",
                "--project-root",
                str(project_root),
                "--q",
                "contract",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            dedupe_keys = {
                (item["kind"], item["path"], item["title"])
                for item in payload["results"]
            }
            self.assertEqual(len(payload["results"]), len(dedupe_keys))

    def test_query_suppresses_low_signal_document_when_richer_same_path_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli(
                "query",
                "--project-root",
                str(project_root),
                "--q",
                "contract",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            richer_paths = {
                item["path"]
                for item in payload["results"]
                if item["kind"] in {"agreement", "change", "task", "decision", "risk", "person", "milestone"}
            }
            low_signal_paths = {
                item["path"]
                for item in payload["results"]
                if item["kind"] in {"document", "code", "config"}
            }
            self.assertFalse(richer_paths & low_signal_paths)

    def test_query_compacts_same_path_families_and_exposes_related_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.write_valid_status(project_root)
            record_result = run_cli(
                "record",
                "new",
                "--project-root",
                str(project_root),
                "--title",
                "Contract review baseline",
                "--summary",
                "Captured the first contract review change record.",
                "--date",
                "2026-04-12",
            )
            self.assertEqual(record_result.returncode, 0, record_result.stderr)

            result = run_cli("query", "--project-root", str(project_root), "--q", "contract", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            change_record = next(
                item for item in payload["results"]
                if item["path"].endswith("2026-04-12-contract-review-baseline.md")
            )
            self.assertEqual(change_record["kind"], "agreement")
            self.assertIn("change", change_record["related_kinds"])

    def test_query_kind_filter_bypasses_family_compaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.write_valid_status(project_root)
            record_result = run_cli(
                "record",
                "new",
                "--project-root",
                str(project_root),
                "--title",
                "Contract review baseline",
                "--summary",
                "Captured the first contract review change record.",
                "--date",
                "2026-04-12",
            )
            self.assertEqual(record_result.returncode, 0, record_result.stderr)

            result = run_cli("query", "--project-root", str(project_root), "--q", "contract", "--kind", "change", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["results"])
            self.assertTrue(all(item["kind"] == "change" for item in payload["results"]))
            self.assertTrue(all("related_kinds" not in item for item in payload["results"]))

    def test_status_json_summarizes_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli("status", "--project-root", str(project_root), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "status")
            self.assertEqual(payload["project"]["profile"], "generic-project")
            self.assertIn("counts", payload["state"])

    def test_artifact_create_register_and_locate_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--workflow-pack",
                "client-service",
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            create_result = run_cli(
                "artifact",
                "create",
                "--project-root",
                str(project_root),
                "--kind",
                "agreement",
                "--title",
                "Hospital Service Contract",
                "--date",
                "2026-04-12",
                "--json",
            )
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            created = json.loads(create_result.stdout)
            self.assertTrue((project_root / created["artifact"]["path"]).exists())
            self.assertEqual(created["artifact"]["slot"], "contracts")

            existing_path = project_root / "finance-note.md"
            existing_path.write_text("# Finance Note\n", encoding="utf-8")
            register_result = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "finance-note.md",
                "--kind",
                "report",
                "--json",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)

            locate_result = run_cli(
                "artifact",
                "locate",
                "--project-root",
                str(project_root),
                "--kind",
                "agreement",
                "--json",
            )
            self.assertEqual(locate_result.returncode, 0, locate_result.stderr)
            located = json.loads(locate_result.stdout)
            self.assertTrue(located["results"])
            self.assertEqual(located["results"][0]["kind"], "agreement")

    def test_portfolio_register_list_and_query_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as portfolio_tmpdir:
            project_root = Path(tmpdir)
            portfolio_root = Path(portfolio_tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--workflow-pack",
                "client-service",
                "--portfolio-workspace",
                "studio",
                "--portfolio-owner",
                "Jing",
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            record_result = run_cli(
                "record",
                "new",
                "--project-root",
                str(project_root),
                "--title",
                "Hospital contract baseline",
                "--summary",
                "Captured the contract baseline.",
                "--date",
                "2026-04-12",
            )
            self.assertEqual(record_result.returncode, 0, record_result.stderr)

            register_result = run_cli(
                "portfolio",
                "register",
                "--project-root",
                str(project_root),
                "--portfolio-root",
                str(portfolio_root),
                "--json",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)

            list_result = run_cli("portfolio", "list", "--portfolio-root", str(portfolio_root), "--json")
            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            listed = json.loads(list_result.stdout)
            self.assertEqual(len(listed["projects"]), 1)

            query_result = run_cli(
                "portfolio",
                "query",
                "--portfolio-root",
                str(portfolio_root),
                "--q",
                "contract",
                "--json",
            )
            self.assertEqual(query_result.returncode, 0, query_result.stderr)
            queried = json.loads(query_result.stdout)
            self.assertTrue(queried["results"])

    def test_object_catalog_extracts_richer_kernel_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            catalog = json.loads((project_root / ".sula" / "objects" / "catalog.json").read_text(encoding="utf-8"))
            kinds = {item["kind"] for item in catalog["objects"]}
            self.assertIn("task", kinds)
            self.assertIn("decision", kinds)
            self.assertIn("risk", kinds)
            self.assertIn("person", kinds)
            self.assertIn("agreement", kinds)
            self.assertIn("milestone", kinds)

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

    def test_doctor_reports_invalid_kernel_event_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            (project_root / ".sula" / "events" / "log.jsonl").write_text("{bad json}\n", encoding="utf-8")

            result = run_cli("doctor", "--project-root", str(project_root), "--strict")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Kernel issues:", result.stdout)
            self.assertIn("invalid kernel event JSON", result.stdout)

    def test_doctor_reports_unknown_adapter_reference_in_source_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            registry_path = project_root / ".sula" / "sources" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry[0]["adapters"] = ["does-not-exist"]
            registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

            result = run_cli("doctor", "--project-root", str(project_root), "--strict")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Kernel issues:", result.stdout)
            self.assertIn("references unknown adapters", result.stdout)

    def test_doctor_reports_invalid_relation_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            relation_path = project_root / ".sula" / "indexes" / "relations.json"
            relation_index = json.loads(relation_path.read_text(encoding="utf-8"))
            relation_index["relations"][0]["from"] = "missing-object"
            relation_path.write_text(json.dumps(relation_index, indent=2), encoding="utf-8")

            result = run_cli("doctor", "--project-root", str(project_root), "--strict")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Kernel issues:", result.stdout)
            self.assertIn("relation references unknown object", result.stdout)

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

    def test_remove_reports_and_preserves_scaffold_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli("remove", "--project-root", str(project_root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sula removal report", result.stdout)
            self.assertIn("preserve scaffold: README.md", result.stdout)
            self.assertTrue((project_root / ".sula" / "project.toml").exists())

    def test_remove_approve_deletes_kernel_and_managed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli("remove", "--project-root", str(project_root), "--approve")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((project_root / ".sula").exists())
            self.assertFalse((project_root / "CODEX.md").exists())
            self.assertFalse((project_root / "docs" / "ops").exists())
            self.assertTrue((project_root / "README.md").exists())
            self.assertTrue((project_root / "STATUS.md").exists())


if __name__ == "__main__":
    unittest.main()
