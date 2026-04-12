from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest
import json
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SULA_SCRIPT = REPO_ROOT / "scripts" / "sula.py"
SITE_BOOTSTRAP_SCRIPT = REPO_ROOT / "site" / "launch" / "bootstrap.py"


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


def run_site_bootstrap(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SITE_BOOTSTRAP_SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
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

    def create_chinese_project(self, project_root: Path) -> None:
        (project_root / "docs").mkdir(parents=True, exist_ok=True)
        (project_root / "README.md").write_text(
            "# 医院短视频项目\n\n医院短视频拍摄合作项目，涉及合同、排期、报表与交付管理。\n",
            encoding="utf-8",
        )
        (project_root / "docs" / "项目地图.md").write_text(
            """# 项目地图

## 任务

- 整理医院合作合同
- 确认拍摄排期

## 决策

- 2026-04-10: 用 Sula 作为项目记忆内核

## 风险

- 合同红线仍待法务确认

## 人员

- 张三

## 协议

- 医院短视频服务合同

## 里程碑

- 2026-04-20: 提交最终合同与排期
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

    def create_file_system_project_with_frontend_tooling(self, project_root: Path) -> None:
        (project_root / "src").mkdir(parents=True, exist_ok=True)
        (project_root / "README.md").write_text(
            "# File Ops System\n\nAI system for managing project files, documents, records, and workspace state.\n",
            encoding="utf-8",
        )
        (project_root / "package.json").write_text(
            json.dumps(
                {
                    "name": "file-ops-system",
                    "description": "AI system for managing project files",
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

    def test_adopt_json_keeps_file_system_projects_generic_even_with_react_tooling(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_file_system_project_with_frontend_tooling(project_root)

            result = run_cli("adopt", "--project-root", str(project_root), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            manifest = payload["report"]["manifest"]
            self.assertEqual(manifest["project"]["profile"], "generic-project")
            self.assertEqual(manifest["workflow"]["pack"], "generic-project")
            self.assertEqual(manifest["stack"]["frontend"], "Project operating interface over files and records")
            self.assertEqual(manifest["stack"]["backend"], "Project files, documents, and external systems")
            self.assertFalse(manifest["rules"]["react_router_allowed"])

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
            self.assertIn("content_locale", question_ids)
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
            manifest = (project_root / ".sula" / "project.toml").read_text(encoding="utf-8")
            self.assertIn("[language]", manifest)
            self.assertIn('content_locale = "en"', manifest)

    def test_onboard_interactive_uses_defaults_and_waits_for_apply_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_cli_input(
                "\n\n\n\n\n\n\n\nn\n",
                "onboard",
                "--project-root",
                str(project_root),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Sula onboarding questions:", result.stdout)
            self.assertIn("What you will get:", result.stdout)
            self.assertIn("Sula was not applied.", result.stdout)
            self.assertFalse((project_root / ".sula" / "project.toml").exists())

    def test_onboard_defaults_to_chinese_for_cjk_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_chinese_project(project_root)

            result = run_cli("onboard", "--project-root", str(project_root), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["suggested_answers"]["content_locale"], "zh-CN")
            self.assertEqual(payload["summary"]["language"]["content_locale"], "zh-CN")

    def test_chinese_locale_renders_localized_status_and_supports_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_chinese_project(project_root)

            adopt_result = run_cli(
                "onboard",
                "--project-root",
                str(project_root),
                "--accept-suggested",
                "--approve",
                "--json",
            )

            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            status_text = (project_root / "STATUS.md").read_text(encoding="utf-8")
            self.assertIn("# 项目状态", status_text)
            self.assertIn("## 摘要", status_text)
            self.assertIn("- 最后更新:", status_text)
            change_index_text = (project_root / "CHANGE-RECORDS.md").read_text(encoding="utf-8")
            self.assertIn("## 用途", change_index_text)
            self.assertIn("## 索引", change_index_text)

            doctor_result = run_cli("doctor", "--project-root", str(project_root), "--strict")
            self.assertEqual(doctor_result.returncode, 0, doctor_result.stderr)

    def test_chinese_locale_artifact_title_generates_stable_file_and_chinese_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_chinese_project(project_root)
            adopt_result = run_cli(
                "onboard",
                "--project-root",
                str(project_root),
                "--accept-suggested",
                "--approve",
                "--json",
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
                "医院短视频合作合同",
                "--date",
                "2026-04-12",
                "--json",
            )
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            payload = json.loads(create_result.stdout)
            artifact_path = project_root / payload["artifact"]["path"]
            self.assertTrue(artifact_path.exists())
            self.assertIn("item-", artifact_path.name)
            artifact_text = artifact_path.read_text(encoding="utf-8")
            self.assertIn("# 医院短视频合作合同", artifact_text)
            self.assertIn("## 摘要", artifact_text)

    def test_existing_project_can_switch_to_chinese_for_new_records_without_reseeding_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            manifest_path = project_root / ".sula" / "project.toml"
            manifest_text = manifest_path.read_text(encoding="utf-8")
            manifest_text = manifest_text.replace('content_locale = "en"', 'content_locale = "zh-CN"')
            manifest_text = manifest_text.replace('interaction_locale = "en"', 'interaction_locale = "zh-CN"')
            manifest_path.write_text(manifest_text, encoding="utf-8")

            record_result = run_cli(
                "record",
                "new",
                "--project-root",
                str(project_root),
                "--kind",
                "change",
                "--title",
                "医院合同推进",
                "--date",
                "2026-04-12",
                "--json",
            )
            self.assertEqual(record_result.returncode, 0, record_result.stderr)
            payload = json.loads(record_result.stdout)
            record_text = (project_root / payload["record"]["path"]).read_text(encoding="utf-8")
            self.assertIn("## 元数据", record_text)
            self.assertIn("## 背景", record_text)

    def test_site_bootstrap_uses_local_source_to_onboard_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_site_bootstrap(
                "--project-root",
                str(project_root),
                "--source-dir",
                str(REPO_ROOT),
                "--accept-suggested",
                "--approve",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "site-launch")
            self.assertEqual(payload["source"]["kind"], "explicit-source-dir")
            self.assertEqual(payload["status"], "ok")
            self.assertTrue((project_root / ".sula" / "project.toml").exists())

    def test_site_bootstrap_reviews_existing_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_site_bootstrap(
                "--project-root",
                str(project_root),
                "--source-dir",
                str(REPO_ROOT),
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "site-launch")
            self.assertEqual(payload["status"], "existing-consumer")
            self.assertEqual(payload["doctor"]["command"], "doctor")
            self.assertEqual(payload["sync_preview"]["command"], "sync")

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
            self.assertEqual(created["artifact"]["project_relative_path"], created["artifact"]["path"])
            self.assertEqual(created["artifact"]["local_access_paths"], [created["artifact"]["path"]])

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
            registered = json.loads(register_result.stdout)
            self.assertEqual(registered["artifact"]["project_relative_path"], "finance-note.md")
            self.assertEqual(registered["artifact"]["local_access_paths"], ["finance-note.md"])
            self.assertEqual(registered["artifact"]["identity_key"], "path|finance-note.md")

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
            self.assertEqual(located["results"][0]["display_path"], located["results"][0]["path"])

    def test_artifact_register_supports_provider_backed_identity_without_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--workflow-pack",
                "client-service",
                "--storage-provider",
                "google-drive",
                "--storage-sync-mode",
                "local-sync",
                "--storage-provider-root-url",
                "https://drive.google.com/drive/folders/hospital-root",
                "--storage-provider-root-id",
                "hospital-root",
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            register_result = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--kind",
                "report",
                "--title",
                "Hospital Intake Report",
                "--date",
                "2026-04-12",
                "--project-relative-path",
                "delivery/2026-04-12-hospital-intake-report-v1",
                "--provider-item-id",
                "doc-abc123",
                "--provider-item-kind",
                "google-doc",
                "--provider-item-url",
                "https://docs.google.com/document/d/doc-abc123/edit",
                "--derived-from",
                "artifact:intake-brief",
                "--json",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)
            registered = json.loads(register_result.stdout)
            artifact = registered["artifact"]
            self.assertEqual(artifact["path"], "delivery/2026-04-12-hospital-intake-report-v1")
            self.assertEqual(artifact["project_relative_path"], "delivery/2026-04-12-hospital-intake-report-v1")
            self.assertEqual(artifact["provider_item_id"], "doc-abc123")
            self.assertEqual(artifact["provider_item_kind"], "google-doc")
            self.assertEqual(artifact["provider_item_url"], "https://docs.google.com/document/d/doc-abc123/edit")
            self.assertEqual(artifact["local_access_paths"], [])
            self.assertEqual(artifact["derived_from"], ["artifact:intake-brief"])
            self.assertIn("provider|google-drive|hospital-root|google-doc|doc-abc123", artifact["identity_key"])

            locate_result = run_cli(
                "artifact",
                "locate",
                "--project-root",
                str(project_root),
                "--q",
                "doc-abc123",
                "--json",
            )
            self.assertEqual(locate_result.returncode, 0, locate_result.stderr)
            located = json.loads(locate_result.stdout)
            self.assertEqual(len(located["results"]), 1)
            self.assertEqual(located["results"][0]["display_path"], "delivery/2026-04-12-hospital-intake-report-v1")

            query_result = run_cli(
                "query",
                "--project-root",
                str(project_root),
                "--q",
                "doc-abc123",
                "--json",
            )
            self.assertEqual(query_result.returncode, 0, query_result.stderr)
            queried = json.loads(query_result.stdout)
            artifact_result = next(item for item in queried["results"] if item["title"] == "Hospital Intake Report")
            self.assertEqual(artifact_result["kind"], "report")
            self.assertEqual(artifact_result["path"], "delivery/2026-04-12-hospital-intake-report-v1")

    def test_artifact_materialize_markdown_to_html_registers_output(self) -> None:
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

            source_path = project_root / "drafts" / "hospital-intake.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(
                "# Hospital Intake Draft\n\n- Confirm legal owner\n- Prepare handoff\n\n| Field | Value |\n| --- | --- |\n| Department | Cardiology |\n",
                encoding="utf-8",
            )
            source_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "drafts/hospital-intake.md",
                "--kind",
                "report",
                "--title",
                "Hospital Intake Draft",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            materialize_result = run_cli(
                "artifact",
                "materialize",
                "--project-root",
                str(project_root),
                "--source-path",
                "drafts/hospital-intake.md",
                "--target-format",
                "html",
                "--json",
            )
            self.assertEqual(materialize_result.returncode, 0, materialize_result.stderr)
            payload = json.loads(materialize_result.stdout)
            artifact = payload["artifact"]
            output_path = project_root / artifact["path"]
            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.name.endswith(".html"))
            self.assertEqual(artifact["derived_from"], [source_artifact["id"]])
            html_text = output_path.read_text(encoding="utf-8")
            self.assertIn("<h1>Hospital Intake Draft</h1>", html_text)
            self.assertIn("<table>", html_text)

    def test_artifact_materialize_csv_to_xlsx_registers_output(self) -> None:
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

            source_path = project_root / "planning" / "shoot-schedule.csv"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("date,owner\n2026-04-12,Alice\n2026-04-13,Bob\n", encoding="utf-8")
            source_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "planning/shoot-schedule.csv",
                "--kind",
                "schedule",
                "--title",
                "Shoot Schedule",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            materialize_result = run_cli(
                "artifact",
                "materialize",
                "--project-root",
                str(project_root),
                "--source-path",
                "planning/shoot-schedule.csv",
                "--target-format",
                "xlsx",
                "--title",
                "Shoot Schedule Export",
                "--json",
            )
            self.assertEqual(materialize_result.returncode, 0, materialize_result.stderr)
            payload = json.loads(materialize_result.stdout)
            artifact = payload["artifact"]
            output_path = project_root / artifact["path"]
            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.name.endswith(".xlsx"))
            self.assertEqual(artifact["derived_from"], [source_artifact["id"]])
            with zipfile.ZipFile(output_path) as archive:
                names = set(archive.namelist())
            self.assertIn("xl/workbook.xml", names)
            self.assertIn("xl/worksheets/sheet1.xml", names)

    def test_artifact_import_plan_materializes_markdown_for_google_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--workflow-pack",
                "client-service",
                "--storage-provider",
                "google-drive",
                "--storage-sync-mode",
                "local-sync",
                "--storage-provider-root-url",
                "https://drive.google.com/drive/folders/hospital-root",
                "--storage-provider-root-id",
                "hospital-root",
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            source_path = project_root / "drafts" / "hospital-intake.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("# Hospital Intake Draft\n\nThis report should become a Google Doc.\n", encoding="utf-8")
            source_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "drafts/hospital-intake.md",
                "--kind",
                "report",
                "--title",
                "Hospital Intake Draft",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            import_result = run_cli(
                "artifact",
                "import-plan",
                "--project-root",
                str(project_root),
                "--source-path",
                "drafts/hospital-intake.md",
                "--provider-item-kind",
                "google-doc",
                "--json",
            )
            self.assertEqual(import_result.returncode, 0, import_result.stderr)
            payload = json.loads(import_result.stdout)
            self.assertEqual(payload["command"], "artifact.import-plan")
            self.assertTrue(payload["bridge_created"])
            bridge_artifact = payload["bridge_artifact"]
            self.assertTrue(bridge_artifact["path"].endswith(".docx"))
            self.assertEqual(bridge_artifact["derived_from"], [source_artifact["id"]])
            provider_import = payload["provider_import"]
            self.assertEqual(provider_import["provider"], "google-drive")
            self.assertEqual(provider_import["provider_item_kind"], "google-doc")
            self.assertEqual(provider_import["bridge_format"], "docx")
            self.assertEqual(
                provider_import["bridge_mime_type"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            self.assertEqual(provider_import["provider_root_id"], "hospital-root")
            self.assertTrue(provider_import["project_relative_path"].endswith("hospital-intake-draft"))
            self.assertEqual(provider_import["register_after_import"]["derived_from"], [bridge_artifact["id"]])
            self.assertIn("--provider-item-kind google-doc", payload["register_command_preview"])
            plan_path = project_root / payload["plan_path"]
            self.assertTrue(plan_path.exists())
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["provider_import"]["bridge_artifact_id"], bridge_artifact["id"])

    def test_artifact_import_plan_uses_artifact_id_for_google_sheet(self) -> None:
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

            source_path = project_root / "planning" / "shoot-schedule.csv"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("date,owner\n2026-04-12,Alice\n", encoding="utf-8")
            source_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "planning/shoot-schedule.csv",
                "--kind",
                "schedule",
                "--title",
                "Shoot Schedule",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            import_result = run_cli(
                "artifact",
                "import-plan",
                "--project-root",
                str(project_root),
                "--artifact-id",
                source_artifact["id"],
                "--provider-item-kind",
                "google-sheet",
                "--json",
            )
            self.assertEqual(import_result.returncode, 0, import_result.stderr)
            payload = json.loads(import_result.stdout)
            self.assertTrue(payload["bridge_artifact"]["path"].endswith(".xlsx"))
            self.assertEqual(payload["provider_import"]["provider"], "google-drive")
            self.assertEqual(payload["provider_import"]["bridge_format"], "xlsx")
            self.assertEqual(payload["provider_import"]["provider_root_id"], "")
            self.assertEqual(payload["provider_import"]["register_after_import"]["provider_item_kind"], "google-sheet")
            plan_path = project_root / payload["plan_path"]
            self.assertTrue(plan_path.exists())

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
