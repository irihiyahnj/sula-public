#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys


SULA_ROOT = Path(__file__).resolve().parent.parent
VERSION = (SULA_ROOT / "VERSION").read_text(encoding="utf-8").strip()
MANIFEST_PATH = Path(".sula/project.toml")
LOCK_PATH = Path(".sula/version.lock")
KERNEL_PATH = Path(".sula/kernel.toml")
NON_PATH_SENTINELS = {"n/a", "none", "local-only", "unknown"}
KERNEL_SKIP_DIRS = {
    ".git",
    ".sula",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "coverage",
}
DISCOVERABLE_SOURCE_SUFFIXES = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".sh",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".toml",
    ".yml",
    ".yaml",
    ".html",
    ".css",
}
MAX_DISCOVERED_SOURCES = 200
WORKFLOW_PACK_CHOICES = [
    "generic-project",
    "client-service",
    "video-production",
    "software-delivery",
    "operating-system",
]
STORAGE_PROVIDER_CHOICES = ["local-fs", "google-drive"]

MANIFEST_SPEC = {
    "project": {
        "name": "string",
        "slug": "string",
        "description": "string",
        "profile": "string",
        "default_agent": "string",
    },
    "repository": {
        "primary_branch": "string",
        "working_branch_prefix": "string",
        "deployment_branch": "string",
    },
    "rules": {
        "highest_rule": "string",
        "custom_backend_allowed": "bool",
        "react_router_allowed": "bool",
    },
    "stack": {
        "frontend": "string",
        "backend": "string",
    },
    "paths": {
        "api_layer": "string",
        "state_layer": "string",
        "app_shell": "string",
        "status_file": "string",
        "change_records_file": "string",
    },
    "commands": {
        "install": "string",
        "dev": "string",
        "build": "string",
        "typecheck": "string",
    },
    "deploy": {
        "base_path": "string",
        "production_url": "string",
        "workflow": "string",
    },
    "auth": {
        "session_expiry_codes": "string_list",
        "permission_denied_codes": "string_list",
    },
}

OPTIONAL_MANIFEST_SPEC = {
    "memory": {
        "change_record_directory": "string",
        "release_record_directory": "string",
        "incident_record_directory": "string",
        "digest_file": "string",
        "status_max_age_days": "int",
    },
    "workflow": {
        "pack": "string",
        "stage": "string",
        "artifacts_root": "string",
    },
    "storage": {
        "provider": "string",
        "sync_mode": "string",
        "workspace_root": "string",
        "provider_root_url": "string",
        "provider_root_id": "string",
    },
    "portfolio": {
        "portfolio_id": "string",
        "workspace": "string",
        "owner": "string",
    },
}

EXISTENCE_WARNING_FIELDS = [
    ("paths", "api_layer"),
    ("paths", "state_layer"),
    ("paths", "app_shell"),
    ("deploy", "workflow"),
]

STATUS_REQUIRED_SECTIONS = [
    "Summary",
    "Health",
    "Current Focus",
    "Blockers",
    "Recent Decisions",
    "Next Review",
]

CHANGE_RECORDS_REQUIRED_SECTIONS = [
    "Purpose",
    "Rules",
    "Index",
    "Detailed Records",
]

CHANGE_RECORD_REQUIRED_HEADINGS = [
    "# ",
    "## Metadata",
    "## Background",
    "## Analysis",
    "## Chosen Plan",
    "## Execution",
    "## Verification",
    "## Rollback",
    "## Data Side-effects",
    "## Follow-up",
    "## Architecture Boundary Check",
]

RELEASE_RECORD_REQUIRED_HEADINGS = [
    "# ",
    "## Metadata",
    "## Scope",
    "## Risks",
    "## Verification",
    "## Rollback",
    "## Follow-up",
]

INCIDENT_RECORD_REQUIRED_HEADINGS = [
    "# ",
    "## Metadata",
    "## Summary",
    "## Impact",
    "## Timeline",
    "## Root Cause",
    "## Resolution",
    "## Follow-up",
]

STATUS_PLACEHOLDERS = ["YYYY-MM-DD", "_add ", "_write ", "_set "]
INDEX_PLACEHOLDERS = ["_no records yet_", "_add project records here_"]
MEMORY_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INLINE_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
CHANGE_RECORD_FILENAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\.md$")
STATUS_UPDATED_PATTERN = re.compile(r"^- last updated:\s*(.+?)\s*$", re.MULTILINE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass
class RenderAction:
    relative_path: Path
    output_path: Path
    rendered_text: str
    overwrite: bool
    origin: str
    status: str
    impact_level: str
    impact_scope: str


@dataclass
class AdoptionReport:
    project_root: Path
    profile: str | None
    config_data: dict | None
    actions: list[RenderAction]
    blockers: list[str]
    warnings: list[str]
    detection_notes: list[str]
    managed_creates: list[RenderAction]
    managed_updates: list[RenderAction]
    scaffold_creates: list[RenderAction]
    scaffold_preserved: list[RenderAction]


@dataclass
class RemovalReport:
    project_root: Path
    config: "ProjectConfig | None"
    blockers: list[str]
    warnings: list[str]
    kernel_remove_paths: list[Path]
    managed_remove_paths: list[Path]
    scaffold_preserve_paths: list[Path]


@dataclass
class ProjectConfig:
    root: Path
    data: dict

    @property
    def profile(self) -> str:
        return self.data["project"]["profile"]

    def memory_setting(self, key: str, default):
        return self.data.get("memory", {}).get(key, default)

    @property
    def change_record_directory(self) -> Path:
        return self.root / self.memory_setting("change_record_directory", "docs/change-records")

    @property
    def release_record_directory(self) -> Path:
        return self.root / self.memory_setting("release_record_directory", "docs/releases")

    @property
    def incident_record_directory(self) -> Path:
        return self.root / self.memory_setting("incident_record_directory", "docs/incidents")

    @property
    def digest_file(self) -> Path:
        return self.root / self.memory_setting("digest_file", ".sula/memory-digest.md")

    @property
    def status_max_age_days(self) -> int:
        return int(self.memory_setting("status_max_age_days", 30))

    def workflow_setting(self, key: str, default):
        return self.data.get("workflow", {}).get(key, default)

    def storage_setting(self, key: str, default):
        return self.data.get("storage", {}).get(key, default)

    def portfolio_setting(self, key: str, default):
        return self.data.get("portfolio", {}).get(key, default)

    @property
    def workflow_pack(self) -> str:
        return str(self.workflow_setting("pack", default_workflow_pack(self.profile)))

    @property
    def workflow_stage(self) -> str:
        return str(self.workflow_setting("stage", "active"))

    @property
    def artifacts_root(self) -> Path:
        return self.root / self.workflow_setting("artifacts_root", "artifacts")

    @property
    def storage_provider(self) -> str:
        return str(self.storage_setting("provider", "local-fs"))

    @property
    def storage_sync_mode(self) -> str:
        return str(self.storage_setting("sync_mode", "local-only"))

    @property
    def storage_workspace_root(self) -> Path:
        raw = str(self.storage_setting("workspace_root", "."))
        return (self.root / raw).resolve() if not Path(raw).is_absolute() else Path(raw)

    @property
    def provider_root_url(self) -> str:
        return str(self.storage_setting("provider_root_url", "local-only"))

    @property
    def provider_root_id(self) -> str:
        return str(self.storage_setting("provider_root_id", "n/a"))

    def token_map(self) -> dict[str, str]:
        auth = self.data["auth"]
        return {
            "PROJECT_NAME": self.data["project"]["name"],
            "PROJECT_SLUG": self.data["project"]["slug"],
            "PROJECT_DESCRIPTION": self.data["project"]["description"],
            "PROFILE_NAME": self.data["project"]["profile"],
            "DEFAULT_AGENT": self.data["project"]["default_agent"],
            "PRIMARY_BRANCH": self.data["repository"]["primary_branch"],
            "WORKING_BRANCH_PREFIX": self.data["repository"]["working_branch_prefix"],
            "DEPLOYMENT_BRANCH": self.data["repository"]["deployment_branch"],
            "HIGHEST_RULE": self.data["rules"]["highest_rule"],
            "CUSTOM_BACKEND_ALLOWED": str(self.data["rules"]["custom_backend_allowed"]).lower(),
            "REACT_ROUTER_ALLOWED": str(self.data["rules"]["react_router_allowed"]).lower(),
            "FRONTEND_STACK": self.data["stack"]["frontend"],
            "BACKEND_STACK": self.data["stack"]["backend"],
            "API_LAYER_PATH": self.data["paths"]["api_layer"],
            "STATE_LAYER_PATH": self.data["paths"]["state_layer"],
            "APP_SHELL_PATH": self.data["paths"]["app_shell"],
            "STATUS_FILE": self.data["paths"]["status_file"],
            "CHANGE_RECORDS_FILE": self.data["paths"]["change_records_file"],
            "CHANGE_RECORD_DIRECTORY": self.memory_setting("change_record_directory", "docs/change-records"),
            "RELEASE_RECORD_DIRECTORY": self.memory_setting("release_record_directory", "docs/releases"),
            "INCIDENT_RECORD_DIRECTORY": self.memory_setting("incident_record_directory", "docs/incidents"),
            "MEMORY_DIGEST_FILE": self.memory_setting("digest_file", ".sula/memory-digest.md"),
            "STATUS_MAX_AGE_DAYS": str(self.memory_setting("status_max_age_days", 30)),
            "INSTALL_COMMAND": self.data["commands"]["install"],
            "DEV_COMMAND": self.data["commands"]["dev"],
            "BUILD_COMMAND": self.data["commands"]["build"],
            "TYPECHECK_COMMAND": self.data["commands"]["typecheck"],
            "BASE_PATH": self.data["deploy"]["base_path"],
            "PRODUCTION_URL": self.data["deploy"]["production_url"],
            "DEPLOY_WORKFLOW": self.data["deploy"]["workflow"],
            "SESSION_EXPIRY_CODES": ", ".join(auth["session_expiry_codes"]),
            "PERMISSION_DENIED_CODES": ", ".join(auth["permission_denied_codes"]),
            "WORKFLOW_PACK": self.workflow_pack,
            "WORKFLOW_STAGE": self.workflow_stage,
            "ARTIFACTS_ROOT": self.workflow_setting("artifacts_root", "artifacts"),
            "STORAGE_PROVIDER": self.storage_provider,
            "STORAGE_SYNC_MODE": self.storage_sync_mode,
            "PORTFOLIO_ID": self.portfolio_setting("portfolio_id", "default"),
            "PORTFOLIO_WORKSPACE": self.portfolio_setting("workspace", "personal"),
            "CURRENT_DATE": date.today().isoformat(),
            "KERNEL_ADAPTERS": ", ".join(self.kernel_adapters()),
            "GIT_MODE": "enabled" if is_git_repository(self.root) else "not-required",
            "SULA_VERSION": VERSION,
        }

    def kernel_adapters(self) -> list[str]:
        adapters = ["generic-project", "docs", "memory"]
        if is_git_repository(self.root):
            adapters.append("repo")
        provider = self.storage_provider
        if provider == "google-drive":
            adapters.append("google-drive")
        elif provider == "local-fs":
            adapters.append("local-fs")
        if self.profile == "react-frontend-erpnext":
            adapters.extend(["deploy", "erpnext"])
        elif self.profile == "sula-core":
            adapters.extend(["registry", "release"])
        return adapters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sula project operating system manager")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create manifest if missing and render managed/scaffold files")
    add_project_root_arg(init_cmd)
    init_cmd.add_argument("--name")
    init_cmd.add_argument("--slug")
    init_cmd.add_argument("--description")
    init_cmd.add_argument("--profile", default="react-frontend-erpnext")
    add_onboarding_metadata_args(init_cmd)
    init_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    sync_cmd = sub.add_parser("sync", help="Sync managed files from Sula into a project")
    add_project_root_arg(sync_cmd)
    sync_cmd.add_argument("--dry-run", action="store_true", help="Show the managed-file sync plan without writing")
    sync_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    remove_cmd = sub.add_parser("remove", help="Inspect, report, and remove Sula from a project")
    add_project_root_arg(remove_cmd)
    remove_cmd.add_argument("--approve", action="store_true", help="Apply the removal plan after reporting it")
    remove_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    query_cmd = sub.add_parser("query", help="Query project kernel state and sources")
    add_project_root_arg(query_cmd)
    query_cmd.add_argument("--q", required=True, help="Search text")
    query_cmd.add_argument("--kind", help="Optional result kind filter such as project, change, source, document")
    query_cmd.add_argument("--adapter", help="Optional adapter filter such as memory, docs, repo, or deploy")
    query_cmd.add_argument("--status", help="Optional status filter such as current, open, planned, or indexed")
    query_cmd.add_argument("--path-prefix", help="Restrict results to paths under this relative prefix")
    query_cmd.add_argument("--since", help="Only include results on or after this ISO date")
    query_cmd.add_argument("--until", help="Only include results on or before this ISO date")
    query_cmd.add_argument("--timeline", action="store_true", help="Sort time-bearing results newest-first")
    query_cmd.add_argument("--limit", type=int, default=10, help="Maximum number of results to return")
    query_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    adopt_cmd = sub.add_parser("adopt", help="Inspect, report, and apply Sula adoption for a repository")
    add_project_root_arg(adopt_cmd)
    adopt_cmd.add_argument("--profile", help="Profile to use when auto-detection is insufficient")
    adopt_cmd.add_argument("--name", help="Override the detected project name")
    adopt_cmd.add_argument("--slug", help="Override the detected project slug")
    adopt_cmd.add_argument("--description", help="Override the detected project description")
    add_onboarding_metadata_args(adopt_cmd)
    adopt_cmd.add_argument("--approve", action="store_true", help="Apply the adoption plan after reporting it")
    adopt_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    onboard_cmd = sub.add_parser("onboard", help="Ask setup questions, explain the operating contract, and optionally adopt Sula")
    add_project_root_arg(onboard_cmd)
    onboard_cmd.add_argument("--profile", help="Profile to use when auto-detection is insufficient")
    onboard_cmd.add_argument("--name", help="Override the detected project name")
    onboard_cmd.add_argument("--slug", help="Override the detected project slug")
    onboard_cmd.add_argument("--description", help="Override the detected project description")
    add_onboarding_metadata_args(onboard_cmd)
    onboard_cmd.add_argument(
        "--accept-suggested",
        action="store_true",
        help="Use suggested onboarding answers for any unanswered questions instead of prompting",
    )
    onboard_cmd.add_argument("--approve", action="store_true", help="Apply the adoption after onboarding")
    onboard_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    doctor_cmd = sub.add_parser("doctor", help="Check manifest, lockfile, and managed files")
    add_project_root_arg(doctor_cmd)
    doctor_cmd.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings such as manifest references that do not exist in the project",
    )
    doctor_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    status_cmd = sub.add_parser("status", help="Summarize current project state")
    add_project_root_arg(status_cmd)
    status_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_cmd = sub.add_parser("artifact", help="Create, register, and locate project artifacts")
    artifact_sub = artifact_cmd.add_subparsers(dest="artifact_command", required=True)
    artifact_create_cmd = artifact_sub.add_parser("create", help="Create a managed project artifact in the workflow slot")
    add_project_root_arg(artifact_create_cmd)
    artifact_create_cmd.add_argument("--kind", required=True, help="Artifact kind such as agreement, report, invoice, schedule")
    artifact_create_cmd.add_argument("--title", required=True)
    artifact_create_cmd.add_argument("--slug")
    artifact_create_cmd.add_argument("--slot")
    artifact_create_cmd.add_argument("--date")
    artifact_create_cmd.add_argument("--summary", default="")
    artifact_create_cmd.add_argument("--extension", default=".md")
    artifact_create_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_register_cmd = artifact_sub.add_parser("register", help="Register an existing project artifact path")
    add_project_root_arg(artifact_register_cmd)
    artifact_register_cmd.add_argument("--path", required=True, help="Path to an existing artifact, relative to project root")
    artifact_register_cmd.add_argument("--kind", required=True)
    artifact_register_cmd.add_argument("--title")
    artifact_register_cmd.add_argument("--slot")
    artifact_register_cmd.add_argument("--summary", default="")
    artifact_register_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_locate_cmd = artifact_sub.add_parser("locate", help="Locate registered artifacts")
    add_project_root_arg(artifact_locate_cmd)
    artifact_locate_cmd.add_argument("--kind")
    artifact_locate_cmd.add_argument("--q", default="")
    artifact_locate_cmd.add_argument("--limit", type=int, default=10)
    artifact_locate_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    record_cmd = sub.add_parser("record", help="Create a memory record inside a project")
    record_sub = record_cmd.add_subparsers(dest="record_command", required=True)
    record_new_cmd = record_sub.add_parser("new", help="Create a new change, release, or incident record")
    add_project_root_arg(record_new_cmd)
    record_new_cmd.add_argument("--kind", choices=["change", "release", "incident"], default="change")
    record_new_cmd.add_argument("--title", required=True)
    record_new_cmd.add_argument("--slug")
    record_new_cmd.add_argument("--date")
    record_new_cmd.add_argument("--summary", default="")
    record_new_cmd.add_argument("--executor")
    record_new_cmd.add_argument("--branch")
    record_new_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    memory_cmd = sub.add_parser("memory", help="Generate a single-project memory digest")
    memory_sub = memory_cmd.add_subparsers(dest="memory_command", required=True)
    memory_digest_cmd = memory_sub.add_parser("digest", help="Generate the project memory digest")
    add_project_root_arg(memory_digest_cmd)
    memory_digest_cmd.add_argument("--output", help="Optional output path relative to the project root")
    memory_digest_cmd.add_argument("--stdout", action="store_true", help="Print the digest instead of writing it")
    memory_digest_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    portfolio_cmd = sub.add_parser("portfolio", help="Manage and query a portfolio of adopted projects")
    portfolio_sub = portfolio_cmd.add_subparsers(dest="portfolio_command", required=True)

    portfolio_register_cmd = portfolio_sub.add_parser("register", help="Register a project in the portfolio registry")
    add_project_root_arg(portfolio_register_cmd)
    add_portfolio_root_arg(portfolio_register_cmd)
    portfolio_register_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    portfolio_list_cmd = portfolio_sub.add_parser("list", help="List registered portfolio projects")
    add_portfolio_root_arg(portfolio_list_cmd)
    portfolio_list_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    portfolio_status_cmd = portfolio_sub.add_parser("status", help="Summarize portfolio health and activity")
    add_portfolio_root_arg(portfolio_status_cmd)
    portfolio_status_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    portfolio_query_cmd = portfolio_sub.add_parser("query", help="Query across registered portfolio projects")
    add_portfolio_root_arg(portfolio_query_cmd)
    portfolio_query_cmd.add_argument("--q", required=True)
    portfolio_query_cmd.add_argument("--kind")
    portfolio_query_cmd.add_argument("--adapter")
    portfolio_query_cmd.add_argument("--status")
    portfolio_query_cmd.add_argument("--path-prefix")
    portfolio_query_cmd.add_argument("--since")
    portfolio_query_cmd.add_argument("--until")
    portfolio_query_cmd.add_argument("--timeline", action="store_true")
    portfolio_query_cmd.add_argument("--limit", type=int, default=20)
    portfolio_query_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    return parser.parse_args()


def add_project_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", required=True, help="Path to the target project root")


def add_onboarding_metadata_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workflow-pack")
    parser.add_argument("--workflow-stage")
    parser.add_argument("--storage-provider")
    parser.add_argument("--storage-sync-mode")
    parser.add_argument("--storage-workspace-root")
    parser.add_argument("--storage-provider-root-url")
    parser.add_argument("--storage-provider-root-id")
    parser.add_argument("--portfolio-id")
    parser.add_argument("--portfolio-workspace")
    parser.add_argument("--portfolio-owner")


def add_portfolio_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--portfolio-root", help="Optional portfolio registry root; defaults to ~/.sula/portfolio")


def emit_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def json_output_requested(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False))


def project_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "name": config.data["project"]["name"],
        "slug": config.data["project"]["slug"],
        "profile": config.profile,
        "root": str(config.root),
        "workflow_pack": config.workflow_pack,
        "workflow_stage": config.workflow_stage,
        "storage_provider": config.storage_provider,
        "storage_sync_mode": config.storage_sync_mode,
        "portfolio_id": config.portfolio_setting("portfolio_id", "default"),
    }


def sync_plan_payload(actions: list[RenderAction]) -> dict[str, object]:
    return {
        "summary": summarize_status_counts(actions),
        "actions": [
            {
                "path": action.relative_path.as_posix(),
                "status": action.status,
                "impact_level": action.impact_level,
                "impact_scope": action.impact_scope,
                "origin": action.origin,
                "managed": action.overwrite,
            }
            for action in actions
        ],
    }


