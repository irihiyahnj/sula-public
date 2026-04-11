#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys


SULA_ROOT = Path(__file__).resolve().parent.parent
VERSION = (SULA_ROOT / "VERSION").read_text(encoding="utf-8").strip()
MANIFEST_PATH = Path(".sula/project.toml")
LOCK_PATH = Path(".sula/version.lock")


@dataclass
class ProjectConfig:
    root: Path
    data: dict

    @property
    def profile(self) -> str:
        return self.data["project"]["profile"]

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

    doctor_cmd = sub.add_parser("doctor", help="Check manifest, lockfile, and managed files")
    add_project_root_arg(doctor_cmd)

    return parser.parse_args()


def add_project_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", required=True, help="Path to the target project root")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()

    if args.command == "init":
        config = ensure_manifest(project_root, args)
        render_all(config, include_scaffold=True)
        write_lockfile(config)
        print(f"Initialized Sula for {config.data['project']['name']} at {project_root}")
        return 0

    config = load_manifest(project_root)
    if args.command == "sync":
        render_all(config, include_scaffold=False)
        write_lockfile(config)
        print(f"Synchronized managed files for {config.data['project']['name']}")
        return 0

    if args.command == "doctor":
        return doctor(config)

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
    ]:
        lines.append(f"[{section_name}]")
        for key, value in manifest[section_name].items():
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
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
    required = {
        "project": ["name", "slug", "description", "profile", "default_agent"],
        "repository": ["primary_branch", "working_branch_prefix", "deployment_branch"],
        "rules": ["highest_rule", "custom_backend_allowed", "react_router_allowed"],
        "stack": ["frontend", "backend"],
        "paths": ["api_layer", "state_layer", "app_shell", "status_file", "change_records_file"],
        "commands": ["install", "dev", "build", "typecheck"],
        "deploy": ["base_path", "production_url", "workflow"],
        "auth": ["session_expiry_codes", "permission_denied_codes"],
    }
    missing: list[str] = []
    for section, keys in required.items():
        if section not in data:
            missing.append(section)
            continue
        for key in keys:
            if key not in data[section]:
                missing.append(f"{section}.{key}")
    if missing:
        raise SystemExit("Manifest missing required fields: " + ", ".join(missing))


def render_all(config: ProjectConfig, *, include_scaffold: bool) -> None:
    tokens = config.token_map()
    apply_template_tree(core_managed_dir(), config.root, tokens, overwrite=True)
    apply_template_tree(profile_managed_dir(config.profile), config.root, tokens, overwrite=True)
    if include_scaffold:
        apply_template_tree(profile_scaffold_dir(config.profile), config.root, tokens, overwrite=False)


def apply_template_tree(source: Path, destination_root: Path, tokens: dict[str, str], *, overwrite: bool) -> None:
    if not source.exists():
        return
    for template in sorted(source.rglob("*")):
        if template.is_dir():
            continue
        relative = template.relative_to(source)
        output_relative = Path(str(relative).removesuffix(".tmpl"))
        output_path = destination_root / output_relative
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists() and not overwrite:
            continue
        text = template.read_text(encoding="utf-8")
        for key, value in tokens.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        output_path.write_text(text, encoding="utf-8")


def doctor(config: ProjectConfig) -> int:
    missing_files: list[str] = []
    placeholder_files: list[str] = []

    for template_root in [core_managed_dir(), profile_managed_dir(config.profile)]:
        for template in sorted(template_root.rglob("*.tmpl")):
            relative = template.relative_to(template_root)
            target = config.root / Path(str(relative).removesuffix(".tmpl"))
            if not target.exists():
                missing_files.append(str(target))
                continue
            if "{{" in target.read_text(encoding="utf-8"):
                placeholder_files.append(str(target))

    lock_file = config.root / LOCK_PATH
    lock_ok = lock_file.exists()

    if missing_files:
        print("Missing managed files:")
        for item in missing_files:
            print(f"  - {item}")
    if placeholder_files:
        print("Files still contain unresolved placeholders:")
        for item in placeholder_files:
            print(f"  - {item}")
    if not lock_ok:
        print(f"Missing lockfile: {lock_file}")

    if not missing_files and not placeholder_files and lock_ok:
        print(f"Sula doctor passed for {config.data['project']['name']}")
        return 0
    return 1


def write_lockfile(config: ProjectConfig) -> None:
    lock_file = config.root / LOCK_PATH
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(
        f'sula_version = "{VERSION}"\nprofile = "{config.profile}"\n',
        encoding="utf-8",
    )


def core_managed_dir() -> Path:
    return SULA_ROOT / "templates/core/managed"


def profile_template_dir(profile: str) -> Path:
    return SULA_ROOT / "templates/profiles" / profile


def profile_managed_dir(profile: str) -> Path:
    return profile_template_dir(profile) / "managed"


def profile_scaffold_dir(profile: str) -> Path:
    return profile_template_dir(profile) / "scaffold"


if __name__ == "__main__":
    sys.exit(main())
