#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys


SULA_ROOT = Path(__file__).resolve().parent.parent
VERSION = (SULA_ROOT / "VERSION").read_text(encoding="utf-8").strip()
MANIFEST_PATH = Path(".sula/project.toml")
LOCK_PATH = Path(".sula/version.lock")

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
    }
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
            "SULA_VERSION": VERSION,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sula project operating system manager")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create manifest if missing and render managed/scaffold files")
    add_project_root_arg(init_cmd)
    init_cmd.add_argument("--name")
    init_cmd.add_argument("--slug")
    init_cmd.add_argument("--description")
    init_cmd.add_argument("--profile", default="react-frontend-erpnext")

    sync_cmd = sub.add_parser("sync", help="Sync managed files from Sula into a project")
    add_project_root_arg(sync_cmd)
    sync_cmd.add_argument("--dry-run", action="store_true", help="Show the managed-file sync plan without writing")

    adopt_cmd = sub.add_parser("adopt", help="Inspect, report, and apply Sula adoption for a repository")
    add_project_root_arg(adopt_cmd)
    adopt_cmd.add_argument("--profile", help="Profile to use when auto-detection is insufficient")
    adopt_cmd.add_argument("--name", help="Override the detected project name")
    adopt_cmd.add_argument("--slug", help="Override the detected project slug")
    adopt_cmd.add_argument("--description", help="Override the detected project description")
    adopt_cmd.add_argument("--approve", action="store_true", help="Apply the adoption plan after reporting it")

    doctor_cmd = sub.add_parser("doctor", help="Check manifest, lockfile, and managed files")
    add_project_root_arg(doctor_cmd)
    doctor_cmd.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings such as manifest references that do not exist in the project",
    )

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

    memory_cmd = sub.add_parser("memory", help="Generate a single-project memory digest")
    memory_sub = memory_cmd.add_subparsers(dest="memory_command", required=True)
    memory_digest_cmd = memory_sub.add_parser("digest", help="Generate the project memory digest")
    add_project_root_arg(memory_digest_cmd)
    memory_digest_cmd.add_argument("--output", help="Optional output path relative to the project root")
    memory_digest_cmd.add_argument("--stdout", action="store_true", help="Print the digest instead of writing it")

    return parser.parse_args()


def add_project_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", required=True, help="Path to the target project root")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()

    if args.command == "init":
        config = ensure_manifest(project_root, args)
        apply_actions(collect_render_actions(config, include_scaffold=True))
        write_lockfile(config)
        print(f"Initialized Sula for {config.data['project']['name']} at {project_root}")
        return 0

    if args.command == "adopt":
        return adopt(project_root, args)

    config = load_manifest(project_root)
    if args.command == "sync":
        actions = collect_render_actions(config, include_scaffold=False)
        if args.dry_run:
            print_sync_plan(config, actions)
            return 0
        apply_actions(actions)
        write_lockfile(config)
        print(f"Synchronized managed files for {config.data['project']['name']}")
        return 0

    if args.command == "doctor":
        return doctor(config, strict=args.strict)

    if args.command == "record":
        if args.record_command == "new":
            return create_record(config, args)
        raise AssertionError("unreachable")

    if args.command == "memory":
        if args.memory_command == "digest":
            return generate_memory_digest(config, args)
        raise AssertionError("unreachable")

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
        "memory": {
            "change_record_directory": "docs/change-records",
            "release_record_directory": "docs/releases",
            "incident_record_directory": "docs/incidents",
            "digest_file": ".sula/memory-digest.md",
            "status_max_age_days": 30,
        },
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
    ]:
        lines.append(f"[{section_name}]")
        for key, value in manifest[section_name].items():
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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


def adopt(project_root: Path, args: argparse.Namespace) -> int:
    report = inspect_adoption(project_root, args)
    print_adoption_report(report)
    if not args.approve:
        return 0
    if report.blockers:
        print("Adoption was not applied because blocking issues remain.")
        return 1
    return apply_adoption(report)


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
    if profile is None:
        blockers.append("could not determine a Sula profile automatically; rerun with `--profile`")

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
    raise SystemExit(f"Unsupported profile for adoption: {profile}")


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
    }


def default_memory_config() -> dict:
    return {
        "change_record_directory": "docs/change-records",
        "release_record_directory": "docs/releases",
        "incident_record_directory": "docs/incidents",
        "digest_file": ".sula/memory-digest.md",
        "status_max_age_days": 30,
    }


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
    return None


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


def detect_repository_url(project_root: Path) -> str | None:
    result = run_git(project_root, ["remote", "get-url", "origin"])
    if result is None or result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def apply_adoption(report: AdoptionReport) -> int:
    assert report.config_data is not None
    config = ProjectConfig(root=report.project_root, data=report.config_data)
    manifest_path = config.root / MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(render_manifest(report.config_data), encoding="utf-8")
    apply_actions(report.actions)
    write_lockfile(config)
    finalize_adoption_traceability(config)
    generate_memory_digest(config, argparse.Namespace(output=None, stdout=False))
    print("Post-adoption validation:")
    doctor_exit = doctor(config, strict=True)
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


def generate_memory_digest(config: ProjectConfig, args: argparse.Namespace) -> int:
    output_path = config.digest_file if not args.output else (config.root / args.output)
    digest = build_memory_digest(config, output_path)
    if args.stdout:
        print(digest, end="")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest, encoding="utf-8")
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


def doctor(config: ProjectConfig, *, strict: bool) -> int:
    missing_files: list[str] = []
    drifted_files: list[str] = []
    placeholder_files: list[str] = []
    lock_issues: list[str] = []
    warnings = collect_doctor_warnings(config)
    memory_errors, memory_warnings = collect_memory_doctor_report(config)
    warnings.extend(memory_warnings)

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

    if missing_files:
        print("Missing managed files:")
        for item in missing_files:
            print(f"  - {item}")
    if drifted_files:
        print("Managed files differ from the current Sula render:")
        for item in drifted_files:
            print(f"  - {item}")
    if placeholder_files:
        print("Files still contain unresolved placeholders:")
        for item in placeholder_files:
            print(f"  - {item}")
    if memory_errors:
        print("Project memory issues:")
        for item in memory_errors:
            print(f"  - {item}")
    if lock_issues:
        print("Lockfile issues:")
        for item in lock_issues:
            print(f"  - {item}")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")

    has_errors = bool(missing_files or drifted_files or placeholder_files or memory_errors or lock_issues)
    if not has_errors and not (strict and warnings):
        print(f"Sula doctor passed for {config.data['project']['name']}")
        return 0
    return 1


def collect_doctor_warnings(config: ProjectConfig) -> list[str]:
    warnings: list[str] = []
    for section, key in EXISTENCE_WARNING_FIELDS:
        relative_value = config.data[section][key]
        target = config.root / relative_value
        if not target.exists():
            warnings.append(f"manifest reference does not exist yet: {section}.{key} -> {relative_value}")
    return warnings


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