def clone_namespace(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(**vars(args))


def default_storage_sync_mode(provider: str) -> str:
    return "local-sync" if provider == "google-drive" else "local-only"


def default_provider_root_url(provider: str) -> str:
    return "unrecorded" if provider == "google-drive" else "local-only"


def default_provider_root_id(provider: str) -> str:
    return "unrecorded" if provider == "google-drive" else "n/a"


def infer_workflow_pack(project_root: Path, profile: str, package_data: dict | None, readme_text: str) -> tuple[str, str]:
    if profile == "sula-core":
        return ("operating-system", "profile `sula-core` maps directly to the `operating-system` workflow pack")
    if profile == "react-frontend-erpnext":
        return ("software-delivery", "React + ERPNext projects default to the `software-delivery` workflow pack")

    lowered = (
        f"{project_root.as_posix()} "
        f"{readme_text} "
        f"{json.dumps(package_data, ensure_ascii=True) if package_data else ''}"
    ).lower()
    if any(term in lowered for term in ["shot-list", "shoot", "filming", "footage", "storyboard", "post-production", "video production"]):
        return ("video-production", "project text looks like a media-production workflow")
    if any(term in lowered for term in ["contract", "agreement", "invoice", "quote", "proposal", "staffing", "client", "supplier", "vendor", "service"]):
        return ("client-service", "project text looks like a client-service workflow")
    if looks_like_project_operating_system(readme_text):
        return ("generic-project", "project text looks like a file-oriented operating system instead of a software product")
    if package_data is not None or any((project_root / candidate).exists() for candidate in ["src", "pyproject.toml", "requirements.txt"]):
        return ("software-delivery", "project layout looks like a software delivery workspace")
    return (default_workflow_pack(profile), "no narrower workflow pack was detected safely, so the generic default is suggested")


def infer_storage_provider(project_root: Path) -> tuple[str, str]:
    lowered = project_root.as_posix().lower()
    if "google drive" in lowered or "googledrive" in lowered or ("cloudstorage" in lowered and "google" in lowered):
        return ("google-drive", "project root lives inside a Google Drive local-sync path")
    return ("local-fs", "project root looks like a normal local filesystem workspace")


def infer_portfolio_workspace(workflow_pack: str, storage_provider: str) -> tuple[str, str]:
    if workflow_pack in {"client-service", "video-production"}:
        return ("client-projects", f"`{workflow_pack}` usually belongs to a shared client workspace")
    if storage_provider == "google-drive":
        return ("drive-workspace", "Drive-synced projects often belong to a shared workspace")
    return ("personal", "personal is the safe default workspace when no broader portfolio grouping is known")


def infer_portfolio_owner() -> tuple[str, str]:
    owner = os.environ.get("SULA_OWNER") or os.environ.get("USER") or os.environ.get("USERNAME") or "n/a"
    return (prettify_name(owner) if owner != "n/a" else owner, "owner defaults from the local environment when available")


def suggest_onboarding_answers(
    project_root: Path,
    profile: str,
    args: argparse.Namespace,
    package_data: dict | None,
    readme_text: str,
) -> dict[str, dict[str, object]]:
    workflow_pack, workflow_reason = infer_workflow_pack(project_root, profile, package_data, readme_text)
    storage_provider, storage_reason = infer_storage_provider(project_root)
    resolved_provider = getattr(args, "storage_provider", None) or storage_provider
    portfolio_workspace, workspace_reason = infer_portfolio_workspace(
        getattr(args, "workflow_pack", None) or workflow_pack,
        resolved_provider,
    )
    portfolio_owner, owner_reason = infer_portfolio_owner()
    portfolio_id_default = sanitize_slug(getattr(args, "portfolio_workspace", None) or portfolio_workspace or "default") or "default"
    return {
        "name": {
            "value": getattr(args, "name", None) or detect_project_name(project_root, package_data, readme_text),
            "reason": "project name is suggested from README, package metadata, or the directory name",
        },
        "description": {
            "value": getattr(args, "description", None) or detect_project_description(package_data, readme_text),
            "reason": "description is suggested from package metadata or the first README paragraph",
        },
        "workflow_pack": {"value": getattr(args, "workflow_pack", None) or workflow_pack, "reason": workflow_reason},
        "workflow_stage": {
            "value": getattr(args, "workflow_stage", None) or "active",
            "reason": "active is the safe default stage for a live project",
        },
        "storage_provider": {"value": resolved_provider, "reason": storage_reason},
        "storage_sync_mode": {
            "value": getattr(args, "storage_sync_mode", None) or default_storage_sync_mode(resolved_provider),
            "reason": "sync mode follows the chosen storage provider",
        },
        "storage_workspace_root": {
            "value": getattr(args, "storage_workspace_root", None) or ".",
            "reason": "workspace root defaults to the project root",
        },
        "storage_provider_root_url": {
            "value": getattr(args, "storage_provider_root_url", None) or default_provider_root_url(resolved_provider),
            "reason": "provider root URL stays removable operating metadata and may be filled in later",
        },
        "storage_provider_root_id": {
            "value": getattr(args, "storage_provider_root_id", None) or default_provider_root_id(resolved_provider),
            "reason": "provider root ID stays optional until the external workspace is recorded precisely",
        },
        "portfolio_workspace": {
            "value": getattr(args, "portfolio_workspace", None) or portfolio_workspace,
            "reason": workspace_reason,
        },
        "portfolio_owner": {
            "value": getattr(args, "portfolio_owner", None) or portfolio_owner,
            "reason": owner_reason,
        },
        "portfolio_id": {
            "value": getattr(args, "portfolio_id", None) or portfolio_id_default,
            "reason": "portfolio id defaults from the workspace label so registrations stay grouped",
        },
    }


def onboarding_questions(
    project_root: Path,
    profile: str,
    args: argparse.Namespace,
    package_data: dict | None,
    readme_text: str,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    suggestions = suggest_onboarding_answers(project_root, profile, args, package_data, readme_text)
    provider_value = str(suggestions["storage_provider"]["value"])
    questions: list[dict[str, object]] = []

    def add_question(
        field: str,
        prompt: str,
        *,
        required: bool,
        choices: list[str] | None = None,
    ) -> None:
        if getattr(args, field, None):
            return
        suggestion = suggestions[field]
        questions.append(
            {
                "id": field,
                "field": field,
                "prompt": prompt,
                "default": suggestion["value"],
                "required": required,
                "choices": choices or [],
                "reason": suggestion["reason"],
            }
        )

    add_question("name", "Project display name", required=True)
    add_question("description", "One-line project description", required=True)
    add_question("workflow_pack", "Workflow pack", required=True, choices=WORKFLOW_PACK_CHOICES)
    add_question("storage_provider", "Storage provider", required=True, choices=STORAGE_PROVIDER_CHOICES)
    if provider_value == "google-drive":
        add_question("storage_sync_mode", "Storage sync mode", required=True, choices=["local-sync"])
        add_question("storage_provider_root_url", "Google Drive folder URL", required=False)
        add_question("storage_provider_root_id", "Google Drive folder ID", required=False)
    add_question("portfolio_workspace", "Portfolio workspace label", required=False)
    add_question("portfolio_owner", "Portfolio owner label", required=False)
    add_question("portfolio_id", "Portfolio id", required=False)
    return questions, suggestions


def fill_args_from_answers(
    args: argparse.Namespace,
    answers: dict[str, object],
    suggestions: dict[str, dict[str, object]] | None = None,
) -> argparse.Namespace:
    resolved = clone_namespace(args)
    merged: dict[str, object] = {}
    if suggestions is not None:
        for field, item in suggestions.items():
            merged[field] = item["value"]
    merged.update(answers)
    for field, value in merged.items():
        if getattr(resolved, field, None) in [None, ""]:
            setattr(resolved, field, value)
    return resolved


def prompt_onboarding_question(question: dict[str, object]) -> str:
    choices = [str(item) for item in question.get("choices", []) if str(item)]
    prompt = str(question["prompt"])
    default = str(question.get("default", ""))
    if choices:
        prompt += " [" + "/".join(choices) + "]"
    if default:
        prompt += f" (default: {default})"
    prompt += ": "
    while True:
        try:
            raw = input(prompt)
        except EOFError:
            return default
        answer = raw.strip()
        if not answer:
            return default
        if not choices or answer in choices:
            return answer
        print("Please choose one of the listed values or press Enter to accept the default.")


def prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    try:
        raw = input(prompt + suffix)
    except EOFError:
        return default
    answer = raw.strip().lower()
    if not answer:
        return default
    if answer in {"y", "yes"}:
        return True
    if answer in {"n", "no"}:
        return False
    return default


def onboarding_summary_payload(
    report: AdoptionReport,
    resolved_args: argparse.Namespace,
    *,
    questions: list[dict[str, object]],
    suggestions: dict[str, dict[str, object]],
) -> dict[str, object]:
    assert report.config_data is not None
    manifest = report.config_data
    workflow = manifest["workflow"]
    storage = manifest["storage"]
    portfolio = manifest["portfolio"]
    artifacts_root = str(workflow["artifacts_root"])
    workflow_definition = workflow_pack_definition(str(workflow["pack"]))
    slot_paths = {
        slot: f"{artifacts_root}/{slot}"
        for slot in workflow_definition.get("slots", [])
        if isinstance(slot, str)
    }
    will_manage = [
        f"{len(report.managed_creates) + len(report.managed_updates)} centrally managed operating files",
        f"{len(report.scaffold_creates)} project-owned scaffold starters",
        "kernel state under `.sula/` for status, objects, sources, events, and query indexes",
        f"artifact routing under `{artifacts_root}` through the `{workflow['pack']}` workflow pack",
        f"storage adapter metadata for `{storage['provider']}` without making the provider part of project truth",
    ]
    if str(portfolio.get("workspace", "personal")) != "personal":
        will_manage.append(f"portfolio registration metadata for workspace `{portfolio['workspace']}`")
    next_commands = [
        "python3 scripts/sula.py status --project-root /path/to/project --json",
        "python3 scripts/sula.py query --project-root /path/to/project --q \"contract\" --json",
        "python3 scripts/sula.py artifact create --project-root /path/to/project --kind agreement --title \"...\"",
    ]
    if str(portfolio.get("workspace", "")):
        next_commands.append(
            "python3 scripts/sula.py portfolio register --project-root /path/to/project --portfolio-root /path/to/portfolio"
        )
    return {
        "project_root": str(report.project_root),
        "profile": report.profile,
        "project": manifest["project"],
        "workflow": {
            "pack": workflow["pack"],
            "stage": workflow["stage"],
            "artifacts_root": artifacts_root,
            "slots": workflow_definition.get("slots", []),
            "slot_paths": slot_paths,
            "artifact_routes": workflow_definition.get("artifact_slots", {}),
        },
        "storage": storage,
        "portfolio": portfolio,
        "questions": questions,
        "suggested_answers": {field: item["value"] for field, item in suggestions.items()},
        "what_you_get": will_manage,
        "next_commands": next_commands,
        "approval_required": not getattr(resolved_args, "approve", False),
    }


def print_onboarding_summary(summary: dict[str, object]) -> None:
    project = summary["project"]
    workflow = summary["workflow"]
    storage = summary["storage"]
    portfolio = summary["portfolio"]
    print(f"Sula onboarding summary for {summary['project_root']}")
    print(f"Project: {project['name']} [{summary['profile']}]")
    print(f"Workflow pack: {workflow['pack']} (stage: {workflow['stage']})")
    print(f"Storage provider: {storage['provider']} ({storage['sync_mode']})")
    print(f"Portfolio workspace: {portfolio['workspace']} / owner: {portfolio['owner']}")
    print("What you will get:")
    for item in summary["what_you_get"]:
        print(f"  - {item}")
    print("Artifact slots:")
    for slot, path in summary["workflow"]["slot_paths"].items():
        print(f"  - {slot}: {path}")
    print("Suggested next commands:")
    for item in summary["next_commands"]:
        print(f"  - {item}")


def default_portfolio_root() -> Path:
    return Path.home() / ".sula" / "portfolio"


def resolve_portfolio_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    return default_portfolio_root().resolve()


def portfolio_registry_path(portfolio_root: Path) -> Path:
    return portfolio_root / "registry.json"


def load_portfolio_registry(portfolio_root: Path) -> dict[str, object]:
    path = portfolio_registry_path(portfolio_root)
    if not path.exists():
        return {"version": VERSION, "projects": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid portfolio registry JSON: {path} ({exc})")
    if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
        raise SystemExit(f"Malformed portfolio registry: {path}")
    return data


def write_portfolio_registry(portfolio_root: Path, registry: dict[str, object]) -> None:
    portfolio_root.mkdir(parents=True, exist_ok=True)
    portfolio_registry_path(portfolio_root).write_text(
        json.dumps(registry, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def workflow_pack_definition(pack: str) -> dict[str, object]:
    packs = {
        "generic-project": {
            "slots": ["intake", "contracts", "planning", "delivery", "finance", "archive"],
            "artifact_slots": {
                "agreement": "contracts",
                "contract": "contracts",
                "quote": "finance",
                "invoice": "finance",
                "report": "delivery",
                "schedule": "planning",
                "brief": "planning",
                "deliverable": "delivery",
                "note": "intake",
            },
        },
        "client-service": {
            "slots": ["intake", "contracts", "planning", "delivery", "finance", "archive"],
            "artifact_slots": {
                "agreement": "contracts",
                "contract": "contracts",
                "quote": "finance",
                "invoice": "finance",
                "report": "delivery",
                "schedule": "planning",
                "brief": "planning",
                "deliverable": "delivery",
                "progress": "delivery",
                "note": "intake",
            },
        },
        "video-production": {
            "slots": ["intake", "contracts", "planning", "production", "delivery", "finance", "archive"],
            "artifact_slots": {
                "agreement": "contracts",
                "contract": "contracts",
                "quote": "finance",
                "invoice": "finance",
                "report": "delivery",
                "schedule": "planning",
                "brief": "planning",
                "shot-list": "production",
                "progress": "production",
                "daily-log": "production",
                "deliverable": "delivery",
                "note": "intake",
            },
        },
        "software-delivery": {
            "slots": ["intake", "planning", "implementation", "delivery", "archive"],
            "artifact_slots": {
                "report": "delivery",
                "schedule": "planning",
                "brief": "planning",
                "deliverable": "delivery",
                "note": "intake",
            },
        },
        "operating-system": {
            "slots": ["design", "operations", "releases", "archive"],
            "artifact_slots": {
                "report": "operations",
                "release": "releases",
                "note": "design",
            },
        },
    }
    return packs.get(pack, packs["generic-project"])


def artifact_slot_for_kind(config: ProjectConfig, artifact_kind: str, explicit_slot: str | None = None) -> str:
    if explicit_slot:
        return explicit_slot
    mapping = workflow_pack_definition(config.workflow_pack).get("artifact_slots", {})
    if isinstance(mapping, dict):
        slot = mapping.get(artifact_kind.lower())
        if isinstance(slot, str) and slot:
            return slot
    return "delivery"


def artifact_catalog_path(config: ProjectConfig) -> Path:
    return config.root / ".sula" / "artifacts" / "catalog.json"


def ensure_artifact_catalog(config: ProjectConfig) -> None:
    path = artifact_catalog_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(json.dumps({"version": VERSION, "artifacts": []}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_artifact_catalog(config: ProjectConfig) -> dict[str, object]:
    ensure_artifact_catalog(config)
    path = artifact_catalog_path(config)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid artifact catalog JSON: {path} ({exc})")
    if not isinstance(data, dict) or not isinstance(data.get("artifacts"), list):
        raise SystemExit(f"Malformed artifact catalog: {path}")
    return data


def write_artifact_catalog(config: ProjectConfig, catalog: dict[str, object]) -> None:
    path = artifact_catalog_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve() if hasattr(args, "project_root") else None

    if args.command == "init":
        assert project_root is not None
        config = ensure_manifest(project_root, args)
        apply_actions(collect_render_actions(config, include_scaffold=True))
        write_lockfile(config)
        refresh_kernel_state(config, event_type="init.applied", summary="Initialized Sula manifest and kernel state.")
        if getattr(args, "json", False):
            emit_json({"command": "init", "status": "ok", "project": project_payload(config)})
            return 0
        print(f"Initialized Sula for {config.data['project']['name']} at {project_root}")
        return 0

    if args.command == "adopt":
        assert project_root is not None
        return adopt(project_root, args)

    if args.command == "onboard":
        assert project_root is not None
        return onboard(project_root, args)

    if args.command == "remove":
        assert project_root is not None
        return remove_sula(project_root, args)

    if args.command == "portfolio":
        return handle_portfolio_command(args)

    assert project_root is not None
    config = load_manifest(project_root)
    if args.command == "sync":
        actions = collect_render_actions(config, include_scaffold=False)
        if args.dry_run:
            if getattr(args, "json", False):
                emit_json({"command": "sync", "status": "dry-run", "project": project_payload(config), "plan": sync_plan_payload(actions)})
                return 0
            print_sync_plan(config, actions)
            return 0
        apply_actions(actions)
        write_lockfile(config)
        refresh_kernel_state(config, event_type="sync.applied", summary="Synchronized managed Sula files.")
        if getattr(args, "json", False):
            emit_json({"command": "sync", "status": "ok", "project": project_payload(config), "plan": sync_plan_payload(actions)})
            return 0
        print(f"Synchronized managed files for {config.data['project']['name']}")
        return 0

    if args.command == "doctor":
        return doctor(config, strict=args.strict, json_mode=json_output_requested(args))

    if args.command == "status":
        return project_status(config, args)

    if args.command == "artifact":
        return handle_artifact_command(config, args)

    if args.command == "record":
        if args.record_command == "new":
            return create_record(config, args)
        raise AssertionError("unreachable")

    if args.command == "memory":
        if args.memory_command == "digest":
            return generate_memory_digest(config, args)
        raise AssertionError("unreachable")

    if args.command == "query":
        return query_project_kernel(config, args)

    raise AssertionError("unreachable")


def ensure_manifest(project_root: Path, args: argparse.Namespace) -> ProjectConfig:
    manifest_file = project_root / MANIFEST_PATH
    if not manifest_file.exists():
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest = build_manifest(args)
        manifest_file.write_text(render_manifest(manifest), encoding="utf-8")
    return load_manifest(project_root)


def build_manifest(args: argparse.Namespace) -> dict:
    name = args.name or "Example Project"
    slug = args.slug or "example-project"
    description = args.description or "Project adopted by Sula"
    profile = args.profile
    workflow = manifest_workflow_config(args, profile)
    storage = manifest_storage_config(args)
    portfolio = manifest_portfolio_config(args)
    if profile == "sula-core":
        return {
            "project": {
                "name": name,
                "slug": slug,
                "description": description,
                "profile": profile,
                "default_agent": "Codex",
            },
            "repository": {
                "primary_branch": "main",
                "working_branch_prefix": "codex/",
                "deployment_branch": "main",
            },
            "rules": {
                "highest_rule": "Preserve the split between centrally managed operating-system files and project-owned business truth.",
                "custom_backend_allowed": False,
                "react_router_allowed": False,
            },
            "stack": {
                "frontend": "Python 3 + Markdown + TOML + template-driven repository automation",
                "backend": "GitHub repository state + local filesystem artifacts",
            },
            "paths": {
                "api_layer": "scripts/sula.py",
                "state_layer": "registry/adopted-projects.toml",
                "app_shell": "README.md",
                "status_file": "STATUS.md",
                "change_records_file": "CHANGE-RECORDS.md",
            },
            "commands": {
                "install": "python3 -m unittest discover -s tests -v",
                "dev": "python3 scripts/sula.py --help",
                "build": "python3 -m unittest discover -s tests -v",
                "typecheck": "python3 -m py_compile scripts/sula.py tests/test_sula.py",
            },
            "deploy": {
                "base_path": "/",
                "production_url": "local-only",
                "workflow": ".github/workflows/ci.yml",
            },
            "auth": {
                "session_expiry_codes": ["n/a"],
                "permission_denied_codes": ["n/a"],
            },
            "memory": default_memory_config(),
            "workflow": workflow,
            "storage": storage,
            "portfolio": portfolio,
        }
    if profile == "generic-project":
        return {
            "project": {
                "name": name,
                "slug": slug,
                "description": description,
                "profile": profile,
                "default_agent": "Codex",
            },
            "repository": {
                "primary_branch": "n/a",
                "working_branch_prefix": "codex/",
                "deployment_branch": "n/a",
            },
            "rules": {
                "highest_rule": "Preserve project-owned truth while using Sula as a removable operating kernel.",
                "custom_backend_allowed": True,
                "react_router_allowed": False,
            },
            "stack": {
                "frontend": "Project-defined components",
                "backend": "Project-defined systems",
            },
            "paths": {
                "api_layer": "README.md",
                "state_layer": ".sula/state/current.md",
                "app_shell": "README.md",
                "status_file": "STATUS.md",
                "change_records_file": "CHANGE-RECORDS.md",
            },
            "commands": {
                "install": "n/a",
                "dev": "n/a",
                "build": "n/a",
                "typecheck": "n/a",
            },
            "deploy": {
                "base_path": "/",
                "production_url": "local-only",
                "workflow": "n/a",
            },
            "auth": {
                "session_expiry_codes": ["n/a"],
                "permission_denied_codes": ["n/a"],
            },
            "memory": default_memory_config(),
            "workflow": workflow,
            "storage": storage,
            "portfolio": portfolio,
        }
    return {
        "project": {
            "name": name,
            "slug": slug,
            "description": description,
            "profile": profile,
            "default_agent": "Codex",
        },
        "repository": {
            "primary_branch": "main",
            "working_branch_prefix": "codex/",
            "deployment_branch": "main",
        },
        "rules": {
            "highest_rule": "Frontend-only orchestration over ERPNext-native capabilities.",
            "custom_backend_allowed": False,
            "react_router_allowed": False,
        },
        "stack": {
            "frontend": "React + TypeScript + Vite",
            "backend": "ERPNext / Frappe",
        },
        "paths": {
            "api_layer": "src/api/erpnext.ts",
            "state_layer": "src/store/useStore.ts",
            "app_shell": "src/App.tsx",
            "status_file": "STATUS.md",
            "change_records_file": "CHANGE-RECORDS.md",
        },
        "commands": {
            "install": "npm install",
            "dev": "npm run dev",
            "build": "npm run build",
            "typecheck": "npx tsc --noEmit",
        },
        "deploy": {
            "base_path": "/",
            "production_url": "https://example.com/",
            "workflow": ".github/workflows/deploy.yml",
        },
        "auth": {
            "session_expiry_codes": ["401", "440"],
            "permission_denied_codes": ["403"],
        },
        "memory": default_memory_config(),
        "workflow": workflow,
        "storage": storage,
        "portfolio": portfolio,
    }


def render_manifest(manifest: dict) -> str:
    lines: list[str] = []
    for section_name in [
        "project",
        "repository",
        "rules",
        "stack",
        "paths",
        "commands",
        "deploy",
        "auth",
        "memory",
        "workflow",
        "storage",
        "portfolio",
    ]:
        if section_name not in manifest:
            continue
        lines.append(f"[{section_name}]")
        for key, value in manifest[section_name].items():
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def manifest_workflow_config(args: argparse.Namespace, profile: str) -> dict:
    return {
        "pack": getattr(args, "workflow_pack", None) or default_workflow_pack(profile),
        "stage": getattr(args, "workflow_stage", None) or "active",
        "artifacts_root": "artifacts",
    }


def manifest_storage_config(args: argparse.Namespace) -> dict:
    provider = getattr(args, "storage_provider", None) or "local-fs"
    return {
        "provider": provider,
        "sync_mode": getattr(args, "storage_sync_mode", None) or default_storage_sync_mode(provider),
        "workspace_root": getattr(args, "storage_workspace_root", None) or ".",
        "provider_root_url": getattr(args, "storage_provider_root_url", None) or default_provider_root_url(provider),
        "provider_root_id": getattr(args, "storage_provider_root_id", None) or default_provider_root_id(provider),
    }


def manifest_portfolio_config(args: argparse.Namespace) -> dict:
    return {
        "portfolio_id": getattr(args, "portfolio_id", None) or "default",
        "workspace": getattr(args, "portfolio_workspace", None) or "personal",
        "owner": getattr(args, "portfolio_owner", None) or "n/a",
    }


def format_toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        inner = ", ".join(format_toml_value(item) for item in value)
        return f"[{inner}]"
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def load_manifest(project_root: Path) -> ProjectConfig:
    manifest_file = project_root / MANIFEST_PATH
    if not manifest_file.exists():
        raise SystemExit(f"Missing manifest: {manifest_file}")
    data = parse_simple_toml(manifest_file.read_text(encoding="utf-8"))
    validate_manifest(data)
    profile_dir = profile_template_dir(data["project"]["profile"])
    if not profile_dir.exists():
        raise SystemExit(f"Unknown profile: {data['project']['profile']}")
    return ProjectConfig(root=project_root, data=data)


def parse_simple_toml(text: str) -> dict:
    data: dict[str, dict] = {}
    current: dict | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current = data.setdefault(section, {})
            continue
        if current is None or "=" not in line:
            raise SystemExit(f"Unsupported manifest line: {raw_line}")
        key, value = line.split("=", 1)
        current[key.strip()] = parse_toml_value(value.strip())
    return data


def parse_toml_value(raw: str):
    if raw == "true":
        return True
    if raw == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith('"') and raw.endswith('"'):
        return parse_string(raw)
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        items = split_list_items(inner)
        return [parse_toml_value(item.strip()) for item in items]
    raise SystemExit(f"Unsupported TOML value: {raw}")


def parse_string(raw: str) -> str:
    body = raw[1:-1]
    body = body.replace('\\"', '"')
    body = body.replace('\\\\', '\\')
    return body


def split_list_items(inner: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    in_string = False
    escape = False
    for char in inner:
        if escape:
            current.append(char)
            escape = False
            continue
        if char == "\\":
            current.append(char)
            escape = True
            continue
        if char == '"':
            current.append(char)
            in_string = not in_string
            continue
        if char == "," and not in_string:
            items.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current))
    return items


def validate_manifest(data: dict) -> None:
    missing: list[str] = []
    unexpected: list[str] = []
    invalid: list[str] = []

    for section in MANIFEST_SPEC:
        if section not in data:
            missing.append(section)
    known_sections = set(MANIFEST_SPEC) | set(OPTIONAL_MANIFEST_SPEC)
    for section in data:
        if section not in known_sections:
            unexpected.append(section)

    for section, keys in MANIFEST_SPEC.items():
        section_data = data.get(section)
        if section_data is None:
            continue
        if not isinstance(section_data, dict):
            invalid.append(f"{section} must be a section table")
            continue
        for key, expected_kind in keys.items():
            if key not in section_data:
                missing.append(f"{section}.{key}")
                continue
            validate_field(section, key, section_data[key], expected_kind, invalid)
        for key in section_data:
            if key not in keys:
                unexpected.append(f"{section}.{key}")

    for section, keys in OPTIONAL_MANIFEST_SPEC.items():
        section_data = data.get(section)
        if section_data is None:
            continue
        if not isinstance(section_data, dict):
            invalid.append(f"{section} must be a section table")
            continue
        for key, expected_kind in keys.items():
            if key not in section_data:
                continue
            validate_field(section, key, section_data[key], expected_kind, invalid)
        for key in section_data:
            if key not in keys:
                unexpected.append(f"{section}.{key}")

    issues: list[str] = []
    if missing:
        issues.append("missing required fields: " + ", ".join(missing))
    if unexpected:
        issues.append("unexpected fields: " + ", ".join(unexpected))
    if invalid:
        issues.append("invalid values: " + "; ".join(invalid))
    if issues:
        raise SystemExit("Manifest validation failed: " + " | ".join(issues))


def validate_field(section: str, key: str, value, expected_kind: str, invalid: list[str]) -> None:
    label = f"{section}.{key}"
    if expected_kind == "string":
        if not isinstance(value, str) or not value.strip():
            invalid.append(f"{label} must be a non-empty string")
        return
    if expected_kind == "bool":
        if not isinstance(value, bool):
            invalid.append(f"{label} must be a boolean")
        return
    if expected_kind == "string_list":
        if not isinstance(value, list) or not value:
            invalid.append(f"{label} must be a non-empty array of strings")
            return
        for item in value:
            if not isinstance(item, str) or not item.strip():
                invalid.append(f"{label} must contain only non-empty strings")
                return
        return
    if expected_kind == "int":
        if not isinstance(value, int):
            invalid.append(f"{label} must be an integer")
            return
        if value < 1:
            invalid.append(f"{label} must be >= 1")
        return
    invalid.append(f"{label} uses unsupported schema kind: {expected_kind}")


def render_action_payload(action: RenderAction) -> dict[str, object]:
    return {
        "path": action.relative_path.as_posix(),
        "status": action.status,
        "managed": action.overwrite,
        "origin": action.origin,
        "impact_level": action.impact_level,
        "impact_scope": action.impact_scope,
    }


def adoption_report_payload(report: AdoptionReport) -> dict[str, object]:
    return {
        "project_root": str(report.project_root),
        "profile": report.profile,
        "manifest": report.config_data,
        "project": report.config_data.get("project") if report.config_data else None,
        "repository": report.config_data.get("repository") if report.config_data else None,
        "warnings": report.warnings,
        "blockers": report.blockers,
        "detection_notes": report.detection_notes,
        "managed_creates": [render_action_payload(action) for action in report.managed_creates],
        "managed_updates": [render_action_payload(action) for action in report.managed_updates],
        "scaffold_creates": [render_action_payload(action) for action in report.scaffold_creates],
        "scaffold_preserved": [render_action_payload(action) for action in report.scaffold_preserved],
    }


def removal_report_payload(report: RemovalReport) -> dict[str, object]:
    return {
        "project_root": str(report.project_root),
        "project": project_payload(report.config) if report.config else None,
        "warnings": report.warnings,
        "blockers": report.blockers,
        "kernel_remove_paths": [path.as_posix() for path in report.kernel_remove_paths],
        "managed_remove_paths": [path.as_posix() for path in report.managed_remove_paths],
        "scaffold_preserve_paths": [path.as_posix() for path in report.scaffold_preserve_paths],
    }


def doctor_payload(
    config: ProjectConfig,
    *,
    missing_files: list[str],
    drifted_files: list[str],
    placeholder_files: list[str],
    memory_errors: list[str],
    lock_issues: list[str],
    kernel_errors: list[str],
    warnings: list[str],
    passed: bool,
) -> dict[str, object]:
    return {
        "project": project_payload(config),
        "passed": passed,
        "missing_files": missing_files,
        "drifted_files": drifted_files,
        "placeholder_files": placeholder_files,
        "memory_errors": memory_errors,
        "lock_issues": lock_issues,
        "kernel_errors": kernel_errors,
        "warnings": warnings,
    }


def existing_consumer_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "project": project_payload(config),
        "next_commands": [
            "python3 scripts/sula.py doctor --project-root /path/to/project --strict",
            "python3 scripts/sula.py sync --project-root /path/to/project --dry-run",
            "python3 scripts/sula.py status --project-root /path/to/project --json",
        ],
    }


def onboard(project_root: Path, args: argparse.Namespace) -> int:
    if (project_root / MANIFEST_PATH).exists():
        config = load_manifest(project_root)
        payload = {"command": "onboard", "status": "existing-consumer", **existing_consumer_payload(config)}
        if json_output_requested(args):
            emit_json(payload)
            return 0
        print(f"{config.data['project']['name']} is already under Sula management.")
        print("Use one of these commands instead:")
        for command in payload["next_commands"]:
            print(f"  - {command}")
        return 0

    package_data = read_package_json(project_root)
    readme_text = read_text_if_exists(project_root / "README.md")
    detection_notes: list[str] = []
    profile = detect_profile(project_root, args.profile, package_data, readme_text, detection_notes)
    questions, suggestions = onboarding_questions(project_root, profile or "generic-project", args, package_data, readme_text)

    if json_output_requested(args) and questions and not getattr(args, "accept_suggested", False):
        preview_args = fill_args_from_answers(args, {}, suggestions)
        report = inspect_adoption(project_root, preview_args)
        summary = onboarding_summary_payload(report, preview_args, questions=questions, suggestions=suggestions)
        emit_json(
            {
                "command": "onboard",
                "status": "questions",
                "questions": questions,
                "suggested_answers": summary["suggested_answers"],
                "summary": summary,
                "report": adoption_report_payload(report),
            }
        )
        return 0

    resolved_args = fill_args_from_answers(args, {}, suggestions)
    if not json_output_requested(args) and questions and not getattr(args, "accept_suggested", False):
        print("Sula onboarding questions:")
        interactive_answers: dict[str, object] = {}
        for question in questions:
            if question["field"] in {"storage_sync_mode", "storage_provider_root_url", "storage_provider_root_id"}:
                current_provider = str(interactive_answers.get("storage_provider") or getattr(args, "storage_provider", None) or suggestions["storage_provider"]["value"])
                if current_provider != "google-drive":
                    continue
            interactive_answers[question["field"]] = prompt_onboarding_question(question)
        refreshed_base = fill_args_from_answers(args, interactive_answers, None)
        refreshed_suggestions = suggest_onboarding_answers(
            project_root,
            profile or "generic-project",
            refreshed_base,
            package_data,
            readme_text,
        )
        resolved_args = fill_args_from_answers(refreshed_base, {}, refreshed_suggestions)
        suggestions = refreshed_suggestions
        questions, _ = onboarding_questions(project_root, profile or "generic-project", resolved_args, package_data, readme_text)

    report = inspect_adoption(project_root, resolved_args)
    summary = onboarding_summary_payload(report, resolved_args, questions=questions, suggestions=suggestions)

    if json_output_requested(args):
        if not getattr(args, "approve", False):
            emit_json(
                {
                    "command": "onboard",
                    "status": "ready",
                    "summary": summary,
                    "report": adoption_report_payload(report),
                }
            )
            return 0
        if report.blockers:
            emit_json(
                {
                    "command": "onboard",
                    "status": "blocked",
                    "summary": summary,
                    "report": adoption_report_payload(report),
                }
            )
            return 1
        return apply_adoption(
            report,
            json_mode=True,
            command_name="onboard",
            extra_payload={"summary": summary},
        )

    print_onboarding_summary(summary)
    if report.blockers:
        print_adoption_report(report)
        print("Sula onboarding cannot continue until the blocking issues are resolved.")
        return 1
    if not getattr(args, "approve", False):
        if prompt_yes_no("Apply Sula now with these answers?", default=False):
            return apply_adoption(report, json_mode=False)
        print("Sula was not applied. Re-run `python3 scripts/sula.py onboard --project-root /path/to/project --approve` to apply after review.")
        return 0
    return apply_adoption(report, json_mode=False)


def adopt(project_root: Path, args: argparse.Namespace) -> int:
    report = inspect_adoption(project_root, args)
    if json_output_requested(args):
        if not args.approve:
            emit_json({"command": "adopt", "status": "report", "report": adoption_report_payload(report)})
            return 0
        if report.blockers:
            emit_json({"command": "adopt", "status": "blocked", "report": adoption_report_payload(report)})
            return 1
        exit_code = apply_adoption(report, json_mode=True)
        return exit_code
    print_adoption_report(report)
    if not args.approve:
        return 0
    if report.blockers:
        print("Adoption was not applied because blocking issues remain.")
        return 1
    return apply_adoption(report, json_mode=False)


def inspect_adoption(project_root: Path, args: argparse.Namespace) -> AdoptionReport:
    blockers: list[str] = []
    warnings: list[str] = []
    detection_notes: list[str] = []

    if not project_root.exists():
        raise SystemExit(f"Project root does not exist: {project_root}")
    if (project_root / MANIFEST_PATH).exists():
        blockers.append("repository already has `.sula/project.toml`; use `sync` or edit the existing manifest instead")

    package_data = read_package_json(project_root)
    readme_text = read_text_if_exists(project_root / "README.md")
    profile = detect_profile(project_root, args.profile, package_data, readme_text, detection_notes)

    config_data = None
    actions: list[RenderAction] = []
    managed_creates: list[RenderAction] = []
    managed_updates: list[RenderAction] = []
    scaffold_creates: list[RenderAction] = []
    scaffold_preserved: list[RenderAction] = []

    if profile is not None:
        config_data = build_adoption_manifest(project_root, profile, args, package_data, readme_text, detection_notes)
        config = ProjectConfig(root=project_root, data=config_data)
        actions = collect_render_actions(config, include_scaffold=True)
        managed_creates = [action for action in actions if action.overwrite and action.status == "create"]
        managed_updates = [action for action in actions if action.overwrite and action.status == "update"]
        scaffold_creates = [action for action in actions if not action.overwrite and action.status == "create"]
        scaffold_preserved = [action for action in actions if not action.overwrite and action.status == "skip"]
        if managed_updates:
            warnings.append(
                "managed files already exist and will be overwritten after approval: "
                + ", ".join(action.relative_path.as_posix() for action in managed_updates)
            )
        if scaffold_preserved:
            warnings.append(
                "project-owned scaffold files already exist and will be preserved: "
                + ", ".join(action.relative_path.as_posix() for action in scaffold_preserved)
            )

    return AdoptionReport(
        project_root=project_root,
        profile=profile,
        config_data=config_data,
        actions=actions,
        blockers=blockers,
        warnings=warnings,
        detection_notes=detection_notes,
        managed_creates=managed_creates,
        managed_updates=managed_updates,
        scaffold_creates=scaffold_creates,
        scaffold_preserved=scaffold_preserved,
    )


def print_adoption_report(report: AdoptionReport) -> None:
    print(f"Sula adoption report for {report.project_root}")
    if report.profile is not None:
        print(f"Recommended profile: {report.profile}")
    if report.config_data is not None:
        project = report.config_data["project"]
        repo = report.config_data["repository"]
        print(f"Detected name: {project['name']}")
        print(f"Detected slug: {project['slug']}")
        print(f"Primary branch: {repo['primary_branch']}")
        print(f"Deployment branch: {repo['deployment_branch']}")
    if report.detection_notes:
        print("Detection notes:")
        for item in report.detection_notes:
            print(f"  - {item}")
    if report.blockers:
        print("Blocking issues:")
        for item in report.blockers:
            print(f"  - {item}")
    if report.warnings:
        print("Warnings:")
        for item in report.warnings:
            print(f"  - {item}")

    print("Planned changes after approval:")
    print(f"  - managed create: {len(report.managed_creates)}")
    print(f"  - managed update: {len(report.managed_updates)}")
    print(f"  - scaffold create: {len(report.scaffold_creates)}")
    print(f"  - scaffold preserve: {len(report.scaffold_preserved)}")
    for action in report.managed_updates[:8]:
        print(f"    overwrite: {action.relative_path.as_posix()} [{action.impact_level}]")
    for action in report.scaffold_preserved[:8]:
        print(f"    preserve: {action.relative_path.as_posix()}")
    print("Approval flow:")
    print("  1. Review this report.")
    print("  2. Re-run the same command with `--approve` to apply the adoption.")


def build_adoption_manifest(
    project_root: Path,
    profile: str,
    args: argparse.Namespace,
    package_data: dict | None,
    readme_text: str,
    detection_notes: list[str],
) -> dict:
    if profile == "sula-core":
        return build_sula_core_manifest(project_root, args, detection_notes)
    if profile == "react-frontend-erpnext":
        return build_react_erpnext_manifest(project_root, args, package_data, readme_text, detection_notes)
    if profile == "generic-project":
        return build_generic_project_manifest(project_root, args, package_data, readme_text, detection_notes)
    raise SystemExit(f"Unsupported profile for adoption: {profile}")


def build_generic_project_manifest(
    project_root: Path,
    args: argparse.Namespace,
    package_data: dict | None,
    readme_text: str,
    detection_notes: list[str],
) -> dict:
    name = args.name or detect_project_name(project_root, package_data, readme_text)
    slug = args.slug or sanitize_slug(package_slug_or_name(project_root, package_data, name))
    description = args.description or detect_project_description(package_data, readme_text)
    git_present = is_git_repository(project_root)
    primary_branch = detect_primary_branch(project_root) if git_present else "n/a"
    deployment_branch = primary_branch if git_present else "n/a"
    app_shell = detect_first_existing_path(
        project_root,
        ["README.md", "docs/README.md", "start.sh", "main.py", "app.py", "src/App.tsx", "src/main.tsx", "index.html"],
    ) or "README.md"
    api_layer = detect_first_existing_path(
        project_root,
        ["start.sh", "main.py", "app.py", "src/main.tsx", "src/App.tsx", "README.md"],
    ) or app_shell
    install_command, dev_command, build_command, typecheck_command = detect_generic_commands(project_root, package_data)
    production_url = detect_production_url(package_data) or "local-only"
    workflow = detect_workflow_path(project_root) or "n/a"
    detection_notes.append("defaulted to `generic-project` because no narrower profile matched safely")
    if git_present:
        detection_notes.append("Git metadata detected; `repo` can act as an optional kernel adapter")
    else:
        detection_notes.append("Git metadata not detected; adoption will proceed without the optional `repo` adapter")
    return {
        "project": {
            "name": name,
            "slug": slug,
            "description": description,
            "profile": "generic-project",
            "default_agent": "Codex",
        },
        "repository": {
            "primary_branch": primary_branch,
            "working_branch_prefix": "codex/",
            "deployment_branch": deployment_branch,
        },
        "rules": {
            "highest_rule": detect_existing_highest_rule(project_root)
            or "Preserve project-owned truth while using Sula as a removable operating kernel.",
            "custom_backend_allowed": True,
            "react_router_allowed": detect_generic_react_router_allowed(package_data, readme_text),
        },
        "stack": {
            "frontend": detect_generic_frontend_stack(project_root, package_data, readme_text),
            "backend": detect_generic_backend_stack(project_root, package_data, readme_text),
        },
        "paths": {
            "api_layer": api_layer,
            "state_layer": ".sula/state/current.md",
            "app_shell": app_shell,
            "status_file": "STATUS.md",
            "change_records_file": "CHANGE-RECORDS.md",
        },
        "commands": {
            "install": install_command,
            "dev": dev_command,
            "build": build_command,
            "typecheck": typecheck_command,
        },
        "deploy": {
            "base_path": detect_base_path(production_url) if production_url.startswith("http") else "/",
            "production_url": production_url,
            "workflow": workflow,
        },
        "auth": {
            "session_expiry_codes": ["n/a"],
            "permission_denied_codes": ["n/a"],
        },
        "memory": default_memory_config(),
        "workflow": manifest_workflow_config(args, "generic-project"),
        "storage": manifest_storage_config(args),
        "portfolio": manifest_portfolio_config(args),
    }


def build_sula_core_manifest(project_root: Path, args: argparse.Namespace, detection_notes: list[str]) -> dict:
    name = args.name or extract_readme_title(read_text_if_exists(project_root / "README.md")) or project_root.name
    slug = args.slug or sanitize_slug(name)
    description = args.description or first_readme_paragraph(read_text_if_exists(project_root / "README.md")) or (
        "Reusable project operating system"
    )
    primary_branch = detect_primary_branch(project_root)
    detection_notes.append("detected `sula-core` from repository layout and local Sula modules")
    return {
        "project": {
            "name": name,
            "slug": slug,
            "description": description,
            "profile": "sula-core",
            "default_agent": "Codex",
        },
        "repository": {
            "primary_branch": primary_branch,
            "working_branch_prefix": "codex/",
            "deployment_branch": primary_branch,
        },
        "rules": {
            "highest_rule": "Preserve the split between centrally managed operating-system files and project-owned business truth.",
            "custom_backend_allowed": False,
            "react_router_allowed": False,
        },
        "stack": {
            "frontend": "Python 3 + Markdown + TOML + template-driven repository automation",
            "backend": "GitHub repository state + local filesystem artifacts",
        },
        "paths": {
            "api_layer": "scripts/sula.py",
            "state_layer": "registry/adopted-projects.toml",
            "app_shell": "README.md",
            "status_file": "STATUS.md",
            "change_records_file": "CHANGE-RECORDS.md",
        },
        "commands": {
            "install": "python3 -m unittest discover -s tests -v",
            "dev": "python3 scripts/sula.py --help",
            "build": "python3 -m unittest discover -s tests -v",
            "typecheck": "python3 -m py_compile scripts/sula.py tests/test_sula.py",
        },
        "deploy": {
            "base_path": "/",
            "production_url": detect_repository_url(project_root) or "https://github.com/example/example",
            "workflow": detect_workflow_path(project_root) or ".github/workflows/ci.yml",
        },
        "auth": {
            "session_expiry_codes": ["n/a"],
            "permission_denied_codes": ["n/a"],
        },
        "memory": default_memory_config(),
        "workflow": manifest_workflow_config(args, "sula-core"),
        "storage": manifest_storage_config(args),
        "portfolio": manifest_portfolio_config(args),
    }


def build_react_erpnext_manifest(
    project_root: Path,
    args: argparse.Namespace,
    package_data: dict | None,
    readme_text: str,
    detection_notes: list[str],
) -> dict:
    name = args.name or detect_project_name(project_root, package_data, readme_text)
    slug = args.slug or sanitize_slug(package_slug_or_name(project_root, package_data, name))
    description = args.description or detect_project_description(package_data, readme_text)
    primary_branch = detect_primary_branch(project_root)
    deployment_branch = primary_branch
    api_layer = detect_first_existing_path(project_root, ["src/api/erpnext.ts", "src/api/frappe.ts", "src/api/client.ts"]) or (
        "src/api/erpnext.ts"
    )
    state_layer = detect_first_existing_path(project_root, ["src/store/useStore.ts", "src/store/index.ts", "src/state/index.ts", "src/store.ts"]) or (
        "src/store/useStore.ts"
    )
    app_shell = detect_first_existing_path(project_root, ["src/App.tsx", "src/main.tsx"]) or "src/App.tsx"
    package_manager = detect_package_manager(project_root)
    dev_command, build_command, typecheck_command = detect_node_commands(package_data, package_manager)
    workflow = detect_workflow_path(project_root) or ".github/workflows/deploy.yml"
    production_url = detect_production_url(package_data) or "https://example.com/"
    base_path = detect_base_path(production_url)
    detection_notes.append("detected `react-frontend-erpnext` from repository paths and ERPNext/Frappe markers")
    return {
        "project": {
            "name": name,
            "slug": slug,
            "description": description,
            "profile": "react-frontend-erpnext",
            "default_agent": "Codex",
        },
        "repository": {
            "primary_branch": primary_branch,
            "working_branch_prefix": "codex/",
            "deployment_branch": deployment_branch,
        },
        "rules": {
            "highest_rule": detect_existing_highest_rule(project_root)
            or "Frontend-only orchestration over ERPNext-native capabilities.",
            "custom_backend_allowed": False,
            "react_router_allowed": detect_react_router_allowed(package_data),
        },
        "stack": {
            "frontend": detect_frontend_stack(package_data),
            "backend": detect_backend_stack(readme_text),
        },
        "paths": {
            "api_layer": api_layer,
            "state_layer": state_layer,
            "app_shell": app_shell,
            "status_file": "STATUS.md",
            "change_records_file": "CHANGE-RECORDS.md",
        },
        "commands": {
            "install": install_command_for_package_manager(package_manager),
            "dev": dev_command,
            "build": build_command,
            "typecheck": typecheck_command,
        },
        "deploy": {
            "base_path": base_path,
            "production_url": production_url,
            "workflow": workflow,
        },
        "auth": {
            "session_expiry_codes": ["401", "440"],
            "permission_denied_codes": ["403"],
        },
        "memory": default_memory_config(),
        "workflow": manifest_workflow_config(args, "react-frontend-erpnext"),
        "storage": manifest_storage_config(args),
        "portfolio": manifest_portfolio_config(args),
    }


def default_memory_config() -> dict:
    return {
        "change_record_directory": "docs/change-records",
        "release_record_directory": "docs/releases",
        "incident_record_directory": "docs/incidents",
        "digest_file": ".sula/memory-digest.md",
        "status_max_age_days": 30,
    }


def default_workflow_pack(profile: str) -> str:
    defaults = {
        "generic-project": "generic-project",
        "react-frontend-erpnext": "software-delivery",
        "sula-core": "operating-system",
    }
    return defaults.get(profile, "generic-project")


def read_package_json(project_root: Path) -> dict | None:
    package_path = project_root / "package.json"
    if not package_path.exists():
        return None
    try:
        return json.loads(package_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def detect_profile(
    project_root: Path,
    explicit_profile: str | None,
    package_data: dict | None,
    readme_text: str,
    detection_notes: list[str],
) -> str | None:
    if explicit_profile:
        detection_notes.append(f"profile forced by caller: {explicit_profile}")
        return explicit_profile
    if (project_root / "scripts" / "sula.py").exists() and (project_root / "templates").exists():
        return "sula-core"

    haystack = f"{readme_text}\n{json.dumps(package_data) if package_data else ''}".lower()
    has_react_shape = package_data is not None or (project_root / "src" / "App.tsx").exists() or (project_root / "src" / "main.tsx").exists()
    has_erpnext_marker = any(
        (project_root / candidate).exists()
        for candidate in ["src/api/erpnext.ts", "src/api/frappe.ts"]
    ) or any(term in haystack for term in ["erpnext", "frappe"])
    if has_react_shape and has_erpnext_marker:
        return "react-frontend-erpnext"
    return "generic-project"


def detect_project_name(project_root: Path, package_data: dict | None, readme_text: str) -> str:
    if package_data is not None:
        for key in ["displayName", "productName", "name"]:
            value = package_data.get(key)
            if isinstance(value, str) and value.strip():
                return prettify_name(value)
    title = extract_readme_title(readme_text)
    if title:
        return title
    return prettify_name(project_root.name)


def package_slug_or_name(project_root: Path, package_data: dict | None, fallback_name: str) -> str:
    if package_data is not None:
        value = package_data.get("name")
        if isinstance(value, str) and value.strip():
            return value
    return fallback_name or project_root.name


def detect_project_description(package_data: dict | None, readme_text: str) -> str:
    if package_data is not None:
        value = package_data.get("description")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return first_readme_paragraph(readme_text) or "Project adopted by Sula"


def extract_readme_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def first_readme_paragraph(text: str) -> str:
    lines: list[str] = []
    started = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if started and lines:
                break
            continue
        if line.startswith("#"):
            continue
        started = True
        lines.append(line)
    return " ".join(lines).strip()


def prettify_name(value: str) -> str:
    cleaned = value.replace("_", " ").replace("-", " ").strip()
    return re.sub(r"\s+", " ", cleaned).title() if cleaned else value


def detect_primary_branch(project_root: Path) -> str:
    result = run_git(project_root, ["symbolic-ref", "refs/remotes/origin/HEAD"])
    if result is not None and result.returncode == 0:
        ref = result.stdout.strip()
        if ref:
            return ref.rsplit("/", 1)[-1]
    for candidate in ["main", "master"]:
        if (project_root / ".git" / "refs" / "heads" / candidate).exists():
            return candidate
    current_branch = detect_git_branch(project_root)
    return current_branch if current_branch != "unknown" else "main"


def is_git_repository(project_root: Path) -> bool:
    result = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return result is not None and result.returncode == 0 and result.stdout.strip() == "true"


def run_git(project_root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None


def detect_first_existing_path(project_root: Path, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if (project_root / candidate).exists():
            return candidate
    return None


def detect_package_manager(project_root: Path) -> str:
    if (project_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def install_command_for_package_manager(package_manager: str) -> str:
    if package_manager == "pnpm":
        return "pnpm install"
    if package_manager == "yarn":
        return "yarn install"
    return "npm install"


def detect_node_commands(package_data: dict | None, package_manager: str) -> tuple[str, str, str]:
    scripts = package_data.get("scripts", {}) if isinstance(package_data, dict) else {}
    if package_manager == "pnpm":
        runner_prefix = "pnpm"
    elif package_manager == "yarn":
        runner_prefix = "yarn"
    else:
        runner_prefix = "npm run"

    def command_for(script_name: str, fallback: str) -> str:
        if script_name in scripts:
            if package_manager == "yarn":
                return f"yarn {script_name}"
            if package_manager == "pnpm":
                return f"pnpm {script_name}"
            return f"npm run {script_name}"
        return fallback

    dev = command_for("dev", f"{runner_prefix} dev")
    build = command_for("build", f"{runner_prefix} build")
    if "typecheck" in scripts:
        typecheck = command_for("typecheck", f"{runner_prefix} typecheck")
    else:
        typecheck = "npx tsc --noEmit"
    return dev, build, typecheck


def detect_generic_commands(project_root: Path, package_data: dict | None) -> tuple[str, str, str, str]:
    if package_data is not None:
        package_manager = detect_package_manager(project_root)
        install = install_command_for_package_manager(package_manager)
        dev, build, typecheck = detect_node_commands(package_data, package_manager)
        return install, dev, build, typecheck
    if (project_root / "requirements.txt").exists():
        return ("python3 -m pip install -r requirements.txt", "n/a", "n/a", "python3 -m py_compile .")
    if (project_root / "pyproject.toml").exists():
        return ("python3 -m pip install -e .", "n/a", "n/a", "n/a")
    return ("n/a", "n/a", "n/a", "n/a")


def detect_workflow_path(project_root: Path) -> str | None:
    workflow_root = project_root / ".github" / "workflows"
    if not workflow_root.exists():
        return None
    deploy_like = sorted(workflow_root.glob("deploy*.yml")) + sorted(workflow_root.glob("deploy*.yaml"))
    if deploy_like:
        return deploy_like[0].relative_to(project_root).as_posix()
    any_workflow = sorted(workflow_root.glob("*.yml")) + sorted(workflow_root.glob("*.yaml"))
    if any_workflow:
        return any_workflow[0].relative_to(project_root).as_posix()
    return None


def detect_production_url(package_data: dict | None) -> str | None:
    if not isinstance(package_data, dict):
        return None
    homepage = package_data.get("homepage")
    if isinstance(homepage, str) and homepage.startswith("http"):
        return homepage
    return None


def detect_base_path(production_url: str) -> str:
    match = re.match(r"https?://[^/]+(/.*)$", production_url)
    if match is None:
        return "/"
    path = match.group(1)
    return path if path.endswith("/") else path + "/"


def detect_existing_highest_rule(project_root: Path) -> str | None:
    agents_path = project_root / "AGENTS.md"
    if not agents_path.exists():
        return None
    text = agents_path.read_text(encoding="utf-8")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("- `") and line.endswith("`"):
            return line.strip("- ").strip("`")
    return None


def detect_react_router_allowed(package_data: dict | None) -> bool:
    if not isinstance(package_data, dict):
        return False
    all_deps = {}
    for key in ["dependencies", "devDependencies"]:
        value = package_data.get(key, {})
        if isinstance(value, dict):
            all_deps.update(value)
    return "react-router" in all_deps or "react-router-dom" in all_deps


def looks_like_project_operating_system(readme_text: str) -> bool:
    lowered = readme_text.lower()
    keywords = [
        "project operating system",
        "operating system",
        "workspace",
        "files",
        "documents",
        "records",
        "portfolio",
        "artifacts",
        "knowledge",
        "memory",
        "google drive",
        "drive-synced",
        "agent",
        "llm",
        "system for managing",
        "文件",
        "文档",
        "记录",
        "工作区",
        "归档",
        "系统",
        "接入",
    ]
    score = sum(1 for term in keywords if term in lowered)
    return score >= 2


def detect_generic_react_router_allowed(package_data: dict | None, readme_text: str) -> bool:
    if looks_like_project_operating_system(readme_text):
        return False
    return detect_react_router_allowed(package_data)


def detect_frontend_stack(package_data: dict | None) -> str:
    if not isinstance(package_data, dict):
        return "React + TypeScript + Vite"
    deps = {}
    for key in ["dependencies", "devDependencies"]:
        value = package_data.get(key, {})
        if isinstance(value, dict):
            deps.update(value)
    parts: list[str] = []
    if "react" in deps:
        parts.append("React")
    if "typescript" in deps:
        parts.append("TypeScript")
    if "vite" in deps:
        parts.append("Vite")
    if "tailwindcss" in deps:
        parts.append("Tailwind CSS")
    if "zustand" in deps:
        parts.append("Zustand")
    return " + ".join(parts) if parts else "React + TypeScript + Vite"


def detect_backend_stack(readme_text: str) -> str:
    lowered = readme_text.lower()
    if "erpnext" in lowered or "frappe" in lowered:
        return "ERPNext / Frappe"
    return "ERPNext / Frappe"


def detect_generic_frontend_stack(project_root: Path, package_data: dict | None, readme_text: str) -> str:
    if looks_like_project_operating_system(readme_text):
        if package_data is not None or any((project_root / candidate).exists() for candidate in ["index.html", "src", "public"]):
            return "Project operating interface over files and records"
        return "Document and file operating interface"
    if package_data is not None:
        return "Project-defined application interface"
    if any((project_root / candidate).exists() for candidate in ["index.html", "src", "public"]):
        return "Project-defined application or document interface"
    return "Project-defined components"


def detect_generic_backend_stack(project_root: Path, package_data: dict | None, readme_text: str) -> str:
    lowered = readme_text.lower()
    if looks_like_project_operating_system(readme_text):
        return "Project files, documents, and external systems"
    if package_data is not None and ("erpnext" in lowered or "frappe" in lowered):
        return "ERPNext / Frappe"
    if (project_root / "requirements.txt").exists() or (project_root / "pyproject.toml").exists():
        return "Python-driven project systems"
    if "contract" in lowered or "agreement" in lowered:
        return "Project documents and external systems"
    return "Project-defined systems"


def detect_repository_url(project_root: Path) -> str | None:
    result = run_git(project_root, ["remote", "get-url", "origin"])
    if result is None or result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def apply_adoption(
    report: AdoptionReport,
    *,
    json_mode: bool = False,
    command_name: str = "adopt",
    extra_payload: dict[str, object] | None = None,
) -> int:
    assert report.config_data is not None
    config = ProjectConfig(root=report.project_root, data=report.config_data)
    manifest_path = config.root / MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(render_manifest(report.config_data), encoding="utf-8")
    apply_actions(report.actions)
    write_lockfile(config)
    finalize_adoption_traceability(config)
    generate_memory_digest(config, argparse.Namespace(output=None, stdout=False, json=False), emit_output=not json_mode)
    refresh_kernel_state(config, event_type="adopt.approved", summary="Applied initial Sula adoption.")
    if not json_mode:
        print("Post-adoption validation:")
    doctor_exit = doctor(config, strict=True, json_mode=json_mode, emit_output=not json_mode)
    if json_mode:
        payload = {
            "command": command_name,
            "status": "ok" if doctor_exit == 0 else "needs-follow-up",
            "project": project_payload(config),
            "report": adoption_report_payload(report),
        }
        if extra_payload:
            payload.update(extra_payload)
        emit_json(payload)
        return doctor_exit
    print_adoption_usage(config)
    if doctor_exit == 0:
        print(f"Sula adoption completed for {config.data['project']['name']}")
    else:
        print("Sula adoption completed with follow-up required before strict compliance is clean.")
    return doctor_exit


def finalize_adoption_traceability(config: ProjectConfig) -> None:
    ensure_initial_status(config)
    ensure_adoption_record(config)


def ensure_initial_status(config: ProjectConfig) -> None:
    status_path = config.root / config.data["paths"]["status_file"]
    if status_path.exists():
        text = status_path.read_text(encoding="utf-8")
        if not any(placeholder in text for placeholder in STATUS_PLACEHOLDERS):
            return
    today = date.today().isoformat()
    text = (
        "# STATUS\n\n"
        f"- last updated: {today}\n\n"
        "## Summary\n\n"
        f"- Initial Sula adoption is complete for this repository under the `{config.profile}` profile.\n"
        "- The repository now has a managed operating-system layer and project-owned memory scaffolds.\n\n"
        "## Health\n\n"
        "- status: yellow\n"
        "- reason: adoption is complete, but the team should review generated rules and preserved project-owned files.\n\n"
        "## Current Focus\n\n"
        "- review the first Sula adoption diff\n"
        "- confirm manifest facts and project-owned scaffold content\n\n"
        "## Blockers\n\n"
        "- none\n\n"
        "## Recent Decisions\n\n"
        f"- {today}: approved initial Sula adoption under the `{config.profile}` profile\n\n"
        "## Next Review\n\n"
        "- owner: project maintainers\n"
        f"- date: {today}\n"
        "- trigger: review after the first managed-file sync or after tightening project-specific rules\n"
    )
    status_path.write_text(text, encoding="utf-8")


def ensure_adoption_record(config: ProjectConfig) -> None:
    today = date.today().isoformat()
    title = "Adopt Sula operating system"
    slug = sanitize_slug(title)
    record_path = config.change_record_directory / f"{today}-{slug}.md"
    if record_path.exists():
        return
    config.change_record_directory.mkdir(parents=True, exist_ok=True)
    branch = detect_git_branch(config.root)
    summary = f"Adopted Sula under the `{config.profile}` profile and generated the initial managed/scaffold operating-system layer."
    content = (
        f"# {title}\n\n"
        "## Metadata\n\n"
        f"- date: {today}\n"
        f"- executor: {config.data['project']['default_agent']}\n"
        f"- branch: {branch}\n"
        "- related commit(s): pending review commit\n"
        "- status: completed\n\n"
        "## Background\n\n"
        f"{summary}\n\n"
        "## Analysis\n\n"
        "- The repository needed a reusable operating-system layer instead of ad hoc rules.\n"
        "- Existing project-owned truth should stay local, so scaffold files must remain reviewable and editable.\n\n"
        "## Chosen Plan\n\n"
        f"- initialize Sula with the `{config.profile}` profile\n"
        "- render managed files and preserve project-owned scaffold files when they already exist\n"
        "- add durable memory structures for status and change tracking\n\n"
        "## Execution\n\n"
        "- created the project manifest and version lock\n"
        "- rendered managed rules, docs, and runbooks\n"
        "- generated or preserved scaffold status and change-history files\n"
        "- generated the first memory digest for fast recall\n\n"
        "## Verification\n\n"
        "- reviewed the adoption report before approval\n"
        "- ran `sula doctor --strict` after applying adoption\n\n"
        "## Rollback\n\n"
        "- revert the adoption commit if the repository should not be managed by Sula\n"
        "- keep project-owned truth and re-evaluate the profile fit before retrying\n\n"
        "## Data Side-effects\n\n"
        "- no runtime data side-effects\n"
        "- repository docs and governance files were added or updated\n\n"
        "## Follow-up\n\n"
        "- review generated managed files and fill in any project-specific hard rules\n"
        "- use `sula sync --dry-run` before future shared upgrades\n\n"
        "## Architecture Boundary Check\n\n"
        "- highest rule impact: the repository now adopts Sula as its reusable operating-system layer without changing its business truth\n"
    )
    record_path.write_text(content, encoding="utf-8")
    update_change_records_index(config, record_path, today, title, summary)
    update_status_for_new_record(config, "change", record_path, today, title)


def print_adoption_usage(config: ProjectConfig) -> None:
    sula_command = f"python3 {SULA_ROOT / 'scripts' / 'sula.py'}"
    print("How to use Sula after adoption:")
    print(f"  - inspect current rules: {config.root / 'AGENTS.md'}")
    print(f"  - validate the repository: {sula_command} doctor --project-root {config.root} --strict")
    print(f"  - preview future upgrades: {sula_command} sync --project-root {config.root} --dry-run")
    print(f"  - preview removal: {sula_command} remove --project-root {config.root}")
    print(f"  - add non-trivial history: {sula_command} record new --project-root {config.root} --title \"...\"")
    print(f"  - regenerate recall summary: {sula_command} memory digest --project-root {config.root}")

def collect_render_actions(config: ProjectConfig, *, include_scaffold: bool) -> list[RenderAction]:
    tokens = config.token_map()
    actions: list[RenderAction] = []
    actions.extend(plan_template_tree(core_managed_dir(), config.root, tokens, overwrite=True, origin="core"))
    actions.extend(
        plan_template_tree(
            profile_managed_dir(config.profile),
            config.root,
            tokens,
            overwrite=True,
            origin=f"profile:{config.profile}",
        )
    )
    if include_scaffold:
        actions.extend(
            plan_template_tree(
                core_scaffold_dir(),
                config.root,
                tokens,
                overwrite=False,
                origin="core-scaffold",
            )
        )
        actions.extend(
            plan_template_tree(
                profile_scaffold_dir(config.profile),
                config.root,
                tokens,
                overwrite=False,
                origin=f"scaffold:{config.profile}",
            )
        )
    return actions


def plan_template_tree(
    source: Path,
    destination_root: Path,
    tokens: dict[str, str],
    *,
    overwrite: bool,
    origin: str,
) -> list[RenderAction]:
    if not source.exists():
        return []
    actions: list[RenderAction] = []
    for template in sorted(source.rglob("*")):
        if template.is_dir():
            continue
        relative = template.relative_to(source)
        output_relative = Path(str(relative).removesuffix(".tmpl"))
        output_path = destination_root / output_relative
        rendered_text = render_template(template, tokens)
        if not output_path.exists():
            status = "create"
        elif not overwrite:
            status = "skip"
        else:
            current_text = output_path.read_text(encoding="utf-8")
            status = "unchanged" if current_text == rendered_text else "update"
        impact_level, impact_scope = classify_sync_impact(output_relative)
        actions.append(
            RenderAction(
                relative_path=output_relative,
                output_path=output_path,
                rendered_text=rendered_text,
                overwrite=overwrite,
                origin=origin,
                status=status,
                impact_level=impact_level,
                impact_scope=impact_scope,
            )
        )
    return actions


def render_template(template: Path, tokens: dict[str, str]) -> str:
    text = template.read_text(encoding="utf-8")
    for key, value in tokens.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def apply_actions(actions: list[RenderAction]) -> None:
    for action in actions:
        if action.status not in {"create", "update"}:
            continue
        action.output_path.parent.mkdir(parents=True, exist_ok=True)
        action.output_path.write_text(action.rendered_text, encoding="utf-8")


def classify_sync_impact(relative_path: Path) -> tuple[str, str]:
    normalized = relative_path.as_posix()
    if normalized in {
        "CODEX.md",
        "CLAUDE.md",
        "GEMINI.md",
        ".github/copilot-instructions.md",
        ".cursor/rules/project.mdc",
    }:
        return "high", "ai-tooling"
    if normalized in {
        "docs/runbooks/auth-and-session.md",
        "docs/runbooks/deploy-and-rollback.md",
    }:
        return "high", "runbook"
    if normalized.startswith("docs/ops/") or normalized.startswith("docs/architecture/") or normalized.startswith(
        "docs/runbooks/"
    ):
        return "medium", "operating-docs"
    if normalized == "docs/README.md":
        return "low", "docs-map"
    return "low", "managed"


def print_sync_plan(config: ProjectConfig, actions: list[RenderAction]) -> None:
    print(f"Managed sync plan for {config.data['project']['name']} against Sula {VERSION}")
    changed = [action for action in actions if action.status in {"create", "update"}]
    if not changed:
        print("  No managed-file changes are pending.")
    else:
        for action in changed:
            print(
                "  - "
                f"{action.status:<6} [{action.impact_level}] {action.relative_path.as_posix()} "
                f"({action.origin}, {action.impact_scope})"
            )
    summary = summarize_status_counts(actions)
    print(
        "Summary: "
        + ", ".join(f"{count} {status}" for status, count in summary.items() if count)
    )
    print("Dry run only. No files were written.")


def summarize_status_counts(actions: list[RenderAction]) -> dict[str, int]:
    summary = {"create": 0, "update": 0, "unchanged": 0, "skip": 0}
    for action in actions:
        summary[action.status] += 1
    return summary


def create_record(config: ProjectConfig, args: argparse.Namespace) -> int:
    record_date = normalize_record_date(args.date)
    slug = sanitize_slug(args.slug or args.title)
    directory = record_directory_for_kind(config, args.kind)
    directory.mkdir(parents=True, exist_ok=True)
    output_path = directory / f"{record_date}-{slug}.md"
    if output_path.exists():
        raise SystemExit(f"Record already exists: {output_path}")

    branch = args.branch or detect_git_branch(config.root)
    summary = args.summary.strip() or "Fill in the key decision or delivery summary."
    template_context = {
        "TITLE": args.title,
        "DATE": record_date,
        "SLUG": slug,
        "EXECUTOR": args.executor or config.data["project"]["default_agent"],
        "BRANCH": branch,
        "SUMMARY": summary,
        "RELATED_COMMITS": "TBD",
        "STATUS": "draft",
        "PROJECT_NAME": config.data["project"]["name"],
    }
    content = render_local_record_template(config, args.kind, template_context)
    output_path.write_text(content, encoding="utf-8")

    if args.kind == "change":
        update_change_records_index(config, output_path, record_date, args.title, summary)
    update_status_for_new_record(config, args.kind, output_path, record_date, args.title)
    refresh_kernel_state(config, event_type=f"record.{args.kind}", summary=f"Added {args.kind} record `{args.title}`.")
    if json_output_requested(args):
        emit_json(
            {
                "command": "record.new",
                "status": "ok",
                "project": project_payload(config),
                "record": {
                    "kind": args.kind,
                    "title": args.title,
                    "date": record_date,
                    "path": output_path.relative_to(config.root).as_posix(),
                    "summary": summary,
                },
            }
        )
        return 0
    print(f"Created {args.kind} record at {output_path}")
    return 0


def normalize_record_date(raw: str | None) -> str:
    if raw is None:
        return date.today().isoformat()
    if not MEMORY_DATE_PATTERN.fullmatch(raw):
        raise SystemExit(f"Invalid date, expected YYYY-MM-DD: {raw}")
    return raw


def sanitize_slug(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = lowered.strip("-")
    if not lowered:
        raise SystemExit("Could not derive a slug from the provided title")
    return lowered


def record_directory_for_kind(config: ProjectConfig, kind: str) -> Path:
    if kind == "change":
        return config.change_record_directory
    if kind == "release":
        return config.release_record_directory
    if kind == "incident":
        return config.incident_record_directory
    raise SystemExit(f"Unsupported record kind: {kind}")


def render_local_record_template(config: ProjectConfig, kind: str, context: dict[str, str]) -> str:
    template_path = local_record_template_path(config, kind)
    if template_path.exists():
        text = template_path.read_text(encoding="utf-8")
    else:
        text = builtin_record_template(kind)
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def local_record_template_path(config: ProjectConfig, kind: str) -> Path:
    return record_directory_for_kind(config, kind) / "_template.md"


def builtin_record_template(kind: str) -> str:
    if kind == "change":
        return """# {{TITLE}}

## Metadata

- date: {{DATE}}
- executor: {{EXECUTOR}}
- branch: {{BRANCH}}
- related commit(s): {{RELATED_COMMITS}}
- status: {{STATUS}}

## Background

{{SUMMARY}}

## Analysis

- _fill in context and options_

## Chosen Plan

- _fill in chosen plan_

## Execution

- _fill in what changed_

## Verification

- _fill in verification_

## Rollback

- _fill in rollback_

## Data Side-effects

- _fill in data or operational side-effects_

## Follow-up

- _fill in follow-up_

## Architecture Boundary Check

- highest rule impact: _fill in_
"""
    if kind == "release":
        return """# {{TITLE}}

## Metadata

- date: {{DATE}}
- executor: {{EXECUTOR}}
- branch: {{BRANCH}}
- status: {{STATUS}}

## Scope

{{SUMMARY}}

## Risks

- _fill in risks_

## Verification

- _fill in verification_

## Rollback

- _fill in rollback_

## Follow-up

- _fill in follow-up_
"""
    if kind == "incident":
        return """# {{TITLE}}

## Metadata

- date: {{DATE}}
- executor: {{EXECUTOR}}
- branch: {{BRANCH}}
- status: {{STATUS}}

## Summary

{{SUMMARY}}

## Impact

- _fill in impact_

## Timeline

- _fill in timeline_

## Root Cause

- _fill in root cause_

## Resolution

- _fill in resolution_

## Follow-up

- _fill in follow-up_
"""
    raise SystemExit(f"Unsupported record kind: {kind}")


def detect_git_branch(project_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unknown"
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def update_change_records_index(
    config: ProjectConfig,
    record_path: Path,
    record_date: str,
    title: str,
    summary: str,
) -> None:
    index_path = config.root / config.data["paths"]["change_records_file"]
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = default_change_records_index(config)
    relative_link_path = os.path.relpath(record_path, start=index_path.parent).replace(os.sep, "/")
    entry = f"- {record_date} - [{title}]({relative_link_path}) - {summary}"

    if "_no records yet_" in text:
        text = text.replace("- _no records yet_", entry)
    else:
        marker = "## Index"
        if marker not in text:
            text = text.rstrip() + "\n\n## Index\n\n" + entry + "\n"
        else:
            insert_at = text.index(marker) + len(marker)
            remainder = text[insert_at:]
            first_heading_match = re.search(r"\n## ", remainder)
            if first_heading_match:
                index_block_end = insert_at + first_heading_match.start()
                index_block = text[insert_at:index_block_end].rstrip()
                new_block = index_block + "\n\n" + entry
                text = text[:insert_at] + new_block + text[index_block_end:]
            else:
                text = text.rstrip() + "\n\n" + entry + "\n"
    index_path.write_text(text.rstrip() + "\n", encoding="utf-8")


def default_change_records_index(config: ProjectConfig) -> str:
    return (
        f"# {config.data['project']['name']} Change Records\n\n"
        "## Purpose\n\n"
        "Track non-trivial changes, decisions, verification, and rollback.\n\n"
        "## Rules\n\n"
        "- Keep index entries concise.\n"
        "- Put detailed records in docs/change-records/.\n\n"
        "## Index\n\n"
        "- _no records yet_\n\n"
        "## Detailed Records\n\n"
        f"- directory: `{config.change_record_directory.relative_to(config.root).as_posix()}`\n"
    )


def update_status_for_new_record(
    config: ProjectConfig,
    kind: str,
    record_path: Path,
    record_date: str,
    title: str,
) -> None:
    status_path = config.root / config.data["paths"]["status_file"]
    if not status_path.exists():
        return
    text = status_path.read_text(encoding="utf-8")
    relative_link_path = os.path.relpath(record_path, start=status_path.parent).replace(os.sep, "/")
    if kind == "change":
        bullet = f"- {record_date}: added [{title}]({relative_link_path})"
    elif kind == "release":
        bullet = f"- {record_date}: added release record [{title}]({relative_link_path})"
    else:
        bullet = f"- {record_date}: added incident record [{title}]({relative_link_path})"
    text = STATUS_UPDATED_PATTERN.sub(f"- last updated: {record_date}", text, count=1)
    text = append_bullet_to_section(text, "Recent Decisions", bullet)
    status_path.write_text(text.rstrip() + "\n", encoding="utf-8")


def append_bullet_to_section(text: str, section_name: str, bullet: str) -> str:
    marker = f"## {section_name}"
    if marker not in text:
        return text.rstrip() + f"\n\n{marker}\n\n{bullet}\n"
    start = text.index(marker) + len(marker)
    remainder = text[start:]
    next_heading = re.search(r"\n## ", remainder)
    end = start + next_heading.start() if next_heading else len(text)
    section_body = text[start:end]
    if bullet in section_body:
        return text
    cleaned = section_body.replace("- _add recent decisions_", "").rstrip()
    new_body = cleaned + ("\n\n" if cleaned.strip() else "\n\n") + bullet + "\n"
    return text[:start] + new_body + text[end:]


def generate_memory_digest(config: ProjectConfig, args: argparse.Namespace, *, emit_output: bool = True) -> int:
    output_path = config.digest_file if not args.output else (config.root / args.output)
    digest = build_memory_digest(config, output_path)
    if args.stdout and emit_output:
        print(digest, end="")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest, encoding="utf-8")
    refresh_kernel_state(config, event_type="memory.digest", summary=f"Regenerated memory digest at `{output_path.relative_to(config.root).as_posix()}`.")
    if json_output_requested(args) and emit_output:
        emit_json(
            {
                "command": "memory.digest",
                "status": "ok",
                "project": project_payload(config),
                "output_path": output_path.relative_to(config.root).as_posix(),
            }
        )
        return 0
    if emit_output:
        print(f"Wrote memory digest to {output_path}")
    return 0


def build_memory_digest(config: ProjectConfig, output_path: Path) -> str:
    status_path = config.root / config.data["paths"]["status_file"]
    change_index_path = config.root / config.data["paths"]["change_records_file"]
    status_text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
    status_sections = markdown_sections(status_text)

    lines = [
        f"# {config.data['project']['name']} Memory Digest",
        "",
        f"- generated on: {date.today().isoformat()}",
        f"- generated by: Sula {VERSION}",
        "- source of truth: project docs and records, not this generated digest",
        "",
        "## Identity",
        "",
        f"- project: {config.data['project']['name']}",
        f"- profile: {config.profile}",
        f"- description: {config.data['project']['description']}",
        f"- highest rule: `{config.data['rules']['highest_rule']}`",
        "",
        "## Current State",
        "",
    ]
    lines.extend(section_digest_lines("Summary", status_sections.get("Summary", "_missing_")))
    lines.extend(section_digest_lines("Health", status_sections.get("Health", "_missing_")))
    lines.extend(section_digest_lines("Current Focus", status_sections.get("Current Focus", "_missing_")))
    lines.extend(section_digest_lines("Blockers", status_sections.get("Blockers", "_missing_")))
    lines.extend(section_digest_lines("Recent Decisions", status_sections.get("Recent Decisions", "_missing_")))
    lines.extend(section_digest_lines("Next Review", status_sections.get("Next Review", "_missing_")))

    lines.extend(["## Recent Change Records", ""])
    lines.extend(record_summary_lines(config.change_record_directory, output_path, limit=5))

    lines.extend(["## Release History", ""])
    lines.extend(record_summary_lines(config.release_record_directory, output_path, limit=3))

    lines.extend(["## Incident History", ""])
    lines.extend(record_summary_lines(config.incident_record_directory, output_path, limit=3))

    lines.extend(["## Open Architecture Exceptions", ""])
    lines.extend(exception_summary_lines(config, output_path))

    lines.extend(
        [
            "## Key References",
            "",
            f"- [Status]({relative_link(output_path, status_path)})",
            f"- [Change Record Index]({relative_link(output_path, change_index_path)})",
            f"- [Project Memory Guide]({relative_link(output_path, config.root / 'docs/ops/project-memory.md')})",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def section_digest_lines(title: str, body: str) -> list[str]:
    cleaned = body.strip() or "_missing_"
    return [f"### {title}", "", cleaned, ""]


def record_summary_lines(directory: Path, output_path: Path, *, limit: int) -> list[str]:
    files = list_record_files(directory)
    if not files:
        return ["- none", ""]
    lines: list[str] = []
    for path in files[:limit]:
        title = extract_markdown_title(path.read_text(encoding="utf-8")) or path.stem
        lines.append(f"- [{title}]({relative_link(output_path, path)})")
    lines.append("")
    return lines


def list_record_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files = [
        path
        for path in sorted(directory.glob("*.md"), reverse=True)
        if path.name not in {"README.md", "_template.md"}
    ]
    return files


def exception_summary_lines(config: ProjectConfig, output_path: Path) -> list[str]:
    path = config.root / "docs/ops/architecture-exception-register.md"
    if not path.exists():
        return ["- no register found", ""]
    text = path.read_text(encoding="utf-8")
    rows = []
    for raw_line in text.splitlines():
        if not raw_line.startswith("|"):
            continue
        if raw_line.startswith("| ID ") or raw_line.startswith("| ---") or "_none yet_" in raw_line:
            continue
        rows.append(raw_line)
    if not rows:
        return ["- none", ""]
    lines = [f"- {len(rows)} open or historical entries in [exception register]({relative_link(output_path, path)})", ""]
    return lines


def markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = line[3:].strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(line)
    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()
    return sections


def extract_markdown_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def relative_link(from_path: Path, to_path: Path) -> str:
    return os.path.relpath(to_path, start=from_path.parent).replace(os.sep, "/")


def doctor(config: ProjectConfig, *, strict: bool, json_mode: bool = False, emit_output: bool = True) -> int:
    missing_files: list[str] = []
    drifted_files: list[str] = []
    placeholder_files: list[str] = []
    lock_issues: list[str] = []
    warnings = collect_doctor_warnings(config)
    memory_errors, memory_warnings = collect_memory_doctor_report(config)
    warnings.extend(memory_warnings)
    kernel_errors, kernel_warnings = collect_kernel_doctor_report(config)
    warnings.extend(kernel_warnings)

    for action in collect_render_actions(config, include_scaffold=False):
        if not action.output_path.exists():
            missing_files.append(str(action.output_path))
            continue
        current_text = action.output_path.read_text(encoding="utf-8")
        if current_text != action.rendered_text:
            drifted_files.append(str(action.output_path))
        if "{{" in current_text:
            placeholder_files.append(str(action.output_path))

    lock_issues.extend(check_lockfile(config))

    if emit_output and not json_mode and missing_files:
        print("Missing managed files:")
        for item in missing_files:
            print(f"  - {item}")
    if emit_output and not json_mode and drifted_files:
        print("Managed files differ from the current Sula render:")
        for item in drifted_files:
            print(f"  - {item}")
    if emit_output and not json_mode and placeholder_files:
        print("Files still contain unresolved placeholders:")
        for item in placeholder_files:
            print(f"  - {item}")
    if emit_output and not json_mode and memory_errors:
        print("Project memory issues:")
        for item in memory_errors:
            print(f"  - {item}")
    if emit_output and not json_mode and lock_issues:
        print("Lockfile issues:")
        for item in lock_issues:
            print(f"  - {item}")
    if emit_output and not json_mode and kernel_errors:
        print("Kernel issues:")
        for item in kernel_errors:
            print(f"  - {item}")
    if emit_output and not json_mode and warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")

    has_errors = bool(missing_files or drifted_files or placeholder_files or memory_errors or lock_issues or kernel_errors)
    passed = not has_errors and not (strict and warnings)
    if json_mode and emit_output:
        emit_json(
            {
                "command": "doctor",
                "status": "ok" if passed else "failed",
                **doctor_payload(
                    config,
                    missing_files=missing_files,
                    drifted_files=drifted_files,
                    placeholder_files=placeholder_files,
                    memory_errors=memory_errors,
                    lock_issues=lock_issues,
                    kernel_errors=kernel_errors,
                    warnings=warnings,
                    passed=passed,
                ),
            }
        )
        return 0 if passed else 1
    if passed:
        if emit_output:
            print(f"Sula doctor passed for {config.data['project']['name']}")
        return 0
    return 1


def collect_doctor_warnings(config: ProjectConfig) -> list[str]:
    warnings: list[str] = []
    for section, key in EXISTENCE_WARNING_FIELDS:
        relative_value = config.data[section][key]
        if relative_value.strip().lower() in NON_PATH_SENTINELS:
            continue
        target = config.root / relative_value
        if not target.exists():
            warnings.append(f"manifest reference does not exist yet: {section}.{key} -> {relative_value}")
    return warnings


def collect_kernel_doctor_report(config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    kernel_root = config.root / ".sula"
    required_files = [
        kernel_root / "kernel.toml",
        kernel_root / "adapters" / "catalog.json",
        kernel_root / "adapters" / "bundles.json",
        kernel_root / "artifacts" / "catalog.json",
        kernel_root / "objects" / "catalog.json",
        kernel_root / "state" / "current.md",
        kernel_root / "sources" / "registry.json",
        kernel_root / "events" / "log.jsonl",
        kernel_root / "indexes" / "catalog.json",
        kernel_root / "indexes" / "relations.json",
        kernel_root / "exports" / "catalog.json",
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"missing kernel artifact: {path}")
    registry_path = kernel_root / "sources" / "registry.json"
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid source registry JSON: {registry_path} ({exc})")
        else:
            if not isinstance(registry, list) or not registry:
                errors.append(f"source registry is empty or malformed: {registry_path}")
            else:
                discovered_entries = [item for item in registry if isinstance(item, dict) and item.get("discovered")]
                if not discovered_entries:
                    warnings.append(f"{registry_path}: no discovered project sources were indexed")
    adapter_catalog_path = kernel_root / "adapters" / "catalog.json"
    adapter_ids: set[str] = set()
    if adapter_catalog_path.exists():
        try:
            adapter_catalog = json.loads(adapter_catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid adapter catalog JSON: {adapter_catalog_path} ({exc})")
        else:
            adapters = adapter_catalog.get("adapters")
            if not isinstance(adapters, list) or not adapters:
                errors.append(f"adapter catalog is empty or malformed: {adapter_catalog_path}")
            else:
                for item in adapters:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                        errors.append(f"adapter catalog entry is malformed: {adapter_catalog_path}")
                        break
                    adapter_ids.add(item["id"])
                if "generic-project" not in adapter_ids:
                    errors.append(f"{adapter_catalog_path}: missing required `generic-project` adapter")
                if is_git_repository(config.root) and "repo" not in adapter_ids:
                    warnings.append(f"{adapter_catalog_path}: git repository detected but `repo` adapter is absent")
    bundle_catalog_path = kernel_root / "adapters" / "bundles.json"
    if bundle_catalog_path.exists() and adapter_ids:
        try:
            bundle_catalog = json.loads(bundle_catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid bundle catalog JSON: {bundle_catalog_path} ({exc})")
        else:
            bundles = bundle_catalog.get("bundles")
            if not isinstance(bundles, list) or not bundles:
                errors.append(f"bundle catalog is empty or malformed: {bundle_catalog_path}")
            else:
                for bundle in bundles:
                    if not isinstance(bundle, dict):
                        errors.append(f"bundle catalog entry is malformed: {bundle_catalog_path}")
                        break
                    bundle_adapters = bundle.get("adapters", [])
                    if not isinstance(bundle_adapters, list):
                        errors.append(f"bundle catalog entry has invalid adapter list: {bundle_catalog_path}")
                        break
                    unknown = [adapter for adapter in bundle_adapters if adapter not in adapter_ids]
                    if unknown:
                        errors.append(f"{bundle_catalog_path}: bundle references unknown adapters {unknown}")
                        break
    artifact_catalog_path = kernel_root / "artifacts" / "catalog.json"
    if artifact_catalog_path.exists():
        try:
            artifact_catalog = json.loads(artifact_catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid artifact catalog JSON: {artifact_catalog_path} ({exc})")
        else:
            artifacts = artifact_catalog.get("artifacts")
            if not isinstance(artifacts, list):
                errors.append(f"artifact catalog is malformed: {artifact_catalog_path}")
    object_catalog_path = kernel_root / "objects" / "catalog.json"
    object_ids: set[str] = set()
    if object_catalog_path.exists():
        try:
            object_catalog = json.loads(object_catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid object catalog JSON: {object_catalog_path} ({exc})")
        else:
            objects = object_catalog.get("objects")
            if not isinstance(objects, list) or not objects:
                errors.append(f"object catalog is empty or malformed: {object_catalog_path}")
            else:
                for item in objects:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                        errors.append(f"object catalog entry is malformed: {object_catalog_path}")
                        break
                    object_ids.add(item["id"])
                if not any(item.get("kind") == "project" for item in objects if isinstance(item, dict)):
                    errors.append(f"{object_catalog_path}: missing required project object")
    if registry_path.exists() and adapter_ids:
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = []
        if isinstance(registry, list):
            for item in registry:
                if not isinstance(item, dict):
                    continue
                adapters = item.get("adapters", [])
                if not isinstance(adapters, list) or not adapters:
                    warnings.append(f"{registry_path}: source `{item.get('path', 'unknown')}` is missing adapter bindings")
                    continue
                unknown = [adapter for adapter in adapters if adapter not in adapter_ids]
                if unknown:
                    errors.append(
                        f"{registry_path}: source `{item.get('path', 'unknown')}` references unknown adapters {unknown}"
                    )
                    break
    relation_index_path = kernel_root / "indexes" / "relations.json"
    if relation_index_path.exists() and object_ids:
        try:
            relation_index = json.loads(relation_index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid relation index JSON: {relation_index_path} ({exc})")
        else:
            relations = relation_index.get("relations")
            if not isinstance(relations, list):
                errors.append(f"relation index is malformed: {relation_index_path}")
            else:
                for relation in relations:
                    if not isinstance(relation, dict):
                        errors.append(f"relation index entry is malformed: {relation_index_path}")
                        break
                    from_id = relation.get("from")
                    if isinstance(from_id, str) and from_id not in object_ids:
                        errors.append(f"{relation_index_path}: relation references unknown object `{from_id}`")
                        break
    event_log_path = kernel_root / "events" / "log.jsonl"
    if event_log_path.exists():
        for line_number, raw_line in enumerate(event_log_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid kernel event JSON at {event_log_path}:{line_number} ({exc})")
                break
    sqlite_cache_path = kernel_root / "cache" / "kernel.db"
    if sqlite_cache_path.exists():
        try:
            with sqlite3.connect(sqlite_cache_path) as connection:
                cursor = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('sources', 'objects', 'relations', 'events', 'documents')"
                )
                table_names = {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as exc:
            errors.append(f"invalid sqlite kernel cache: {sqlite_cache_path} ({exc})")
        else:
            missing_tables = sorted({"sources", "objects", "relations", "events", "documents"} - table_names)
            if missing_tables:
                errors.append(f"{sqlite_cache_path}: missing required tables {missing_tables}")
    else:
        warnings.append(f"{sqlite_cache_path}: rebuildable SQLite cache is missing")
    return errors, warnings


def collect_memory_doctor_report(config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    status_path = config.root / config.data["paths"]["status_file"]
    if not status_path.exists():
        errors.append(f"missing status file: {status_path}")
    else:
        status_errors, status_warnings = validate_status_file(status_path, config.status_max_age_days)
        errors.extend(status_errors)
        warnings.extend(status_warnings)

    index_path = config.root / config.data["paths"]["change_records_file"]
    if not index_path.exists():
        errors.append(f"missing change record index: {index_path}")
    else:
        index_errors, index_warnings = validate_change_record_index(index_path, config)
        errors.extend(index_errors)
        warnings.extend(index_warnings)

    change_errors, change_warnings = validate_record_directory(
        config.change_record_directory,
        kind="change",
        required_headings=CHANGE_RECORD_REQUIRED_HEADINGS,
        required=True,
    )
    release_errors, release_warnings = validate_record_directory(
        config.release_record_directory,
        kind="release",
        required_headings=RELEASE_RECORD_REQUIRED_HEADINGS,
        required=False,
    )
    incident_errors, incident_warnings = validate_record_directory(
        config.incident_record_directory,
        kind="incident",
        required_headings=INCIDENT_RECORD_REQUIRED_HEADINGS,
        required=False,
    )
    errors.extend(change_errors)
    errors.extend(release_errors)
    errors.extend(incident_errors)
    warnings.extend(change_warnings)
    warnings.extend(release_warnings)
    warnings.extend(incident_warnings)

    register_path = config.root / "docs/ops/architecture-exception-register.md"
    if register_path.exists():
        register_errors, register_warnings = validate_exception_register(register_path, config)
        errors.extend(register_errors)
        warnings.extend(register_warnings)

    return errors, warnings


def validate_status_file(status_path: Path, status_max_age_days: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = status_path.read_text(encoding="utf-8")
    sections = markdown_sections(text)
    for section in STATUS_REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"{status_path}: missing section `## {section}`")

    updated_match = STATUS_UPDATED_PATTERN.search(text)
    if updated_match is None:
        errors.append(f"{status_path}: missing `- last updated:` line")
    else:
        raw_date = updated_match.group(1).strip()
        if not MEMORY_DATE_PATTERN.fullmatch(raw_date):
            errors.append(f"{status_path}: invalid last updated date `{raw_date}`")
        else:
            age_days = (date.today() - datetime.strptime(raw_date, "%Y-%m-%d").date()).days
            if age_days > status_max_age_days:
                warnings.append(
                    f"{status_path}: status is {age_days} days old, over the {status_max_age_days}-day freshness target"
                )

    for placeholder in STATUS_PLACEHOLDERS:
        if placeholder in text:
            warnings.append(f"{status_path}: placeholder content still present ({placeholder})")
            break
    return errors, warnings


def validate_change_record_index(index_path: Path, config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = index_path.read_text(encoding="utf-8")
    sections = markdown_sections(text)
    for section in CHANGE_RECORDS_REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"{index_path}: missing section `## {section}`")

    if any(placeholder in text for placeholder in INDEX_PLACEHOLDERS):
        warnings.append(f"{index_path}: no detailed records are indexed yet")

    for _, target in MARKDOWN_LINK_PATTERN.findall(text):
        if "change-records/" not in target:
            continue
        resolved = (index_path.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{index_path}: indexed change record is missing -> {target}")
    if not config.change_record_directory.exists():
        errors.append(f"missing change record directory: {config.change_record_directory}")
    return errors, warnings


def validate_record_directory(
    directory: Path,
    *,
    kind: str,
    required_headings: list[str],
    required: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not directory.exists():
        message = f"missing {kind} record directory: {directory}"
        if required:
            errors.append(message)
        else:
            warnings.append(message)
        return errors, warnings

    files = list_record_files(directory)
    if required and not files:
        warnings.append(f"{directory}: no {kind} records exist yet")
    for path in files:
        if not CHANGE_RECORD_FILENAME_PATTERN.fullmatch(path.name):
            errors.append(f"{path}: filename must match YYYY-MM-DD-slug.md")
        text = path.read_text(encoding="utf-8")
        for heading in required_headings:
            if heading not in text:
                errors.append(f"{path}: missing required heading `{heading}`")
        if "YYYY-MM-DD" in text or "_fill in" in text or "TBD" in text:
            warnings.append(f"{path}: placeholder content still present")
    return errors, warnings


def validate_exception_register(register_path: Path, config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = register_path.read_text(encoding="utf-8")
    found_reference = False
    for raw_line in text.splitlines():
        if not raw_line.startswith("|"):
            continue
        if raw_line.startswith("| ID ") or raw_line.startswith("| ---") or "_none yet_" in raw_line:
            continue
        if "docs/change-records/" not in raw_line:
            warnings.append(f"{register_path}: exception row is missing a change-record reference -> {raw_line}")
            continue
        found_reference = True
        for _, target in MARKDOWN_LINK_PATTERN.findall(raw_line):
            if "change-records/" not in target:
                continue
            resolved = (register_path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{register_path}: exception reference target is missing -> {target}")
    if not found_reference and "_none yet_" not in text:
        warnings.append(f"{register_path}: no explicit exception references found")
    return errors, warnings


def check_lockfile(config: ProjectConfig) -> list[str]:
    lock_file = config.root / LOCK_PATH
    if not lock_file.exists():
        return [f"missing lockfile: {lock_file}"]

    try:
        raw = parse_flat_kv_toml(lock_file.read_text(encoding="utf-8"))
    except SystemExit as exc:
        return [f"invalid lockfile: {exc}"]

    issues: list[str] = []
    expected_profile = config.profile
    actual_version = raw.get("sula_version")
    actual_profile = raw.get("profile")

    if actual_version != VERSION:
        issues.append(f"lockfile sula_version is {actual_version!r}, expected {VERSION!r}")
    if actual_profile != expected_profile:
        issues.append(f"lockfile profile is {actual_profile!r}, expected {expected_profile!r}")
    return issues


def parse_flat_kv_toml(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") or "=" not in line:
            raise SystemExit(f"Unsupported lockfile line: {raw_line}")
        key, value = line.split("=", 1)
        parsed = parse_toml_value(value.strip())
        if not isinstance(parsed, str):
            raise SystemExit(f"Unsupported lockfile value for {key.strip()}: {value.strip()}")
        data[key.strip()] = parsed
    return data


def write_lockfile(config: ProjectConfig) -> None:
    lock_file = config.root / LOCK_PATH
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(
        f'sula_version = "{VERSION}"\nprofile = "{config.profile}"\n',
        encoding="utf-8",
    )


def refresh_kernel_state(config: ProjectConfig, *, event_type: str | None = None, summary: str | None = None) -> None:
    kernel_root = config.root / ".sula"
    for relative in ["adapters", "artifacts", "objects", "sources", "state", "events", "indexes", "cache", "exports"]:
        (kernel_root / relative).mkdir(parents=True, exist_ok=True)

    event_log_path = kernel_root / "events" / "log.jsonl"
    if not event_log_path.exists():
        event_log_path.write_text("", encoding="utf-8")
    if event_type and summary:
        append_kernel_event(config, event_log_path, event_type, summary)

    (kernel_root / "kernel.toml").write_text(render_kernel_manifest(config), encoding="utf-8")
    (kernel_root / "adapters" / "catalog.json").write_text(render_adapter_catalog(config), encoding="utf-8")
    (kernel_root / "adapters" / "bundles.json").write_text(render_bundle_catalog(config), encoding="utf-8")
    ensure_artifact_catalog(config)
    (kernel_root / "sources" / "registry.json").write_text(render_source_registry(config), encoding="utf-8")
    (kernel_root / "objects" / "catalog.json").write_text(render_object_catalog(config), encoding="utf-8")
    (kernel_root / "state" / "current.md").write_text(render_kernel_current_state(config), encoding="utf-8")
    (kernel_root / "indexes" / "catalog.json").write_text(render_index_catalog(config), encoding="utf-8")
    (kernel_root / "indexes" / "relations.json").write_text(render_relation_index(config), encoding="utf-8")
    (kernel_root / "exports" / "catalog.json").write_text(render_export_catalog(config), encoding="utf-8")
    (kernel_root / "cache" / "query-index.json").write_text(render_query_cache(config), encoding="utf-8")
    rebuild_kernel_sqlite_cache(config)
    cache_readme = kernel_root / "cache" / "README.md"
    if not cache_readme.exists():
        cache_readme.write_text(
            "# Sula Cache\n\nThis directory stores disposable local caches. It is safe to delete and rebuild.\n",
            encoding="utf-8",
        )


def append_kernel_event(config: ProjectConfig, event_log_path: Path, event_type: str, summary: str) -> None:
    event = {
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "event_type": event_type,
        "summary": summary,
        "profile": config.profile,
        "project": config.data["project"]["slug"],
    }
    with event_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def render_kernel_manifest(config: ProjectConfig) -> str:
    adapters = ", ".join(format_toml_value(adapter) for adapter in config.kernel_adapters())
    git_enabled = "true" if is_git_repository(config.root) else "false"
    return (
        "[kernel]\n"
        f'sula_version = "{VERSION}"\n'
        f'profile = "{config.profile}"\n'
        f"adapters = [{adapters}]\n"
        f"git_enabled = {git_enabled}\n"
        'adapter_catalog = ".sula/adapters/catalog.json"\n'
        'bundle_catalog = ".sula/adapters/bundles.json"\n'
        'artifact_catalog = ".sula/artifacts/catalog.json"\n'
        'object_catalog = ".sula/objects/catalog.json"\n'
        'state_snapshot = ".sula/state/current.md"\n'
        'source_registry = ".sula/sources/registry.json"\n'
        'event_log = ".sula/events/log.jsonl"\n'
        'index_catalog = ".sula/indexes/catalog.json"\n'
        'relation_index = ".sula/indexes/relations.json"\n'
        'sqlite_cache = ".sula/cache/kernel.db"\n'
        'export_catalog = ".sula/exports/catalog.json"\n'
        'removal_mode = "explicit-remove-command"\n'
    )


def render_source_registry(config: ProjectConfig) -> str:
    return json.dumps(build_source_registry(config), indent=2, ensure_ascii=True) + "\n"


def render_adapter_catalog(config: ProjectConfig) -> str:
    catalog = {
        "version": VERSION,
        "profile": config.profile,
        "adapters": build_adapter_catalog(config),
    }
    return json.dumps(catalog, indent=2, ensure_ascii=True) + "\n"


def render_bundle_catalog(config: ProjectConfig) -> str:
    bundle_catalog = {
        "version": VERSION,
        "profile": config.profile,
        "bundles": [
            {
                "id": f"bundle:{config.profile}",
                "profile": config.profile,
                "adapters": config.kernel_adapters(),
                "description": profile_bundle_description(config.profile),
            }
        ],
    }
    return json.dumps(bundle_catalog, indent=2, ensure_ascii=True) + "\n"


def render_object_catalog(config: ProjectConfig) -> str:
    catalog = {
        "version": VERSION,
        "profile": config.profile,
        "objects": build_object_catalog(config),
    }
    return json.dumps(catalog, indent=2, ensure_ascii=True) + "\n"


def render_query_cache(config: ProjectConfig) -> str:
    documents = build_query_documents(config)
    postings: dict[str, list[str]] = {}
    for document in documents:
        for token in tokenize_text(
            " ".join(
                [
                    document["title"],
                    document["summary"],
                    document["path"],
                    " ".join(document["tags"]),
                    " ".join(document.get("adapters", [])),
                ]
            )
        ):
            postings.setdefault(token, [])
            if document["id"] not in postings[token]:
                postings[token].append(document["id"])
    cache = {
        "version": VERSION,
        "profile": config.profile,
        "documents": documents,
        "postings": postings,
    }
    return json.dumps(cache, indent=2, ensure_ascii=True) + "\n"


def build_adapter_catalog(config: ProjectConfig) -> list[dict[str, object]]:
    adapters: list[dict[str, object]] = []
    for adapter in config.kernel_adapters():
        item = {
            "id": adapter,
            "kind": adapter_kind(adapter),
            "required": adapter in {"generic-project", "docs", "memory"},
            "enabled": True,
            "git_required": adapter == "repo",
            "description": adapter_description(adapter),
            "source_matchers": adapter_source_matchers(adapter),
        }
        if adapter in {"local-fs", "google-drive"}:
            item["provider"] = config.storage_provider
            item["sync_mode"] = config.storage_sync_mode
            item["workspace_root"] = str(config.storage_workspace_root)
            item["provider_root_url"] = config.provider_root_url
            item["provider_root_id"] = config.provider_root_id
        adapters.append(item)
    return adapters


def build_source_registry(config: ProjectConfig) -> list[dict[str, object]]:
    candidates = [
        ("project-manifest", "sula-manifest", MANIFEST_PATH.as_posix()),
        ("status", "state", config.data["paths"]["status_file"]),
        ("change-records", "change-index", config.data["paths"]["change_records_file"]),
        ("agents", "instructions", "AGENTS.md"),
        ("readme", "overview", "README.md"),
        ("app-shell", "project-entry", config.data["paths"]["app_shell"]),
        ("api-layer", "project-entry", config.data["paths"]["api_layer"]),
        ("kernel-state", "kernel-state", ".sula/state/current.md"),
        ("memory-digest", "derived-export", config.memory_setting("digest_file", ".sula/memory-digest.md")),
        ("artifacts-catalog", "artifact-index", ".sula/artifacts/catalog.json"),
    ]
    seen: set[str] = set()
    entries: list[dict[str, object]] = []
    for source_id, kind, relative_path in candidates:
        if relative_path in seen:
            continue
        seen.add(relative_path)
        path = config.root / relative_path
        entries.append(
            {
                "id": source_id,
                "kind": kind,
                "path": relative_path,
                "exists": path.exists(),
                "source_of_truth": not relative_path.startswith(".sula/"),
                "adapters": adapters_for_source(config, relative_path, kind),
            }
        )
    if is_git_repository(config.root):
        entries.append(
            {
                "id": "git-repository",
                "kind": "repo",
                "path": ".git",
                "exists": True,
                "source_of_truth": False,
                "adapters": ["repo"],
            }
        )
    entries.append(
        {
            "id": "storage-workspace",
            "kind": "storage-root",
            "path": os.path.relpath(config.storage_workspace_root, start=config.root) if config.storage_workspace_root != config.root else ".",
            "exists": config.storage_workspace_root.exists(),
            "source_of_truth": config.storage_provider == "local-fs",
            "adapters": [config.storage_provider],
            "provider_root_url": config.provider_root_url,
            "provider_root_id": config.provider_root_id,
        }
    )
    for discovered in discover_project_sources(config):
        entries.append(discovered)
    return entries


def discover_project_sources(config: ProjectConfig) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in iter_discoverable_files(config.root):
        relative_path = path.relative_to(config.root).as_posix()
        entries.append(
            {
                "id": f"source:{sanitize_source_id(relative_path)}",
                "kind": detect_source_kind(relative_path),
                "path": relative_path,
                "exists": True,
                "source_of_truth": True,
                "discovered": True,
                "size_bytes": path.stat().st_size,
                "anchor_strategy": detect_anchor_strategy(relative_path),
                "adapters": adapters_for_source(config, relative_path, detect_source_kind(relative_path)),
            }
        )
        if len(entries) >= MAX_DISCOVERED_SOURCES:
            break
    return entries


def iter_discoverable_files(project_root: Path):
    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(project_root).parts
        if any(part in KERNEL_SKIP_DIRS for part in relative_parts[:-1]):
            continue
        if path.suffix.lower() not in DISCOVERABLE_SOURCE_SUFFIXES:
            continue
        yield path


def sanitize_source_id(relative_path: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", "-", relative_path.lower()).strip("-")
    return sanitized or "root"


def detect_source_kind(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower()
    if suffix in {".md", ".txt", ".rst"}:
        return "document"
    if suffix in {".py", ".sh", ".js", ".jsx", ".ts", ".tsx"}:
        return "code"
    if suffix in {".json", ".toml", ".yml", ".yaml"}:
        return "config"
    if suffix in {".html", ".css"}:
        return "interface"
    return "file"


def detect_anchor_strategy(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower()
    if suffix in {".md", ".txt", ".rst"}:
        return "heading-or-line"
    return "line"


def adapters_for_source(config: ProjectConfig, relative_path: str, source_kind: str) -> list[str]:
    adapters: list[str] = ["generic-project"]
    lowered = relative_path.lower()
    if config.storage_provider in {"google-drive", "local-fs"}:
        adapters.append(config.storage_provider)
    if source_kind in {"document", "interface"} or lowered.endswith("readme.md"):
        adapters.append("docs")
    if lowered.startswith(".sula/") or lowered in {
        config.data["paths"]["status_file"].lower(),
        config.data["paths"]["change_records_file"].lower(),
    } or "change-records/" in lowered or "releases/" in lowered or "incidents/" in lowered:
        adapters.append("memory")
    if is_git_repository(config.root) and not lowered.startswith(".sula/"):
        adapters.append("repo")
    if config.profile == "react-frontend-erpnext":
        if source_kind in {"code", "interface"}:
            adapters.append("erpnext")
        if lowered.startswith(".github/workflows/") or "deploy" in lowered:
            adapters.append("deploy")
    if config.profile == "sula-core":
        if "registry/" in lowered:
            adapters.append("registry")
        if "release" in lowered or "version" in lowered or lowered == "changelog.md":
            adapters.append("release")
    return dedupe_preserve_order(adapters)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def adapter_kind(adapter: str) -> str:
    if adapter == "generic-project":
        return "base"
    if adapter in {"docs", "memory", "repo", "local-fs", "google-drive"}:
        return "core"
    return "profile-extension"


def adapter_description(adapter: str) -> str:
    descriptions = {
        "generic-project": "Minimum removable project kernel.",
        "docs": "Project documents and source anchors.",
        "memory": "State, change history, and recall views.",
        "repo": "Git-aware repository metadata and workflows.",
        "local-fs": "Local filesystem workspace adapter.",
        "google-drive": "Google Drive workspace adapter in local-sync mode or future direct mode.",
        "deploy": "Deployment-related sources and workflows.",
        "erpnext": "React frontend over ERPNext/Frappe integration surfaces.",
        "registry": "Registry and rollout metadata for operating-system repositories.",
        "release": "Release/versioning sources and rollout history.",
    }
    return descriptions.get(adapter, "Project adapter.")


def profile_bundle_description(profile: str) -> str:
    descriptions = {
        "generic-project": "Baseline bundle for unknown, in-progress, or non-Git projects.",
        "react-frontend-erpnext": "Bundle for React frontends orchestrating ERPNext/Frappe systems.",
        "sula-core": "Bundle for repositories that are themselves reusable operating-system projects.",
    }
    return descriptions.get(profile, "Project bundle.")


def adapter_source_matchers(adapter: str) -> list[str]:
    matchers = {
        "generic-project": ["*"],
        "docs": ["README.md", "docs/**", "*.md"],
        "memory": [".sula/**", "STATUS.md", "CHANGE-RECORDS.md", "docs/change-records/**", "docs/releases/**", "docs/incidents/**"],
        "repo": [".git", ".github/**", "*"],
        "local-fs": ["*"],
        "google-drive": ["*"],
        "deploy": [".github/workflows/**", "*deploy*"],
        "erpnext": ["src/api/**", "src/App.tsx", "src/main.tsx"],
        "registry": ["registry/**"],
        "release": ["CHANGELOG.md", "VERSION", "docs/releases/**", "docs/versioning.md"],
    }
    return matchers.get(adapter, ["*"])


def build_object_catalog(config: ProjectConfig) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    status_path = config.root / config.data["paths"]["status_file"]
    status_sections = markdown_sections(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    status_updated = extract_status_updated_date(status_path.read_text(encoding="utf-8")) if status_path.exists() else None
    objects.append(
        {
            "id": f"project:{config.data['project']['slug']}",
            "kind": "project",
            "title": config.data["project"]["name"],
            "summary": config.data["project"]["description"],
            "status": "active",
            "path": MANIFEST_PATH.as_posix(),
            "source_paths": [MANIFEST_PATH.as_posix(), config.data["paths"]["status_file"]],
            "adapters": config.kernel_adapters(),
            "tags": [config.profile],
            "date": status_updated,
        }
    )
    objects.append(
        {
            "id": "state:current",
            "kind": "state",
            "title": "Current Project State",
            "summary": status_sections.get("Summary", "_missing_"),
            "status": "current",
            "path": config.data["paths"]["status_file"],
            "source_paths": [config.data["paths"]["status_file"]],
            "adapters": ["generic-project", "memory"],
            "tags": ["state"],
            "date": status_updated,
        }
    )
    objects.extend(build_status_objects(config, status_sections, status_updated))
    objects.extend(build_record_objects(config.root, config.change_record_directory, "change", ["generic-project", "memory"]))
    objects.extend(build_record_objects(config.root, config.release_record_directory, "release", ["generic-project", "memory"]))
    objects.extend(build_record_objects(config.root, config.incident_record_directory, "incident", ["generic-project", "memory"]))
    objects.extend(build_artifact_objects(config))
    for source in build_source_registry(config):
        if not source.get("discovered"):
            continue
        source_path = config.root / str(source["path"])
        source_summary_text = source_summary(source_path)
        objects.append(
            {
                "id": f"object:{source['id']}",
                "kind": source.get("kind", "source"),
                "title": Path(str(source["path"])).name,
                "summary": source_summary_text,
                "status": "indexed",
                "path": source["path"],
                "source_paths": [source["path"]],
                "adapters": source.get("adapters", ["generic-project"]),
                "tags": ["discovered-source"],
                "date": detect_source_date(source_path, source_summary_text),
            }
        )
        objects.extend(build_discovered_source_objects(source_path, str(source["path"]), source.get("adapters", ["generic-project"])))
    return dedupe_objects(objects)


def build_artifact_objects(config: ProjectConfig) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    catalog = load_artifact_catalog(config)
    for artifact in catalog.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        source_paths = [str(artifact.get("path", ""))] if artifact.get("path") else []
        objects.append(
            {
                "id": str(artifact.get("id", "")),
                "kind": str(artifact.get("kind", "artifact")),
                "title": str(artifact.get("title", Path(str(artifact.get("path", ""))).name)),
                "summary": str(artifact.get("summary", "")),
                "status": str(artifact.get("status", "registered")),
                "path": str(artifact.get("path", "")),
                "source_paths": source_paths,
                "adapters": dedupe_preserve_order(
                    [config.storage_provider, "generic-project", "docs"] + ([config.storage_provider] if config.storage_provider else [])
                ),
                "tags": ["artifact", str(artifact.get("slot", "delivery")), config.workflow_pack],
                "date": normalize_optional_text(artifact.get("date", "")),
            }
        )
    return objects


def build_record_objects(project_root: Path, directory: Path, kind: str, adapters: list[str]) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    for record_path in list_record_files(directory):
        text = record_path.read_text(encoding="utf-8")
        title = extract_markdown_title(text) or record_path.stem
        relative_path = record_path.relative_to(project_root).as_posix()
        record_date = detect_record_date(record_path, text)
        objects.append(
            {
                "id": f"{kind}:{record_path.stem}",
                "kind": kind,
                "title": title,
                "summary": first_readme_paragraph(text),
                "status": "recorded",
                "path": relative_path,
                "source_paths": [relative_path],
                "adapters": adapters,
                "tags": [kind],
                "date": record_date,
            }
        )
        if kind == "release":
            objects.append(
                {
                    "id": f"milestone:{record_path.stem}",
                    "kind": "milestone",
                    "title": title,
                    "summary": first_readme_paragraph(text) or "Recorded release milestone.",
                    "status": "shipped",
                    "path": relative_path,
                    "source_paths": [relative_path],
                    "adapters": adapters,
                    "tags": ["release-milestone"],
                    "date": record_date,
                }
            )
        if kind == "incident":
            objects.append(
                {
                    "id": f"risk:{record_path.stem}",
                    "kind": "risk",
                    "title": title,
                    "summary": first_readme_paragraph(text) or "Recorded incident and follow-up risk.",
                    "status": "incident",
                    "path": relative_path,
                    "source_paths": [relative_path],
                    "adapters": adapters,
                    "tags": ["incident-risk"],
                    "date": record_date,
                }
            )
        objects.extend(build_section_objects(relative_path, text, adapters, default_date=record_date))
        if looks_like_agreement(relative_path, title, text):
            objects.append(
                {
                    "id": f"agreement:{record_path.stem}",
                    "kind": "agreement",
                    "title": title,
                    "summary": first_readme_paragraph(text) or "Agreement-related record.",
                    "status": "active",
                    "path": relative_path,
                    "source_paths": [relative_path],
                    "adapters": adapters,
                    "tags": ["agreement"],
                    "date": record_date,
                }
            )
    return objects


def build_status_objects(
    config: ProjectConfig,
    status_sections: dict[str, str],
    status_updated: str | None,
) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    status_path = config.data["paths"]["status_file"]
    adapters = ["generic-project", "memory"]
    current_focus = markdown_bullet_items(status_sections.get("Current Focus", ""))
    for item in current_focus:
        objects.append(
            {
                "id": f"task:status:{sanitize_source_id(item)}",
                "kind": "task",
                "title": truncate_title(item),
                "summary": item,
                "status": "open",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["current-focus", "status"],
                "date": status_updated,
            }
        )
    blockers = markdown_bullet_items(status_sections.get("Blockers", ""))
    for item in blockers:
        if line_is_empty_placeholder(item):
            continue
        objects.append(
            {
                "id": f"risk:status:{sanitize_source_id(item)}",
                "kind": "risk",
                "title": truncate_title(item),
                "summary": item,
                "status": "open",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["blocker", "status"],
                "date": status_updated,
            }
        )
    decisions = markdown_bullet_items(status_sections.get("Recent Decisions", ""))
    for item in decisions:
        objects.append(
            {
                "id": f"decision:status:{sanitize_source_id(item)}",
                "kind": "decision",
                "title": truncate_title(item),
                "summary": item,
                "status": "decided",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["recent-decision", "status"],
                "date": extract_inline_date(item) or status_updated,
            }
        )
    next_review_fields = markdown_key_values(status_sections.get("Next Review", ""))
    owner = next_review_fields.get("owner")
    if owner:
        objects.append(
            {
                "id": f"person:status:{sanitize_source_id(owner)}",
                "kind": "person",
                "title": owner,
                "summary": f"Current review owner for {config.data['project']['name']}.",
                "status": "responsible",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["next-review-owner", "status"],
                "date": status_updated,
            }
        )
    review_date = next_review_fields.get("date")
    if review_date:
        trigger = next_review_fields.get("trigger", "")
        milestone_summary = " ".join(part for part in ["Next review checkpoint.", trigger] if part).strip()
        objects.append(
            {
                "id": f"milestone:status:next-review:{sanitize_source_id(review_date)}",
                "kind": "milestone",
                "title": "Next Review",
                "summary": milestone_summary or "Next review checkpoint.",
                "status": "planned",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["next-review", "status"],
                "date": review_date,
            }
        )
    health_fields = markdown_key_values(status_sections.get("Health", ""))
    health_status = health_fields.get("status", "").lower()
    health_reason = health_fields.get("reason", "")
    if health_status and health_status not in {"green", "healthy", "stable"}:
        objects.append(
            {
                "id": f"risk:health:{sanitize_source_id(health_status + '-' + health_reason)}",
                "kind": "risk",
                "title": f"Project health is {health_status}",
                "summary": health_reason or f"Health status reported as {health_status}.",
                "status": "watch",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["health", "status"],
                "date": status_updated,
            }
        )
    return objects


def build_discovered_source_objects(source_path: Path, relative_path: str, adapters: list[str]) -> list[dict[str, object]]:
    if not source_path.exists() or source_path.is_dir():
        return []
    suffix = source_path.suffix.lower()
    if suffix not in {".md", ".txt", ".rst"}:
        return []
    text = source_path.read_text(encoding="utf-8", errors="ignore")
    objects = build_section_objects(relative_path, text, adapters, default_date=detect_source_date(source_path, text))
    title = extract_markdown_title(text) or source_path.stem
    if looks_like_agreement(relative_path, title, text):
        objects.append(
            {
                "id": f"agreement:source:{sanitize_source_id(relative_path)}",
                "kind": "agreement",
                "title": title,
                "summary": first_readme_paragraph(text) or "Agreement source document.",
                "status": "active",
                "path": relative_path,
                "source_paths": [relative_path],
                "adapters": adapters,
                "tags": ["agreement", "source"],
                "date": detect_source_date(source_path, text),
            }
        )
    return objects


def build_section_objects(
    relative_path: str,
    text: str,
    adapters: list[str],
    *,
    default_date: str | None,
) -> list[dict[str, object]]:
    section_map = {
        "Tasks": ("task", "open", ["task"]),
        "Decisions": ("decision", "decided", ["decision"]),
        "Risks": ("risk", "open", ["risk"]),
        "People": ("person", "active", ["person"]),
        "Agreements": ("agreement", "active", ["agreement"]),
        "Milestones": ("milestone", "planned", ["milestone"]),
    }
    objects: list[dict[str, object]] = []
    sections = markdown_sections(text)
    for heading, (kind, status, tags) in section_map.items():
        for item in markdown_bullet_items(sections.get(heading, "")):
            objects.append(
                {
                    "id": f"{kind}:{sanitize_source_id(relative_path)}:{sanitize_source_id(item)}",
                    "kind": kind,
                    "title": truncate_title(item),
                    "summary": item,
                    "status": status,
                    "path": relative_path,
                    "source_paths": [relative_path],
                    "adapters": adapters,
                    "tags": tags + ["section-object"],
                    "date": extract_inline_date(item) or default_date,
                }
            )
    return objects


def dedupe_objects(objects: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in objects:
        object_id = str(item.get("id", ""))
        if not object_id or object_id in seen:
            continue
        seen.add(object_id)
        deduped.append(item)
    return deduped


def extract_status_updated_date(text: str) -> str | None:
    match = STATUS_UPDATED_PATTERN.search(text)
    if match is None:
        return None
    raw_date = match.group(1).strip()
    return raw_date if MEMORY_DATE_PATTERN.fullmatch(raw_date) else None


def detect_record_date(record_path: Path, text: str) -> str | None:
    metadata = markdown_key_values(markdown_sections(text).get("Metadata", ""))
    if metadata.get("date") and MEMORY_DATE_PATTERN.fullmatch(metadata["date"]):
        return metadata["date"]
    prefix = record_path.stem[:10]
    if MEMORY_DATE_PATTERN.fullmatch(prefix):
        return prefix
    return extract_inline_date(text)


def detect_source_date(path: Path, text: str) -> str | None:
    prefix = path.stem[:10]
    if MEMORY_DATE_PATTERN.fullmatch(prefix):
        return prefix
    return extract_inline_date(text)


def extract_inline_date(text: str) -> str | None:
    match = INLINE_DATE_PATTERN.search(text)
    return match.group(0) if match else None


def markdown_bullet_items(text: str) -> list[str]:
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            value = line[2:].strip()
            if value:
                items.append(value)
    return items


def markdown_key_values(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in markdown_bullet_items(text):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def line_is_empty_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in {"none", "n/a", "none.", "_none_", "_missing_"}


def truncate_title(value: str, limit: int = 80) -> str:
    collapsed = re.sub(r"\s+", " ", value).strip()
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 3].rstrip() + "..."


def looks_like_agreement(relative_path: str, title: str, text: str) -> bool:
    haystack = " ".join([relative_path.lower(), title.lower(), text[:500].lower()])
    return any(term in haystack for term in ["contract", "agreement", "msa", "statement of work", "sow"])


def source_summary(path: Path) -> str:
    if not path.exists():
        return "_missing_"
    if path.is_dir():
        return path.name
    text = path.read_text(encoding="utf-8", errors="ignore")
    summary = first_readme_paragraph(text)
    if summary:
        return summary[:240]
    return extract_markdown_title(text) or path.name


def render_kernel_current_state(config: ProjectConfig) -> str:
    status_path = config.root / config.data["paths"]["status_file"]
    status_sections = markdown_sections(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    lines = [
        "# Current State Snapshot",
        "",
        f"- generated on: {date.today().isoformat()}",
        f"- project: {config.data['project']['name']}",
        f"- profile: `{config.profile}`",
        "- source priority: STATUS.md and project records override this generated snapshot",
        "",
    ]
    for section_name in ["Summary", "Health", "Current Focus", "Blockers", "Recent Decisions", "Next Review"]:
        lines.append(f"## {section_name}")
        lines.append("")
        lines.append((status_sections.get(section_name, "_missing_") or "_missing_").strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_index_catalog(config: ProjectConfig) -> str:
    registry = build_source_registry(config)
    adapters = build_adapter_catalog(config)
    objects = build_object_catalog(config)
    artifacts = load_artifact_catalog(config).get("artifacts", [])
    discovered_sources = [item for item in registry if item.get("discovered")]
    catalog = {
        "version": VERSION,
        "profile": config.profile,
        "counts": {
            "registered_sources": len(registry),
            "discovered_sources": len(discovered_sources),
            "adapters": len(adapters),
            "artifacts": len(artifacts) if isinstance(artifacts, list) else 0,
            "objects": len(objects),
            "source_adapter_links": sum(len(item.get("adapters", [])) for item in registry if isinstance(item, dict)),
        },
        "adapter_catalog": ".sula/adapters/catalog.json",
        "indexes": [
            {"name": "source-registry", "path": ".sula/sources/registry.json", "rebuildable": True},
            {"name": "adapter-catalog", "path": ".sula/adapters/catalog.json", "rebuildable": True},
            {"name": "artifact-catalog", "path": ".sula/artifacts/catalog.json", "rebuildable": False},
            {"name": "object-catalog", "path": ".sula/objects/catalog.json", "rebuildable": True},
            {"name": "current-state", "path": ".sula/state/current.md", "rebuildable": True},
            {"name": "event-log", "path": ".sula/events/log.jsonl", "rebuildable": False},
            {"name": "relation-index", "path": ".sula/indexes/relations.json", "rebuildable": True},
            {"name": "sqlite-cache", "path": ".sula/cache/kernel.db", "rebuildable": True},
            {"name": "memory-digest", "path": config.memory_setting("digest_file", ".sula/memory-digest.md"), "rebuildable": True},
        ],
    }
    return json.dumps(catalog, indent=2, ensure_ascii=True) + "\n"


def render_relation_index(config: ProjectConfig) -> str:
    registry = build_source_registry(config)
    objects = build_object_catalog(config)
    relation_index = {
        "version": VERSION,
        "profile": config.profile,
        "relations": build_relation_entries(objects, registry),
    }
    return json.dumps(relation_index, indent=2, ensure_ascii=True) + "\n"


def build_relation_entries(objects: list[dict[str, object]], registry: list[dict[str, object]]) -> list[dict[str, object]]:
    source_ids_by_path = {
        item["path"]: item["id"]
        for item in registry
        if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("id"), str)
    }
    relations: list[dict[str, object]] = []
    for obj in objects:
        source_paths = obj.get("source_paths", [])
        if not isinstance(source_paths, list):
            continue
        for source_path in source_paths:
            if source_path not in source_ids_by_path:
                continue
            relations.append(
                {
                    "from": obj["id"],
                    "to": source_ids_by_path[source_path],
                    "type": "derived-from",
                }
            )
    return relations


def build_query_documents(config: ProjectConfig) -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    object_catalog = build_object_catalog(config)
    source_registry = build_source_registry(config)
    for item in object_catalog:
        documents.append(
            {
                "id": str(item.get("id")),
                "entity_type": "object",
                "kind": str(item.get("kind", "object")),
                "title": str(item.get("title", "")),
                "summary": str(item.get("summary", "")),
                "path": str(item.get("path", "")),
                "tags": [str(tag) for tag in item.get("tags", [])] if isinstance(item.get("tags", []), list) else [],
                "adapters": [str(tag) for tag in item.get("adapters", [])] if isinstance(item.get("adapters", []), list) else [],
                "status": normalize_optional_text(item.get("status", "")),
                "date": normalize_optional_text(item.get("date", "")),
            }
        )
    for item in source_registry:
        documents.append(
            {
                "id": str(item.get("id")),
                "entity_type": "source",
                "kind": str(item.get("kind", "source")),
                "title": Path(str(item.get("path", ""))).name,
                "summary": source_summary(config.root / str(item.get("path", ""))) if item.get("exists") else "",
                "path": str(item.get("path", "")),
                "tags": [str(tag) for tag in item.get("adapters", [])] if isinstance(item.get("adapters", []), list) else [],
                "adapters": [str(tag) for tag in item.get("adapters", [])] if isinstance(item.get("adapters", []), list) else [],
                "status": "indexed" if item.get("exists") else "missing",
                "date": "",
            }
        )
    return documents


def query_project_kernel(config: ProjectConfig, args: argparse.Namespace) -> int:
    results = search_kernel(
        config,
        args.q,
        kind=args.kind,
        adapter=args.adapter,
        status=args.status,
        path_prefix=args.path_prefix,
        since=args.since,
        until=args.until,
        timeline=args.timeline,
        limit=args.limit,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "query": args.q,
                    "kind": args.kind,
                    "adapter": args.adapter,
                    "status": args.status,
                    "path_prefix": args.path_prefix,
                    "timeline": args.timeline,
                    "since": args.since,
                    "until": args.until,
                    "results": results,
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0
    print(f"Sula query results for {config.data['project']['name']}: {args.q}")
    if not results:
        print("  No results.")
        return 0
    for result in results:
        date_prefix = f"{result['date']} " if result.get("date") else ""
        status_suffix = f" status={result['status']}" if result.get("status") else ""
        related_suffix = ""
        if result.get("related_kinds"):
            related_suffix = " related=" + ",".join(str(kind_name) for kind_name in result["related_kinds"])
        print(
            "  - "
            f"{date_prefix}[{result['kind']}] score={result['score']}{status_suffix}{related_suffix} "
            f"{result['title']} :: {result['path']}"
        )
    return 0


def search_kernel(
    config: ProjectConfig,
    query: str,
    *,
    kind: str | None,
    adapter: str | None,
    status: str | None,
    path_prefix: str | None,
    since: str | None,
    until: str | None,
    timeline: bool,
    limit: int,
) -> list[dict[str, object]]:
    normalized_query = query.strip().lower()
    query_tokens = tokenize_text(normalized_query)
    object_catalog_path = config.root / ".sula" / "objects" / "catalog.json"
    source_registry_path = config.root / ".sula" / "sources" / "registry.json"
    query_cache_path = config.root / ".sula" / "cache" / "query-index.json"
    sqlite_cache_path = config.root / ".sula" / "cache" / "kernel.db"
    if not object_catalog_path.exists() or not source_registry_path.exists():
        refresh_kernel_state(config, event_type="query.rebuild", summary="Rebuilt kernel state before query.")
    if not query_cache_path.exists():
        refresh_kernel_state(config, event_type="query.cache", summary="Built query cache for local retrieval.")
    if sqlite_cache_path.exists():
        sqlite_results = search_kernel_sqlite(
            sqlite_cache_path,
            normalized_query,
            query_tokens,
            kind=kind,
            adapter=adapter,
            status=status,
            path_prefix=path_prefix,
            since=since,
            until=until,
            timeline=timeline,
            limit=limit,
        )
        if sqlite_results:
            return sqlite_results
    object_catalog = json.loads(object_catalog_path.read_text(encoding="utf-8"))
    source_registry = json.loads(source_registry_path.read_text(encoding="utf-8"))
    query_cache = json.loads(query_cache_path.read_text(encoding="utf-8"))
    shortlisted_ids = shortlist_candidate_ids(query_cache, query_tokens)
    candidates: list[dict[str, object]] = []
    for item in object_catalog.get("objects", []):
        if shortlisted_ids and str(item.get("id")) not in shortlisted_ids:
            continue
        result = score_candidate(
            item,
            normalized_query,
            query_tokens,
            kind=kind,
            adapter=adapter,
            status=status,
            path_prefix=path_prefix,
            since=since,
            until=until,
            allow_empty=timeline,
        )
        if result is not None:
            candidates.append(result)
    for item in source_registry:
        if shortlisted_ids and str(item.get("id")) not in shortlisted_ids:
            continue
        source_candidate = {
            "id": item.get("id"),
            "entity_type": "source",
            "kind": item.get("kind", "source"),
            "title": Path(str(item.get("path", "source"))).name,
            "summary": "",
            "path": item.get("path", ""),
            "tags": item.get("adapters", []),
            "adapters": item.get("adapters", []),
            "status": "indexed" if item.get("exists") else "missing",
            "date": "",
        }
        result = score_candidate(
            source_candidate,
            normalized_query,
            query_tokens,
            kind=kind,
            adapter=adapter,
            status=status,
            path_prefix=path_prefix,
            since=since,
            until=until,
            allow_empty=timeline,
        )
        if result is not None:
            candidates.append(result)
    return finalize_query_results(
        candidates,
        timeline=timeline,
        limit=limit,
        explicit_kind=kind,
        normalized_query=normalized_query,
        query_tokens=query_tokens,
    )


def shortlist_candidate_ids(query_cache: dict[str, object], query_tokens: list[str]) -> set[str]:
    postings = query_cache.get("postings", {})
    if not isinstance(postings, dict) or not query_tokens:
        return set()
    shortlist: set[str] = set()
    for token in query_tokens:
        values = postings.get(token, [])
        if not isinstance(values, list):
            continue
        shortlist.update(str(value) for value in values)
    return shortlist


def score_candidate(
    item: dict[str, object],
    normalized_query: str,
    query_tokens: list[str],
    *,
    kind: str | None,
    adapter: str | None,
    status: str | None,
    path_prefix: str | None,
    since: str | None,
    until: str | None,
    allow_empty: bool,
) -> dict[str, object] | None:
    candidate_kind = str(item.get("kind", "unknown"))
    if kind and candidate_kind != kind:
        return None
    path = str(item.get("path", ""))
    title = str(item.get("title", path or item.get("id", "unknown")))
    summary = str(item.get("summary", ""))
    tags = [str(value) for value in item.get("tags", [])] if isinstance(item.get("tags", []), list) else []
    adapters = [str(value) for value in item.get("adapters", [])] if isinstance(item.get("adapters", []), list) else []
    candidate_status = normalize_optional_text(item.get("status", ""))
    candidate_date = normalize_optional_text(item.get("date", ""))
    entity_type = normalize_optional_text(item.get("entity_type", "object")) or "object"
    if adapter and adapter not in adapters:
        return None
    if status and candidate_status != status:
        return None
    if path_prefix and not path.startswith(path_prefix):
        return None
    if since and (not candidate_date or candidate_date < since):
        return None
    if until and (not candidate_date or candidate_date > until):
        return None
    haystack = " ".join(
        [str(item.get("id", "")), candidate_kind, title, summary, path, " ".join(tags), " ".join(adapters), candidate_status]
    ).lower()
    score = 0
    if normalized_query == str(item.get("id", "")).lower():
        score += 100
    if normalized_query == path.lower():
        score += 90
    if normalized_query and normalized_query in title.lower():
        score += 60
    if normalized_query and normalized_query in path.lower():
        score += 50
    if normalized_query and normalized_query in summary.lower():
        score += 40
    score += entity_type_score_bonus(entity_type)
    score += kind_score_bonus(candidate_kind)
    haystack_tokens = set(tokenize_text(haystack))
    for token in query_tokens:
        if token in haystack_tokens:
            score += 10
    if score <= 0 and not allow_empty:
        return None
    if allow_empty and not normalized_query:
        score = max(score, 1)
    return {
        "id": item.get("id"),
        "kind": candidate_kind,
        "title": title,
        "path": path,
        "summary": summary,
        "score": score,
        "status": candidate_status,
        "date": candidate_date,
        "entity_type": entity_type,
        "family": kind_family(candidate_kind),
    }


def candidate_sort_key(item: dict[str, object], timeline: bool) -> tuple[object, ...]:
    if timeline:
        return (
            str(item.get("date", "")),
            int(item.get("score", 0)),
            entity_type_preference(str(item.get("entity_type", "object"))),
            kind_sort_priority(str(item.get("kind", ""))),
            str(item.get("title", "")),
        )
    return (
        -int(item.get("score", 0)),
        -entity_type_preference(str(item.get("entity_type", "object"))),
        kind_sort_priority(str(item.get("kind", ""))),
        str(item.get("title", "")),
    )


def finalize_query_results(
    candidates: list[dict[str, object]],
    *,
    timeline: bool,
    limit: int,
    explicit_kind: str | None,
    normalized_query: str,
    query_tokens: list[str],
) -> list[dict[str, object]]:
    ordered = sorted(candidates, key=lambda item: candidate_sort_key(item, timeline), reverse=timeline)
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    richer_paths: set[str] = set()
    for item in ordered:
        dedupe_key = query_result_dedupe_key(item)
        if dedupe_key in seen:
            continue
        path = normalize_optional_text(item.get("path", "")).lower()
        kind = normalize_optional_text(item.get("kind", "")).lower()
        if path and path in richer_paths and is_low_signal_kind(kind):
            continue
        seen.add(dedupe_key)
        deduped.append(item)
        if path and not is_low_signal_kind(kind):
            richer_paths.add(path)
    if explicit_kind:
        return deduped[: max(1, limit)]
    return compact_query_result_families(
        deduped,
        timeline=timeline,
        limit=limit,
        normalized_query=normalized_query,
        query_tokens=query_tokens,
    )


def query_result_dedupe_key(item: dict[str, object]) -> str:
    path = normalize_optional_text(item.get("path", "")).lower()
    kind = normalize_optional_text(item.get("kind", "")).lower()
    title = normalize_query_text(normalize_optional_text(item.get("title", "")))
    date_value = normalize_optional_text(item.get("date", ""))
    if kind == "event":
        return f"{kind}|{date_value}|{title}|{path}"
    return f"{kind}|{path}|{title}"


def normalize_query_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def compact_query_result_families(
    candidates: list[dict[str, object]],
    *,
    timeline: bool,
    limit: int,
    normalized_query: str,
    query_tokens: list[str],
) -> list[dict[str, object]]:
    intent_weights = family_intent_weights(normalized_query, query_tokens)
    grouped: dict[str, list[dict[str, object]]] = {}
    passthrough: list[dict[str, object]] = []
    for item in candidates:
        path = normalize_optional_text(item.get("path", ""))
        kind = normalize_optional_text(item.get("kind", ""))
        if not path or kind == "event":
            passthrough.append(item)
            continue
        grouped.setdefault(path, []).append(item)

    compacted: list[dict[str, object]] = []
    for path, items in grouped.items():
        if len(items) == 1:
            compacted.append(items[0])
            continue
        representatives = choose_family_representatives(items, intent_weights=intent_weights, timeline=timeline)
        primary = choose_path_primary(representatives, intent_weights=intent_weights, timeline=timeline)
        related_kinds = sorted(
            {
                normalize_optional_text(item.get("kind", ""))
                for item in representatives
                if item is not primary and normalize_optional_text(item.get("kind", ""))
            }
        )
        if related_kinds:
            primary = dict(primary)
            primary["related_kinds"] = related_kinds
            primary["related_count"] = len(related_kinds)
        compacted.append(primary)

    combined = passthrough + compacted
    combined.sort(key=lambda item: candidate_sort_key(item, timeline), reverse=timeline)
    return combined[: max(1, limit)]


def choose_family_representatives(
    items: list[dict[str, object]],
    *,
    intent_weights: dict[str, int],
    timeline: bool,
) -> list[dict[str, object]]:
    best_by_family: dict[str, dict[str, object]] = {}
    for item in items:
        family = normalize_optional_text(item.get("family", kind_family(normalize_optional_text(item.get("kind", "")))))
        current = best_by_family.get(family)
        if current is None or path_primary_sort_key(item, intent_weights=intent_weights, timeline=timeline) > path_primary_sort_key(
            current,
            intent_weights=intent_weights,
            timeline=timeline,
        ):
            best_by_family[family] = item
    return list(best_by_family.values())


def choose_path_primary(
    items: list[dict[str, object]],
    *,
    intent_weights: dict[str, int],
    timeline: bool,
) -> dict[str, object]:
    return max(items, key=lambda item: path_primary_sort_key(item, intent_weights=intent_weights, timeline=timeline))


def path_primary_sort_key(
    item: dict[str, object],
    *,
    intent_weights: dict[str, int],
    timeline: bool,
) -> tuple[object, ...]:
    family = normalize_optional_text(item.get("family", kind_family(normalize_optional_text(item.get("kind", "")))))
    return (
        intent_weights.get(family, 0),
        int(item.get("score", 0)),
        entity_type_preference(normalize_optional_text(item.get("entity_type", "object"))),
        -kind_sort_priority(normalize_optional_text(item.get("kind", ""))),
        normalize_optional_text(item.get("date", "")) if timeline else "",
        normalize_optional_text(item.get("title", "")),
    )


def family_intent_weights(normalized_query: str, query_tokens: list[str]) -> dict[str, int]:
    weights = {
        "state": 1,
        "execution": 1,
        "governance": 1,
        "business": 1,
        "record": 1,
        "source": 0,
        "event": 0,
    }
    token_set = set(query_tokens)
    lowered = normalized_query.lower()
    if token_set & {"contract", "agreement", "msa", "sow", "legal", "vendor", "supplier", "staffing", "people", "person"}:
        weights["business"] += 6
    if token_set & {"decision", "decide", "why", "risk", "blocker", "policy"}:
        weights["governance"] += 6
    if token_set & {"task", "todo", "next", "milestone", "review", "deliver"}:
        weights["execution"] += 6
    if token_set & {"change", "release", "incident", "history", "record", "rollback", "deploy"}:
        weights["record"] += 6
    if token_set & {"status", "state", "summary", "health", "progress"}:
        weights["state"] += 6
    if token_set & {"readme", "document", "docs", "code", "config", "file"}:
        weights["source"] += 4
    if "contract" in lowered and "change" not in lowered:
        weights["business"] += 2
    return weights


def entity_type_score_bonus(entity_type: str) -> int:
    bonuses = {
        "object": 6,
        "event": 4,
        "source": 0,
    }
    return bonuses.get(entity_type, 0)


def kind_family(kind: str) -> str:
    families = {
        "project": "state",
        "state": "state",
        "task": "execution",
        "milestone": "execution",
        "decision": "governance",
        "risk": "governance",
        "agreement": "business",
        "person": "business",
        "change": "record",
        "release": "record",
        "incident": "record",
        "event": "event",
        "document": "source",
        "code": "source",
        "config": "source",
        "interface": "source",
        "file": "source",
        "repo": "source",
        "source": "source",
    }
    return families.get(kind, "source")


def kind_score_bonus(kind: str) -> int:
    bonuses = {
        "project": 8,
        "state": 7,
        "task": 6,
        "decision": 6,
        "risk": 6,
        "person": 5,
        "agreement": 5,
        "milestone": 5,
        "change": 4,
        "release": 4,
        "incident": 4,
        "event": 3,
        "document": 1,
        "code": 1,
        "config": 1,
    }
    return bonuses.get(kind, 0)


def entity_type_preference(entity_type: str) -> int:
    preferences = {
        "object": 3,
        "event": 2,
        "source": 1,
    }
    return preferences.get(entity_type, 0)


def kind_sort_priority(kind: str) -> int:
    priorities = {
        "project": 0,
        "state": 1,
        "task": 2,
        "decision": 3,
        "risk": 4,
        "agreement": 5,
        "milestone": 6,
        "person": 7,
        "change": 8,
        "release": 9,
        "incident": 10,
        "event": 11,
        "document": 12,
        "code": 13,
        "config": 14,
    }
    return priorities.get(kind, 99)


def is_low_signal_kind(kind: str) -> bool:
    return kind in {"document", "code", "config", "interface", "file", "repo", "source"}


def rebuild_kernel_sqlite_cache(config: ProjectConfig) -> None:
    kernel_root = config.root / ".sula"
    object_catalog = json.loads((kernel_root / "objects" / "catalog.json").read_text(encoding="utf-8"))
    source_registry = json.loads((kernel_root / "sources" / "registry.json").read_text(encoding="utf-8"))
    relation_index = json.loads((kernel_root / "indexes" / "relations.json").read_text(encoding="utf-8"))
    documents = build_query_documents(config)
    events = read_kernel_events(kernel_root / "events" / "log.jsonl")
    db_path = kernel_root / "cache" / "kernel.db"
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.executescript(
            """
            DROP TABLE IF EXISTS sources;
            DROP TABLE IF EXISTS objects;
            DROP TABLE IF EXISTS relations;
            DROP TABLE IF EXISTS events;
            DROP TABLE IF EXISTS documents;
            CREATE TABLE sources (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                path TEXT NOT NULL,
                exists_flag INTEGER NOT NULL,
                source_of_truth INTEGER NOT NULL,
                discovered INTEGER NOT NULL,
                summary TEXT,
                adapters_json TEXT,
                anchor_strategy TEXT,
                size_bytes INTEGER
            );
            CREATE TABLE objects (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                status TEXT,
                path TEXT,
                date_value TEXT,
                adapters_json TEXT,
                tags_json TEXT,
                source_paths_json TEXT
            );
            CREATE TABLE relations (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL
            );
            CREATE TABLE events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                profile TEXT,
                project TEXT
            );
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                path TEXT,
                status TEXT,
                date_value TEXT,
                tags_text TEXT,
                adapters_text TEXT,
                searchable_text TEXT NOT NULL
            );
            CREATE INDEX idx_sources_kind_path ON sources(kind, path);
            CREATE INDEX idx_objects_kind_status_path ON objects(kind, status, path);
            CREATE INDEX idx_objects_date ON objects(date_value);
            CREATE INDEX idx_relations_source ON relations(source_id);
            CREATE INDEX idx_relations_target ON relations(target_id);
            CREATE INDEX idx_events_timestamp ON events(timestamp);
            CREATE INDEX idx_documents_kind_status_path ON documents(kind, status, path);
            CREATE INDEX idx_documents_date ON documents(date_value);
            """
        )
        for item in source_registry:
            cursor.execute(
                """
                INSERT INTO sources (
                    id, kind, path, exists_flag, source_of_truth, discovered, summary, adapters_json, anchor_strategy, size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.get("id", "")),
                    str(item.get("kind", "source")),
                    str(item.get("path", "")),
                    1 if item.get("exists") else 0,
                    1 if item.get("source_of_truth") else 0,
                    1 if item.get("discovered") else 0,
                    source_summary(config.root / str(item.get("path", ""))) if item.get("exists") else "",
                    json.dumps(item.get("adapters", []), ensure_ascii=True),
                    str(item.get("anchor_strategy", "")),
                    int(item.get("size_bytes", 0) or 0),
                ),
            )
        for item in object_catalog.get("objects", []):
            cursor.execute(
                """
                INSERT INTO objects (
                    id, kind, title, summary, status, path, date_value, adapters_json, tags_json, source_paths_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.get("id", "")),
                    str(item.get("kind", "object")),
                    str(item.get("title", "")),
                    str(item.get("summary", "")),
                    str(item.get("status", "")),
                    str(item.get("path", "")),
                    str(item.get("date", "") or ""),
                    json.dumps(item.get("adapters", []), ensure_ascii=True),
                    json.dumps(item.get("tags", []), ensure_ascii=True),
                    json.dumps(item.get("source_paths", []), ensure_ascii=True),
                ),
            )
        for item in relation_index.get("relations", []):
            cursor.execute(
                "INSERT INTO relations (source_id, target_id, relation_type) VALUES (?, ?, ?)",
                (str(item.get("from", "")), str(item.get("to", "")), str(item.get("type", ""))),
            )
        for item in events:
            cursor.execute(
                "INSERT INTO events (timestamp, event_type, summary, profile, project) VALUES (?, ?, ?, ?, ?)",
                (
                    str(item.get("timestamp", "")),
                    str(item.get("event_type", "")),
                    str(item.get("summary", "")),
                    str(item.get("profile", "")),
                    str(item.get("project", "")),
                ),
            )
        for item in documents:
            cursor.execute(
                """
                INSERT INTO documents (
                    doc_id, entity_type, kind, title, summary, path, status, date_value, tags_text, adapters_text, searchable_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.get("id", "")),
                    str(item.get("entity_type", "object")),
                    str(item.get("kind", "object")),
                    str(item.get("title", "")),
                    str(item.get("summary", "")),
                    str(item.get("path", "")),
                    str(item.get("status", "")),
                    str(item.get("date", "") or ""),
                    " ".join(str(tag) for tag in item.get("tags", [])),
                    " ".join(str(adapter) for adapter in item.get("adapters", [])),
                    " ".join(
                        [
                            str(item.get("id", "")),
                            str(item.get("kind", "")),
                            str(item.get("title", "")),
                            str(item.get("summary", "")),
                            str(item.get("path", "")),
                            " ".join(str(tag) for tag in item.get("tags", [])),
                            " ".join(str(adapter) for adapter in item.get("adapters", [])),
                            str(item.get("status", "")),
                            str(item.get("date", "")),
                        ]
                    ).lower(),
                ),
            )
        for item in events:
            cursor.execute(
                """
                INSERT INTO documents (
                    doc_id, entity_type, kind, title, summary, path, status, date_value, tags_text, adapters_text, searchable_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"event:{item.get('timestamp', '')}:{item.get('event_type', '')}",
                    "event",
                    "event",
                    str(item.get("event_type", "")),
                    str(item.get("summary", "")),
                    ".sula/events/log.jsonl",
                    "recorded",
                    str(item.get("timestamp", "")),
                    "event kernel",
                    "generic-project memory",
                    " ".join(
                        [
                            str(item.get("event_type", "")),
                            str(item.get("summary", "")),
                            str(item.get("profile", "")),
                            str(item.get("project", "")),
                        ]
                    ).lower(),
                ),
            )
        connection.commit()


def read_kernel_events(event_log_path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    if not event_log_path.exists():
        return events
    for raw_line in event_log_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def detect_document_entity_type(document_id: str) -> str:
    if document_id.startswith("source:") or document_id in {"project-manifest", "status", "change-records", "agents", "readme", "app-shell", "api-layer", "kernel-state", "memory-digest", "git-repository"}:
        return "source"
    return "object"


def search_kernel_sqlite(
    db_path: Path,
    normalized_query: str,
    query_tokens: list[str],
    *,
    kind: str | None,
    adapter: str | None,
    status: str | None,
    path_prefix: str | None,
    since: str | None,
    until: str | None,
    timeline: bool,
    limit: int,
) -> list[dict[str, object]]:
    where_clauses = ["1 = 1"]
    parameters: list[object] = []
    if kind:
        where_clauses.append("kind = ?")
        parameters.append(kind)
    if adapter:
        where_clauses.append("instr(adapters_text, ?) > 0")
        parameters.append(adapter)
    if status:
        where_clauses.append("status = ?")
        parameters.append(status)
    if path_prefix:
        where_clauses.append("path LIKE ?")
        parameters.append(f"{path_prefix}%")
    if since:
        where_clauses.append("date_value >= ?")
        parameters.append(since)
    if until:
        where_clauses.append("date_value <= ?")
        parameters.append(until)
    if timeline:
        where_clauses.append("date_value != ''")
    if normalized_query:
        search_terms = [normalized_query] + [token for token in query_tokens if token != normalized_query]
        search_clauses = []
        for term in search_terms:
            search_clauses.append("searchable_text LIKE ?")
            parameters.append(f"%{term}%")
        where_clauses.append("(" + " OR ".join(search_clauses) + ")")
    sql = (
        "SELECT doc_id, entity_type, kind, title, summary, path, status, date_value "
        "FROM documents WHERE "
        + " AND ".join(where_clauses)
    )
    if timeline:
        sql += " ORDER BY date_value DESC, kind ASC, title ASC LIMIT ?"
    else:
        sql += " LIMIT ?"
    parameters.append(max(limit * 8, 40))
    results: list[dict[str, object]] = []
    with sqlite3.connect(db_path) as connection:
        for row in connection.execute(sql, parameters):
            candidate = {
                "id": row[0],
                "entity_type": row[1],
                "kind": row[2],
                "title": row[3],
                "summary": row[4],
                "path": row[5],
                "status": row[6],
                "date": row[7],
                "tags": [],
                "adapters": [],
            }
            result = score_candidate(
                candidate,
                normalized_query,
                query_tokens,
                kind=kind,
                adapter=None,
                status=None,
                path_prefix=None,
                since=None,
                until=None,
                allow_empty=timeline,
            )
            if result is not None:
                results.append(result)
    return finalize_query_results(
        results,
        timeline=timeline,
        limit=limit,
        explicit_kind=kind,
        normalized_query=normalized_query,
        query_tokens=query_tokens,
    )


def tokenize_text(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


def normalize_optional_text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def project_status(config: ProjectConfig, args: argparse.Namespace) -> int:
    payload = project_status_payload(config)
    if json_output_requested(args):
        emit_json({"command": "status", "status": "ok", "project": project_payload(config), "state": payload})
        return 0
    print(f"Sula status for {config.data['project']['name']}")
    print(f"  Profile: {config.profile}")
    print(f"  Workflow: {config.workflow_pack} ({config.workflow_stage})")
    print(f"  Storage: {config.storage_provider} [{config.storage_sync_mode}]")
    print(f"  Summary: {payload['summary']}")
    print(f"  Health: {payload['health']}")
    print(f"  Open tasks: {payload['counts']['open_tasks']}")
    print(f"  Open risks: {payload['counts']['open_risks']}")
    print(f"  Artifacts: {payload['counts']['artifacts']}")
    if payload["recent_events"]:
        print("  Recent events:")
        for item in payload["recent_events"]:
            print(f"    - {item['timestamp']} {item['event_type']}: {item['summary']}")
    return 0


def project_status_payload(config: ProjectConfig) -> dict[str, object]:
    kernel_root = config.root / ".sula"
    if not (kernel_root / "objects" / "catalog.json").exists():
        refresh_kernel_state(config, event_type="status.rebuild", summary="Rebuilt kernel state for status command.")
    state_path = kernel_root / "state" / "current.md"
    state_sections = markdown_sections(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    object_catalog = load_json_file(kernel_root / "objects" / "catalog.json", default={"objects": []})
    objects = object_catalog.get("objects", []) if isinstance(object_catalog, dict) else []
    artifact_catalog = load_artifact_catalog(config)
    recent_events = read_kernel_events(kernel_root / "events" / "log.jsonl")[-5:]
    open_tasks = [item for item in objects if isinstance(item, dict) and item.get("kind") == "task" and item.get("status") in {"open", "planned"}]
    open_risks = [item for item in objects if isinstance(item, dict) and item.get("kind") == "risk" and item.get("status") in {"open", "watch", "incident"}]
    milestones = [item for item in objects if isinstance(item, dict) and item.get("kind") == "milestone"]
    return {
        "summary": state_sections.get("Summary", "_missing_"),
        "health": state_sections.get("Health", "_missing_"),
        "current_focus": markdown_bullet_items(state_sections.get("Current Focus", "")),
        "blockers": markdown_bullet_items(state_sections.get("Blockers", "")),
        "recent_decisions": markdown_bullet_items(state_sections.get("Recent Decisions", "")),
        "next_review": markdown_key_values(state_sections.get("Next Review", "")),
        "workflow": {
            "pack": config.workflow_pack,
            "stage": config.workflow_stage,
            "artifacts_root": config.artifacts_root.relative_to(config.root).as_posix() if config.artifacts_root.is_relative_to(config.root) else str(config.artifacts_root),
        },
        "storage": {
            "provider": config.storage_provider,
            "sync_mode": config.storage_sync_mode,
            "workspace_root": str(config.storage_workspace_root),
            "provider_root_url": config.provider_root_url,
            "provider_root_id": config.provider_root_id,
        },
        "counts": {
            "open_tasks": len(open_tasks),
            "open_risks": len(open_risks),
            "milestones": len(milestones),
            "artifacts": len(artifact_catalog.get("artifacts", [])),
            "sources": len(load_json_file(kernel_root / "sources" / "registry.json", default=[])),
        },
        "recent_events": recent_events,
    }


def handle_artifact_command(config: ProjectConfig, args: argparse.Namespace) -> int:
    if args.artifact_command == "create":
        return artifact_create(config, args)
    if args.artifact_command == "register":
        return artifact_register(config, args)
    if args.artifact_command == "locate":
        return artifact_locate(config, args)
    raise AssertionError("unreachable")


def artifact_create(config: ProjectConfig, args: argparse.Namespace) -> int:
    ensure_artifact_catalog(config)
    record_date = normalize_record_date(args.date)
    artifact_kind = args.kind.lower()
    slot = artifact_slot_for_kind(config, artifact_kind, args.slot)
    extension = args.extension if args.extension.startswith(".") else f".{args.extension}"
    slug = sanitize_slug(args.slug or args.title)
    target_dir = config.artifacts_root / slot
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{record_date}-{slug}{extension}"
    if output_path.exists():
        raise SystemExit(f"Artifact already exists: {output_path}")
    summary = args.summary.strip() or f"{artifact_kind} artifact for {config.data['project']['name']}"
    output_path.write_text(render_artifact_template(config, artifact_kind, args.title, summary, record_date, slot), encoding="utf-8")
    entry = register_artifact_entry(
        config,
        path=output_path.relative_to(config.root).as_posix(),
        artifact_kind=artifact_kind,
        title=args.title,
        slot=slot,
        summary=summary,
        date_value=record_date,
    )
    refresh_kernel_state(config, event_type="artifact.create", summary=f"Created {artifact_kind} artifact `{args.title}`.")
    if json_output_requested(args):
        emit_json({"command": "artifact.create", "status": "ok", "project": project_payload(config), "artifact": entry})
        return 0
    print(f"Created {artifact_kind} artifact at {output_path}")
    return 0


def artifact_register(config: ProjectConfig, args: argparse.Namespace) -> int:
    ensure_artifact_catalog(config)
    relative_path = args.path.strip()
    path = config.root / relative_path
    if not path.exists():
        raise SystemExit(f"Artifact path does not exist: {path}")
    slot = artifact_slot_for_kind(config, args.kind.lower(), args.slot)
    entry = register_artifact_entry(
        config,
        path=relative_path,
        artifact_kind=args.kind.lower(),
        title=args.title or path.name,
        slot=slot,
        summary=args.summary.strip() or source_summary(path),
        date_value=detect_source_date(path, source_summary(path)),
    )
    refresh_kernel_state(config, event_type="artifact.register", summary=f"Registered artifact `{entry['title']}`.")
    if json_output_requested(args):
        emit_json({"command": "artifact.register", "status": "ok", "project": project_payload(config), "artifact": entry})
        return 0
    print(f"Registered artifact {relative_path}")
    return 0


def artifact_locate(config: ProjectConfig, args: argparse.Namespace) -> int:
    catalog = load_artifact_catalog(config)
    results: list[dict[str, object]] = []
    query = args.q.strip().lower()
    for item in catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        if args.kind and str(item.get("kind")) != args.kind:
            continue
        haystack = " ".join(
            [
                str(item.get("id", "")),
                str(item.get("kind", "")),
                str(item.get("title", "")),
                str(item.get("slot", "")),
                str(item.get("path", "")),
                str(item.get("summary", "")),
            ]
        ).lower()
        if query and query not in haystack:
            continue
        results.append(item)
    results.sort(key=lambda item: (str(item.get("date", "")), str(item.get("kind", "")), str(item.get("title", ""))), reverse=True)
    results = results[: max(1, args.limit)]
    if json_output_requested(args):
        emit_json({"command": "artifact.locate", "status": "ok", "project": project_payload(config), "results": results})
        return 0
    print(f"Artifacts for {config.data['project']['name']}:")
    if not results:
        print("  No artifacts.")
        return 0
    for item in results:
        print(f"  - [{item['kind']}] {item['title']} :: {item['path']} ({item['slot']})")
    return 0


def register_artifact_entry(
    config: ProjectConfig,
    *,
    path: str,
    artifact_kind: str,
    title: str,
    slot: str,
    summary: str,
    date_value: str | None,
) -> dict[str, object]:
    catalog = load_artifact_catalog(config)
    artifact_id = f"artifact:{sanitize_source_id(path)}"
    entry = {
        "id": artifact_id,
        "kind": artifact_kind,
        "title": title,
        "slot": slot,
        "path": path,
        "summary": summary,
        "date": date_value or "",
        "status": "active",
        "workflow_pack": config.workflow_pack,
        "storage_provider": config.storage_provider,
        "storage_sync_mode": config.storage_sync_mode,
        "provider_root_url": config.provider_root_url,
        "provider_root_id": config.provider_root_id,
    }
    artifacts = [item for item in catalog.get("artifacts", []) if isinstance(item, dict) and item.get("id") != artifact_id]
    artifacts.append(entry)
    artifacts.sort(key=lambda item: (str(item.get("date", "")), str(item.get("path", ""))))
    catalog["version"] = VERSION
    catalog["artifacts"] = artifacts
    write_artifact_catalog(config, catalog)
    return entry


def render_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Metadata",
        "",
        f"- date: {record_date}",
        f"- kind: {artifact_kind}",
        f"- project: {config.data['project']['name']}",
        f"- workflow pack: {config.workflow_pack}",
        f"- workflow slot: {slot}",
        f"- storage provider: {config.storage_provider}",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Details",
        "",
        "- _fill in details_",
        "",
    ]
    return "\n".join(lines)


def handle_portfolio_command(args: argparse.Namespace) -> int:
    portfolio_root = resolve_portfolio_root(getattr(args, "portfolio_root", None))
    if args.portfolio_command == "register":
        assert hasattr(args, "project_root")
        config = load_manifest(Path(args.project_root).expanduser().resolve())
        registry = load_portfolio_registry(portfolio_root)
        entry = summarize_project_for_portfolio(config)
        projects = [item for item in registry.get("projects", []) if isinstance(item, dict) and item.get("root") != entry["root"]]
        projects.append(entry)
        projects.sort(key=lambda item: (str(item.get("workspace", "")), str(item.get("name", ""))))
        registry["version"] = VERSION
        registry["projects"] = projects
        write_portfolio_registry(portfolio_root, registry)
        if json_output_requested(args):
            emit_json({"command": "portfolio.register", "status": "ok", "portfolio_root": str(portfolio_root), "project": entry})
            return 0
        print(f"Registered {entry['name']} in portfolio {portfolio_root}")
        return 0
    if args.portfolio_command == "list":
        registry = load_portfolio_registry(portfolio_root)
        if json_output_requested(args):
            emit_json({"command": "portfolio.list", "status": "ok", "portfolio_root": str(portfolio_root), "projects": registry.get("projects", [])})
            return 0
        print(f"Sula portfolio at {portfolio_root}")
        for item in registry.get("projects", []):
            print(f"  - {item['name']} [{item['workflow_pack']}] :: {item['root']}")
        return 0
    if args.portfolio_command == "status":
        registry = load_portfolio_registry(portfolio_root)
        projects = registry.get("projects", [])
        payload = {
            "portfolio_root": str(portfolio_root),
            "project_count": len(projects),
            "providers": sorted({str(item.get('storage_provider', 'local-fs')) for item in projects if isinstance(item, dict)}),
            "workspaces": sorted({str(item.get('workspace', 'personal')) for item in projects if isinstance(item, dict)}),
            "projects": projects,
        }
        if json_output_requested(args):
            emit_json({"command": "portfolio.status", "status": "ok", **payload})
            return 0
        print(f"Portfolio status for {portfolio_root}")
        print(f"  Projects: {payload['project_count']}")
        print(f"  Providers: {', '.join(payload['providers']) if payload['providers'] else 'none'}")
        return 0
    if args.portfolio_command == "query":
        registry = load_portfolio_registry(portfolio_root)
        results: list[dict[str, object]] = []
        for item in registry.get("projects", []):
            if not isinstance(item, dict) or not isinstance(item.get("root"), str):
                continue
            project_root = Path(item["root"])
            manifest_path = project_root / MANIFEST_PATH
            if not manifest_path.exists():
                continue
            config = load_manifest(project_root)
            for result in search_kernel(
                config,
                args.q,
                kind=args.kind,
                adapter=args.adapter,
                status=args.status,
                path_prefix=args.path_prefix,
                since=args.since,
                until=args.until,
                timeline=args.timeline,
                limit=max(args.limit, 20),
            ):
                merged = dict(result)
                merged["project_name"] = config.data["project"]["name"]
                merged["project_slug"] = config.data["project"]["slug"]
                merged["project_root"] = str(config.root)
                results.append(merged)
        results.sort(key=lambda item: (-int(item.get("score", 0)), str(item.get("project_name", "")), str(item.get("title", ""))))
        results = results[: max(1, args.limit)]
        if json_output_requested(args):
            emit_json({"command": "portfolio.query", "status": "ok", "portfolio_root": str(portfolio_root), "results": results})
            return 0
        print(f"Portfolio query results for {portfolio_root}: {args.q}")
        for item in results:
            print(f"  - {item['project_name']} [{item['kind']}] {item['title']} :: {item['path']}")
        if not results:
            print("  No results.")
        return 0
    raise AssertionError("unreachable")


def summarize_project_for_portfolio(config: ProjectConfig) -> dict[str, object]:
    payload = project_status_payload(config)
    return {
        "name": config.data["project"]["name"],
        "slug": config.data["project"]["slug"],
        "root": str(config.root),
        "profile": config.profile,
        "workflow_pack": config.workflow_pack,
        "workflow_stage": config.workflow_stage,
        "storage_provider": config.storage_provider,
        "storage_sync_mode": config.storage_sync_mode,
        "workspace": config.portfolio_setting("workspace", "personal"),
        "portfolio_id": config.portfolio_setting("portfolio_id", "default"),
        "owner": config.portfolio_setting("owner", "n/a"),
        "summary": payload["summary"],
        "health": payload["health"],
        "last_activity": payload["recent_events"][-1]["timestamp"] if payload["recent_events"] else "",
    }


def load_json_file(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def render_export_catalog(config: ProjectConfig) -> str:
    exports = {
        "version": VERSION,
        "exports": [
            {"path": config.data["paths"]["status_file"], "kind": "status", "project_owned": True},
            {"path": config.data["paths"]["change_records_file"], "kind": "change-index", "project_owned": True},
            {"path": config.memory_setting("digest_file", ".sula/memory-digest.md"), "kind": "memory-digest", "project_owned": False},
        ],
    }
    return json.dumps(exports, indent=2, ensure_ascii=True) + "\n"


def remove_sula(project_root: Path, args: argparse.Namespace) -> int:
    report = inspect_removal(project_root)
    if json_output_requested(args):
        if not args.approve:
            emit_json({"command": "remove", "status": "report", "report": removal_report_payload(report)})
            return 0
        if report.blockers:
            emit_json({"command": "remove", "status": "blocked", "report": removal_report_payload(report)})
            return 1
        apply_removal(report)
        emit_json({"command": "remove", "status": "ok", "report": removal_report_payload(report)})
        return 0
    print_removal_report(report)
    if not args.approve:
        return 0
    if report.blockers:
        print("Removal was not applied because blocking issues remain.")
        return 1
    apply_removal(report)
    print(f"Sula removal completed for {project_root}")
    return 0


def inspect_removal(project_root: Path) -> RemovalReport:
    blockers: list[str] = []
    warnings: list[str] = []
    if not project_root.exists():
        raise SystemExit(f"Project root does not exist: {project_root}")
    manifest_path = project_root / MANIFEST_PATH
    if not manifest_path.exists():
        blockers.append("repository does not have `.sula/project.toml`; nothing to remove")
        return RemovalReport(project_root, None, blockers, warnings, [], [], [])

    config = load_manifest(project_root)
    managed_paths = sorted(
        {
            action.output_path
            for action in collect_render_actions(config, include_scaffold=False)
            if action.output_path.exists() and not action.output_path.is_relative_to(project_root / ".sula")
        },
        key=lambda path: path.as_posix(),
    )
    scaffold_paths = sorted(
        {
            action.output_path
            for action in collect_render_actions(config, include_scaffold=True)
            if not action.overwrite and action.output_path.exists()
        },
        key=lambda path: path.as_posix(),
    )
    kernel_root = project_root / ".sula"
    if not kernel_root.exists():
        warnings.append("`.sula/` is already missing; only managed files can be removed")
    return RemovalReport(
        project_root=project_root,
        config=config,
        blockers=blockers,
        warnings=warnings,
        kernel_remove_paths=[kernel_root] if kernel_root.exists() else [],
        managed_remove_paths=managed_paths,
        scaffold_preserve_paths=scaffold_paths,
    )


def print_removal_report(report: RemovalReport) -> None:
    print(f"Sula removal report for {report.project_root}")
    if report.config is not None:
        print(f"Active profile: {report.config.profile}")
    if report.blockers:
        print("Blocking issues:")
        for item in report.blockers:
            print(f"  - {item}")
    if report.warnings:
        print("Warnings:")
        for item in report.warnings:
            print(f"  - {item}")
    print("Planned changes after approval:")
    print(f"  - kernel remove: {len(report.kernel_remove_paths)}")
    print(f"  - managed remove: {len(report.managed_remove_paths)}")
    print(f"  - scaffold preserve: {len(report.scaffold_preserve_paths)}")
    for path in report.kernel_remove_paths[:4]:
        print(f"    remove kernel: {path.relative_to(report.project_root).as_posix()}")
    for path in report.managed_remove_paths[:8]:
        print(f"    remove managed: {path.relative_to(report.project_root).as_posix()}")
    for path in report.scaffold_preserve_paths[:8]:
        print(f"    preserve scaffold: {path.relative_to(report.project_root).as_posix()}")
    print("Approval flow:")
    print("  1. Review this report.")
    print("  2. Re-run the same command with `--approve` to apply the removal.")


def apply_removal(report: RemovalReport) -> None:
    for path in report.managed_remove_paths:
        if path.exists():
            path.unlink()
            remove_empty_parent_dirs(path.parent, report.project_root)
    for path in report.kernel_remove_paths:
        if path.exists():
            shutil.rmtree(path)


def remove_empty_parent_dirs(start: Path, stop_root: Path) -> None:
    current = start
    while current != stop_root:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def core_managed_dir() -> Path:
    return SULA_ROOT / "templates/core/managed"


def core_scaffold_dir() -> Path:
    return SULA_ROOT / "templates/core/scaffold"


def profile_template_dir(profile: str) -> Path:
    return SULA_ROOT / "templates/profiles" / profile


def profile_managed_dir(profile: str) -> Path:
    return profile_template_dir(profile) / "managed"


def profile_scaffold_dir(profile: str) -> Path:
    return profile_template_dir(profile) / "scaffold"


if __name__ == "__main__":
    sys.exit(main())
