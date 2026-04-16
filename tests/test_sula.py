from __future__ import annotations

from datetime import date
import subprocess
import tempfile
from pathlib import Path
import unittest
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SULA_SCRIPT = REPO_ROOT / "scripts" / "sula.py"
SITE_BOOTSTRAP_SCRIPT = REPO_ROOT / "site" / "launch" / "bootstrap.py"


def run_cli(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    return subprocess.run(
        ["python3", str(SULA_SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=command_env,
    )


def run_cli_input(input_text: str, *args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    return subprocess.run(
        ["python3", str(SULA_SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=command_env,
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
    def write_provider_fixture(self, fixture_root: Path, *, provider_item_kind: str, provider_item_id: str, payload: dict) -> Path:
        fixture_root.mkdir(parents=True, exist_ok=True)
        fixture_path = fixture_root / f"{provider_item_kind}--{provider_item_id}.json"
        fixture_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return fixture_path

    def start_token_server(self, response_payload: dict[str, object]) -> tuple[HTTPServer, str]:
        class TokenHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_payload, ensure_ascii=True).encode("utf-8"))

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                return

        server = HTTPServer(("127.0.0.1", 0), TokenHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, f"http://127.0.0.1:{server.server_port}/token"

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

    def init_git_repo(self, project_root: Path) -> None:
        subprocess.run(["git", "init", "-b", "main"], cwd=project_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], cwd=project_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_root, check=True, capture_output=True, text=True)

    def init_sula_core_project(self, project_root: Path) -> subprocess.CompletedProcess[str]:
        return run_cli(
            "init",
            "--project-root",
            str(project_root),
            "--name",
            "Sula Core Test",
            "--slug",
            "sula-core-test",
            "--description",
            "Self-managed Sula Core test root",
            "--profile",
            "sula-core",
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

    def seed_valid_change_record(self, project_root: Path, *, title: str, slug: str) -> None:
        result = run_cli(
            "record",
            "new",
            "--project-root",
            str(project_root),
            "--title",
            title,
            "--slug",
            slug,
            "--summary",
            "Seed a durable canary history item for verification.",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        record_path = project_root / "docs" / "change-records" / f"{date.today().isoformat()}-{slug}.md"
        record_path.write_text(
            f"""# {title}

## Metadata

- date: {date.today().isoformat()}
- executor: Codex
- branch: main
- related commit(s): fixture
- status: completed

## Background

Canary verification fixtures need at least one non-placeholder change record so `doctor --strict` and `check` reflect the same bar used by real canaries.

## Analysis

- the fixture should model a minimally healthy managed project
- verification should fail when history is missing or placeholder-only

## Chosen Plan

- seed one durable change record
- rebuild generated memory after finalizing the record

## Execution

- added a finalized change record for the canary fixture

## Verification

- `python3 scripts/sula.py record new --project-root {project_root} --title "{title}"`

## Rollback

- remove this fixture-only change record

## Data Side-effects

- the fixture gains one indexed change record

## Follow-up

- none

## Architecture Boundary Check

- highest rule impact: preserved; canary verification still requires real project history
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
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertTrue((project_root / "README.md").exists())
            self.assertTrue((project_root / "docs" / "change-records" / "_template.md").exists())
            self.assertTrue((project_root / "docs" / "releases" / "_template.md").exists())
            self.assertTrue((project_root / "docs" / "incidents" / "_template.md").exists())
            self.assertIn("python3 scripts/sula.py check --project-root .", (project_root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn(
                "Additional Sula projection docs appear only when their packs are enabled.",
                (project_root / "README.md").read_text(encoding="utf-8"),
            )
            self.assertFalse((project_root / "CODEX.md").exists())
            self.assertFalse((project_root / "docs" / "ops").exists())
            self.assertFalse((project_root / "docs" / "runbooks").exists())

            manifest = (project_root / ".sula" / "project.toml").read_text(encoding="utf-8")
            self.assertIn("[document_design]", manifest)
            self.assertIn("[projection]", manifest)
            self.assertIn('mode = "detached"', manifest)
            self.assertIn('principles_path = "n/a"', manifest)

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
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertFalse((project_root / "CODEX.md").exists())
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
            self.assertIn("[document_design]", manifest)

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

    def test_site_bootstrap_requires_explicit_source_until_public_repo_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            result = run_site_bootstrap(
                "--project-root",
                str(project_root),
                "--json",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Canonical public Sula source is not published yet", result.stderr)

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
            self.assertIn('mode = "detached"', manifest)
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertFalse((project_root / "docs" / "runbooks" / "project-operations.md").exists())

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

    def test_artifact_create_schedule_uses_formal_schedule_bundle(self) -> None:
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
                "schedule",
                "--title",
                "Hospital Shoot Schedule",
                "--date",
                "2026-04-12",
                "--json",
            )
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            payload = json.loads(create_result.stdout)
            artifact = payload["artifact"]
            self.assertEqual(artifact["slot"], "planning")
            artifact_text = (project_root / artifact["path"]).read_text(encoding="utf-8")
            self.assertIn("document bundle: monthly-gantt-dual-actions-raci", artifact_text)
            self.assertIn("## Monthly Overview", artifact_text)
            self.assertIn("## Role-split Gantt", artifact_text)
            self.assertIn("## Counterparty Action Table", artifact_text)
            self.assertIn("## Internal Action Table", artifact_text)
            self.assertIn("## Responsibility Matrix", artifact_text)
            self.assertIn("```mermaid", artifact_text)

    def test_artifact_create_formal_document_bundles_cover_multiple_genres(self) -> None:
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

            cases = [
                (
                    "plan",
                    "Hospital Rollout Plan",
                    "planning",
                    "document genre: proposal",
                    "document bundle: problem-solution-workplan-raci",
                    ["## Executive Summary", "## Proposed Approach", "## Risks And Decisions"],
                ),
                (
                    "report",
                    "Hospital Weekly Report",
                    "delivery",
                    "document genre: report",
                    "document bundle: executive-findings-actions",
                    ["## Key Findings", "## Progress And Risks", "## Next Actions"],
                ),
                (
                    "process",
                    "Hospital Intake Process",
                    "planning",
                    "document genre: process",
                    "document bundle: purpose-workflow-controls-records",
                    ["## Workflow Steps", "## Controls And Exceptions", "## Artifacts And Records"],
                ),
                (
                    "training",
                    "Hospital Coordinator Training",
                    "delivery",
                    "document genre: training",
                    "document bundle: outcomes-agenda-delivery-assessment-followup",
                    ["## Audience And Outcomes", "## Session Plan", "## Follow-up And Records"],
                ),
            ]

            for kind, title, expected_slot, expected_genre, expected_bundle, headings in cases:
                create_result = run_cli(
                    "artifact",
                    "create",
                    "--project-root",
                    str(project_root),
                    "--kind",
                    kind,
                    "--title",
                    title,
                    "--date",
                    "2026-04-12",
                    "--slug",
                    f"{kind}-artifact",
                    "--json",
                )
                self.assertEqual(create_result.returncode, 0, create_result.stderr)
                payload = json.loads(create_result.stdout)
                artifact = payload["artifact"]
                self.assertEqual(artifact["slot"], expected_slot)
                artifact_text = (project_root / artifact["path"]).read_text(encoding="utf-8")
                self.assertIn(expected_genre, artifact_text)
                self.assertIn(expected_bundle, artifact_text)
                for heading in headings:
                    self.assertIn(heading, artifact_text)

    def test_software_delivery_adoption_sets_workflow_policy_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_react_erpnext_repo(project_root)

            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            manifest_text = (project_root / ".sula" / "project.toml").read_text(encoding="utf-8")
            self.assertIn('docs_root = "docs/workflows"', manifest_text)
            self.assertIn('execution_mode = "review-heavy"', manifest_text)
            self.assertIn('design_gate = "complex-only"', manifest_text)
            self.assertIn('plan_gate = "multi-step"', manifest_text)
            self.assertIn('review_policy = "task-checkpoints"', manifest_text)
            self.assertIn('workspace_isolation = "branch"', manifest_text)
            self.assertIn('testing_policy = "verify-first"', manifest_text)
            self.assertIn('closeout_policy = "explicit"', manifest_text)

            status_result = run_cli(
                "status",
                "--project-root",
                str(project_root),
                "--json",
            )
            self.assertEqual(status_result.returncode, 0, status_result.stderr)
            status_payload = json.loads(status_result.stdout)
            self.assertEqual(status_payload["state"]["workflow"]["docs_root"], "docs/workflows")
            self.assertEqual(status_payload["state"]["workflow"]["execution_mode"], "review-heavy")
            self.assertEqual(status_payload["state"]["workflow"]["workspace_isolation"], "branch")

    def test_workflow_assess_recommends_spec_plan_and_review_for_complex_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_react_erpnext_repo(project_root)

            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            assess_result = run_cli(
                "workflow",
                "assess",
                "--project-root",
                str(project_root),
                "--task",
                "Refactor the auth flow, design provider sync rules, and update rollout docs.",
                "--json",
            )
            self.assertEqual(assess_result.returncode, 0, assess_result.stderr)
            payload = json.loads(assess_result.stdout)
            self.assertEqual(payload["command"], "workflow.assess")
            self.assertTrue(payload["assessment"]["task_profile"]["multi_step"])
            self.assertTrue(payload["assessment"]["task_profile"]["complex"])
            self.assertEqual(payload["assessment"]["recommended"]["execution_mode"], "review-heavy")
            self.assertEqual(payload["assessment"]["recommended"]["workspace_isolation"], "branch")
            self.assertTrue(payload["assessment"]["recommended"]["requires_spec"])
            self.assertTrue(payload["assessment"]["recommended"]["requires_plan"])
            self.assertTrue(payload["assessment"]["recommended"]["requires_review"])
            self.assertEqual(payload["assessment"]["recommended"]["scaffolds"], ["spec", "plan", "review"])

    def test_workflow_scaffold_creates_durable_source_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_react_erpnext_repo(project_root)

            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            spec_result = run_cli(
                "workflow",
                "scaffold",
                "--project-root",
                str(project_root),
                "--kind",
                "spec",
                "--title",
                "Auth Sync Spec",
                "--date",
                "2026-04-16",
                "--json",
            )
            self.assertEqual(spec_result.returncode, 0, spec_result.stderr)
            spec_payload = json.loads(spec_result.stdout)
            self.assertEqual(spec_payload["workflow_document"]["path"], "docs/workflows/specs/2026-04-16-auth-sync-spec.md")
            spec_text = (project_root / spec_payload["workflow_document"]["path"]).read_text(encoding="utf-8")
            self.assertIn("## Problem Statement", spec_text)
            self.assertIn("## Verification Plan", spec_text)

            plan_result = run_cli(
                "workflow",
                "scaffold",
                "--project-root",
                str(project_root),
                "--kind",
                "plan",
                "--title",
                "Auth Sync Plan",
                "--date",
                "2026-04-16",
                "--json",
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
            plan_payload = json.loads(plan_result.stdout)
            self.assertEqual(plan_payload["workflow_document"]["path"], "docs/workflows/plans/2026-04-16-auth-sync-plan.md")
            plan_text = (project_root / plan_payload["workflow_document"]["path"]).read_text(encoding="utf-8")
            self.assertIn("document bundle: problem-solution-workplan-raci", plan_text)
            self.assertIn("## Executive Summary", plan_text)

            review_result = run_cli(
                "workflow",
                "scaffold",
                "--project-root",
                str(project_root),
                "--kind",
                "review",
                "--title",
                "Auth Sync Review",
                "--date",
                "2026-04-16",
                "--json",
            )
            self.assertEqual(review_result.returncode, 0, review_result.stderr)
            review_payload = json.loads(review_result.stdout)
            self.assertEqual(review_payload["workflow_document"]["path"], "docs/workflows/reviews/2026-04-16-auth-sync-review.md")
            review_text = (project_root / review_payload["workflow_document"]["path"]).read_text(encoding="utf-8")
            self.assertIn("## Findings", review_text)
            self.assertIn("## Release Gate", review_text)

    def test_workflow_branch_and_close_cover_branch_isolation_and_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_react_erpnext_repo(project_root)
            self.init_git_repo(project_root)

            adopt_result = run_cli(
                "adopt",
                "--project-root",
                str(project_root),
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            branch_result = run_cli(
                "workflow",
                "branch",
                "--project-root",
                str(project_root),
                "--task",
                "Refactor auth sync flow",
                "--create",
                "--json",
            )
            self.assertEqual(branch_result.returncode, 0, branch_result.stderr)
            branch_payload = json.loads(branch_result.stdout)
            self.assertEqual(branch_payload["status"], "created")
            self.assertEqual(branch_payload["workflow_branch"]["branch_name"], "codex/refactor-auth-sync-flow")

            scaffold_result = run_cli(
                "workflow",
                "scaffold",
                "--project-root",
                str(project_root),
                "--kind",
                "review",
                "--title",
                "Refactor Auth Sync Flow",
                "--date",
                "2026-04-16",
                "--json",
            )
            self.assertEqual(scaffold_result.returncode, 0, scaffold_result.stderr)

            spec_result = run_cli(
                "workflow",
                "scaffold",
                "--project-root",
                str(project_root),
                "--kind",
                "spec",
                "--title",
                "Refactor Auth Sync Flow",
                "--date",
                "2026-04-16",
                "--json",
            )
            self.assertEqual(spec_result.returncode, 0, spec_result.stderr)

            plan_result = run_cli(
                "workflow",
                "scaffold",
                "--project-root",
                str(project_root),
                "--kind",
                "plan",
                "--title",
                "Refactor Auth Sync Flow",
                "--date",
                "2026-04-16",
                "--json",
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stderr)

            close_result = run_cli(
                "workflow",
                "close",
                "--project-root",
                str(project_root),
                "--task",
                "Refactor auth sync flow",
                "--json",
            )
            self.assertEqual(close_result.returncode, 0, close_result.stderr)
            close_payload = json.loads(close_result.stdout)
            self.assertEqual(close_payload["status"], "pr-needed")
            self.assertTrue(close_payload["git"]["current_branch"].startswith("codex/"))
            self.assertTrue(close_payload["checks"]["check_passed"])
            self.assertFalse(close_payload["git"]["clean_worktree"])

    def test_canary_verify_runs_local_registry_canaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "registry").mkdir(parents=True, exist_ok=True)
            canary_root = root / "canary-project"
            result = run_cli(
                "init",
                "--project-root",
                str(canary_root),
                "--name",
                "Canary Project",
                "--slug",
                "canary-project",
                "--description",
                "Canary verification fixture",
                "--profile",
                "generic-project",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.write_valid_status(canary_root)
            self.seed_valid_change_record(canary_root, title="Seed canary fixture", slug="seed-canary-fixture")
            digest_result = run_cli(
                "memory",
                "digest",
                "--project-root",
                str(canary_root),
            )
            self.assertEqual(digest_result.returncode, 0, digest_result.stderr)

            (root / "registry" / "adopted-projects.toml").write_text(
                """[[project]]
slug = "canary-project"
name = "Canary Project"
profile = "generic-project"
repository = "local"
primary_branch = "n/a"
deployment_branch = "n/a"
current_sula_version = "0.11.0"
sync_status = "canary"
canary = true
local_root = "canary-project"
owner = "Test"
notes = "Fixture"
""",
                encoding="utf-8",
            )

            verify_result = run_cli(
                "canary",
                "verify",
                "--project-root",
                str(root),
                "--all",
                "--json",
            )
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
            payload = json.loads(verify_result.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["reports"][0]["status"], "ok")

    def test_release_export_public_creates_clean_tree_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "repo"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / "README.md").write_text("# Public Repo\n", encoding="utf-8")
            (project_root / "docs").mkdir()
            (project_root / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")

            export_root = Path(tmpdir) / "public-export"
            export_result = run_cli(
                "release",
                "export-public",
                "--project-root",
                str(project_root),
                "--output",
                str(export_root),
                "--json",
            )
            self.assertEqual(export_result.returncode, 0, export_result.stderr)
            payload = json.loads(export_result.stdout)
            self.assertTrue((export_root / "README.md").exists())
            self.assertTrue((export_root / "docs" / "guide.md").exists())
            self.assertTrue((export_root / payload["manifest"]).exists())
            manifest_text = (export_root / payload["manifest"]).read_text(encoding="utf-8")
            self.assertIn("public_release_strategy: fresh-public-repo", manifest_text)
            self.assertIn("Suggested Initialization", manifest_text)

    def test_release_readiness_reports_missing_governance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "README.md").write_text("# Repo\n", encoding="utf-8")
            readiness_result = run_cli(
                "release",
                "readiness",
                "--project-root",
                str(project_root),
                "--json",
            )
            self.assertEqual(readiness_result.returncode, 1, readiness_result.stderr)
            payload = json.loads(readiness_result.stdout)
            self.assertEqual(payload["status"], "failed")
            self.assertIn("CONTRIBUTING.md", "\n".join(payload["missing_governance_files"]))

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
            bridge_path = project_root / bridge_artifact["path"]
            self.assertTrue(bridge_path.exists())
            with zipfile.ZipFile(bridge_path) as archive:
                names = set(archive.namelist())
            self.assertIn("word/document.xml", names)
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
            expected_relative_path = f"delivery/{date.today().isoformat()}-hospital-intake-draft"
            self.assertEqual(provider_import["project_relative_path"], expected_relative_path)
            self.assertEqual(provider_import["provider_parent_relative_path"], "delivery")
            self.assertEqual(provider_import["register_after_import"]["derived_from"], [bridge_artifact["id"]])
            self.assertIn("--provider-item-kind google-doc", payload["register_command_preview"])
            self.assertIn(f"--project-relative-path {expected_relative_path}", payload["register_command_preview"])
            plan_path = project_root / payload["plan_path"]
            self.assertTrue(plan_path.exists())
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["provider_import"]["bridge_artifact_id"], bridge_artifact["id"])

    def test_provider_native_register_defaults_to_slot_relative_project_path(self) -> None:
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
                "Shared Report Provider",
                "--date",
                "2026-04-12",
                "--provider-item-id",
                "doc-direct-1",
                "--provider-item-kind",
                "google-doc",
                "--provider-item-url",
                "https://docs.google.com/document/d/doc-direct-1/edit",
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--json",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)
            artifact = json.loads(register_result.stdout)["artifact"]
            self.assertEqual(artifact["project_relative_path"], "delivery/2026-04-12-shared-report-provider")
            self.assertEqual(artifact["path"], "delivery/2026-04-12-shared-report-provider")

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

    def test_query_freshness_intent_prefers_provider_truth_for_multi_editor_artifact(self) -> None:
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
            source_path.write_text("# Hospital Intake Draft\n\nShared source draft.\n", encoding="utf-8")
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
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--last-refreshed-at",
                "2026-04-12T08:00:00Z",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            provider_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--kind",
                "report",
                "--title",
                "Hospital Intake Shared Doc",
                "--project-relative-path",
                "delivery/2026-04-12-hospital-intake-report-v1",
                "--provider-item-id",
                "doc-abc123",
                "--provider-item-kind",
                "google-doc",
                "--provider-item-url",
                "https://docs.google.com/document/d/doc-abc123/edit",
                "--derived-from",
                source_artifact["id"],
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--last-provider-sync-at",
                "2099-04-12T10:00:00Z",
                "--json",
            )
            self.assertEqual(provider_register.returncode, 0, provider_register.stderr)
            provider_artifact = json.loads(provider_register.stdout)["artifact"]

            query_result = run_cli(
                "query",
                "--project-root",
                str(project_root),
                "--q",
                "先看最新版本再继续",
                "--json",
            )
            self.assertEqual(query_result.returncode, 0, query_result.stderr)
            payload = json.loads(query_result.stdout)
            self.assertTrue(payload["freshness_intent_detected"])
            self.assertTrue(payload["results"])
            first = payload["results"][0]
            self.assertEqual(first["truth_source_type"], "provider-native")
            self.assertEqual(first["truth_source_artifact_id"], provider_artifact["id"])
            self.assertEqual(first["collaboration_mode"], "multi-editor")
            self.assertTrue(first["local_copy_stale_risk"])
            self.assertEqual(first["freshness_status"], "local-copy-may-be-stale")

            status_result = run_cli("status", "--project-root", str(project_root), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr)
            status_payload = json.loads(status_result.stdout)
            self.assertEqual(status_payload["state"]["truth_sources"]["provider_native"], 1)
            self.assertEqual(status_payload["state"]["truth_sources"]["local_copy_risk_count"], 1)

    def test_artifact_refresh_updates_provider_metadata_and_snapshot_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as fixture_tmpdir:
            project_root = Path(tmpdir)
            fixture_root = Path(fixture_tmpdir)
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
            source_path.write_text("# Hospital Intake Draft\n\nShared source draft.\n", encoding="utf-8")
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
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            provider_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--kind",
                "report",
                "--title",
                "Hospital Intake Shared Doc",
                "--project-relative-path",
                "delivery/2026-04-12-hospital-intake-report-v1",
                "--provider-item-id",
                "doc-abc123",
                "--provider-item-kind",
                "google-doc",
                "--provider-item-url",
                "https://docs.google.com/document/d/doc-abc123/edit",
                "--derived-from",
                source_artifact["id"],
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--json",
            )
            self.assertEqual(provider_register.returncode, 0, provider_register.stderr)
            provider_artifact = json.loads(provider_register.stdout)["artifact"]

            self.write_provider_fixture(
                fixture_root,
                provider_item_kind="google-doc",
                provider_item_id="doc-abc123",
                payload={
                    "metadata": {
                        "id": "doc-abc123",
                        "name": "Hospital Intake Shared Doc",
                        "modifiedTime": "2026-04-12T10:00:00Z",
                        "version": "42",
                        "webViewLink": "https://docs.google.com/document/d/doc-abc123/edit",
                        "etag": "etag-42",
                    },
                    "document": {
                        "title": "Hospital Intake Shared Doc",
                        "body": {
                            "content": [
                                {
                                    "paragraph": {
                                        "elements": [{"textRun": {"content": "Latest provider content.\n"}}],
                                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                                    }
                                }
                            ]
                        },
                    },
                },
            )
            env = {"SULA_PROVIDER_FIXTURE_DIR": str(fixture_root)}
            refresh_result = run_cli(
                "artifact",
                "refresh",
                "--project-root",
                str(project_root),
                "--artifact-id",
                provider_artifact["id"],
                "--json",
                env=env,
            )
            self.assertEqual(refresh_result.returncode, 0, refresh_result.stderr)
            payload = json.loads(refresh_result.stdout)
            self.assertEqual(payload["refresh"]["ok"], 1)
            refresh_row = payload["refresh"]["results"][0]
            self.assertEqual(refresh_row["status"], "ok")
            self.assertEqual(refresh_row["provider_revision_id"], "42")
            snapshot_path = project_root / refresh_row["provider_snapshot_path"]
            self.assertTrue(snapshot_path.exists())
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["provider_revision_id"], "42")
            self.assertIn("Latest provider content.", snapshot["normalized_content"]["plain_text"])

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
            refreshed = next(item for item in located["results"] if item["id"] == provider_artifact["id"])
            self.assertEqual(refreshed["provider_revision_id"], "42")
            self.assertEqual(refreshed["provider_last_fetch_status"], "ok")

    def test_query_freshness_intent_auto_refreshes_provider_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as fixture_tmpdir:
            project_root = Path(tmpdir)
            fixture_root = Path(fixture_tmpdir)
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

            source_path = project_root / "drafts" / "shared-report.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("# Shared Report\n\nLocal copy.\n", encoding="utf-8")
            source_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "drafts/shared-report.md",
                "--kind",
                "report",
                "--title",
                "Shared Report Local",
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--json",
            )
            self.assertEqual(source_register.returncode, 0, source_register.stderr)
            source_artifact = json.loads(source_register.stdout)["artifact"]

            provider_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--kind",
                "report",
                "--title",
                "Shared Report Provider",
                "--project-relative-path",
                "delivery/shared-report",
                "--provider-item-id",
                "doc-shared-1",
                "--provider-item-kind",
                "google-doc",
                "--provider-item-url",
                "https://docs.google.com/document/d/doc-shared-1/edit",
                "--derived-from",
                source_artifact["id"],
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--json",
            )
            self.assertEqual(provider_register.returncode, 0, provider_register.stderr)
            provider_artifact = json.loads(provider_register.stdout)["artifact"]

            self.write_provider_fixture(
                fixture_root,
                provider_item_kind="google-doc",
                provider_item_id="doc-shared-1",
                payload={
                    "metadata": {
                        "id": "doc-shared-1",
                        "name": "Shared Report Provider",
                        "modifiedTime": "2026-04-12T11:00:00Z",
                        "version": "77",
                        "webViewLink": "https://docs.google.com/document/d/doc-shared-1/edit",
                    },
                    "document": {
                        "title": "Shared Report Provider",
                        "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Fresh provider version.\n"}}]}}]},
                    },
                },
            )
            env = {"SULA_PROVIDER_FIXTURE_DIR": str(fixture_root)}
            query_result = run_cli(
                "query",
                "--project-root",
                str(project_root),
                "--q",
                "先看最新版本再继续",
                "--json",
                env=env,
            )
            self.assertEqual(query_result.returncode, 0, query_result.stderr)
            payload = json.loads(query_result.stdout)
            self.assertTrue(payload["freshness_intent_detected"])
            self.assertEqual(payload["refresh"]["ok"], 1)
            first = next(item for item in payload["results"] if item["id"] == provider_artifact["id"])
            self.assertEqual(first["provider_revision_id"], "77")
            self.assertEqual(first["provider_modified_at"], "2026-04-12T11:00:00Z")
            self.assertEqual(first["provider_last_fetch_status"], "ok")
            self.assertEqual(first["truth_source_type"], "provider-native")
            self.assertEqual(first["provider_target_path"], "delivery/shared-report")
            self.assertEqual(first["provider_parent_relative_path"], "delivery")

    def test_provider_refresh_can_use_oauth_store_refresh_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as fixture_tmpdir, tempfile.TemporaryDirectory() as oauth_tmpdir:
            project_root = Path(tmpdir)
            fixture_root = Path(fixture_tmpdir)
            oauth_file = Path(oauth_tmpdir) / "google-oauth.json"
            token_server, token_uri = self.start_token_server(
                {
                    "access_token": "refreshed-access-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/documents.readonly https://www.googleapis.com/auth/spreadsheets.readonly",
                }
            )
            try:
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

                oauth_file.write_text(
                    json.dumps(
                        {
                            "provider": "google-drive",
                            "client_id": "desktop-client-id.apps.googleusercontent.com",
                            "client_secret": "",
                            "token_uri": token_uri,
                            "refresh_token": "refresh-token-value",
                            "access_token": "",
                            "access_token_expires_at": "2000-01-01T00:00:00Z",
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                source_path = project_root / "drafts" / "shared-report.md"
                source_path.parent.mkdir(parents=True, exist_ok=True)
                source_path.write_text("# Shared Report\n\nLocal copy.\n", encoding="utf-8")
                source_register = run_cli(
                    "artifact",
                    "register",
                    "--project-root",
                    str(project_root),
                    "--path",
                    "drafts/shared-report.md",
                    "--kind",
                    "report",
                    "--title",
                    "Shared Report Local",
                    "--collaboration-mode",
                    "multi-editor",
                    "--source-of-truth",
                    "provider-native",
                    "--json",
                )
                self.assertEqual(source_register.returncode, 0, source_register.stderr)
                source_artifact = json.loads(source_register.stdout)["artifact"]

                provider_register = run_cli(
                    "artifact",
                    "register",
                    "--project-root",
                    str(project_root),
                    "--kind",
                    "report",
                    "--title",
                    "Shared Report Provider",
                    "--project-relative-path",
                    "delivery/shared-report",
                    "--provider-item-id",
                    "doc-oauth-1",
                    "--provider-item-kind",
                    "google-doc",
                    "--provider-item-url",
                    "https://docs.google.com/document/d/doc-oauth-1/edit",
                    "--derived-from",
                    source_artifact["id"],
                    "--collaboration-mode",
                    "multi-editor",
                    "--source-of-truth",
                    "provider-native",
                    "--json",
                )
                self.assertEqual(provider_register.returncode, 0, provider_register.stderr)

                self.write_provider_fixture(
                    fixture_root,
                    provider_item_kind="google-doc",
                    provider_item_id="doc-oauth-1",
                    payload={
                        "metadata": {
                            "id": "doc-oauth-1",
                            "name": "Shared Report Provider",
                            "modifiedTime": "2026-04-12T12:00:00Z",
                            "version": "88",
                            "webViewLink": "https://docs.google.com/document/d/doc-oauth-1/edit",
                        },
                        "document": {
                            "title": "Shared Report Provider",
                            "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "OAuth refreshed provider version.\n"}}]}}]},
                        },
                    },
                )
                env = {
                    "SULA_PROVIDER_FIXTURE_DIR": str(fixture_root),
                    "SULA_GOOGLE_OAUTH_FILE": str(oauth_file),
                }
                refresh_result = run_cli(
                    "artifact",
                    "refresh",
                    "--project-root",
                    str(project_root),
                    "--all-collaborative",
                    "--json",
                    env=env,
                )
                self.assertEqual(refresh_result.returncode, 0, refresh_result.stderr)
                payload = json.loads(refresh_result.stdout)
                self.assertEqual(payload["refresh"]["ok"], 1)
                updated_oauth = json.loads(oauth_file.read_text(encoding="utf-8"))
                self.assertEqual(updated_oauth["access_token"], "refreshed-access-token")
            finally:
                token_server.shutdown()
                token_server.server_close()

    def test_provider_refresh_prefers_project_local_oauth_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as fixture_tmpdir:
            project_root = Path(tmpdir)
            fixture_root = Path(fixture_tmpdir)
            oauth_file = project_root / ".sula" / "local" / "google-oauth.json"
            token_server, token_uri = self.start_token_server(
                {
                    "access_token": "project-local-access-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/documents.readonly https://www.googleapis.com/auth/spreadsheets.readonly",
                }
            )
            try:
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

                oauth_file.parent.mkdir(parents=True, exist_ok=True)
                oauth_file.write_text(
                    json.dumps(
                        {
                            "provider": "google-drive",
                            "client_id": "desktop-client-id.apps.googleusercontent.com",
                            "client_secret": "",
                            "token_uri": token_uri,
                            "refresh_token": "project-local-refresh-token",
                            "access_token": "",
                            "access_token_expires_at": "2000-01-01T00:00:00Z",
                        },
                        indent=2,
                        ensure_ascii=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                provider_register = run_cli(
                    "artifact",
                    "register",
                    "--project-root",
                    str(project_root),
                    "--kind",
                    "report",
                    "--title",
                    "Shared Report Provider",
                    "--project-relative-path",
                    "delivery/shared-report",
                    "--provider-item-id",
                    "doc-project-local-1",
                    "--provider-item-kind",
                    "google-doc",
                    "--provider-item-url",
                    "https://docs.google.com/document/d/doc-project-local-1/edit",
                    "--collaboration-mode",
                    "multi-editor",
                    "--source-of-truth",
                    "provider-native",
                    "--json",
                )
                self.assertEqual(provider_register.returncode, 0, provider_register.stderr)

                self.write_provider_fixture(
                    fixture_root,
                    provider_item_kind="google-doc",
                    provider_item_id="doc-project-local-1",
                    payload={
                        "metadata": {
                            "id": "doc-project-local-1",
                            "name": "Shared Report Provider",
                            "modifiedTime": "2026-04-12T12:30:00Z",
                            "version": "91",
                            "webViewLink": "https://docs.google.com/document/d/doc-project-local-1/edit",
                        },
                        "document": {
                            "title": "Shared Report Provider",
                            "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Project local OAuth refresh.\n"}}]}}]},
                        },
                    },
                )
                refresh_result = run_cli(
                    "artifact",
                    "refresh",
                    "--project-root",
                    str(project_root),
                    "--all-collaborative",
                    "--json",
                    env={"SULA_PROVIDER_FIXTURE_DIR": str(fixture_root)},
                )
                self.assertEqual(refresh_result.returncode, 0, refresh_result.stderr)
                payload = json.loads(refresh_result.stdout)
                self.assertEqual(payload["refresh"]["ok"], 1)
                updated_oauth = json.loads(oauth_file.read_text(encoding="utf-8"))
                self.assertEqual(updated_oauth["access_token"], "project-local-access-token")

                status_result = run_cli("status", "--project-root", str(project_root), "--json")
                self.assertEqual(status_result.returncode, 0, status_result.stderr)
                status_payload = json.loads(status_result.stdout)
                self.assertEqual(status_payload["state"]["storage"]["google_oauth_store_path"], ".sula/local/google-oauth.json")
            finally:
                token_server.shutdown()
                token_server.server_close()

    def test_freshness_check_reports_provider_metadata_gap_instead_of_assuming_local_latest(self) -> None:
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
                "--approve",
            )
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            source_path = project_root / "drafts" / "shared-report.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("# Shared Report\n\n多人协作草稿。\n", encoding="utf-8")
            register_result = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--path",
                "drafts/shared-report.md",
                "--kind",
                "report",
                "--title",
                "Shared Report",
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--last-refreshed-at",
                "2026-04-12T08:00:00Z",
                "--json",
            )
            self.assertEqual(register_result.returncode, 0, register_result.stderr)

            locate_result = run_cli(
                "artifact",
                "locate",
                "--project-root",
                str(project_root),
                "--q",
                "共享文档为准",
                "--json",
            )
            self.assertEqual(locate_result.returncode, 0, locate_result.stderr)
            payload = json.loads(locate_result.stdout)
            self.assertTrue(payload["freshness_intent_detected"])
            self.assertEqual(len(payload["results"]), 1)
            artifact = payload["results"][0]
            self.assertEqual(artifact["truth_source_type"], "provider-native")
            self.assertEqual(artifact["freshness_status"], "provider-metadata-missing")
            self.assertIn("provider_root_url", artifact["missing_provider_metadata"])
            self.assertIn("provider_root_id", artifact["missing_provider_metadata"])
            self.assertIn("provider_item_id", artifact["missing_provider_metadata"])
            self.assertIn("provider_item_kind", artifact["missing_provider_metadata"])
            self.assertIn("provider_item_url", artifact["missing_provider_metadata"])
            self.assertIn("Re-register this artifact", artifact["minimal_register_action"])

    def test_artifact_family_tracks_workspace_provider_and_derivative_shapes(self) -> None:
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
            source_path.write_text("# Hospital Intake Draft\n\nFamily tracking source.\n", encoding="utf-8")
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
                "docx",
                "--title",
                "Hospital Intake Export",
                "--json",
            )
            self.assertEqual(materialize_result.returncode, 0, materialize_result.stderr)
            bridge_artifact = json.loads(materialize_result.stdout)["artifact"]
            bridge_path = project_root / bridge_artifact["path"]
            self.assertTrue(bridge_path.exists())
            with zipfile.ZipFile(bridge_path) as archive:
                names = set(archive.namelist())
            self.assertIn("word/document.xml", names)

            provider_register = run_cli(
                "artifact",
                "register",
                "--project-root",
                str(project_root),
                "--kind",
                "report",
                "--title",
                "Hospital Intake Shared Doc",
                "--project-relative-path",
                "delivery/2026-04-12-hospital-intake-report-v1",
                "--provider-item-id",
                "doc-abc123",
                "--provider-item-kind",
                "google-doc",
                "--provider-item-url",
                "https://docs.google.com/document/d/doc-abc123/edit",
                "--derived-from",
                bridge_artifact["id"],
                "--collaboration-mode",
                "multi-editor",
                "--source-of-truth",
                "provider-native",
                "--json",
            )
            self.assertEqual(provider_register.returncode, 0, provider_register.stderr)
            provider_artifact = json.loads(provider_register.stdout)["artifact"]

            locate_result = run_cli(
                "artifact",
                "locate",
                "--project-root",
                str(project_root),
                "--q",
                "Hospital Intake",
                "--json",
            )
            self.assertEqual(locate_result.returncode, 0, locate_result.stderr)
            payload = json.loads(locate_result.stdout)
            family_entries = [
                item
                for item in payload["results"]
                if item["id"] in {source_artifact["id"], bridge_artifact["id"], provider_artifact["id"]}
            ]
            self.assertEqual(len(family_entries), 3)
            self.assertEqual({item["family_key"] for item in family_entries}, {source_artifact["family_key"]})
            self.assertEqual(
                {item["artifact_role"] for item in family_entries},
                {"workspace-source", "exported-derivative", "provider-native-source"},
            )

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
            init_result = run_cli("init", "--project-root", str(project_root), "--projection-mode", "governed")
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

    def test_projection_mode_switch_to_governed_materializes_deeper_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.assertFalse((project_root / "CODEX.md").exists())

            mode_result = run_cli(
                "projection",
                "mode",
                "--project-root",
                str(project_root),
                "--set",
                "governed",
                "--json",
            )

            self.assertEqual(mode_result.returncode, 0, mode_result.stderr)
            payload = json.loads(mode_result.stdout)
            self.assertEqual(payload["projection"]["mode"], "governed")
            self.assertIn("ai-tooling", payload["projection"]["enabled_packs"])
            self.assertTrue((project_root / "CODEX.md").exists())
            self.assertTrue((project_root / "docs" / "ops" / "project-memory.md").exists())

    def test_projection_enable_ai_tooling_auto_enables_ops_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.assertFalse((project_root / "CODEX.md").exists())
            self.assertFalse((project_root / "docs" / "README.md").exists())

            enable_result = run_cli(
                "projection",
                "enable",
                "--project-root",
                str(project_root),
                "--pack",
                "ai-tooling",
                "--json",
            )

            self.assertEqual(enable_result.returncode, 0, enable_result.stderr)
            payload = json.loads(enable_result.stdout)
            self.assertIn("ai-tooling", payload["projection"]["enabled_packs"])
            self.assertIn("ops-core", payload["projection"]["enabled_packs"])
            self.assertTrue((project_root / "CODEX.md").exists())
            self.assertTrue((project_root / "docs" / "README.md").exists())

    def test_projection_disable_ai_tooling_cleans_managed_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--projection-mode", "governed", "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.assertTrue((project_root / "CODEX.md").exists())

            disable_result = run_cli(
                "projection",
                "disable",
                "--project-root",
                str(project_root),
                "--pack",
                "ai-tooling",
                "--json",
            )

            self.assertEqual(disable_result.returncode, 0, disable_result.stderr)
            payload = json.loads(disable_result.stdout)
            self.assertNotIn("ai-tooling", payload["projection"]["enabled_packs"])
            self.assertFalse((project_root / "CODEX.md").exists())
            self.assertTrue((project_root / "AGENTS.md").exists())

    def test_projection_disable_rejects_pack_with_enabled_dependents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--projection-mode", "governed", "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            disable_result = run_cli("projection", "disable", "--project-root", str(project_root), "--pack", "ops-core")

            self.assertNotEqual(disable_result.returncode, 0)
            self.assertIn("dependent packs remain enabled", disable_result.stderr)
            self.assertTrue((project_root / "docs" / "README.md").exists())

    def test_sync_defaults_legacy_consumer_without_projection_section_to_governed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)

            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--projection-mode", "governed", "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.assertTrue((project_root / "CODEX.md").exists())

            manifest_path = project_root / ".sula" / "project.toml"
            manifest = manifest_path.read_text(encoding="utf-8")
            projection_start = manifest.index("[projection]")
            manifest_path.write_text(manifest[:projection_start].rstrip() + "\n", encoding="utf-8")

            (project_root / "CODEX.md").unlink()

            sync_result = run_cli("sync", "--project-root", str(project_root))

            self.assertEqual(sync_result.returncode, 0, sync_result.stderr)
            self.assertTrue((project_root / "CODEX.md").exists())

            projection_result = run_cli("projection", "list", "--project-root", str(project_root), "--json")
            self.assertEqual(projection_result.returncode, 0, projection_result.stderr)
            payload = json.loads(projection_result.stdout)
            self.assertEqual(payload["projection"]["mode"], "governed")
            self.assertIn("ai-tooling", payload["projection"]["enabled_packs"])

    def test_sync_updates_managed_files_and_preserves_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            init_result = run_cli("init", "--project-root", str(project_root), "--projection-mode", "governed")
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
            init_result = run_cli("init", "--project-root", str(project_root), "--projection-mode", "governed")
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
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--projection-mode", "governed", "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            (project_root / ".sula" / "events" / "log.jsonl").write_text("{bad json}\n", encoding="utf-8")

            result = run_cli("doctor", "--project-root", str(project_root), "--strict")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Kernel issues:", result.stdout)
            self.assertIn("invalid kernel event JSON", result.stdout)

    def test_query_handles_duplicate_event_type_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            event_log = project_root / ".sula" / "events" / "log.jsonl"
            event_log.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-04-15T12:00:00Z",
                                "event_type": "artifact.register",
                                "summary": "Registered draft A.",
                                "profile": "generic-project",
                                "project": "Field Ops",
                            },
                            ensure_ascii=True,
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-04-15T12:00:00Z",
                                "event_type": "artifact.register",
                                "summary": "Registered draft B.",
                                "profile": "generic-project",
                                "project": "Field Ops",
                            },
                            ensure_ascii=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            cache_root = project_root / ".sula" / "cache"
            for cache_name in ["kernel.db", "query-index.json"]:
                cache_path = cache_root / cache_name
                if cache_path.exists():
                    cache_path.unlink()

            result = run_cli("query", "--project-root", str(project_root), "--q", "Registered draft", "--kind", "event", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            event_results = [item for item in payload["results"] if item["kind"] == "event"]
            self.assertGreaterEqual(len(event_results), 1)

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

    def test_check_passes_for_freshly_adopted_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            result = run_cli("check", "--project-root", str(project_root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SULA CHECK OK", result.stdout)
            self.assertIn("event_log_entries=", result.stdout)
            self.assertIn("change_records=", result.stdout)

    def test_check_detects_stale_generated_state_until_memory_digest_rebuilds_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            status_path = project_root / "STATUS.md"
            status_text = status_path.read_text(encoding="utf-8")
            status_path.write_text(
                status_text.replace(
                    f"- Initial Sula adoption is complete for this repository under the `generic-project` profile in `detached` projection mode.",
                    "- Initial Sula adoption is complete for this repository in detached projection mode, and the daily Sula check gate is now required for state-sync work.",
                ),
                encoding="utf-8",
            )

            failed = run_cli("check", "--project-root", str(project_root))

            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("SULA CHECK FAILED", failed.stdout)
            self.assertIn(".sula/state/current.md", failed.stdout)
            self.assertIn(".sula/memory-digest.md", failed.stdout)
            self.assertIn("memory digest", failed.stdout)

            rebuild = run_cli("memory", "digest", "--project-root", str(project_root))
            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)

            passed = run_cli("check", "--project-root", str(project_root))
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertIn("SULA CHECK OK", passed.stdout)

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

    def test_feedback_capture_creates_bundle_and_archive_for_managed_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--projection-mode", "governed", "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            (project_root / "CODEX.md").write_text("local managed improvement\n", encoding="utf-8")

            result = run_cli(
                "feedback",
                "capture",
                "--project-root",
                str(project_root),
                "--title",
                "Route reusable drift upstream",
                "--summary",
                "Captured a reusable managed-file fix from one adopted project.",
                "--shared-rationale",
                "Every adopted project should be able to turn local managed-file fixes into reviewable Sula Core feedback.",
                "--local-fix-summary",
                "Adjusted the local managed instructions after a real usage issue.",
                "--requested-outcome",
                "Add a central Sula Core intake and review workflow.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            feedback = payload["feedback"]
            bundle_root = project_root / feedback["bundle_path"]
            archive_path = project_root / feedback["archive_path"]

            self.assertTrue(bundle_root.exists())
            self.assertTrue(archive_path.exists())
            self.assertTrue((bundle_root / "bundle.json").exists())
            self.assertTrue((bundle_root / "changes.patch").exists())

            bundle = json.loads((bundle_root / "bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["feedback"]["title"], "Route reusable drift upstream")
            self.assertEqual(bundle["managed_changes"][0]["path"], "CODEX.md")
            self.assertFalse(bundle["doctor"]["passed"])

            with zipfile.ZipFile(archive_path) as archive:
                self.assertIn(f"{feedback['id']}/bundle.json", archive.namelist())

    def test_feedback_ingest_show_list_and_decide_track_core_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as project_tmpdir, tempfile.TemporaryDirectory() as core_tmpdir:
            project_root = Path(project_tmpdir)
            core_root = Path(core_tmpdir)
            self.create_generic_project(project_root)
            adopt_result = run_cli("adopt", "--project-root", str(project_root), "--projection-mode", "governed", "--approve")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)

            (project_root / "CODEX.md").write_text("local managed improvement\n", encoding="utf-8")
            capture_result = run_cli(
                "feedback",
                "capture",
                "--project-root",
                str(project_root),
                "--title",
                "Standardize upstream feedback",
                "--summary",
                "Converted a local Sula fix into a reusable bundle for core review.",
                "--shared-rationale",
                "This should become a central workflow instead of remaining a one-project patch.",
                "--json",
            )
            self.assertEqual(capture_result.returncode, 0, capture_result.stderr)
            captured = json.loads(capture_result.stdout)["feedback"]
            archive_path = project_root / captured["archive_path"]

            core_init = self.init_sula_core_project(core_root)
            self.assertEqual(core_init.returncode, 0, core_init.stderr)

            ingest_result = run_cli(
                "feedback",
                "ingest",
                "--project-root",
                str(core_root),
                "--bundle-path",
                str(archive_path),
                "--json",
            )
            self.assertEqual(ingest_result.returncode, 0, ingest_result.stderr)
            ingested = json.loads(ingest_result.stdout)["feedback"]
            self.assertEqual(ingested["status"], "open")

            show_result = run_cli(
                "feedback",
                "show",
                "--project-root",
                str(core_root),
                "--feedback-id",
                ingested["id"],
                "--json",
            )
            self.assertEqual(show_result.returncode, 0, show_result.stderr)
            shown = json.loads(show_result.stdout)
            self.assertEqual(shown["bundle"]["feedback"]["title"], "Standardize upstream feedback")

            decide_result = run_cli(
                "feedback",
                "decide",
                "--project-root",
                str(core_root),
                "--feedback-id",
                ingested["id"],
                "--decision",
                "accepted",
                "--note",
                "Promote this into the shared Sula Core release path.",
                "--target-version",
                "0.11.0",
                "--linked-change-record",
                "docs/change-records/2026-04-12-add-feedback-bundles-and-core-review-workflow.md",
                "--json",
            )
            self.assertEqual(decide_result.returncode, 0, decide_result.stderr)
            decided = json.loads(decide_result.stdout)["feedback"]
            self.assertEqual(decided["status"], "accepted")
            self.assertEqual(decided["latest_decision"]["target_version"], "0.11.0")

            list_result = run_cli(
                "feedback",
                "list",
                "--project-root",
                str(core_root),
                "--status",
                "accepted",
                "--json",
            )
            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            listed = json.loads(list_result.stdout)["items"]
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["id"], ingested["id"])

            catalog = json.loads((core_root / "registry" / "feedback" / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["items"][0]["status"], "accepted")
            decision = json.loads(
                (core_root / "registry" / "feedback" / "inbox" / ingested["id"] / "decision.json").read_text(encoding="utf-8")
            )
            self.assertEqual(decision["decision"], "accepted")

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
