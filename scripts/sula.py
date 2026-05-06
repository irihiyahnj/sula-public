#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import difflib
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
from urllib import error, parse, request
import zipfile

from sula_providers import ProviderAdapterError, ProviderSnapshot, ProviderTaskListSnapshot, create_provider_adapter


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
LANGUAGE_CHOICES = ["zh-CN", "en"]
PROJECTION_MODE_CHOICES = ["detached", "collaborative", "governed"]
WORKFLOW_EXECUTION_MODE_CHOICES = ["solo-inline", "review-heavy", "subagent-parallel"]
WORKFLOW_DESIGN_GATE_CHOICES = ["never", "complex-only", "always"]
WORKFLOW_PLAN_GATE_CHOICES = ["never", "multi-step", "always"]
WORKFLOW_REVIEW_POLICY_CHOICES = ["none", "batch", "task-checkpoints", "strict"]
WORKFLOW_ISOLATION_CHOICES = ["none", "branch", "worktree"]
WORKFLOW_TESTING_POLICY_CHOICES = ["inherit", "verify-first", "tdd"]
WORKFLOW_CLOSEOUT_POLICY_CHOICES = ["inherit", "explicit"]
WORKFLOW_SCAFFOLD_KIND_CHOICES = ["spec", "plan", "review"]
ORCHESTRATION_MODE_CHOICES = ["ticket-runner", "review-assistant", "status-only"]
ORCHESTRATION_TASK_SOURCE_CHOICES = ["local", "provider-task-document", "provider-api"]
ORCHESTRATION_RUNNER_CHOICES = ["dry-run", "codex-sdk", "codex-app-server", "shell-command"]
ORCHESTRATION_WORKSPACE_MODE_CHOICES = ["none", "branch", "worktree", "copy", "container", "remote"]
ORCHESTRATION_TRUST_PROFILE_CHOICES = ["local-sandboxed", "trusted-local", "remote-sandboxed"]
ORCHESTRATION_RISK_CHOICES = ["low", "medium", "high"]
ORCHESTRATION_STATUS_SURFACE_CHOICES = ["sula", "external"]
ORCHESTRATION_VERIFICATION_ADAPTER_CHOICES = ["local-file", "artifact-catalog", "provider-metadata", "pull-request-url", "url"]
ORCHESTRATION_REMOTE_VERIFICATION_POLICY_CHOICES = ["reference-only", "opportunistic", "required"]
ORCHESTRATION_RUN_STATUSES = ["blocked", "planned", "running", "failed", "human-review", "accepted", "cancelled"]
ORCHESTRATION_VISIBLE_ACTIVE_STATES = {"planned", "running", "human-review"}
AGENT_ROUTING_MODE_CHOICES = ["off", "assist", "plan-execute-review", "review-only", "executor-only"]
AGENT_ROUTING_VISIBILITY_CHOICES = ["off", "on-demand", "always"]
AGENT_ROUTING_BUDGET_POLICY_CHOICES = ["cost-aware", "speed-first", "quality-first"]
AGENT_ROUTING_ON_REVIEW_FAIL_CHOICES = ["return-to-executor", "block", "ask"]
AGENT_ROUTING_ROLE_CHOICES = ["host", "planner", "executor", "verifier", "reviewer", "acceptor"]
AGENT_ROUTING_BUDGET_BREACH_CHOICES = ["ask", "stop", "downgrade"]
AUTOMATION_MODE_CHOICES = ["observe", "assist", "execute"]
AUTOMATION_EVENT_SOURCE_CHOICES = ["sula-cli", "provider", "status", "artifact", "workflow", "external"]
ORCHESTRATION_TRIGGER_SOURCE_KIND_CHOICES = [
    "cli-intent",
    "sula-command",
    "webhook",
    "github-issue",
    "linear-issue",
    "provider-task-document",
    "external",
]
AGENT_BEHAVIOR_QUALITY_POLICY_CHOICES = ["sula-karpathy-inspired", "minimal"]
AGENT_BEHAVIOR_CLARIFICATION_POLICY_CHOICES = ["non-trivial-only", "always", "never"]
AGENT_BEHAVIOR_DIFF_SCOPE_POLICY_CHOICES = ["surgical", "task-scoped", "open"]
AGENT_BEHAVIOR_SUCCESS_CRITERIA_POLICY_CHOICES = ["required", "recommended", "off"]
AGENT_BEHAVIOR_ASSUMPTION_POLICY_CHOICES = ["surface-when-uncertain", "always", "off"]
AGENT_BEHAVIOR_COMPLEXITY_POLICY_CHOICES = ["simplicity-first", "project-default"]
MEMORY_CAPTURE_POLICY_CHOICES = ["off", "explicit", "guided"]
MEMORY_PROMOTION_POLICY_CHOICES = ["manual", "review-required", "auto-derived"]
MEMORY_QUERY_ROUTING_CHOICES = ["literal", "deterministic", "deterministic-plus-hints"]
MEMORY_SEMANTIC_CACHE_CHOICES = ["off", "optional", "canary"]
MEMORY_CAPTURE_CATEGORY_CHOICES = ["note", "task", "decision", "risk", "rule"]
MEMORY_PROMOTION_TARGET_CHOICES = ["task", "decision", "risk", "rule", "state", "workflow-artifact"]
MEMORY_CAPTURE_STATUS_CHOICES = ["staged", "promoted", "discarded"]
FEEDBACK_KIND_CHOICES = ["bug", "improvement", "docs", "policy", "regression"]
FEEDBACK_SEVERITY_CHOICES = ["low", "medium", "high", "critical"]
FEEDBACK_DECISION_CHOICES = ["triaged", "accepted", "deferred", "rejected", "released"]
FEEDBACK_BUNDLE_SCHEMA_VERSION = 1
PROVIDER_IMPORT_KIND_SPECS = {
    "google-doc": {
        "provider": "google-drive",
        "default_target_format": "docx",
        "allowed_target_formats": ("docx", "html"),
        "mime_types": {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "html": "text/html",
        },
        "existing_suffixes": {".docx", ".html"},
        "source_suffixes": {".docx", ".html", ".md", ".txt"},
    },
    "google-sheet": {
        "provider": "google-drive",
        "default_target_format": "xlsx",
        "allowed_target_formats": ("xlsx",),
        "mime_types": {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
        "existing_suffixes": {".xlsx"},
        "source_suffixes": {".xlsx", ".csv", ".tsv", ".json"},
    },
}
PROVIDER_NATIVE_ITEM_KINDS = {"google-doc", "google-sheet"}
ARTIFACT_ROLE_CHOICES = ["workspace-source", "provider-native-source", "exported-derivative"]
SOURCE_OF_TRUTH_CHOICES = ["auto", "workspace", "provider-native"]
COLLABORATION_MODE_CHOICES = ["single-editor", "multi-editor"]
EXPORT_DERIVATIVE_SUFFIXES = {".docx", ".html", ".pdf", ".xlsx"}
FRESHNESS_INTENT_PHRASES = [
    "先看最新版本再继续",
    "这份共享文件可能被别人改过",
    "这份表很多人在 google 上一起改",
    "共享文档为准",
    "共享文件为准",
    "别人刚改过",
    "刚改过",
    "最新版本",
    "最新",
    "多人协作",
    "共同编辑",
    "一起改",
    "look at the latest version first",
    "latest version",
    "most recent version",
    "shared document",
    "shared doc",
    "source of truth",
    "others just changed",
    "someone else changed",
    "just changed",
    "refresh before continue",
]
FORMAL_DOCUMENT_GENRES = ("schedule", "proposal", "report", "process", "training")
FORMAL_DOCUMENT_BUNDLE_DEFAULTS = {
    "schedule": "monthly-gantt-dual-actions-raci",
    "proposal": "problem-solution-workplan-raci",
    "report": "executive-findings-actions",
    "process": "purpose-workflow-controls-records",
    "training": "outcomes-agenda-delivery-assessment-followup",
}
DOCUMENT_GENRE_BY_KIND = {
    "schedule": "schedule",
    "timeline": "schedule",
    "calendar": "schedule",
    "proposal": "proposal",
    "plan": "proposal",
    "report": "report",
    "progress": "report",
    "summary": "report",
    "update": "report",
    "process": "process",
    "workflow": "process",
    "procedure": "process",
    "sop": "process",
    "runbook": "process",
    "training": "training",
    "workshop": "training",
    "enablement": "training",
    "onboarding": "training",
}
DOCUMENT_TITLE_GENRE_KEYWORDS = {
    "schedule": ("schedule", "timeline", "calendar", "roadmap", "排期", "日程", "进度表", "甘特"),
    "proposal": ("proposal", "work plan", "workplan", "implementation plan", "方案", "计划", "实施方案"),
    "report": ("report", "weekly update", "monthly update", "summary", "汇报", "报告", "周报", "月报", "总结"),
    "process": ("process", "workflow", "procedure", "sop", "runbook", "流程", "机制", "作业指导"),
    "training": ("training", "workshop", "enablement", "onboarding", "培训", "课件", "授课"),
}

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
        "status_recent_decision_limit": "int",
        "status_current_focus_limit": "int",
        "status_blocker_limit": "int",
        "status_archive_file": "string",
        "capture_policy": "string",
        "promotion_policy": "string",
        "rule_registry": "bool",
        "job_tracking": "bool",
        "query_routing": "string",
        "semantic_cache": "string",
        "session_retention_days": "int",
        "promotion_file": "string",
    },
    "workflow": {
        "pack": "string",
        "stage": "string",
        "artifacts_root": "string",
        "docs_root": "string",
        "execution_mode": "string",
        "design_gate": "string",
        "plan_gate": "string",
        "review_policy": "string",
        "workspace_isolation": "string",
        "testing_policy": "string",
        "closeout_policy": "string",
    },
    "orchestration": {
        "enabled": "bool",
        "mode": "string",
        "task_source": "string",
        "runner": "string",
        "runner_command": "string_optional",
        "runner_endpoint": "string_optional",
        "runner_token_env": "string_optional",
        "tasks_path": "string",
        "provider_task_item_id": "string_optional",
        "provider_task_item_kind": "string_optional",
        "provider_task_item_url": "string_optional",
        "workspace_root": "string",
        "workspace_mode": "string",
        "trust_profile": "string",
        "allow_project_root_runner": "bool",
        "max_concurrent_runs": "int",
        "max_retry_count": "int",
        "max_run_minutes": "int",
        "daily_budget_minutes": "int",
        "unattended_risk_ceiling": "string",
        "require_human_approval_for": "string_list",
        "status_surface": "string",
        "verification_adapters": "string_list",
        "remote_verification_policy": "string",
    },
    "automation": {
        "enabled": "bool",
        "mode": "string",
        "auto_intake": "bool",
        "auto_plan": "bool",
        "auto_dispatch": "bool",
        "risk_ceiling": "string",
        "approval_required_for": "string_list",
        "event_sources": "string_list",
    },
    "agent_behavior": {
        "quality_policy": "string",
        "clarification_policy": "string",
        "diff_scope_policy": "string",
        "success_criteria_policy": "string",
        "assumption_policy": "string",
        "complexity_policy": "string",
        "require_verification": "bool",
        "forbid_drive_by_refactors": "bool",
    },
    "agent_routing": {
        "enabled": "bool",
        "mode": "string",
        "visibility": "string",
        "default_budget_policy": "string",
        "budget_breach_behavior": "string",
        "max_review_cycles": "int",
        "on_review_fail": "string",
        "require_final_acceptance": "bool",
        "roles": "dict",
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
    "language": {
        "content_locale": "string",
        "interaction_locale": "string",
        "preserve_user_input_language": "bool",
    },
    "document_design": {
        "principles_path": "string",
        "source_first": "bool",
        "register_derived_artifacts": "bool",
        "preferred_source_format": "string",
        "schedule_bundle": "string",
        "proposal_bundle": "string",
        "report_bundle": "string",
        "process_bundle": "string",
        "training_bundle": "string",
    },
    "projection": {
        "mode": "string",
        "enabled_packs": "string_list",
    },
}

EXISTENCE_WARNING_FIELDS = [
    ("paths", "api_layer"),
    ("paths", "state_layer"),
    ("paths", "app_shell"),
    ("deploy", "workflow"),
    ("document_design", "principles_path"),
]

STATUS_REQUIRED_SECTIONS = [
    "Summary",
    "Health",
    "Current Focus",
    "Blockers",
    "Recent Decisions",
    "Next Review",
    "Handoff",
]

CHANGE_RECORDS_REQUIRED_SECTIONS = [
    "Purpose",
    "Rules",
    "Index",
    "Detailed Records",
]

CHANGE_RECORD_REQUIRED_SECTIONS = [
    "Metadata",
    "Background",
    "Analysis",
    "Chosen Plan",
    "Execution",
    "Verification",
    "Rollback",
    "Data Side-effects",
    "Follow-up",
    "Architecture Boundary Check",
]

RELEASE_RECORD_REQUIRED_SECTIONS = [
    "Metadata",
    "Scope",
    "Risks",
    "Verification",
    "Rollback",
    "Follow-up",
]

INCIDENT_RECORD_REQUIRED_SECTIONS = [
    "Metadata",
    "Summary",
    "Impact",
    "Timeline",
    "Root Cause",
    "Resolution",
    "Follow-up",
]

STATUS_PLACEHOLDERS = ["YYYY-MM-DD", "_add ", "_write ", "_set ", "_补充", "_写下", "_填写"]
INDEX_PLACEHOLDERS = ["_no records yet_", "_add project records here_", "_暂无记录_", "_在此补充项目记录_"]
MEMORY_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INLINE_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
CHANGE_RECORD_FILENAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\.md$")
STATUS_UPDATED_PATTERN = re.compile(r"^- (?:last updated|最后更新):\s*(.+?)\s*$", re.MULTILINE)
GENERATED_ON_PATTERN = re.compile(r"^- (?:generated on|生成于):\s*(.+?)\s*$", re.MULTILINE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
NON_ASCII_CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")

SECTION_LABELS = {
    "Summary": {"en": "Summary", "zh": "摘要"},
    "Health": {"en": "Health", "zh": "健康状态"},
    "Current Focus": {"en": "Current Focus", "zh": "当前重点"},
    "Blockers": {"en": "Blockers", "zh": "阻塞项"},
    "Recent Decisions": {"en": "Recent Decisions", "zh": "近期决策"},
    "Next Review": {"en": "Next Review", "zh": "下次复盘"},
    "Handoff": {"en": "Handoff", "zh": "交接"},
    "Purpose": {"en": "Purpose", "zh": "用途"},
    "Rules": {"en": "Rules", "zh": "规则"},
    "Index": {"en": "Index", "zh": "索引"},
    "Detailed Records": {"en": "Detailed Records", "zh": "详细记录"},
    "Metadata": {"en": "Metadata", "zh": "元数据"},
    "Background": {"en": "Background", "zh": "背景"},
    "Analysis": {"en": "Analysis", "zh": "分析"},
    "Chosen Plan": {"en": "Chosen Plan", "zh": "选定方案"},
    "Execution": {"en": "Execution", "zh": "执行"},
    "Verification": {"en": "Verification", "zh": "验证"},
    "Rollback": {"en": "Rollback", "zh": "回退"},
    "Data Side-effects": {"en": "Data Side-effects", "zh": "数据副作用"},
    "Follow-up": {"en": "Follow-up", "zh": "后续"},
    "Architecture Boundary Check": {"en": "Architecture Boundary Check", "zh": "架构边界检查"},
    "Scope": {"en": "Scope", "zh": "范围"},
    "Risks": {"en": "Risks", "zh": "风险"},
    "Impact": {"en": "Impact", "zh": "影响"},
    "Timeline": {"en": "Timeline", "zh": "时间线"},
    "Root Cause": {"en": "Root Cause", "zh": "根因"},
    "Resolution": {"en": "Resolution", "zh": "解决"},
    "Tasks": {"en": "Tasks", "zh": "任务"},
    "Decisions": {"en": "Decisions", "zh": "决策"},
    "State Updates": {"en": "State Updates", "zh": "状态更新"},
    "Workflow Artifacts": {"en": "Workflow Artifacts", "zh": "工作流文档"},
    "People": {"en": "People", "zh": "人员"},
    "Agreements": {"en": "Agreements", "zh": "协议"},
    "Milestones": {"en": "Milestones", "zh": "里程碑"},
    "Identity": {"en": "Identity", "zh": "项目标识"},
    "Current State": {"en": "Current State", "zh": "当前状态"},
    "Recent Change Records": {"en": "Recent Change Records", "zh": "近期变更记录"},
    "Release History": {"en": "Release History", "zh": "发布历史"},
    "Incident History": {"en": "Incident History", "zh": "事故历史"},
    "Open Architecture Exceptions": {"en": "Open Architecture Exceptions", "zh": "开放的架构例外"},
    "Key References": {"en": "Key References", "zh": "关键参考"},
}

FIELD_LABEL_ALIASES = {
    "last updated": {"en": "last updated", "zh": "最后更新"},
    "status": {"en": "status", "zh": "状态"},
    "reason": {"en": "reason", "zh": "原因"},
    "owner": {"en": "owner", "zh": "负责人"},
    "date": {"en": "date", "zh": "日期"},
    "trigger": {"en": "trigger", "zh": "触发条件"},
    "ready": {"en": "ready", "zh": "可交接"},
    "start here": {"en": "start here", "zh": "从这里开始"},
    "latest record": {"en": "latest record", "zh": "最新记录"},
    "next action": {"en": "next action", "zh": "下一步动作"},
    "next owner": {"en": "next owner", "zh": "下一步负责人"},
    "next due": {"en": "next due", "zh": "下一步截止"},
    "done when": {"en": "done when", "zh": "完成定义"},
    "blockers": {"en": "blockers", "zh": "阻塞"},
    "source of truth": {"en": "source of truth", "zh": "真相源"},
    "source freshness": {"en": "source freshness", "zh": "真相新鲜度"},
    "verification command": {"en": "verification command", "zh": "验证命令"},
    "verification result": {"en": "verification result", "zh": "验证结果"},
    "verification date": {"en": "verification date", "zh": "验证日期"},
    "git branch": {"en": "git branch", "zh": "Git 分支"},
    "git commit": {"en": "git commit", "zh": "Git 提交"},
    "git working tree": {"en": "git working tree", "zh": "Git 工作区"},
    "executor": {"en": "executor", "zh": "执行者"},
    "branch": {"en": "branch", "zh": "分支"},
    "related commit(s)": {"en": "related commit(s)", "zh": "关联提交"},
    "directory": {"en": "directory", "zh": "目录"},
    "template": {"en": "template", "zh": "模板"},
    "project": {"en": "project", "zh": "项目"},
    "kind": {"en": "kind", "zh": "类型"},
    "workflow pack": {"en": "workflow pack", "zh": "工作流包"},
    "workflow slot": {"en": "workflow slot", "zh": "工作流槽位"},
    "storage provider": {"en": "storage provider", "zh": "存储提供方"},
    "generated on": {"en": "generated on", "zh": "生成于"},
    "generated by": {"en": "generated by", "zh": "生成工具"},
    "profile": {"en": "profile", "zh": "配置档"},
    "description": {"en": "description", "zh": "说明"},
    "highest rule": {"en": "highest rule", "zh": "最高规则"},
}

STRING_ALIASES = {
    "_no records yet_": {"en": "_no records yet_", "zh": "_暂无记录_"},
    "_add project records here_": {"en": "_add project records here_", "zh": "_在此补充项目记录_"},
    "none": {"en": "none", "zh": "无"},
    "_missing_": {"en": "_missing_", "zh": "_缺失_"},
}


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
        return int(self.memory_setting("status_max_age_days", 14))

    @property
    def status_recent_decision_limit(self) -> int:
        return int(self.memory_setting("status_recent_decision_limit", 100))

    @property
    def status_current_focus_limit(self) -> int:
        return int(self.memory_setting("status_current_focus_limit", 100))

    @property
    def status_blocker_limit(self) -> int:
        return int(self.memory_setting("status_blocker_limit", 100))

    @property
    def status_archive_file(self) -> Path:
        return self.root / self.memory_setting("status_archive_file", "docs/ops/status-archive.md")

    @property
    def session_retention_days(self) -> int:
        return int(self.memory_setting("session_retention_days", 7))

    @property
    def promotion_file(self) -> Path:
        return self.root / self.memory_setting("promotion_file", "docs/ops/session-promotions.md")

    @property
    def session_capture_store(self) -> Path:
        return self.root / ".sula" / "state" / "session" / "captures.jsonl"

    @property
    def memory_jobs_history_path(self) -> Path:
        return self.root / ".sula" / "state" / "jobs" / "history.jsonl"

    @property
    def memory_jobs_latest_path(self) -> Path:
        return self.root / ".sula" / "state" / "jobs" / "latest.json"

    def workflow_setting(self, key: str, default):
        return self.data.get("workflow", {}).get(key, default)

    def orchestration_setting(self, key: str, default):
        return self.data.get("orchestration", {}).get(key, default)

    def agent_behavior_setting(self, key: str, default):
        return self.data.get("agent_behavior", {}).get(key, default)

    def agent_routing_setting(self, key: str, default):
        section = self.data.get("agent_routing", {})
        if not isinstance(section, dict):
            return default
        return section.get(key, default)

    def storage_setting(self, key: str, default):
        return self.data.get("storage", {}).get(key, default)

    def portfolio_setting(self, key: str, default):
        return self.data.get("portfolio", {}).get(key, default)

    def language_setting(self, key: str, default):
        return self.data.get("language", {}).get(key, default)

    def document_design_setting(self, key: str, default):
        return self.data.get("document_design", {}).get(key, default)

    def projection_setting(self, key: str, default):
        return self.data.get("projection", {}).get(key, default)

    @property
    def workflow_pack(self) -> str:
        return str(self.workflow_setting("pack", default_workflow_pack(self.profile)))

    @property
    def projection_mode(self) -> str:
        return normalize_projection_mode(str(self.projection_setting("mode", default_projection_mode_for_existing_consumer(self.profile))))

    @property
    def enabled_projection_packs(self) -> list[str]:
        explicit = self.projection_setting("enabled_packs", [])
        if isinstance(explicit, list) and explicit:
            return normalize_projection_packs(self.profile, explicit)
        return default_projection_packs(self.profile, self.projection_mode)

    @property
    def workflow_stage(self) -> str:
        return str(self.workflow_setting("stage", "active"))

    @property
    def artifacts_root(self) -> Path:
        return self.root / self.workflow_setting("artifacts_root", "artifacts")

    @property
    def workflow_docs_root(self) -> Path:
        return self.root / self.workflow_setting("docs_root", "docs/workflows")

    @property
    def workflow_execution_mode(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("execution_mode", defaults["execution_mode"]),
            WORKFLOW_EXECUTION_MODE_CHOICES,
            defaults["execution_mode"],
        )

    @property
    def workflow_design_gate(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("design_gate", defaults["design_gate"]),
            WORKFLOW_DESIGN_GATE_CHOICES,
            defaults["design_gate"],
        )

    @property
    def workflow_plan_gate(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("plan_gate", defaults["plan_gate"]),
            WORKFLOW_PLAN_GATE_CHOICES,
            defaults["plan_gate"],
        )

    @property
    def workflow_review_policy(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("review_policy", defaults["review_policy"]),
            WORKFLOW_REVIEW_POLICY_CHOICES,
            defaults["review_policy"],
        )

    @property
    def workflow_workspace_isolation(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("workspace_isolation", defaults["workspace_isolation"]),
            WORKFLOW_ISOLATION_CHOICES,
            defaults["workspace_isolation"],
        )

    @property
    def workflow_testing_policy(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("testing_policy", defaults["testing_policy"]),
            WORKFLOW_TESTING_POLICY_CHOICES,
            defaults["testing_policy"],
        )

    @property
    def workflow_closeout_policy(self) -> str:
        defaults = default_workflow_policy_config(self.workflow_pack)
        return normalize_workflow_choice(
            self.workflow_setting("closeout_policy", defaults["closeout_policy"]),
            WORKFLOW_CLOSEOUT_POLICY_CHOICES,
            defaults["closeout_policy"],
        )

    @property
    def orchestration_enabled(self) -> bool:
        return bool(self.orchestration_setting("enabled", True))

    @property
    def orchestration_mode(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("mode", "ticket-runner"),
            ORCHESTRATION_MODE_CHOICES,
            "ticket-runner",
        )

    @property
    def orchestration_task_source(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("task_source", "local"),
            ORCHESTRATION_TASK_SOURCE_CHOICES,
            "local",
        )

    @property
    def orchestration_runner(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("runner", "dry-run"),
            ORCHESTRATION_RUNNER_CHOICES,
            "dry-run",
        )

    @property
    def orchestration_runner_command(self) -> str:
        return normalize_optional_text(self.orchestration_setting("runner_command", ""))

    @property
    def orchestration_runner_endpoint(self) -> str:
        return normalize_optional_text(self.orchestration_setting("runner_endpoint", "")).strip()

    @property
    def orchestration_runner_token_env(self) -> str:
        return normalize_optional_text(self.orchestration_setting("runner_token_env", "SULA_CODEX_APP_SERVER_TOKEN")).strip()

    @property
    def orchestration_tasks_path(self) -> Path:
        raw = str(self.orchestration_setting("tasks_path", "docs/workflows/tasks.json"))
        return (self.root / raw).resolve() if not Path(raw).is_absolute() else Path(raw)

    @property
    def orchestration_provider_task_item_id(self) -> str:
        return normalize_optional_text(self.orchestration_setting("provider_task_item_id", "")).strip()

    @property
    def orchestration_provider_task_item_kind(self) -> str:
        return normalize_optional_text(self.orchestration_setting("provider_task_item_kind", "")).strip()

    @property
    def orchestration_provider_task_item_url(self) -> str:
        return normalize_optional_text(self.orchestration_setting("provider_task_item_url", "")).strip()

    @property
    def orchestration_workspace_root(self) -> Path:
        raw = str(self.orchestration_setting("workspace_root", ".sula/local/workspaces"))
        return (self.root / raw).resolve() if not Path(raw).is_absolute() else Path(raw)

    @property
    def orchestration_workspace_mode(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("workspace_mode", "none"),
            ORCHESTRATION_WORKSPACE_MODE_CHOICES,
            "none",
        )

    @property
    def orchestration_allow_project_root_runner(self) -> bool:
        return bool(self.orchestration_setting("allow_project_root_runner", False))

    @property
    def orchestration_trust_profile(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("trust_profile", "local-sandboxed"),
            ORCHESTRATION_TRUST_PROFILE_CHOICES,
            "local-sandboxed",
        )

    @property
    def orchestration_max_concurrent_runs(self) -> int:
        return int(self.orchestration_setting("max_concurrent_runs", 1))

    @property
    def orchestration_max_retry_count(self) -> int:
        return int(self.orchestration_setting("max_retry_count", 1))

    @property
    def orchestration_max_run_minutes(self) -> int:
        return int(self.orchestration_setting("max_run_minutes", 30))

    @property
    def orchestration_daily_budget_minutes(self) -> int:
        return int(self.orchestration_setting("daily_budget_minutes", 120))

    @property
    def orchestration_unattended_risk_ceiling(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("unattended_risk_ceiling", "low"),
            ORCHESTRATION_RISK_CHOICES,
            "low",
        )

    @property
    def orchestration_require_human_approval_for(self) -> list[str]:
        value = self.orchestration_setting("require_human_approval_for", ["release", "security", "provider-write", "destructive"])
        if not isinstance(value, list):
            return ["release", "security", "provider-write", "destructive"]
        return [str(item).strip() for item in value if str(item).strip()]

    @property
    def orchestration_status_surface(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("status_surface", "sula"),
            ORCHESTRATION_STATUS_SURFACE_CHOICES,
            "sula",
        )

    @property
    def orchestration_verification_adapters(self) -> list[str]:
        value = self.orchestration_setting(
            "verification_adapters",
            ["local-file", "artifact-catalog", "provider-metadata", "pull-request-url", "url"],
        )
        if not isinstance(value, list):
            return ["local-file", "artifact-catalog", "provider-metadata", "pull-request-url", "url"]
        adapters: list[str] = []
        for item in value:
            normalized = normalize_optional_text(item).strip().lower()
            if normalized in ORCHESTRATION_VERIFICATION_ADAPTER_CHOICES and normalized not in adapters:
                adapters.append(normalized)
        return adapters or ["local-file", "artifact-catalog", "provider-metadata", "pull-request-url", "url"]

    @property
    def orchestration_remote_verification_policy(self) -> str:
        return normalize_workflow_choice(
            self.orchestration_setting("remote_verification_policy", "opportunistic"),
            ORCHESTRATION_REMOTE_VERIFICATION_POLICY_CHOICES,
            "opportunistic",
        )

    def automation_setting(self, key: str, default):
        section = self.data.get("automation", {})
        if not isinstance(section, dict):
            return default
        return section.get(key, default)

    @property
    def automation_enabled(self) -> bool:
        return bool(self.automation_setting("enabled", True))

    @property
    def automation_mode(self) -> str:
        return normalize_workflow_choice(
            self.automation_setting("mode", "execute"),
            AUTOMATION_MODE_CHOICES,
            "execute",
        )

    @property
    def automation_auto_intake(self) -> bool:
        return bool(self.automation_setting("auto_intake", True))

    @property
    def automation_auto_plan(self) -> bool:
        return bool(self.automation_setting("auto_plan", True))

    @property
    def automation_auto_dispatch(self) -> bool:
        return bool(self.automation_setting("auto_dispatch", True))

    @property
    def automation_risk_ceiling(self) -> str:
        return normalize_workflow_choice(
            self.automation_setting("risk_ceiling", "low"),
            ORCHESTRATION_RISK_CHOICES,
            "low",
        )

    @property
    def automation_approval_required_for(self) -> list[str]:
        value = self.automation_setting("approval_required_for", ["release", "security", "provider-write", "destructive"])
        if not isinstance(value, list):
            return ["release", "security", "provider-write", "destructive"]
        return [str(item).strip() for item in value if str(item).strip()]

    @property
    def automation_event_sources(self) -> list[str]:
        value = self.automation_setting("event_sources", ["sula-cli", "provider", "status", "artifact", "workflow", "external"])
        if not isinstance(value, list):
            return ["sula-cli", "provider", "status", "artifact", "workflow", "external"]
        sources: list[str] = []
        for item in value:
            normalized = normalize_optional_text(item).strip().lower()
            if normalized in AUTOMATION_EVENT_SOURCE_CHOICES and normalized not in sources:
                sources.append(normalized)
        return sources or ["sula-cli", "provider", "status", "artifact", "workflow", "external"]

    @property
    def automation_state_root(self) -> Path:
        return self.root / ".sula" / "state" / "automation"

    @property
    def orchestration_state_root(self) -> Path:
        return self.root / ".sula" / "state" / "orchestration"

    @property
    def orchestration_events_path(self) -> Path:
        return self.orchestration_state_root / "events.jsonl"

    @property
    def orchestration_active_path(self) -> Path:
        return self.orchestration_state_root / "active.json"

    @property
    def agent_routing_enabled(self) -> bool:
        return bool(self.agent_routing_setting("enabled", True))

    @property
    def agent_routing_mode(self) -> str:
        return normalize_workflow_choice(
            self.agent_routing_setting("mode", "assist"),
            AGENT_ROUTING_MODE_CHOICES,
            "assist",
        )

    @property
    def agent_routing_visibility(self) -> str:
        return normalize_workflow_choice(
            self.agent_routing_setting("visibility", "always"),
            AGENT_ROUTING_VISIBILITY_CHOICES,
            "always",
        )

    @property
    def agent_routing_default_budget_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_routing_setting("default_budget_policy", "cost-aware"),
            AGENT_ROUTING_BUDGET_POLICY_CHOICES,
            "cost-aware",
        )

    @property
    def agent_routing_budget_breach_behavior(self) -> str:
        return normalize_workflow_choice(
            self.agent_routing_setting("budget_breach_behavior", "ask"),
            AGENT_ROUTING_BUDGET_BREACH_CHOICES,
            "ask",
        )

    @property
    def agent_routing_max_review_cycles(self) -> int:
        try:
            return max(1, int(self.agent_routing_setting("max_review_cycles", 3)))
        except (TypeError, ValueError):
            return 3

    @property
    def agent_routing_on_review_fail(self) -> str:
        return normalize_workflow_choice(
            self.agent_routing_setting("on_review_fail", "return-to-executor"),
            AGENT_ROUTING_ON_REVIEW_FAIL_CHOICES,
            "return-to-executor",
        )

    @property
    def agent_routing_require_final_acceptance(self) -> bool:
        return bool(self.agent_routing_setting("require_final_acceptance", True))

    @property
    def agent_routing_roles(self) -> dict[str, dict[str, object]]:
        value = self.agent_routing_setting("roles", {})
        if not isinstance(value, dict):
            value = {}
        return normalize_agent_routing_roles(value)

    @property
    def agent_provider_config_path(self) -> Path:
        return self.root / ".sula" / "local" / "agent-providers.json"

    @property
    def agent_quality_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_behavior_setting("quality_policy", "sula-karpathy-inspired"),
            AGENT_BEHAVIOR_QUALITY_POLICY_CHOICES,
            "sula-karpathy-inspired",
        )

    @property
    def agent_clarification_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_behavior_setting("clarification_policy", "non-trivial-only"),
            AGENT_BEHAVIOR_CLARIFICATION_POLICY_CHOICES,
            "non-trivial-only",
        )

    @property
    def agent_diff_scope_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_behavior_setting("diff_scope_policy", "surgical"),
            AGENT_BEHAVIOR_DIFF_SCOPE_POLICY_CHOICES,
            "surgical",
        )

    @property
    def agent_success_criteria_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_behavior_setting("success_criteria_policy", "required"),
            AGENT_BEHAVIOR_SUCCESS_CRITERIA_POLICY_CHOICES,
            "required",
        )

    @property
    def agent_assumption_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_behavior_setting("assumption_policy", "surface-when-uncertain"),
            AGENT_BEHAVIOR_ASSUMPTION_POLICY_CHOICES,
            "surface-when-uncertain",
        )

    @property
    def agent_complexity_policy(self) -> str:
        return normalize_workflow_choice(
            self.agent_behavior_setting("complexity_policy", "simplicity-first"),
            AGENT_BEHAVIOR_COMPLEXITY_POLICY_CHOICES,
            "simplicity-first",
        )

    @property
    def agent_require_verification(self) -> bool:
        return bool(self.agent_behavior_setting("require_verification", True))

    @property
    def agent_forbid_drive_by_refactors(self) -> bool:
        return bool(self.agent_behavior_setting("forbid_drive_by_refactors", True))

    @property
    def provider_import_root(self) -> Path:
        return self.root / ".sula" / "exports" / "provider-imports"

    @property
    def provider_snapshot_root(self) -> Path:
        return self.root / ".sula" / "cache" / "provider-snapshots"

    @property
    def local_state_root(self) -> Path:
        return self.root / ".sula" / "local"

    @property
    def project_google_oauth_file(self) -> Path:
        return self.local_state_root / "google-oauth.json"

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

    @property
    def content_locale(self) -> str:
        return normalize_locale(str(self.language_setting("content_locale", "en")))

    @property
    def interaction_locale(self) -> str:
        return normalize_locale(str(self.language_setting("interaction_locale", self.content_locale)))

    @property
    def document_design_principles_path(self) -> str:
        return str(self.document_design_setting("principles_path", "docs/ops/document-design-principles.md"))

    @property
    def document_source_first(self) -> bool:
        return bool(self.document_design_setting("source_first", True))

    @property
    def register_derived_artifacts(self) -> bool:
        return bool(self.document_design_setting("register_derived_artifacts", True))

    @property
    def preferred_document_source_format(self) -> str:
        return str(self.document_design_setting("preferred_source_format", "markdown"))

    def document_bundle_for_genre(self, genre: str) -> str:
        if genre not in FORMAL_DOCUMENT_BUNDLE_DEFAULTS:
            return ""
        return str(self.document_design_setting(f"{genre}_bundle", FORMAL_DOCUMENT_BUNDLE_DEFAULTS[genre]))

    def token_map(self) -> dict[str, str]:
        auth = self.data["auth"]
        tokens = {
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
            "STATUS_MAX_AGE_DAYS": str(self.memory_setting("status_max_age_days", 14)),
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
            "WORKFLOW_DOCS_ROOT": self.workflow_setting("docs_root", "docs/workflows"),
            "WORKFLOW_EXECUTION_MODE": self.workflow_execution_mode,
            "WORKFLOW_DESIGN_GATE": self.workflow_design_gate,
            "WORKFLOW_PLAN_GATE": self.workflow_plan_gate,
            "WORKFLOW_REVIEW_POLICY": self.workflow_review_policy,
            "WORKFLOW_ISOLATION": self.workflow_workspace_isolation,
            "WORKFLOW_TESTING_POLICY": self.workflow_testing_policy,
            "WORKFLOW_CLOSEOUT_POLICY": self.workflow_closeout_policy,
            "ORCHESTRATION_ENABLED": str(self.orchestration_enabled).lower(),
            "ORCHESTRATION_MODE": self.orchestration_mode,
            "ORCHESTRATION_TASK_SOURCE": self.orchestration_task_source,
            "ORCHESTRATION_RUNNER": self.orchestration_runner,
            "ORCHESTRATION_RUNNER_COMMAND": self.orchestration_runner_command,
            "ORCHESTRATION_WORKSPACE_MODE": self.orchestration_workspace_mode,
            "AGENT_QUALITY_POLICY": self.agent_quality_policy,
            "AGENT_DIFF_SCOPE_POLICY": self.agent_diff_scope_policy,
            "AGENT_SUCCESS_CRITERIA_POLICY": self.agent_success_criteria_policy,
            "STORAGE_PROVIDER": self.storage_provider,
            "STORAGE_SYNC_MODE": self.storage_sync_mode,
            "PORTFOLIO_ID": self.portfolio_setting("portfolio_id", "default"),
            "PORTFOLIO_WORKSPACE": self.portfolio_setting("workspace", "personal"),
            "CONTENT_LOCALE": self.content_locale,
            "INTERACTION_LOCALE": self.interaction_locale,
            "DOCUMENT_DESIGN_PRINCIPLES_PATH": self.document_design_principles_path,
            "DOCUMENT_SOURCE_FIRST": str(self.document_source_first).lower(),
            "DOCUMENT_REGISTER_DERIVED_ARTIFACTS": str(self.register_derived_artifacts).lower(),
            "DOCUMENT_PREFERRED_SOURCE_FORMAT": self.preferred_document_source_format,
            "SCHEDULE_BUNDLE": self.document_bundle_for_genre("schedule"),
            "PROPOSAL_BUNDLE": self.document_bundle_for_genre("proposal"),
            "REPORT_BUNDLE": self.document_bundle_for_genre("report"),
            "PROCESS_BUNDLE": self.document_bundle_for_genre("process"),
            "TRAINING_BUNDLE": self.document_bundle_for_genre("training"),
            "PROJECTION_MODE": self.projection_mode,
            "PROJECTION_PACKS": ", ".join(self.enabled_projection_packs),
            "CURRENT_DATE": date.today().isoformat(),
            "KERNEL_ADAPTERS": ", ".join(self.kernel_adapters()),
            "GIT_MODE": "enabled" if is_git_repository(self.root) else "not-required",
            "SULA_VERSION": VERSION,
        }
        tokens.update(template_locale_tokens(self.content_locale))
        return tokens

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


def normalize_locale(raw: str | None, default: str = "en") -> str:
    value = (raw or default).strip()
    lowered = value.lower()
    if lowered in {"zh", "zh-cn", "zh-hans", "zh-sg"}:
        return "zh-CN"
    if lowered in {"en", "en-us", "en-gb"}:
        return "en"
    return value or default


def locale_family(raw: str | None) -> str:
    return "zh" if normalize_locale(raw).lower().startswith("zh") else "en"


def contains_cjk(text: str) -> bool:
    return bool(NON_ASCII_CJK_PATTERN.search(text))


def localized_section_name(name: str, locale: str) -> str:
    return SECTION_LABELS.get(name, {}).get(locale_family(locale), name)


def build_section_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for canonical, variants in SECTION_LABELS.items():
        aliases[canonical.casefold()] = canonical
        for variant in variants.values():
            aliases[str(variant).casefold()] = canonical
    return aliases


SECTION_ALIASES = build_section_aliases()


def canonical_section_name(name: str) -> str:
    return SECTION_ALIASES.get(name.strip().casefold(), name.strip())


def localized_field_label(name: str, locale: str) -> str:
    return FIELD_LABEL_ALIASES.get(name, {}).get(locale_family(locale), name)


def build_field_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for canonical, variants in FIELD_LABEL_ALIASES.items():
        aliases[canonical.casefold()] = canonical
        for variant in variants.values():
            aliases[str(variant).casefold()] = canonical
    return aliases


FIELD_ALIASES = build_field_aliases()


def canonical_field_name(name: str) -> str:
    return FIELD_ALIASES.get(name.strip().casefold(), name.strip().lower())


def localized_string(key: str, locale: str) -> str:
    variants = STRING_ALIASES.get(key)
    if variants is None:
        return key
    return variants.get(locale_family(locale), key)


def infer_content_locale(project_root: Path, readme_text: str) -> tuple[str, str]:
    if contains_cjk(readme_text) or contains_cjk(project_root.as_posix()):
        return ("zh-CN", "project text or path already contains Chinese, so Chinese is the safest default")
    return ("en", "English is the safe fallback when no stronger project language signal exists yet")


def template_locale_tokens(locale: str) -> dict[str, str]:
    if locale_family(locale) == "zh":
        return {
            "STATUS_H1": "# 项目状态",
            "STATUS_UPDATED_LINE": "- 最后更新: YYYY-MM-DD",
            "STATUS_SUMMARY_HEADING": "## 摘要",
            "STATUS_SUMMARY_PLACEHOLDER": "- _写一段简短的当前项目摘要_",
            "STATUS_HEALTH_HEADING": "## 健康状态",
            "STATUS_HEALTH_STATUS_LINE": "- 状态: _绿色 / 黄色 / 红色_",
            "STATUS_HEALTH_REASON_LINE": "- 原因: _写下当前运行健康原因_",
            "STATUS_CURRENT_FOCUS_HEADING": "## 当前重点",
            "STATUS_CURRENT_FOCUS_PLACEHOLDER": "- _补充当前进行中的工作流_",
            "STATUS_BLOCKERS_HEADING": "## 阻塞项",
            "STATUS_BLOCKERS_PLACEHOLDER": "- _补充阻塞项，或写无_",
            "STATUS_RECENT_DECISIONS_HEADING": "## 近期决策",
            "STATUS_RECENT_DECISIONS_PLACEHOLDER": "- _补充近期决策_",
            "STATUS_NEXT_REVIEW_HEADING": "## 下次复盘",
            "STATUS_NEXT_REVIEW_OWNER_LINE": "- 负责人: _填写负责人_",
            "STATUS_NEXT_REVIEW_DATE_LINE": "- 日期: YYYY-MM-DD",
            "STATUS_NEXT_REVIEW_TRIGGER_LINE": "- 触发条件: _写下触发下次复盘的条件_",
            "STATUS_HANDOFF_HEADING": "## 交接",
            "STATUS_HANDOFF_READY_LINE": "- 可交接: no",
            "STATUS_HANDOFF_START_HERE_LINE": "- 从这里开始: `path/to/file`; `another/path`",
            "STATUS_HANDOFF_LATEST_RECORD_LINE": "- 最新记录: `docs/change-records/YYYY-MM-DD-topic.md`",
            "STATUS_HANDOFF_NEXT_ACTION_LINE": "- 下一步动作: 查看 `docs/change-records/YYYY-MM-DD-topic.md`; 运行 `python3 scripts/sula.py check --project-root .`",
            "STATUS_HANDOFF_NEXT_OWNER_LINE": "- 下一步负责人: _写下接手人_",
            "STATUS_HANDOFF_NEXT_DUE_LINE": "- 下一步截止: YYYY-MM-DD",
            "STATUS_HANDOFF_DONE_WHEN_LINE": "- 完成定义: 结果 `SULA CHECK OK`; 产物 `STATUS.md`",
            "STATUS_HANDOFF_BLOCKERS_LINE": "- 阻塞: _写无，或写明阻塞点_",
            "STATUS_HANDOFF_SOURCE_OF_TRUTH_LINE": "- 真相源: _写下当前应优先查看的真相文件或链接_",
            "STATUS_HANDOFF_SOURCE_FRESHNESS_LINE": "- 真相新鲜度: n/a / current / needs-refresh / stale-risk",
            "STATUS_HANDOFF_VERIFICATION_COMMAND_LINE": "- 验证命令: _写下最后一次关键验证命令_",
            "STATUS_HANDOFF_VERIFICATION_RESULT_LINE": "- 验证结果: pass / fail / n/a",
            "STATUS_HANDOFF_VERIFICATION_DATE_LINE": "- 验证日期: YYYY-MM-DD",
            "STATUS_HANDOFF_GIT_BRANCH_LINE": "- Git 分支: n/a",
            "STATUS_HANDOFF_GIT_COMMIT_LINE": "- Git 提交: n/a",
            "STATUS_HANDOFF_GIT_WORKTREE_LINE": "- Git 工作区: n/a / clean / dirty",
            "CHANGE_RECORDS_H1": "# {{PROJECT_NAME}} 变更记录",
            "CHANGE_RECORDS_INTRO": "这个文件用于索引项目中的非琐碎变更。",
            "CHANGE_RECORDS_PURPOSE_HEADING": "## 用途",
            "CHANGE_RECORDS_RULES_HEADING": "## 规则",
            "CHANGE_RECORDS_INDEX_HEADING": "## 索引",
            "CHANGE_RECORDS_EMPTY_INDEX_LINE": "- _暂无记录_",
            "CHANGE_RECORDS_DETAILS_HEADING": "## 详细记录",
            "CHANGE_RECORDS_DIRECTORY_LINE": "- 目录: `{{CHANGE_RECORD_DIRECTORY}}/`",
            "CHANGE_RECORDS_TEMPLATE_LINE": "- 模板: [{{CHANGE_RECORD_DIRECTORY}}/_template.md]({{CHANGE_RECORD_DIRECTORY}}/_template.md)",
            "CHANGE_RECORDS_README_H1": "# 变更记录",
            "CHANGE_RECORDS_README_TEMPLATE_LINE": "- [记录模板](_template.md)",
            "RELEASE_RECORDS_README_H1": "# 发布记录",
            "RELEASE_RECORDS_README_TEMPLATE_LINE": "- [发布模板](_template.md)",
            "INCIDENT_RECORDS_README_H1": "# 事故记录",
            "INCIDENT_RECORDS_README_TEMPLATE_LINE": "- [事故模板](_template.md)",
            "RECORD_METADATA_HEADING": "## 元数据",
            "RECORD_DATE_LINE": "- 日期: {{DATE}}",
            "RECORD_EXECUTOR_LINE": "- 执行者: {{EXECUTOR}}",
            "RECORD_BRANCH_LINE": "- 分支: {{BRANCH}}",
            "RECORD_RELATED_COMMITS_LINE": "- 关联提交: {{RELATED_COMMITS}}",
            "RECORD_STATUS_LINE": "- 状态: {{STATUS}}",
            "CHANGE_RECORD_BACKGROUND_HEADING": "## 背景",
            "CHANGE_RECORD_ANALYSIS_HEADING": "## 分析",
            "CHANGE_RECORD_ANALYSIS_PLACEHOLDER": "- _补充背景与选项_",
            "CHANGE_RECORD_CHOSEN_PLAN_HEADING": "## 选定方案",
            "CHANGE_RECORD_CHOSEN_PLAN_PLACEHOLDER": "- _补充选定方案_",
            "CHANGE_RECORD_EXECUTION_HEADING": "## 执行",
            "CHANGE_RECORD_EXECUTION_PLACEHOLDER": "- _补充已执行的变更_",
            "CHANGE_RECORD_VERIFICATION_HEADING": "## 验证",
            "CHANGE_RECORD_VERIFICATION_PLACEHOLDER": "- _补充验证方式_",
            "CHANGE_RECORD_ROLLBACK_HEADING": "## 回退",
            "CHANGE_RECORD_ROLLBACK_PLACEHOLDER": "- _补充回退方式_",
            "CHANGE_RECORD_DATA_SIDE_EFFECTS_HEADING": "## 数据副作用",
            "CHANGE_RECORD_DATA_SIDE_EFFECTS_PLACEHOLDER": "- _补充数据或运行副作用_",
            "CHANGE_RECORD_FOLLOW_UP_HEADING": "## 后续",
            "CHANGE_RECORD_FOLLOW_UP_PLACEHOLDER": "- _补充后续事项_",
            "CHANGE_RECORD_ARCHITECTURE_BOUNDARY_HEADING": "## 架构边界检查",
            "CHANGE_RECORD_ARCHITECTURE_BOUNDARY_LINE": "- 最高规则影响: _补充说明_",
            "RELEASE_RECORD_SCOPE_HEADING": "## 范围",
            "RELEASE_RECORD_RISKS_HEADING": "## 风险",
            "RELEASE_RECORD_RISKS_PLACEHOLDER": "- _补充风险_",
            "INCIDENT_RECORD_SUMMARY_HEADING": "## 摘要",
            "INCIDENT_RECORD_IMPACT_HEADING": "## 影响",
            "INCIDENT_RECORD_IMPACT_PLACEHOLDER": "- _补充影响_",
            "INCIDENT_RECORD_TIMELINE_HEADING": "## 时间线",
            "INCIDENT_RECORD_TIMELINE_PLACEHOLDER": "- _补充时间线_",
            "INCIDENT_RECORD_ROOT_CAUSE_HEADING": "## 根因",
            "INCIDENT_RECORD_ROOT_CAUSE_PLACEHOLDER": "- _补充根因_",
            "INCIDENT_RECORD_RESOLUTION_HEADING": "## 解决",
            "INCIDENT_RECORD_RESOLUTION_PLACEHOLDER": "- _补充解决方式_",
        }
    return {
        "STATUS_H1": "# STATUS",
        "STATUS_UPDATED_LINE": "- last updated: YYYY-MM-DD",
        "STATUS_SUMMARY_HEADING": "## Summary",
        "STATUS_SUMMARY_PLACEHOLDER": "- _write a short current-project summary_",
        "STATUS_HEALTH_HEADING": "## Health",
        "STATUS_HEALTH_STATUS_LINE": "- status: _green / yellow / red_",
        "STATUS_HEALTH_REASON_LINE": "- reason: _write the current operating health_",
        "STATUS_CURRENT_FOCUS_HEADING": "## Current Focus",
        "STATUS_CURRENT_FOCUS_PLACEHOLDER": "- _add active workstreams_",
        "STATUS_BLOCKERS_HEADING": "## Blockers",
        "STATUS_BLOCKERS_PLACEHOLDER": "- _add blockers or write none_",
        "STATUS_RECENT_DECISIONS_HEADING": "## Recent Decisions",
        "STATUS_RECENT_DECISIONS_PLACEHOLDER": "- _add recent decisions_",
        "STATUS_NEXT_REVIEW_HEADING": "## Next Review",
        "STATUS_NEXT_REVIEW_OWNER_LINE": "- owner: _set owner_",
        "STATUS_NEXT_REVIEW_DATE_LINE": "- date: YYYY-MM-DD",
        "STATUS_NEXT_REVIEW_TRIGGER_LINE": "- trigger: _write what should trigger the next review_",
        "STATUS_HANDOFF_HEADING": "## Handoff",
        "STATUS_HANDOFF_READY_LINE": "- ready: no",
        "STATUS_HANDOFF_START_HERE_LINE": "- start here: `path/to/file`; `another/path`",
        "STATUS_HANDOFF_LATEST_RECORD_LINE": "- latest record: `docs/change-records/YYYY-MM-DD-topic.md`",
        "STATUS_HANDOFF_NEXT_ACTION_LINE": "- next action: review `docs/change-records/YYYY-MM-DD-topic.md`; run `python3 scripts/sula.py check --project-root .`",
        "STATUS_HANDOFF_NEXT_OWNER_LINE": "- next owner: _write the next responsible operator_",
        "STATUS_HANDOFF_NEXT_DUE_LINE": "- next due: YYYY-MM-DD",
        "STATUS_HANDOFF_DONE_WHEN_LINE": "- done when: result `SULA CHECK OK`; artifact `STATUS.md`",
        "STATUS_HANDOFF_BLOCKERS_LINE": "- blockers: _write none or name the blocker_",
        "STATUS_HANDOFF_SOURCE_OF_TRUTH_LINE": "- source of truth: _write the file or link the next operator should trust first_",
        "STATUS_HANDOFF_SOURCE_FRESHNESS_LINE": "- source freshness: n/a / current / needs-refresh / stale-risk",
        "STATUS_HANDOFF_VERIFICATION_COMMAND_LINE": "- verification command: _write the last critical verification command_",
        "STATUS_HANDOFF_VERIFICATION_RESULT_LINE": "- verification result: pass / fail / n/a",
        "STATUS_HANDOFF_VERIFICATION_DATE_LINE": "- verification date: YYYY-MM-DD",
        "STATUS_HANDOFF_GIT_BRANCH_LINE": "- git branch: n/a",
        "STATUS_HANDOFF_GIT_COMMIT_LINE": "- git commit: n/a",
        "STATUS_HANDOFF_GIT_WORKTREE_LINE": "- git working tree: n/a / clean / dirty",
        "CHANGE_RECORDS_H1": "# {{PROJECT_NAME}} Change Records",
        "CHANGE_RECORDS_INTRO": "This file is the index for non-trivial project changes.",
        "CHANGE_RECORDS_PURPOSE_HEADING": "## Purpose",
        "CHANGE_RECORDS_RULES_HEADING": "## Rules",
        "CHANGE_RECORDS_INDEX_HEADING": "## Index",
        "CHANGE_RECORDS_EMPTY_INDEX_LINE": "- _no records yet_",
        "CHANGE_RECORDS_DETAILS_HEADING": "## Detailed Records",
        "CHANGE_RECORDS_DIRECTORY_LINE": "- directory: `{{CHANGE_RECORD_DIRECTORY}}/`",
        "CHANGE_RECORDS_TEMPLATE_LINE": "- template: [{{CHANGE_RECORD_DIRECTORY}}/_template.md]({{CHANGE_RECORD_DIRECTORY}}/_template.md)",
        "CHANGE_RECORDS_README_H1": "# Change Records",
        "CHANGE_RECORDS_README_TEMPLATE_LINE": "- [Record Template](_template.md)",
        "RELEASE_RECORDS_README_H1": "# Release Records",
        "RELEASE_RECORDS_README_TEMPLATE_LINE": "- [Release Template](_template.md)",
        "INCIDENT_RECORDS_README_H1": "# Incident Records",
        "INCIDENT_RECORDS_README_TEMPLATE_LINE": "- [Incident Template](_template.md)",
        "RECORD_METADATA_HEADING": "## Metadata",
        "RECORD_DATE_LINE": "- date: {{DATE}}",
        "RECORD_EXECUTOR_LINE": "- executor: {{EXECUTOR}}",
        "RECORD_BRANCH_LINE": "- branch: {{BRANCH}}",
        "RECORD_RELATED_COMMITS_LINE": "- related commit(s): {{RELATED_COMMITS}}",
        "RECORD_STATUS_LINE": "- status: {{STATUS}}",
        "CHANGE_RECORD_BACKGROUND_HEADING": "## Background",
        "CHANGE_RECORD_ANALYSIS_HEADING": "## Analysis",
        "CHANGE_RECORD_ANALYSIS_PLACEHOLDER": "- _fill in context and options_",
        "CHANGE_RECORD_CHOSEN_PLAN_HEADING": "## Chosen Plan",
        "CHANGE_RECORD_CHOSEN_PLAN_PLACEHOLDER": "- _fill in chosen plan_",
        "CHANGE_RECORD_EXECUTION_HEADING": "## Execution",
        "CHANGE_RECORD_EXECUTION_PLACEHOLDER": "- _fill in what changed_",
        "CHANGE_RECORD_VERIFICATION_HEADING": "## Verification",
        "CHANGE_RECORD_VERIFICATION_PLACEHOLDER": "- _fill in verification_",
        "CHANGE_RECORD_ROLLBACK_HEADING": "## Rollback",
        "CHANGE_RECORD_ROLLBACK_PLACEHOLDER": "- _fill in rollback_",
        "CHANGE_RECORD_DATA_SIDE_EFFECTS_HEADING": "## Data Side-effects",
        "CHANGE_RECORD_DATA_SIDE_EFFECTS_PLACEHOLDER": "- _fill in data or operational side-effects_",
        "CHANGE_RECORD_FOLLOW_UP_HEADING": "## Follow-up",
        "CHANGE_RECORD_FOLLOW_UP_PLACEHOLDER": "- _fill in follow-up_",
        "CHANGE_RECORD_ARCHITECTURE_BOUNDARY_HEADING": "## Architecture Boundary Check",
        "CHANGE_RECORD_ARCHITECTURE_BOUNDARY_LINE": "- highest rule impact: _fill in_",
        "RELEASE_RECORD_SCOPE_HEADING": "## Scope",
        "RELEASE_RECORD_RISKS_HEADING": "## Risks",
        "RELEASE_RECORD_RISKS_PLACEHOLDER": "- _fill in risks_",
        "INCIDENT_RECORD_SUMMARY_HEADING": "## Summary",
        "INCIDENT_RECORD_IMPACT_HEADING": "## Impact",
        "INCIDENT_RECORD_IMPACT_PLACEHOLDER": "- _fill in impact_",
        "INCIDENT_RECORD_TIMELINE_HEADING": "## Timeline",
        "INCIDENT_RECORD_TIMELINE_PLACEHOLDER": "- _fill in timeline_",
        "INCIDENT_RECORD_ROOT_CAUSE_HEADING": "## Root Cause",
        "INCIDENT_RECORD_ROOT_CAUSE_PLACEHOLDER": "- _fill in root cause_",
        "INCIDENT_RECORD_RESOLUTION_HEADING": "## Resolution",
        "INCIDENT_RECORD_RESOLUTION_PLACEHOLDER": "- _fill in resolution_",
    }


TEMPLATE_LINE_TRANSLATIONS = {
    "zh": {
        "Track why the project changed, what was verified, how rollback should work, and which durable rules moved.": "记录项目为什么发生变化、验证了什么、如何回退，以及哪些长期规则被调整。",
        "Git records code differences. Change records explain:": "Git 记录代码差异；变更记录需要解释：",
        "- why the change happened": "- 变更为什么发生",
        "- how the decision was made": "- 决策如何形成",
        "- what was verified": "- 验证了什么",
        "- how rollback works": "- 如何回退",
        "- what data or operational side-effects exist": "- 有哪些数据或运行副作用",
        "Track why Sula changed, how sync impact was evaluated, what was verified, and how rollback should work.": "记录 Sula 为什么变化、如何评估 sync 影响、验证了什么，以及如何回退。",
        "- keep this file short and index-oriented": "- 保持这个文件简短，并以索引为主",
        "- put detailed records in `{{CHANGE_RECORD_DIRECTORY}}/`": "- 详细记录放在 `{{CHANGE_RECORD_DIRECTORY}}/` 中",
        "- use release records for rollout history beyond one change": "- 对超出单次变更的发布历史，使用发布记录",
        "- use incident records for broken flows, outages, or recovery work": "- 对中断流程、故障或恢复工作，使用事故记录",
        "- use release records for rollout history that goes beyond a single code change": "- 对超出单次代码变更的发布历史，使用发布记录",
        "- mention sync impact explicitly in non-trivial records": "- 在非琐碎记录中显式写出 sync 影响",
        "- use release records when the rollout itself needs durable history": "- 当发布过程本身需要长期留痕时，使用发布记录",
        "Store detailed non-trivial change records in this directory.": "在这个目录中保存详细的非琐碎变更记录。",
        "## Naming Rule": "## 命名规则",
        "## When To Add One": "## 何时新增",
        "- architecture-affecting change": "- 影响架构的变更",
        "- non-trivial bug fix": "- 非琐碎缺陷修复",
        "- deployment-risk change": "- 带发布风险的变更",
        "- auth/session/permission change": "- 认证 / 会话 / 权限变更",
        "- data-side-effect change": "- 带数据副作用的变更",
        "## Template": "## 模板",
        "Store release-specific rollout notes in this directory when deployment history matters.": "当发布历史需要长期保留时，在这个目录中记录发布过程说明。",
        "Store incident or recovery history in this directory.": "在这个目录中记录事故或恢复历史。",
        "## Metadata": "## 元数据",
        "## Background": "## 背景",
        "## Analysis": "## 分析",
        "## Chosen Plan": "## 选定方案",
        "## Execution": "## 执行",
        "## Verification": "## 验证",
        "## Rollback": "## 回退",
        "## Data Side-effects": "## 数据副作用",
        "## Follow-up": "## 后续",
        "## Architecture Boundary Check": "## 架构边界检查",
        "- date: {{DATE}}": "- 日期: {{DATE}}",
        "- executor: {{EXECUTOR}}": "- 执行者: {{EXECUTOR}}",
        "- branch: {{BRANCH}}": "- 分支: {{BRANCH}}",
        "- related commit(s): {{RELATED_COMMITS}}": "- 关联提交: {{RELATED_COMMITS}}",
        "- status: {{STATUS}}": "- 状态: {{STATUS}}",
        "- _fill in context and options_": "- _补充背景与选项_",
        "- _fill in chosen plan_": "- _补充选定方案_",
        "- _fill in what changed_": "- _补充已执行的变更_",
        "- _fill in verification_": "- _补充验证方式_",
        "- _fill in rollback_": "- _补充回退方式_",
        "- _fill in data or operational side-effects_": "- _补充数据或运行副作用_",
        "- _fill in follow-up_": "- _补充后续事项_",
        "- highest rule impact: _fill in_": "- 最高规则影响: _补充说明_",
        "## Scope": "## 范围",
        "## Risks": "## 风险",
        "- _fill in risks_": "- _补充风险_",
        "## Summary": "## 摘要",
        "## Impact": "## 影响",
        "- _fill in impact_": "- _补充影响_",
        "## Timeline": "## 时间线",
        "- _fill in timeline_": "- _补充时间线_",
        "## Root Cause": "## 根因",
        "- _fill in root cause_": "- _补充根因_",
        "## Resolution": "## 解决",
        "- _fill in resolution_": "- _补充解决方式_",
    }
}


def localize_template_text(text: str, locale: str) -> str:
    family = locale_family(locale)
    replacements = TEMPLATE_LINE_TRANSLATIONS.get(family, {})
    if not replacements:
        return text
    lines = [replacements.get(line, line) for line in text.splitlines()]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sula project operating system manager")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create manifest if missing and render the selected Sula projections")
    add_project_root_arg(init_cmd)
    init_cmd.add_argument("--name")
    init_cmd.add_argument("--slug")
    init_cmd.add_argument("--description")
    init_cmd.add_argument("--profile", default="react-frontend-erpnext")
    add_onboarding_metadata_args(init_cmd)
    init_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    sync_cmd = sub.add_parser("sync", help="Sync the enabled Sula projections into a project")
    add_project_root_arg(sync_cmd)
    sync_cmd.add_argument("--dry-run", action="store_true", help="Show the managed-file sync plan without writing")
    sync_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    remove_cmd = sub.add_parser("remove", help="Inspect, report, and remove Sula from a project")
    add_project_root_arg(remove_cmd)
    remove_cmd.add_argument("--approve", action="store_true", help="Apply the removal plan after reporting it")
    remove_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    projection_cmd = sub.add_parser("projection", help="Inspect and control visible Sula projection packs")
    projection_sub = projection_cmd.add_subparsers(dest="projection_command", required=True)

    projection_list_cmd = projection_sub.add_parser("list", help="List active and available projection packs")
    add_project_root_arg(projection_list_cmd)
    projection_list_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    projection_mode_cmd = projection_sub.add_parser("mode", help="Switch the projection mode for this project")
    add_project_root_arg(projection_mode_cmd)
    projection_mode_cmd.add_argument("--set", dest="mode", choices=PROJECTION_MODE_CHOICES, required=True)
    projection_mode_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    projection_enable_cmd = projection_sub.add_parser("enable", help="Enable one visible projection pack and sync it")
    add_project_root_arg(projection_enable_cmd)
    projection_enable_cmd.add_argument("--pack", required=True)
    projection_enable_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    projection_disable_cmd = projection_sub.add_parser("disable", help="Disable one visible projection pack and clean managed leftovers")
    add_project_root_arg(projection_disable_cmd)
    projection_disable_cmd.add_argument("--pack", required=True)
    projection_disable_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

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
    onboard_cmd.add_argument("--project-root", help="Path to the target project root (not needed when --repo-url is provided)")
    onboard_cmd.add_argument("--repo-url", help="Git repository URL to clone and onboard (alternative to --project-root)")
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

    check_cmd = sub.add_parser("check", help="Run the daily Sula state-sync verification workflow")
    add_project_root_arg(check_cmd)
    check_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    status_cmd = sub.add_parser("status", help="Summarize current project state")
    add_project_root_arg(status_cmd)
    status_cmd.add_argument("--refresh-provider", action="store_true", help="Refresh collaborative provider-native truth sources before summarizing")
    status_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    session_cmd = sub.add_parser("session", help="Show Sula session startup context for any coding CLI")
    session_sub = session_cmd.add_subparsers(dest="session_command", required=True)
    session_start_cmd = session_sub.add_parser("start", help="Print the Sula-owned session status banner")
    add_project_root_arg(session_start_cmd)
    session_start_cmd.add_argument("--host-agent", default="", help="Optional current CLI/agent name")
    session_start_cmd.add_argument("--host-provider", default="", help="Optional current chat provider")
    session_start_cmd.add_argument("--host-model", default="", help="Optional current chat model")
    session_start_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    agent_routing_cmd = sub.add_parser("agent-routing", help="Inspect role-based model routing policy")
    agent_routing_sub = agent_routing_cmd.add_subparsers(dest="agent_routing_command", required=True)
    agent_routing_status_cmd = agent_routing_sub.add_parser("status", help="Show resolved agent routing policy and provider readiness")
    add_project_root_arg(agent_routing_status_cmd)
    agent_routing_status_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    agent_routing_doctor_cmd = agent_routing_sub.add_parser("doctor", help="Validate local agent provider routing config")
    add_project_root_arg(agent_routing_doctor_cmd)
    agent_routing_doctor_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    agent_routing_configure_cmd = agent_routing_sub.add_parser("configure", help="Remember the executor CLI/model routing choice")
    add_project_root_arg(agent_routing_configure_cmd)
    agent_routing_configure_cmd.add_argument("--runner", choices=ORCHESTRATION_RUNNER_CHOICES, help="Runner adapter to use for executor dispatch")
    agent_routing_configure_cmd.add_argument("--runner-command", help="Local command used by shell-command or codex-sdk runners")
    agent_routing_configure_cmd.add_argument("--runner-endpoint", help="HTTP endpoint used by codex-app-server runners")
    agent_routing_configure_cmd.add_argument("--provider", help="Executor provider label, such as claudecode, hermes, or deepseek")
    agent_routing_configure_cmd.add_argument("--model", help="Executor model label to display and pass to runners")
    agent_routing_configure_cmd.add_argument("--reasoning-effort", help="Executor reasoning effort label, such as high or xhigh")
    agent_routing_configure_cmd.add_argument("--provider-kind", default="cli", help="Local provider kind recorded in .sula/local/agent-providers.json")
    agent_routing_configure_cmd.add_argument("--endpoint-env", default="", help="Optional env var name for provider endpoint")
    agent_routing_configure_cmd.add_argument("--api-key-env", default="", help="Optional env var name for provider API key")
    agent_routing_configure_cmd.add_argument("--workspace-mode", choices=ORCHESTRATION_WORKSPACE_MODE_CHOICES, help="Workspace mode for executor runs")
    write_access_group = agent_routing_configure_cmd.add_mutually_exclusive_group()
    write_access_group.add_argument("--write-access", dest="write_access", action="store_true", help="Allow executor role to write in its workspace")
    write_access_group.add_argument("--no-write-access", dest="write_access", action="store_false", help="Keep executor role read-only")
    agent_routing_configure_cmd.set_defaults(write_access=None)
    agent_routing_configure_cmd.add_argument("--replace", action="store_true", help="Replace the remembered routing choice")
    agent_routing_configure_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    workflow_cmd = sub.add_parser("workflow", help="Assess workflow policy and scaffold durable workflow documents")
    workflow_sub = workflow_cmd.add_subparsers(dest="workflow_command", required=True)

    workflow_assess_cmd = workflow_sub.add_parser("assess", help="Assess workflow rigor and recommended next artifacts for a task")
    add_project_root_arg(workflow_assess_cmd)
    workflow_assess_cmd.add_argument("--task", help="Optional task description to assess")
    workflow_assess_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    workflow_scaffold_cmd = workflow_sub.add_parser("scaffold", help="Create a durable workflow source document")
    add_project_root_arg(workflow_scaffold_cmd)
    workflow_scaffold_cmd.add_argument("--kind", required=True, choices=WORKFLOW_SCAFFOLD_KIND_CHOICES)
    workflow_scaffold_cmd.add_argument("--title", required=True)
    workflow_scaffold_cmd.add_argument("--slug")
    workflow_scaffold_cmd.add_argument("--date")
    workflow_scaffold_cmd.add_argument("--summary", default="")
    workflow_scaffold_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    workflow_branch_cmd = workflow_sub.add_parser("branch", help="Plan or create the workspace-isolation branch/worktree for a task")
    add_project_root_arg(workflow_branch_cmd)
    workflow_branch_cmd.add_argument("--task", required=True, help="Task description used to derive the branch or worktree name")
    workflow_branch_cmd.add_argument("--slug", help="Optional slug override for the branch or worktree name")
    workflow_branch_cmd.add_argument("--create", action="store_true", help="Create the branch or worktree instead of only planning it")
    workflow_branch_cmd.add_argument("--base-branch", help="Optional base branch override")
    workflow_branch_cmd.add_argument("--worktree-root", help="Optional worktree directory root for worktree isolation")
    workflow_branch_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    workflow_close_cmd = workflow_sub.add_parser("close", help="Evaluate whether a task is ready to close under the project's workflow policy")
    add_project_root_arg(workflow_close_cmd)
    workflow_close_cmd.add_argument("--task", required=True, help="Task description used to derive required workflow artifacts")
    workflow_close_cmd.add_argument("--slug", help="Optional slug override for matching workflow documents")
    workflow_close_cmd.add_argument("--doctor-strict", action="store_true", help="Also require `doctor --strict` to pass")
    workflow_close_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    workflow_start_cmd = workflow_sub.add_parser("start", help="Composite entry point: assess, scaffold, branch, and intake a task in one step")
    add_project_root_arg(workflow_start_cmd)
    workflow_start_cmd.add_argument("--task", required=True, help="Task description")
    workflow_start_cmd.add_argument("--title", help="Short title (defaults to --task)")
    workflow_start_cmd.add_argument("--acceptance", action="append", default=[], help="Acceptance criterion (repeatable)")
    workflow_start_cmd.add_argument("--validation", action="append", default=[], help="Validation requirement (repeatable)")
    workflow_start_cmd.add_argument("--label", action="append", default=[], help="Task label (repeatable)")
    workflow_start_cmd.add_argument("--priority", default="normal", help="Task priority (default normal)")
    workflow_start_cmd.add_argument("--skip-branch", action="store_true", help="Skip branch/worktree creation")
    workflow_start_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_cmd = sub.add_parser("orchestration", help="Inspect and run optional task orchestration")
    orchestration_sub = orchestration_cmd.add_subparsers(dest="orchestration_command", required=True)

    orchestration_status_cmd = orchestration_sub.add_parser("status", help="Summarize orchestration config and run state")
    add_project_root_arg(orchestration_status_cmd)
    orchestration_status_cmd.add_argument("--compact", action="store_true", help="Print one compact execution status line")
    orchestration_status_cmd.add_argument("--watch", action="store_true", help="Refresh status until the active run reaches a terminal state")
    orchestration_status_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_tasks_cmd = orchestration_sub.add_parser("tasks", help="List normalized orchestration tasks")
    add_project_root_arg(orchestration_tasks_cmd)
    orchestration_tasks_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_timeline_cmd = orchestration_sub.add_parser("timeline", help="Show recent orchestration role/stage events")
    add_project_root_arg(orchestration_timeline_cmd)
    orchestration_timeline_cmd.add_argument("--limit", type=int, default=20)
    orchestration_timeline_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_intake_cmd = orchestration_sub.add_parser("intake", help="Capture a CLI/user intent as a normalized local orchestration task")
    add_project_root_arg(orchestration_intake_cmd)
    orchestration_intake_cmd.add_argument("--title", required=True)
    orchestration_intake_cmd.add_argument("--description", default="")
    orchestration_intake_cmd.add_argument("--acceptance", action="append", default=[], help="Acceptance criterion. Repeat for multiple criteria.")
    orchestration_intake_cmd.add_argument("--validation", action="append", default=[], help="Validation requirement. Repeat for multiple requirements.")
    orchestration_intake_cmd.add_argument("--label", action="append", default=[], help="Task label. Repeat for multiple labels.")
    orchestration_intake_cmd.add_argument("--risk-hint", action="append", default=[], help="Risk hint. Repeat for multiple hints.")
    orchestration_intake_cmd.add_argument("--priority", default="normal")
    orchestration_intake_cmd.add_argument("--identifier")
    orchestration_intake_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_trigger_cmd = orchestration_sub.add_parser("trigger", help="Capture any Sula-connected event as normalized orchestration task intent")
    add_project_root_arg(orchestration_trigger_cmd)
    orchestration_trigger_cmd.add_argument("--source-kind", required=True, choices=ORCHESTRATION_TRIGGER_SOURCE_KIND_CHOICES)
    orchestration_trigger_cmd.add_argument("--source-url", default="")
    orchestration_trigger_cmd.add_argument("--identity-key", required=True, help="Stable source identity used for dedupe across triggers")
    orchestration_trigger_cmd.add_argument("--event-kind", default="intent")
    orchestration_trigger_cmd.add_argument("--title", required=True)
    orchestration_trigger_cmd.add_argument("--description", default="")
    orchestration_trigger_cmd.add_argument("--acceptance", action="append", default=[], help="Acceptance criterion. Repeat for multiple criteria.")
    orchestration_trigger_cmd.add_argument("--validation", action="append", default=[], help="Validation requirement. Repeat for multiple requirements.")
    orchestration_trigger_cmd.add_argument("--label", action="append", default=[], help="Task label. Repeat for multiple labels.")
    orchestration_trigger_cmd.add_argument("--risk-hint", action="append", default=[], help="Risk hint. Repeat for multiple hints.")
    orchestration_trigger_cmd.add_argument("--priority", default="normal")
    orchestration_trigger_cmd.add_argument("--run", action="store_true", help="Immediately dispatch the task when it is eligible")
    orchestration_trigger_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_run_cmd = orchestration_sub.add_parser("run", help="Create a bounded orchestration run for one task")
    add_project_root_arg(orchestration_run_cmd)
    orchestration_run_cmd.add_argument("--task-id", required=True)
    orchestration_run_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_close_cmd = orchestration_sub.add_parser("close", help="Evaluate closeout evidence and optionally accept a run")
    add_project_root_arg(orchestration_close_cmd)
    orchestration_close_cmd.add_argument("--run-id", required=True)
    orchestration_close_cmd.add_argument("--evidence", action="append", default=[], help="Validation evidence summary. Repeat for multiple evidence items.")
    orchestration_close_cmd.add_argument("--touched-file", action="append", default=[], help="Touched file path. Repeat for multiple files.")
    orchestration_close_cmd.add_argument("--link", action="append", default=[], help="Related artifact, PR, provider item, or record link.")
    orchestration_close_cmd.add_argument("--lesson", action="append", default=[], help="Reusable lesson proposed for later memory or feedback review.")
    orchestration_close_cmd.add_argument("--accept", action="store_true", help="Mark the run accepted when evidence is sufficient")
    orchestration_close_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_cancel_cmd = orchestration_sub.add_parser("cancel", help="Mark an orchestration run as cancelled")
    add_project_root_arg(orchestration_cancel_cmd)
    orchestration_cancel_cmd.add_argument("--run-id", required=True)
    orchestration_cancel_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_stop_all_cmd = orchestration_sub.add_parser("stop-all", help="Cancel all active orchestration runs")
    add_project_root_arg(orchestration_stop_all_cmd)
    orchestration_stop_all_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    orchestration_doctor_cmd = orchestration_sub.add_parser("doctor", help="Check orchestration policy and local state")
    add_project_root_arg(orchestration_doctor_cmd)
    orchestration_doctor_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    canary_cmd = sub.add_parser("canary", help="Inspect and verify rollout canaries from the adopted-project registry")
    canary_sub = canary_cmd.add_subparsers(dest="canary_command", required=True)

    canary_list_cmd = canary_sub.add_parser("list", help="List canary projects from the adoption registry")
    add_project_root_arg(canary_list_cmd)
    canary_list_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    canary_verify_cmd = canary_sub.add_parser("verify", help="Run sync/doctor/check against local canary projects")
    add_project_root_arg(canary_verify_cmd)
    canary_verify_group = canary_verify_cmd.add_mutually_exclusive_group()
    canary_verify_group.add_argument("--slug", action="append", default=[], help="Only verify one or more specific canary slugs")
    canary_verify_group.add_argument("--all", action="store_true", help="Verify all registry entries that are marked as canaries")
    canary_verify_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    release_cmd = sub.add_parser("release", help="Audit release readiness and prepare clean public-release exports")
    release_sub = release_cmd.add_subparsers(dest="release_command", required=True)

    release_readiness_cmd = release_sub.add_parser("readiness", help="Audit current-tree, canary, and public-release readiness")
    add_project_root_arg(release_readiness_cmd)
    release_readiness_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    release_export_cmd = release_sub.add_parser("export-public", help="Export a clean tracked-file tree for a fresh public repository")
    add_project_root_arg(release_export_cmd)
    release_export_cmd.add_argument("--output", required=True, help="Destination directory for the clean export")
    release_export_cmd.add_argument("--overwrite", action="store_true", help="Overwrite the destination if it already exists")
    release_export_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_cmd = sub.add_parser("artifact", help="Create, register, and locate project artifacts")
    artifact_sub = artifact_cmd.add_subparsers(dest="artifact_command", required=True)
    artifact_create_cmd = artifact_sub.add_parser("create", help="Create a managed project artifact in the workflow slot")
    add_project_root_arg(artifact_create_cmd)
    artifact_create_cmd.add_argument(
        "--kind",
        required=True,
        help="Artifact kind such as agreement, proposal, report, process, training, invoice, or schedule",
    )
    artifact_create_cmd.add_argument("--title", required=True)
    artifact_create_cmd.add_argument("--slug")
    artifact_create_cmd.add_argument("--slot")
    artifact_create_cmd.add_argument("--date")
    artifact_create_cmd.add_argument("--summary", default="")
    artifact_create_cmd.add_argument("--extension", default=".md")
    artifact_create_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_register_cmd = artifact_sub.add_parser("register", help="Register an existing project artifact path")
    add_project_root_arg(artifact_register_cmd)
    artifact_register_cmd.add_argument("--path", help="Existing artifact path relative to project root or absolute within project root")
    artifact_register_cmd.add_argument("--kind", required=True)
    artifact_register_cmd.add_argument("--title")
    artifact_register_cmd.add_argument("--date")
    artifact_register_cmd.add_argument("--slot")
    artifact_register_cmd.add_argument("--summary", default="")
    artifact_register_cmd.add_argument("--project-relative-path", help="Stable project-relative location for provider-backed artifacts")
    artifact_register_cmd.add_argument("--provider-item-id", help="Stable provider item id such as a Google Doc or Sheet id")
    artifact_register_cmd.add_argument("--provider-item-kind", help="Provider item kind such as google-doc, google-sheet, or drive-file")
    artifact_register_cmd.add_argument("--provider-item-url", help="Stable provider URL for this artifact")
    artifact_register_cmd.add_argument(
        "--source-of-truth",
        choices=SOURCE_OF_TRUTH_CHOICES,
        help="Truth-source preference for this artifact family: auto, workspace, or provider-native",
    )
    artifact_register_cmd.add_argument(
        "--collaboration-mode",
        choices=COLLABORATION_MODE_CHOICES,
        help="Collaboration mode for this artifact: single-editor or multi-editor",
    )
    artifact_register_cmd.add_argument(
        "--artifact-role",
        choices=ARTIFACT_ROLE_CHOICES,
        help="Optional explicit artifact role: workspace-source, provider-native-source, or exported-derivative",
    )
    artifact_register_cmd.add_argument("--last-refreshed-at", help="ISO timestamp for the last truth-source refresh or evaluation")
    artifact_register_cmd.add_argument("--last-provider-sync-at", help="ISO timestamp for the latest known provider-side update")
    artifact_register_cmd.add_argument(
        "--derived-from",
        action="append",
        default=[],
        help="Artifact id this artifact derives from. Repeat for multiple source artifacts.",
    )
    artifact_register_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_materialize_cmd = artifact_sub.add_parser(
        "materialize",
        help="Materialize a concrete document or spreadsheet artifact from a source file",
    )
    add_project_root_arg(artifact_materialize_cmd)
    artifact_materialize_cmd.add_argument("--source-path", required=True, help="Source file relative to project root")
    artifact_materialize_cmd.add_argument("--target-format", required=True, choices=["html", "docx", "xlsx"])
    artifact_materialize_cmd.add_argument("--kind", help="Artifact kind for routing, defaults to the source artifact kind when known")
    artifact_materialize_cmd.add_argument("--title", help="Artifact title, defaults to the source stem")
    artifact_materialize_cmd.add_argument("--slug")
    artifact_materialize_cmd.add_argument("--slot")
    artifact_materialize_cmd.add_argument("--date")
    artifact_materialize_cmd.add_argument("--summary", default="")
    artifact_materialize_cmd.add_argument("--sheet-name", default="Sheet1")
    artifact_materialize_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_import_plan_cmd = artifact_sub.add_parser(
        "import-plan",
        help="Prepare a machine-readable provider import plan and any required bridge artifact",
    )
    add_project_root_arg(artifact_import_plan_cmd)
    artifact_import_plan_group = artifact_import_plan_cmd.add_mutually_exclusive_group(required=True)
    artifact_import_plan_group.add_argument("--source-path", help="Source file relative to project root")
    artifact_import_plan_group.add_argument("--artifact-id", help="Existing artifact id to use as the import source")
    artifact_import_plan_cmd.add_argument("--provider", help="Target provider, defaults from the provider item kind")
    artifact_import_plan_cmd.add_argument("--provider-item-kind", required=True, choices=sorted(PROVIDER_IMPORT_KIND_SPECS))
    artifact_import_plan_cmd.add_argument("--target-format", choices=["html", "docx", "xlsx"], help="Optional bridge format override")
    artifact_import_plan_cmd.add_argument("--kind", help="Artifact kind for routing, defaults to the source artifact kind when known")
    artifact_import_plan_cmd.add_argument("--title", help="Import title, defaults to the source title or filename")
    artifact_import_plan_cmd.add_argument("--slug")
    artifact_import_plan_cmd.add_argument("--slot")
    artifact_import_plan_cmd.add_argument("--date")
    artifact_import_plan_cmd.add_argument("--project-relative-path", help="Stable provider-backed project-relative path after import")
    artifact_import_plan_cmd.add_argument("--summary", default="")
    artifact_import_plan_cmd.add_argument("--sheet-name", default="Sheet1")
    artifact_import_plan_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_locate_cmd = artifact_sub.add_parser("locate", help="Locate registered artifacts")
    add_project_root_arg(artifact_locate_cmd)
    artifact_locate_cmd.add_argument("--kind")
    artifact_locate_cmd.add_argument("--q", default="")
    artifact_locate_cmd.add_argument("--limit", type=int, default=10)
    artifact_locate_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    artifact_refresh_cmd = artifact_sub.add_parser("refresh", help="Refresh provider-native truth sources and freshness metadata")
    add_project_root_arg(artifact_refresh_cmd)
    artifact_refresh_group = artifact_refresh_cmd.add_mutually_exclusive_group(required=True)
    artifact_refresh_group.add_argument("--artifact-id", help="Refresh one artifact family by registered artifact id")
    artifact_refresh_group.add_argument("--family-key", help="Refresh one artifact family by family key")
    artifact_refresh_group.add_argument("--q", help="Refresh provider-native artifact families matching this query")
    artifact_refresh_group.add_argument("--all-collaborative", action="store_true", help="Refresh all collaborative provider-native artifact families")
    artifact_refresh_cmd.add_argument("--limit", type=int, default=5)
    artifact_refresh_cmd.add_argument("--force", action="store_true", help="Refresh even when TTL says the cached provider check is still fresh")
    artifact_refresh_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    report_cmd = sub.add_parser("report", help="Write a session report into STATUS.md Summary and regenerate derived state")
    add_project_root_arg(report_cmd)
    report_cmd.add_argument("--summary", required=True, help="Human-readable summary of what was done this session")
    report_cmd.add_argument("--lightweight", action="store_true", help="Write summary to STATUS.md only; skip memory-digest and kernel regeneration")
    report_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    test_cmd = sub.add_parser("test", help="Run project tests with tiered scope (quick module full)")
    add_project_root_arg(test_cmd)
    test_cmd.add_argument("--quick", action="store_true", help="Run quick validation: check + doctor --strict")
    test_cmd.add_argument("--module", help="Run tests matching a module prefix (e.g. orchestration, check, adopt)")
    test_cmd.add_argument("--full", action="store_true", help="Run the full test suite (all tests)")
    test_cmd.add_argument("--list", action="store_true", dest="list_modules", help="List available test modules with test counts")

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
    memory_capture_cmd = memory_sub.add_parser("capture", help="Capture temporary session context for later review or promotion")
    add_project_root_arg(memory_capture_cmd)
    memory_capture_cmd.add_argument("--title", required=True)
    memory_capture_cmd.add_argument("--summary", required=True)
    memory_capture_cmd.add_argument("--category", choices=MEMORY_CAPTURE_CATEGORY_CHOICES, default="note")
    memory_capture_cmd.add_argument("--source-path", help="Optional project-relative source path that informed the capture")
    memory_capture_cmd.add_argument("--confidence", type=int, choices=[1, 2, 3, 4, 5], default=3)
    memory_capture_cmd.add_argument("--session-id", default="")
    memory_capture_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    memory_review_cmd = memory_sub.add_parser("review", help="Review staged or historical session captures")
    add_project_root_arg(memory_review_cmd)
    memory_review_cmd.add_argument("--status", choices=MEMORY_CAPTURE_STATUS_CHOICES)
    memory_review_cmd.add_argument("--limit", type=int, default=20)
    memory_review_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    memory_promote_cmd = memory_sub.add_parser("promote", help="Promote a reviewed capture into a durable operating source")
    add_project_root_arg(memory_promote_cmd)
    memory_promote_cmd.add_argument("--capture-id", required=True)
    memory_promote_cmd.add_argument("--to", choices=MEMORY_PROMOTION_TARGET_CHOICES, required=True)
    memory_promote_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    memory_clear_cmd = memory_sub.add_parser("clear", help="Clear disposable memory state")
    add_project_root_arg(memory_clear_cmd)
    memory_clear_group = memory_clear_cmd.add_mutually_exclusive_group(required=True)
    memory_clear_group.add_argument("--derived", action="store_true", help="Delete disposable query and sqlite caches")
    memory_clear_group.add_argument("--reviewed-captures", action="store_true", help="Delete promoted and discarded captures from the session store")
    memory_clear_group.add_argument("--all-captures", action="store_true", help="Delete the entire session capture store")
    memory_clear_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    memory_jobs_cmd = memory_sub.add_parser("jobs", help="Inspect memory-related job history")
    add_project_root_arg(memory_jobs_cmd)
    memory_jobs_cmd.add_argument("--limit", type=int, default=20)
    memory_jobs_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

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

    portfolio_orchestration_cmd = portfolio_sub.add_parser("orchestration", help="Summarize orchestration state across registered projects")
    add_portfolio_root_arg(portfolio_orchestration_cmd)
    portfolio_orchestration_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

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

    feedback_cmd = sub.add_parser("feedback", help="Capture and review reusable feedback between adopted projects and Sula Core")
    feedback_sub = feedback_cmd.add_subparsers(dest="feedback_command", required=True)

    feedback_capture_cmd = feedback_sub.add_parser("capture", help="Capture local managed-file feedback from an adopted project")
    add_project_root_arg(feedback_capture_cmd)
    feedback_capture_cmd.add_argument("--title", required=True)
    feedback_capture_cmd.add_argument("--summary", required=True)
    feedback_capture_cmd.add_argument("--kind", choices=FEEDBACK_KIND_CHOICES, default="improvement")
    feedback_capture_cmd.add_argument("--severity", choices=FEEDBACK_SEVERITY_CHOICES, default="medium")
    feedback_capture_cmd.add_argument("--shared-rationale", required=True)
    feedback_capture_cmd.add_argument("--local-fix-summary", default="")
    feedback_capture_cmd.add_argument("--requested-outcome", default="")
    feedback_capture_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    feedback_ingest_cmd = feedback_sub.add_parser("ingest", help="Ingest a feedback bundle into Sula Core review state")
    add_project_root_arg(feedback_ingest_cmd)
    feedback_ingest_cmd.add_argument("--bundle-path", required=True, help="Path to a feedback bundle directory or zip archive")
    feedback_ingest_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    feedback_list_cmd = feedback_sub.add_parser("list", help="List feedback tracked by Sula Core")
    add_project_root_arg(feedback_list_cmd)
    feedback_list_cmd.add_argument("--status", choices=["open", *FEEDBACK_DECISION_CHOICES])
    feedback_list_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    feedback_show_cmd = feedback_sub.add_parser("show", help="Show one feedback bundle tracked by Sula Core")
    add_project_root_arg(feedback_show_cmd)
    feedback_show_cmd.add_argument("--feedback-id", required=True)
    feedback_show_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    feedback_decide_cmd = feedback_sub.add_parser("decide", help="Record a Sula Core review decision for one feedback item")
    add_project_root_arg(feedback_decide_cmd)
    feedback_decide_cmd.add_argument("--feedback-id", required=True)
    feedback_decide_cmd.add_argument("--decision", required=True, choices=FEEDBACK_DECISION_CHOICES)
    feedback_decide_cmd.add_argument("--note", required=True)
    feedback_decide_cmd.add_argument("--target-version")
    feedback_decide_cmd.add_argument("--linked-change-record")
    feedback_decide_cmd.add_argument("--linked-release")
    feedback_decide_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    provider_cmd = sub.add_parser("provider", help="Inspect optional provider adapter capabilities")
    provider_sub = provider_cmd.add_subparsers(dest="provider_command", required=True)
    provider_capabilities_cmd = provider_sub.add_parser("capabilities", help="Report provider adapter capabilities for this project")
    add_project_root_arg(provider_capabilities_cmd)
    provider_capabilities_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    mcp_cmd = sub.add_parser("mcp", help="Expose Sula through a dependency-light MCP-compatible tool surface")
    mcp_sub = mcp_cmd.add_subparsers(dest="mcp_command", required=True)
    mcp_tools_cmd = mcp_sub.add_parser("tools", help="List Sula MCP-compatible tools")
    mcp_tools_cmd.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")

    mcp_call_cmd = mcp_sub.add_parser("call", help="Call one Sula MCP-compatible tool and print a JSON result")
    mcp_call_cmd.add_argument("--tool", required=True)
    mcp_call_cmd.add_argument("--project-root", help="Project root for project-scoped tools")
    add_portfolio_root_arg(mcp_call_cmd)
    mcp_call_cmd.add_argument("--arguments-json", default="{}", help="JSON object passed as tool arguments")
    mcp_call_cmd.add_argument("--policy-file", help="Optional local MCP policy file")
    mcp_call_cmd.add_argument("--allow-project-root", action="append", default=[], help="Allow one project root for this invocation")
    mcp_call_cmd.add_argument("--enable-write-class", action="append", default=[], help="Enable one write class for this invocation")

    mcp_serve_cmd = mcp_sub.add_parser("serve", help="Serve a minimal JSON-RPC MCP-compatible stdio loop")
    mcp_serve_cmd.add_argument("--policy-file", help="Optional local MCP policy file")
    mcp_serve_cmd.add_argument("--allow-project-root", action="append", default=[], help="Allow one project root for this server")
    mcp_serve_cmd.add_argument("--enable-write-class", action="append", default=[], help="Enable one write class for this server")
    add_portfolio_root_arg(mcp_serve_cmd)

    return parser.parse_args()


def add_project_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", required=True, help="Path to the target project root")


def add_onboarding_metadata_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--content-locale")
    parser.add_argument("--interaction-locale")
    parser.add_argument("--projection-mode", choices=PROJECTION_MODE_CHOICES)
    parser.add_argument("--workflow-pack")
    parser.add_argument("--workflow-stage")
    parser.add_argument("--workflow-docs-root")
    parser.add_argument("--workflow-execution-mode", choices=WORKFLOW_EXECUTION_MODE_CHOICES)
    parser.add_argument("--workflow-design-gate", choices=WORKFLOW_DESIGN_GATE_CHOICES)
    parser.add_argument("--workflow-plan-gate", choices=WORKFLOW_PLAN_GATE_CHOICES)
    parser.add_argument("--workflow-review-policy", choices=WORKFLOW_REVIEW_POLICY_CHOICES)
    parser.add_argument("--workflow-workspace-isolation", choices=WORKFLOW_ISOLATION_CHOICES)
    parser.add_argument("--workflow-testing-policy", choices=WORKFLOW_TESTING_POLICY_CHOICES)
    parser.add_argument("--workflow-closeout-policy", choices=WORKFLOW_CLOSEOUT_POLICY_CHOICES)
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


def agent_behavior_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "quality_policy": config.agent_quality_policy,
        "clarification_policy": config.agent_clarification_policy,
        "diff_scope_policy": config.agent_diff_scope_policy,
        "success_criteria_policy": config.agent_success_criteria_policy,
        "assumption_policy": config.agent_assumption_policy,
        "complexity_policy": config.agent_complexity_policy,
        "require_verification": config.agent_require_verification,
        "forbid_drive_by_refactors": config.agent_forbid_drive_by_refactors,
    }


def agent_routing_config_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "enabled": config.agent_routing_enabled,
        "mode": config.agent_routing_mode,
        "visibility": config.agent_routing_visibility,
        "default_budget_policy": config.agent_routing_default_budget_policy,
        "budget_breach_behavior": config.agent_routing_budget_breach_behavior,
        "max_review_cycles": config.agent_routing_max_review_cycles,
        "on_review_fail": config.agent_routing_on_review_fail,
        "require_final_acceptance": config.agent_routing_require_final_acceptance,
        "roles": config.agent_routing_roles,
    }


def automation_config_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "enabled": config.automation_enabled,
        "mode": config.automation_mode,
        "auto_intake": config.automation_auto_intake,
        "auto_plan": config.automation_auto_plan,
        "auto_dispatch": config.automation_auto_dispatch,
        "risk_ceiling": config.automation_risk_ceiling,
        "approval_required_for": config.automation_approval_required_for,
        "event_sources": config.automation_event_sources,
    }


def project_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "name": config.data["project"]["name"],
        "slug": config.data["project"]["slug"],
        "profile": config.profile,
        "projection_mode": config.projection_mode,
        "enabled_projection_packs": config.enabled_projection_packs,
        "root": str(config.root),
        "workflow_pack": config.workflow_pack,
        "workflow_stage": config.workflow_stage,
        "workflow_execution_mode": config.workflow_execution_mode,
        "workflow_docs_root": config.workflow_docs_root.relative_to(config.root).as_posix()
        if config.workflow_docs_root.is_relative_to(config.root)
        else str(config.workflow_docs_root),
        "automation": automation_config_payload(config),
        "orchestration": orchestration_config_payload(config),
        "agent_behavior": agent_behavior_payload(config),
        "agent_routing": agent_routing_config_payload(config),
        "storage_provider": config.storage_provider,
        "storage_sync_mode": config.storage_sync_mode,
        "portfolio_id": config.portfolio_setting("portfolio_id", "default"),
        "content_locale": config.content_locale,
        "interaction_locale": config.interaction_locale,
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
    if any(term in lowered for term in ["shot-list", "shoot", "filming", "footage", "storyboard", "post-production", "video production", "拍摄", "镜头", "后期", "视频制作"]):
        return ("video-production", "project text looks like a media-production workflow")
    if any(term in lowered for term in ["contract", "agreement", "invoice", "quote", "proposal", "staffing", "client", "supplier", "vendor", "service", "合同", "协议", "发票", "报价", "客户", "供应商", "服务"]):
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
    content_locale, content_locale_reason = infer_content_locale(project_root, readme_text)
    suggested_projection_mode = normalize_projection_mode(
        getattr(args, "projection_mode", None),
        default_projection_mode_for_new_manifest(profile),
    )
    resolved_content_locale = normalize_locale(getattr(args, "content_locale", None) or content_locale)
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
        "content_locale": {
            "value": resolved_content_locale,
            "reason": content_locale_reason,
        },
        "interaction_locale": {
            "value": normalize_locale(getattr(args, "interaction_locale", None) or resolved_content_locale),
            "reason": "interactive prompts default to the same language as generated docs and records",
        },
        "projection_mode": {
            "value": suggested_projection_mode,
            "reason": (
                "new projects default to the lowest visible Sula footprint first and can opt into deeper projections later"
                if suggested_projection_mode == "detached"
                else "this profile benefits from a deeper visible governance surface by default"
            ),
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
    zh = locale_family(str(suggestions["interaction_locale"]["value"])) == "zh"
    questions: list[dict[str, object]] = []

    def add_question(
        field: str,
        prompt: str,
        *,
        required: bool,
        choices: list[str] | None = None,
        allow_custom: bool = False,
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
                "allow_custom": allow_custom,
                "reason": suggestion["reason"],
            }
        )

    add_question("name", "项目显示名称" if zh else "Project display name", required=True)
    add_question("description", "项目一句话说明" if zh else "One-line project description", required=True)
    add_question(
        "content_locale",
        "生成文档与记录的默认语言" if zh else "Generated docs and records language",
        required=True,
        choices=LANGUAGE_CHOICES,
        allow_custom=True,
    )
    add_question(
        "projection_mode",
        "Sula 投影深度" if zh else "Sula projection depth",
        required=True,
        choices=PROJECTION_MODE_CHOICES,
    )
    add_question("workflow_pack", "工作流包" if zh else "Workflow pack", required=True, choices=WORKFLOW_PACK_CHOICES)
    add_question("storage_provider", "存储提供方" if zh else "Storage provider", required=True, choices=STORAGE_PROVIDER_CHOICES)
    if provider_value == "google-drive":
        add_question("storage_sync_mode", "存储同步模式" if zh else "Storage sync mode", required=True, choices=["local-sync"])
        add_question("storage_provider_root_url", "Google Drive 文件夹 URL" if zh else "Google Drive folder URL", required=False)
        add_question("storage_provider_root_id", "Google Drive 文件夹 ID" if zh else "Google Drive folder ID", required=False)
    add_question("portfolio_workspace", "Portfolio 工作区标签" if zh else "Portfolio workspace label", required=False)
    add_question("portfolio_owner", "Portfolio 负责人" if zh else "Portfolio owner label", required=False)
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
    allow_custom = bool(question.get("allow_custom", False))
    prompt = str(question["prompt"])
    zh = contains_cjk(prompt)
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
        if not choices or answer in choices or allow_custom:
            return answer
        print("请输入列出的值之一，或直接回车接受默认值。" if zh else "Please choose one of the listed values or press Enter to accept the default.")


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
    language = manifest["language"]
    projection = manifest.get("projection", {})
    zh = locale_family(str(language["interaction_locale"])) == "zh"
    artifacts_root = str(workflow["artifacts_root"])
    workflow_definition = workflow_pack_definition(str(workflow["pack"]))
    slot_paths = {
        slot: f"{artifacts_root}/{slot}"
        for slot in workflow_definition.get("slots", [])
        if isinstance(slot, str)
    }
    will_manage = [
        (
            f"{len(report.managed_creates) + len(report.managed_updates)} 个可覆盖更新的 projection 文件"
            if zh
            else f"{len(report.managed_creates) + len(report.managed_updates)} overwrite-capable projection files"
        ),
        (
            f"{len(report.scaffold_creates)} 个项目自有 scaffold 起始文件"
            if zh
            else f"{len(report.scaffold_creates)} project-owned scaffold starters"
        ),
        "`.sula/` 下的 kernel 状态，用于状态、对象、来源、事件与查询索引" if zh else "kernel state under `.sula/` for status, objects, sources, events, and query indexes",
        (
            f"当前 projection 模式为 `{projection.get('mode', 'detached')}`，已启用 {', '.join(projection.get('enabled_packs', [])) or 'none'}"
            if zh
            else f"projection mode `{projection.get('mode', 'detached')}` with visible packs {', '.join(projection.get('enabled_packs', [])) or 'none'}"
        ),
        (
            f"通过 `{workflow['pack']}` workflow pack 在 `{artifacts_root}` 下进行文件路由"
            if zh
            else f"artifact routing under `{artifacts_root}` through the `{workflow['pack']}` workflow pack"
        ),
        (
            f"记录 `{storage['provider']}` 的 storage adapter 元数据，但不把 provider 本身写成项目真相"
            if zh
            else f"storage adapter metadata for `{storage['provider']}` without making the provider part of project truth"
        ),
        (
            f"staged memory 工作流：先写入 `{manifest['memory']['promotion_file']}` 对应的提升链路，再通过 review / promote 决定哪些临时结论成为长期上下文"
            if zh
            else f"staged memory workflow with review and promotion into durable context through `{manifest['memory']['promotion_file']}`"
        ),
    ]
    if str(portfolio.get("workspace", "personal")) != "personal":
        will_manage.append(
            f"为工作区 `{portfolio['workspace']}` 记录 portfolio 注册元数据"
            if zh
            else f"portfolio registration metadata for workspace `{portfolio['workspace']}`"
        )
    next_commands = [
        "python3 scripts/sula.py status --project-root /path/to/project --json",
        "python3 scripts/sula.py query --project-root /path/to/project --q \"contract\" --json",
        "python3 scripts/sula.py memory capture --project-root /path/to/project --title \"...\" --summary \"...\"",
        "python3 scripts/sula.py memory review --project-root /path/to/project --json",
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
        "projection": {
            "mode": projection.get("mode", default_projection_mode_for_existing_consumer(str(manifest["project"]["profile"]))),
            "enabled_packs": projection.get("enabled_packs", []),
        },
        "memory": {
            "capture_policy": manifest["memory"]["capture_policy"],
            "promotion_policy": manifest["memory"]["promotion_policy"],
            "query_routing": manifest["memory"]["query_routing"],
            "promotion_file": manifest["memory"]["promotion_file"],
            "session_retention_days": manifest["memory"]["session_retention_days"],
        },
        "storage": storage,
        "portfolio": portfolio,
        "language": language,
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
    language = summary["language"]
    zh = locale_family(str(language["interaction_locale"])) == "zh"
    if zh:
        print(f"{summary['project_root']} 的 Sula 接入摘要")
        print(f"项目: {project['name']} [{summary['profile']}]")
        print(f"投影模式: {summary['projection']['mode']} ({', '.join(summary['projection']['enabled_packs']) or 'none'})")
        print(f"工作流包: {workflow['pack']} (阶段: {workflow['stage']})")
        print(
            f"记忆流程: capture={summary['memory']['capture_policy']} / promote={summary['memory']['promotion_policy']} / route={summary['memory']['query_routing']}"
        )
        print(f"提升文件: {summary['memory']['promotion_file']} (保留 {summary['memory']['session_retention_days']} 天 staged captures)")
        print(f"存储提供方: {storage['provider']} ({storage['sync_mode']})")
        print(f"Portfolio 工作区: {portfolio['workspace']} / 负责人: {portfolio['owner']}")
        print(f"文档语言: {language['content_locale']} / 交互语言: {language['interaction_locale']}")
        print("接入后你会得到：")
    else:
        print(f"Sula onboarding summary for {summary['project_root']}")
        print(f"Project: {project['name']} [{summary['profile']}]")
        print(f"Projection mode: {summary['projection']['mode']} ({', '.join(summary['projection']['enabled_packs']) or 'none'})")
        print(f"Workflow pack: {workflow['pack']} (stage: {workflow['stage']})")
        print(
            f"Memory lifecycle: capture={summary['memory']['capture_policy']} / promote={summary['memory']['promotion_policy']} / route={summary['memory']['query_routing']}"
        )
        print(f"Promotion file: {summary['memory']['promotion_file']} (keep staged captures for {summary['memory']['session_retention_days']} days)")
        print(f"Storage provider: {storage['provider']} ({storage['sync_mode']})")
        print(f"Portfolio workspace: {portfolio['workspace']} / owner: {portfolio['owner']}")
        print(f"Document language: {language['content_locale']} / interaction language: {language['interaction_locale']}")
        print("What you will get:")
    for item in summary["what_you_get"]:
        print(f"  - {item}")
    print("文件槽位：" if zh else "Artifact slots:")
    for slot, path in summary["workflow"]["slot_paths"].items():
        print(f"  - {slot}: {path}")
    print("建议下一步命令：" if zh else "Suggested next commands:")
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
                "timeline": "planning",
                "proposal": "planning",
                "plan": "planning",
                "spec": "planning",
                "brief": "planning",
                "process": "planning",
                "workflow": "planning",
                "procedure": "planning",
                "sop": "planning",
                "runbook": "planning",
                "review": "delivery",
                "deliverable": "delivery",
                "training": "delivery",
                "workshop": "delivery",
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
                "timeline": "planning",
                "proposal": "planning",
                "plan": "planning",
                "spec": "planning",
                "brief": "planning",
                "process": "planning",
                "workflow": "planning",
                "procedure": "planning",
                "sop": "planning",
                "runbook": "planning",
                "review": "delivery",
                "deliverable": "delivery",
                "progress": "delivery",
                "training": "delivery",
                "workshop": "delivery",
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
                "timeline": "planning",
                "proposal": "planning",
                "plan": "planning",
                "spec": "planning",
                "brief": "planning",
                "process": "planning",
                "workflow": "planning",
                "procedure": "planning",
                "sop": "planning",
                "runbook": "planning",
                "review": "delivery",
                "shot-list": "production",
                "progress": "production",
                "daily-log": "production",
                "deliverable": "delivery",
                "training": "delivery",
                "workshop": "delivery",
                "note": "intake",
            },
        },
        "software-delivery": {
            "slots": ["intake", "planning", "implementation", "delivery", "archive"],
            "artifact_slots": {
                "report": "delivery",
                "schedule": "planning",
                "timeline": "planning",
                "proposal": "planning",
                "plan": "planning",
                "spec": "planning",
                "brief": "planning",
                "process": "planning",
                "workflow": "planning",
                "procedure": "planning",
                "sop": "planning",
                "runbook": "planning",
                "review": "delivery",
                "deliverable": "delivery",
                "training": "delivery",
                "workshop": "delivery",
                "note": "intake",
            },
        },
        "operating-system": {
            "slots": ["design", "operations", "releases", "archive"],
            "artifact_slots": {
                "report": "operations",
                "schedule": "operations",
                "timeline": "operations",
                "proposal": "design",
                "plan": "design",
                "spec": "design",
                "process": "operations",
                "workflow": "operations",
                "procedure": "operations",
                "sop": "operations",
                "runbook": "operations",
                "review": "operations",
                "training": "operations",
                "workshop": "operations",
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
    project_root_raw = getattr(args, "project_root", None)
    project_root = Path(project_root_raw).expanduser().resolve() if project_root_raw else None

    if args.command == "init":
        assert project_root is not None
        config = ensure_manifest(project_root, args)
        apply_projection_state(config, collect_render_actions(config, include_scaffold=True))
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
        repo_url = getattr(args, "repo_url", None) or ""
        if repo_url.strip():
            import tempfile
            import subprocess
            tmp_dir = Path(tempfile.mkdtemp(prefix="sula-onboard-"))
            repo_dest = tmp_dir / "repo"
            print(f"Cloning {repo_url} ...")
            result = subprocess.run(["git", "clone", repo_url.strip(), str(repo_dest)], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to clone repository: {result.stderr.strip()}", file=sys.stderr)
                return 1
            project_root = repo_dest.resolve()
            print(f"Cloned to {project_root}")
        else:
            assert project_root is not None, "Use --project-root <path> or --repo-url <git-url>"
        return onboard(project_root, args)

    if args.command == "remove":
        assert project_root is not None
        return remove_sula(project_root, args)

    if args.command == "projection":
        assert project_root is not None
        return handle_projection_command(project_root, args)

    if args.command == "portfolio":
        return handle_portfolio_command(args)

    if args.command == "feedback":
        return handle_feedback_command(args)

    if args.command == "mcp":
        return handle_mcp_command(args)

    if args.command == "canary":
        assert project_root is not None
        return handle_canary_command(project_root, args)

    if args.command == "release":
        assert project_root is not None
        return handle_release_command(project_root, args)

    assert project_root is not None
    config = load_manifest(project_root)
    if args.command == "sync":
        actions = collect_render_actions(config, include_scaffold=True)
        if args.dry_run:
            pending = [action.relative_path.as_posix() for action in actions if action.status != "unchanged"]
            automation_result = automation_observe_event(
                config,
                source_kind="sula-cli",
                event_kind="sync.dry-run",
                title="Sula sync dry run",
                summary=f"Sync dry run found {len(pending)} pending managed-file action(s).",
                identity_key="sync-dry-run:" + date.today().isoformat(),
                payload={"pending_actions": pending[:20], "pending_count": len(pending)},
            )
            if getattr(args, "json", False):
                emit_json({"command": "sync", "status": "dry-run", "project": project_payload(config), "plan": sync_plan_payload(actions)})
                return 0
            print_sula_activity_feedback(config, automation_result)
            print_sync_plan(config, actions)
            return 0
        apply_projection_state(config, actions)
        write_lockfile(config)
        refresh_kernel_state(config, event_type="sync.applied", summary="Synchronized enabled Sula projections.")
        automation_result = automation_observe_event(
            config,
            source_kind="sula-cli",
            event_kind="sync.applied",
            title="Sula sync",
            summary="Synchronized enabled Sula projections.",
            identity_key="sync:" + date.today().isoformat(),
            payload={"action_count": len(actions)},
        )
        if getattr(args, "json", False):
            emit_json({"command": "sync", "status": "ok", "project": project_payload(config), "plan": sync_plan_payload(actions)})
            return 0
        print_sula_activity_feedback(config, automation_result)
        print(f"Synchronized enabled projections for {config.data['project']['name']}")
        return 0

    if args.command == "doctor":
        return doctor(config, strict=args.strict, json_mode=json_output_requested(args))

    if args.command == "check":
        return daily_check(config, json_mode=json_output_requested(args))

    if args.command == "status":
        return project_status(config, args)

    if args.command == "session":
        if args.session_command == "start":
            return session_start(config, args)
        raise AssertionError("unreachable")

    if args.command == "agent-routing":
        if args.agent_routing_command == "status":
            return agent_routing_status(config, args)
        if args.agent_routing_command == "doctor":
            return agent_routing_doctor(config, args)
        if args.agent_routing_command == "configure":
            return agent_routing_configure(project_root, config, args)
        raise AssertionError("unreachable")

    if args.command == "workflow":
        return handle_workflow_command(config, args)

    if args.command == "orchestration":
        return handle_orchestration_command(config, args)

    if args.command == "artifact":
        return handle_artifact_command(config, args)

    if args.command == "record":
        if args.record_command == "new":
            return create_record(config, args)
        raise AssertionError("unreachable")

    if args.command == "report":
        return cmd_report(config, args)

    if args.command == "memory":
        return handle_memory_command(config, args)

    if args.command == "query":
        return query_project_kernel(config, args)

    if args.command == "test":
        return cmd_test(config, args)

    if args.command == "provider":
        return handle_provider_command(config, args)

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
    projection = manifest_projection_config(args, profile)
    workflow = manifest_workflow_config(args, profile)
    orchestration = default_orchestration_config()
    automation = default_automation_config()
    agent_behavior = default_agent_behavior_config()
    agent_routing = default_agent_routing_config()
    storage = manifest_storage_config(args)
    portfolio = manifest_portfolio_config(args)
    language = manifest_language_config(args)
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
            "automation": automation,
            "orchestration": orchestration,
            "agent_behavior": agent_behavior,
            "agent_routing": agent_routing,
            "storage": storage,
            "portfolio": portfolio,
            "language": language,
            "document_design": default_document_design_config(projection_mode=projection["mode"]),
            "projection": projection,
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
            "automation": automation,
            "orchestration": orchestration,
            "agent_behavior": agent_behavior,
            "agent_routing": agent_routing,
            "storage": storage,
            "portfolio": portfolio,
            "language": language,
            "document_design": default_document_design_config(projection_mode=projection["mode"]),
            "projection": projection,
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
        "automation": automation,
        "orchestration": orchestration,
        "agent_behavior": agent_behavior,
        "agent_routing": agent_routing,
        "storage": storage,
        "portfolio": portfolio,
        "language": language,
        "document_design": default_document_design_config(projection_mode=projection["mode"]),
        "projection": projection,
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
        "automation",
        "orchestration",
        "agent_behavior",
        "agent_routing",
        "storage",
        "portfolio",
        "language",
        "document_design",
        "projection",
    ]:
        if section_name not in manifest:
            continue
        lines.append(f"[{section_name}]")
        for key, value in manifest[section_name].items():
            if section_name == "agent_routing" and key == "roles":
                continue
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
        if section_name == "agent_routing":
            roles = manifest[section_name].get("roles", {})
            if isinstance(roles, dict):
                for role_name in AGENT_ROUTING_ROLE_CHOICES:
                    role = roles.get(role_name, {})
                    if not isinstance(role, dict):
                        continue
                    lines.append(f"[agent_routing.roles.{role_name}]")
                    for key, value in role.items():
                        lines.append(f"{key} = {format_toml_value(value)}")
                    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def manifest_workflow_config(args: argparse.Namespace, profile: str) -> dict:
    pack = getattr(args, "workflow_pack", None) or default_workflow_pack(profile)
    defaults = default_workflow_policy_config(pack)
    return {
        "pack": pack,
        "stage": getattr(args, "workflow_stage", None) or "active",
        "artifacts_root": "artifacts",
        "docs_root": getattr(args, "workflow_docs_root", None) or "docs/workflows",
        "execution_mode": getattr(args, "workflow_execution_mode", None) or defaults["execution_mode"],
        "design_gate": getattr(args, "workflow_design_gate", None) or defaults["design_gate"],
        "plan_gate": getattr(args, "workflow_plan_gate", None) or defaults["plan_gate"],
        "review_policy": getattr(args, "workflow_review_policy", None) or defaults["review_policy"],
        "workspace_isolation": getattr(args, "workflow_workspace_isolation", None) or defaults["workspace_isolation"],
        "testing_policy": getattr(args, "workflow_testing_policy", None) or defaults["testing_policy"],
        "closeout_policy": getattr(args, "workflow_closeout_policy", None) or defaults["closeout_policy"],
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


def manifest_language_config(args: argparse.Namespace) -> dict:
    content_locale = normalize_locale(getattr(args, "content_locale", None) or "en")
    return {
        "content_locale": content_locale,
        "interaction_locale": normalize_locale(getattr(args, "interaction_locale", None) or content_locale),
        "preserve_user_input_language": True,
    }


def manifest_projection_config(args: argparse.Namespace, profile: str) -> dict:
    mode = normalize_projection_mode(getattr(args, "projection_mode", None), default_projection_mode_for_new_manifest(profile))
    return {
        "mode": mode,
        "enabled_packs": default_projection_packs(profile, mode),
    }


def default_document_design_config(*, projection_mode: str) -> dict:
    principles_path = "docs/ops/document-design-principles.md" if normalize_projection_mode(projection_mode) != "detached" else "n/a"
    return {
        "principles_path": principles_path,
        "source_first": True,
        "register_derived_artifacts": True,
        "preferred_source_format": "markdown",
        "schedule_bundle": FORMAL_DOCUMENT_BUNDLE_DEFAULTS["schedule"],
        "proposal_bundle": FORMAL_DOCUMENT_BUNDLE_DEFAULTS["proposal"],
        "report_bundle": FORMAL_DOCUMENT_BUNDLE_DEFAULTS["report"],
        "process_bundle": FORMAL_DOCUMENT_BUNDLE_DEFAULTS["process"],
        "training_bundle": FORMAL_DOCUMENT_BUNDLE_DEFAULTS["training"],
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
            current = data
            for part in section.split("."):
                normalized = part.strip()
                if not normalized:
                    raise SystemExit(f"Unsupported manifest section: {raw_line}")
                next_section = current.setdefault(normalized, {})
                if not isinstance(next_section, dict):
                    raise SystemExit(f"Manifest section collides with scalar value: {section}")
                current = next_section
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

    workflow_section = data.get("workflow")
    if isinstance(workflow_section, dict):
        validate_choice_field("workflow", "execution_mode", workflow_section.get("execution_mode"), WORKFLOW_EXECUTION_MODE_CHOICES, invalid)
        validate_choice_field("workflow", "design_gate", workflow_section.get("design_gate"), WORKFLOW_DESIGN_GATE_CHOICES, invalid)
        validate_choice_field("workflow", "plan_gate", workflow_section.get("plan_gate"), WORKFLOW_PLAN_GATE_CHOICES, invalid)
        validate_choice_field("workflow", "review_policy", workflow_section.get("review_policy"), WORKFLOW_REVIEW_POLICY_CHOICES, invalid)
        validate_choice_field("workflow", "workspace_isolation", workflow_section.get("workspace_isolation"), WORKFLOW_ISOLATION_CHOICES, invalid)
        validate_choice_field("workflow", "testing_policy", workflow_section.get("testing_policy"), WORKFLOW_TESTING_POLICY_CHOICES, invalid)
        validate_choice_field("workflow", "closeout_policy", workflow_section.get("closeout_policy"), WORKFLOW_CLOSEOUT_POLICY_CHOICES, invalid)
    orchestration_section = data.get("orchestration")
    if isinstance(orchestration_section, dict):
        validate_choice_field("orchestration", "mode", orchestration_section.get("mode"), ORCHESTRATION_MODE_CHOICES, invalid)
        validate_choice_field("orchestration", "task_source", orchestration_section.get("task_source"), ORCHESTRATION_TASK_SOURCE_CHOICES, invalid)
        validate_choice_field("orchestration", "runner", orchestration_section.get("runner"), ORCHESTRATION_RUNNER_CHOICES, invalid)
        validate_choice_field("orchestration", "workspace_mode", orchestration_section.get("workspace_mode"), ORCHESTRATION_WORKSPACE_MODE_CHOICES, invalid)
        validate_choice_field("orchestration", "trust_profile", orchestration_section.get("trust_profile"), ORCHESTRATION_TRUST_PROFILE_CHOICES, invalid)
        validate_choice_field("orchestration", "unattended_risk_ceiling", orchestration_section.get("unattended_risk_ceiling"), ORCHESTRATION_RISK_CHOICES, invalid)
        validate_choice_field("orchestration", "status_surface", orchestration_section.get("status_surface"), ORCHESTRATION_STATUS_SURFACE_CHOICES, invalid)
        validate_choice_list_field(
            "orchestration",
            "verification_adapters",
            orchestration_section.get("verification_adapters"),
            ORCHESTRATION_VERIFICATION_ADAPTER_CHOICES,
            invalid,
        )
        validate_choice_field(
            "orchestration",
            "remote_verification_policy",
            orchestration_section.get("remote_verification_policy"),
            ORCHESTRATION_REMOTE_VERIFICATION_POLICY_CHOICES,
            invalid,
        )
    automation_section = data.get("automation")
    if isinstance(automation_section, dict):
        validate_choice_field("automation", "mode", automation_section.get("mode"), AUTOMATION_MODE_CHOICES, invalid)
        validate_choice_field("automation", "risk_ceiling", automation_section.get("risk_ceiling"), ORCHESTRATION_RISK_CHOICES, invalid)
        validate_choice_list_field(
            "automation",
            "event_sources",
            automation_section.get("event_sources"),
            AUTOMATION_EVENT_SOURCE_CHOICES,
            invalid,
        )
    agent_behavior_section = data.get("agent_behavior")
    if isinstance(agent_behavior_section, dict):
        validate_choice_field("agent_behavior", "quality_policy", agent_behavior_section.get("quality_policy"), AGENT_BEHAVIOR_QUALITY_POLICY_CHOICES, invalid)
        validate_choice_field("agent_behavior", "clarification_policy", agent_behavior_section.get("clarification_policy"), AGENT_BEHAVIOR_CLARIFICATION_POLICY_CHOICES, invalid)
        validate_choice_field("agent_behavior", "diff_scope_policy", agent_behavior_section.get("diff_scope_policy"), AGENT_BEHAVIOR_DIFF_SCOPE_POLICY_CHOICES, invalid)
        validate_choice_field("agent_behavior", "success_criteria_policy", agent_behavior_section.get("success_criteria_policy"), AGENT_BEHAVIOR_SUCCESS_CRITERIA_POLICY_CHOICES, invalid)
        validate_choice_field("agent_behavior", "assumption_policy", agent_behavior_section.get("assumption_policy"), AGENT_BEHAVIOR_ASSUMPTION_POLICY_CHOICES, invalid)
        validate_choice_field("agent_behavior", "complexity_policy", agent_behavior_section.get("complexity_policy"), AGENT_BEHAVIOR_COMPLEXITY_POLICY_CHOICES, invalid)
    agent_routing_section = data.get("agent_routing")
    if isinstance(agent_routing_section, dict):
        validate_choice_field("agent_routing", "mode", agent_routing_section.get("mode"), AGENT_ROUTING_MODE_CHOICES, invalid)
        validate_choice_field("agent_routing", "visibility", agent_routing_section.get("visibility"), AGENT_ROUTING_VISIBILITY_CHOICES, invalid)
        validate_choice_field("agent_routing", "default_budget_policy", agent_routing_section.get("default_budget_policy"), AGENT_ROUTING_BUDGET_POLICY_CHOICES, invalid)
        validate_choice_field("agent_routing", "budget_breach_behavior", agent_routing_section.get("budget_breach_behavior"), AGENT_ROUTING_BUDGET_BREACH_CHOICES, invalid)
        validate_choice_field("agent_routing", "on_review_fail", agent_routing_section.get("on_review_fail"), AGENT_ROUTING_ON_REVIEW_FAIL_CHOICES, invalid)
        roles = agent_routing_section.get("roles", {})
        if isinstance(roles, dict):
            for role_name, role_payload in roles.items():
                if role_name not in AGENT_ROUTING_ROLE_CHOICES:
                    unexpected.append(f"agent_routing.roles.{role_name}")
                    continue
                if not isinstance(role_payload, dict):
                    invalid.append(f"agent_routing.roles.{role_name} must be a table")
                    continue
                for key in role_payload:
                    if key not in {"provider", "model", "reasoning_effort", "write_access", "workspace_mode"}:
                        unexpected.append(f"agent_routing.roles.{role_name}.{key}")
                validate_choice_field(
                    f"agent_routing.roles.{role_name}",
                    "workspace_mode",
                    role_payload.get("workspace_mode"),
                    ORCHESTRATION_WORKSPACE_MODE_CHOICES,
                    invalid,
                )
    memory_section = data.get("memory")
    if isinstance(memory_section, dict):
        validate_choice_field("memory", "capture_policy", memory_section.get("capture_policy"), MEMORY_CAPTURE_POLICY_CHOICES, invalid)
        validate_choice_field("memory", "promotion_policy", memory_section.get("promotion_policy"), MEMORY_PROMOTION_POLICY_CHOICES, invalid)
        validate_choice_field("memory", "query_routing", memory_section.get("query_routing"), MEMORY_QUERY_ROUTING_CHOICES, invalid)
        validate_choice_field("memory", "semantic_cache", memory_section.get("semantic_cache"), MEMORY_SEMANTIC_CACHE_CHOICES, invalid)

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
    if expected_kind == "string_optional":
        if not isinstance(value, str):
            invalid.append(f"{label} must be a string")
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
    if expected_kind == "dict":
        if not isinstance(value, dict):
            invalid.append(f"{label} must be a table")
        return
    invalid.append(f"{label} uses unsupported schema kind: {expected_kind}")


def validate_choice_field(section: str, key: str, value: object, allowed: list[str], invalid: list[str]) -> None:
    if value is None:
        return
    normalized = normalize_optional_text(value)
    if normalized and normalized not in allowed:
        invalid.append(f"{section}.{key} must be one of: {', '.join(allowed)}")


def validate_choice_list_field(section: str, key: str, value: object, allowed: list[str], invalid: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        invalid.append(f"{section}.{key} must be an array")
        return
    invalid_items = [normalize_optional_text(item) for item in value if normalize_optional_text(item) not in allowed]
    if invalid_items:
        invalid.append(f"{section}.{key} contains unsupported values: {', '.join(invalid_items)}")


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
    advisories: list[str],
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
        "advisories": advisories,
    }


def existing_consumer_payload(config: ProjectConfig) -> dict[str, object]:
    memory_summary = memory_state_summary(config)
    return {
        "project": project_payload(config),
        "language": {
            "content_locale": config.content_locale,
            "interaction_locale": config.interaction_locale,
        },
        "memory": {
            "promotion_file": memory_summary["promotion_file"],
            "session_capture_store": memory_summary["session_capture_store"],
            "capture_policy": memory_summary["capture_policy"],
            "promotion_policy": memory_summary["promotion_policy"],
            "query_routing": memory_summary["query_routing"],
        },
        "next_commands": [
            "python3 scripts/sula.py doctor --project-root /path/to/project --strict",
            "python3 scripts/sula.py sync --project-root /path/to/project --dry-run",
            "python3 scripts/sula.py projection list --project-root /path/to/project --json",
            "python3 scripts/sula.py status --project-root /path/to/project --json",
            "python3 scripts/sula.py memory review --project-root /path/to/project --json",
        ],
    }


def onboard(project_root: Path, args: argparse.Namespace) -> int:
    if (project_root / MANIFEST_PATH).exists():
        config = load_manifest(project_root)
        payload = {"command": "onboard", "status": "existing-consumer", **existing_consumer_payload(config)}
        if json_output_requested(args):
            emit_json(payload)
            return 0
        if locale_family(config.interaction_locale) == "zh":
            print(f"{config.data['project']['name']} 已经由 Sula 管理。")
            print("请改用以下命令：")
        else:
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
        interaction_locale = normalize_locale(getattr(args, "interaction_locale", None) or suggestions["interaction_locale"]["value"])
        print("Sula 接入问题：" if locale_family(interaction_locale) == "zh" else "Sula onboarding questions:")
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
        if locale_family(summary["language"]["interaction_locale"]) == "zh":
            print("在阻塞问题解决之前，Sula 接入无法继续。")
        else:
            print("Sula onboarding cannot continue until the blocking issues are resolved.")
        return 1
    if not getattr(args, "approve", False):
        prompt = "是否按这些答案立即应用 Sula？" if locale_family(summary["language"]["interaction_locale"]) == "zh" else "Apply Sula now with these answers?"
        if prompt_yes_no(prompt, default=False):
            return apply_adoption(report, json_mode=False)
        if locale_family(summary["language"]["interaction_locale"]) == "zh":
            print("Sula 尚未应用。复核后重新运行 `python3 scripts/sula.py onboard --project-root /path/to/project --approve` 即可应用。")
        else:
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
        projection = report.config_data.get("projection", {})
        print(f"Detected name: {project['name']}")
        print(f"Detected slug: {project['slug']}")
        print(f"Projection mode: {projection.get('mode', default_projection_mode_for_existing_consumer(project['profile']))}")
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
    projection = manifest_projection_config(args, "generic-project")
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
    language = manifest_language_config(args)
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
        "automation": default_automation_config(),
        "orchestration": default_orchestration_config(),
        "agent_behavior": default_agent_behavior_config(),
        "agent_routing": default_agent_routing_config(),
        "storage": manifest_storage_config(args),
        "portfolio": manifest_portfolio_config(args),
        "language": language,
        "document_design": default_document_design_config(projection_mode=projection["mode"]),
        "projection": projection,
    }


def build_sula_core_manifest(project_root: Path, args: argparse.Namespace, detection_notes: list[str]) -> dict:
    name = args.name or extract_readme_title(read_text_if_exists(project_root / "README.md")) or project_root.name
    slug = args.slug or sanitize_slug(name)
    description = args.description or first_readme_paragraph(read_text_if_exists(project_root / "README.md")) or (
        "Reusable project operating system"
    )
    primary_branch = detect_primary_branch(project_root)
    language = manifest_language_config(args)
    projection = manifest_projection_config(args, "sula-core")
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
        "automation": default_automation_config(),
        "orchestration": default_orchestration_config(),
        "agent_behavior": default_agent_behavior_config(),
        "agent_routing": default_agent_routing_config(),
        "storage": manifest_storage_config(args),
        "portfolio": manifest_portfolio_config(args),
        "language": language,
        "document_design": default_document_design_config(projection_mode=projection["mode"]),
        "projection": projection,
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
    language = manifest_language_config(args)
    projection = manifest_projection_config(args, "react-frontend-erpnext")
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
        "automation": default_automation_config(),
        "orchestration": default_orchestration_config(),
        "agent_behavior": default_agent_behavior_config(),
        "agent_routing": default_agent_routing_config(),
        "storage": manifest_storage_config(args),
        "portfolio": manifest_portfolio_config(args),
        "language": language,
        "document_design": default_document_design_config(projection_mode=projection["mode"]),
        "projection": projection,
    }


def default_memory_config() -> dict:
    return {
        "change_record_directory": "docs/change-records",
        "release_record_directory": "docs/releases",
        "incident_record_directory": "docs/incidents",
        "digest_file": ".sula/memory-digest.md",
        "status_max_age_days": 14,
        "status_archive_file": "docs/ops/status-archive.md",
        "capture_policy": "explicit",
        "promotion_policy": "review-required",
        "rule_registry": True,
        "job_tracking": True,
        "query_routing": "deterministic",
        "semantic_cache": "off",
        "session_retention_days": 7,
        "promotion_file": "docs/ops/session-promotions.md",
    }


def default_automation_config() -> dict:
    return {
        "enabled": True,
        "mode": "execute",
        "auto_intake": True,
        "auto_plan": True,
        "auto_dispatch": True,
        "risk_ceiling": "low",
        "approval_required_for": ["release", "security", "provider-write", "destructive"],
        "event_sources": ["sula-cli", "provider", "status", "artifact", "workflow", "external"],
    }


def default_orchestration_config() -> dict:
    return {
        "enabled": True,
        "mode": "ticket-runner",
        "task_source": "local",
        "runner": "dry-run",
        "runner_command": "",
        "runner_endpoint": "",
        "runner_token_env": "SULA_CODEX_APP_SERVER_TOKEN",
        "tasks_path": "docs/workflows/tasks.json",
        "provider_task_item_id": "",
        "provider_task_item_kind": "",
        "provider_task_item_url": "",
        "workspace_root": ".sula/local/workspaces",
        "workspace_mode": "none",
        "trust_profile": "local-sandboxed",
        "allow_project_root_runner": False,
        "max_concurrent_runs": 1,
        "max_retry_count": 1,
        "max_run_minutes": 30,
        "daily_budget_minutes": 120,
        "unattended_risk_ceiling": "low",
        "require_human_approval_for": ["release", "security", "provider-write", "destructive"],
        "status_surface": "sula",
        "verification_adapters": ["local-file", "artifact-catalog", "provider-metadata", "pull-request-url", "url"],
        "remote_verification_policy": "opportunistic",
    }


def default_agent_behavior_config() -> dict:
    return {
        "quality_policy": "sula-karpathy-inspired",
        "clarification_policy": "non-trivial-only",
        "diff_scope_policy": "surgical",
        "success_criteria_policy": "required",
        "assumption_policy": "surface-when-uncertain",
        "complexity_policy": "simplicity-first",
        "require_verification": True,
        "forbid_drive_by_refactors": True,
    }


def default_agent_routing_roles() -> dict[str, dict[str, object]]:
    return {
        "host": {
            "provider": "unknown",
            "model": "unknown",
            "reasoning_effort": "",
            "write_access": False,
            "workspace_mode": "none",
        },
        "planner": {
            "provider": "host",
            "model": "current-session",
            "reasoning_effort": "high",
            "write_access": False,
            "workspace_mode": "none",
        },
        "executor": {
            "provider": "local",
            "model": "configured-runner",
            "reasoning_effort": "",
            "write_access": False,
            "workspace_mode": "copy",
        },
        "verifier": {
            "provider": "local",
            "model": "shell",
            "reasoning_effort": "",
            "write_access": False,
            "workspace_mode": "none",
        },
        "reviewer": {
            "provider": "host",
            "model": "current-session",
            "reasoning_effort": "high",
            "write_access": False,
            "workspace_mode": "none",
        },
        "acceptor": {
            "provider": "human",
            "model": "operator",
            "reasoning_effort": "",
            "write_access": False,
            "workspace_mode": "none",
        },
    }


def default_agent_routing_config() -> dict:
    return {
        "enabled": True,
        "mode": "assist",
        "visibility": "always",
        "default_budget_policy": "cost-aware",
        "budget_breach_behavior": "ask",
        "max_review_cycles": 3,
        "on_review_fail": "return-to-executor",
        "require_final_acceptance": True,
        "roles": default_agent_routing_roles(),
    }


def default_workflow_pack(profile: str) -> str:
    defaults = {
        "generic-project": "generic-project",
        "react-frontend-erpnext": "software-delivery",
        "sula-core": "operating-system",
    }
    return defaults.get(profile, "generic-project")


def default_workflow_policy_config(pack: str) -> dict[str, str]:
    if pack in {"software-delivery", "operating-system"}:
        return {
            "execution_mode": "review-heavy",
            "design_gate": "complex-only",
            "plan_gate": "multi-step",
            "review_policy": "task-checkpoints",
            "workspace_isolation": "branch",
            "testing_policy": "verify-first",
            "closeout_policy": "explicit",
        }
    return {
        "execution_mode": "solo-inline",
        "design_gate": "complex-only",
        "plan_gate": "multi-step",
        "review_policy": "batch",
        "workspace_isolation": "none",
        "testing_policy": "inherit",
        "closeout_policy": "explicit",
    }


def normalize_workflow_choice(value: object, allowed: list[str], default: str) -> str:
    normalized = normalize_optional_text(value)
    return normalized if normalized in allowed else default


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


def is_clean_git_worktree(project_root: Path) -> bool:
    result = run_git(project_root, ["status", "--short"])
    return result is not None and result.returncode == 0 and not result.stdout.strip()


def detect_git_commit(project_root: Path) -> str:
    if not is_git_repository(project_root):
        return "n/a"
    result = run_git(project_root, ["rev-parse", "--short=12", "HEAD"])
    if result is None or result.returncode != 0:
        return "no-commits"
    return result.stdout.strip() or "no-commits"


def latest_git_commit_date(project_root: Path) -> str | None:
    if not is_git_repository(project_root):
        return None
    result = run_git(project_root, ["log", "-1", "--format=%cs"])
    if result is None or result.returncode != 0:
        return None
    return result.stdout.strip() or None


def detect_git_worktree_state(project_root: Path) -> str:
    if not is_git_repository(project_root):
        return "n/a"
    return "clean" if is_clean_git_worktree(project_root) else "dirty"


def parse_table_array_toml(text: str, table_name: str) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    marker = f"[[{table_name}]]"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == marker:
            current = {}
            entries.append(current)
            continue
        if current is None or "=" not in line:
            continue
        key, value = line.split("=", 1)
        current[key.strip()] = parse_toml_value(value.strip())
    return entries


def load_adoption_registry(project_root: Path) -> list[dict[str, object]]:
    registry_path = project_root / "registry" / "adopted-projects.toml"
    if not registry_path.exists():
        return []
    try:
        return [item for item in parse_table_array_toml(registry_path.read_text(encoding="utf-8"), "project") if isinstance(item, dict)]
    except SystemExit as exc:
        raise SystemExit(f"Invalid adoption registry: {registry_path} ({exc})")


def adoption_registry_canaries(project_root: Path) -> list[dict[str, object]]:
    canaries: list[dict[str, object]] = []
    for entry in load_adoption_registry(project_root):
        if bool(entry.get("canary", False)):
            canaries.append(entry)
    return canaries


def resolve_registry_local_root(project_root: Path, entry: dict[str, object]) -> Path | None:
    local_root = normalize_optional_text(entry.get("local_root", ""))
    if local_root:
        path = Path(local_root)
        return (project_root / path).resolve() if not path.is_absolute() else path
    repository = normalize_optional_text(entry.get("repository", ""))
    if repository == "in-repo example":
        slug = normalize_optional_text(entry.get("slug", ""))
        if slug == "okoktoto-v5-example":
            return (project_root / "examples" / "okoktoto").resolve()
    if normalize_optional_text(entry.get("slug", "")) == "sula-root":
        return project_root.resolve()
    return None


def validate_canary_registry_coverage(project_root: Path) -> tuple[list[str], list[dict[str, object]]]:
    entries = load_adoption_registry(project_root)
    canaries = [entry for entry in entries if bool(entry.get("canary", False))]
    covered_profiles = {normalize_optional_text(entry.get("profile", "")) for entry in canaries}
    expected_profiles = {
        normalize_optional_text(entry.get("profile", ""))
        for entry in entries
        if normalize_optional_text(entry.get("sync_status", "")) != "retired"
    }
    expected_profiles.discard("")
    missing = [profile for profile in sorted(expected_profiles) if profile not in covered_profiles]
    return missing, canaries


def run_sula_subcommand(subcommand: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SULA_ROOT / "scripts" / "sula.py"), *subcommand],
        cwd=str(SULA_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def canary_verification_report(project_root: Path, entry: dict[str, object]) -> dict[str, object]:
    slug = normalize_optional_text(entry.get("slug", ""))
    local_root = resolve_registry_local_root(project_root, entry)
    if local_root is None:
        return {
            "slug": slug,
            "name": normalize_optional_text(entry.get("name", "")),
            "status": "missing-local-root",
            "local_root": "",
            "checks": [],
            "issues": ["registry entry does not declare a resolvable local_root"],
        }
    if not local_root.exists():
        return {
            "slug": slug,
            "name": normalize_optional_text(entry.get("name", "")),
            "status": "missing-local-root",
            "local_root": str(local_root),
            "checks": [],
            "issues": [f"local_root does not exist: {local_root}"],
        }
    checks = [
        ("sync_dry_run", ["sync", "--project-root", str(local_root), "--dry-run"]),
        ("doctor_strict", ["doctor", "--project-root", str(local_root), "--strict"]),
        ("memory_digest", ["memory", "digest", "--project-root", str(local_root)]),
        ("check", ["check", "--project-root", str(local_root)]),
    ]
    results: list[dict[str, object]] = []
    issues: list[str] = []
    overall = "ok"
    for label, command in checks:
        completed = run_sula_subcommand(command, cwd=project_root)
        passed = completed.returncode == 0
        results.append(
            {
                "name": label,
                "passed": passed,
                "command": " ".join(command),
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if not passed:
            overall = "failed"
            issues.append(f"{label} failed")
    return {
        "slug": slug,
        "name": normalize_optional_text(entry.get("name", "")),
        "status": overall,
        "local_root": str(local_root),
        "checks": results,
        "issues": issues,
    }


def handle_canary_command(project_root: Path, args: argparse.Namespace) -> int:
    canaries = adoption_registry_canaries(project_root)
    if args.canary_command == "list":
        payload = []
        for entry in canaries:
            local_root = resolve_registry_local_root(project_root, entry)
            payload.append(
                {
                    "slug": normalize_optional_text(entry.get("slug", "")),
                    "name": normalize_optional_text(entry.get("name", "")),
                    "profile": normalize_optional_text(entry.get("profile", "")),
                    "sync_status": normalize_optional_text(entry.get("sync_status", "")),
                    "owner": normalize_optional_text(entry.get("owner", "")),
                    "local_root": str(local_root) if local_root else "",
                    "notes": normalize_optional_text(entry.get("notes", "")),
                }
            )
        if json_output_requested(args):
            emit_json({"command": "canary.list", "status": "ok", "project_root": str(project_root), "canaries": payload})
            return 0
        print(f"Canaries for {project_root}")
        for item in payload:
            print(f"  - {item['slug']} [{item['profile']}] :: {item['local_root'] or 'unresolved'}")
        if not payload:
            print("  No canaries.")
        return 0
    if args.canary_command == "verify":
        selected = canaries if args.all or not args.slug else [entry for entry in canaries if normalize_optional_text(entry.get("slug", "")) in set(args.slug)]
        reports = [canary_verification_report(project_root, entry) for entry in selected]
        passed = all(item["status"] == "ok" for item in reports) if reports else False
        missing_profiles, _ = validate_canary_registry_coverage(project_root)
        payload = {
            "command": "canary.verify",
            "status": "ok" if passed and not missing_profiles else "failed",
            "project_root": str(project_root),
            "missing_canary_profiles": missing_profiles,
            "reports": reports,
        }
        if json_output_requested(args):
            emit_json(payload)
            return 0 if payload["status"] == "ok" else 1
        print(f"Canary verification for {project_root}")
        if missing_profiles:
            print(f"  Missing canary profiles: {', '.join(missing_profiles)}")
        for item in reports:
            print(f"  - {item['slug']}: {item['status']}")
        return 0 if payload["status"] == "ok" else 1
    raise AssertionError("unreachable")


def tracked_files_for_release(project_root: Path) -> list[Path]:
    result = run_git(project_root, ["ls-files"])
    if result is not None and result.returncode == 0:
        return [project_root / line.strip() for line in result.stdout.splitlines() if line.strip()]
    files: list[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        files.append(path)
    return files


def scan_public_release_content(project_root: Path) -> tuple[list[str], list[str], list[str]]:
    local_paths: list[str] = []
    cloud_refs: list[str] = []
    secret_like: list[str] = []
    patterns = [
        (re.compile(r"/Users/[^/\s]+/(Library/CloudStorage|Documents|Desktop|Downloads|workspace)[^\s]*"), local_paths),
        (re.compile(r"CloudStorage/GoogleDrive-[^/\s]+@|GoogleDrive-[^/\s]+@"), cloud_refs),
        (re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----"), secret_like),
        (re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), secret_like),
        (re.compile(r"sk-[0-9A-Za-z]{20,}"), secret_like),
    ]
    for path in tracked_files_for_release(project_root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, bucket in patterns:
            if pattern.search(text):
                bucket.append(path.relative_to(project_root).as_posix())
    return sorted(set(local_paths)), sorted(set(cloud_refs)), sorted(set(secret_like))


def public_governance_paths(project_root: Path) -> list[str]:
    required = [
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        ".github/pull_request_template.md",
        "docs/reference/public-release-readiness.md",
        "site/sula.json",
        "site/launch/bootstrap.py",
    ]
    return [item for item in required if not (project_root / item).exists()]


def git_history_release_issues(project_root: Path) -> list[str]:
    issues: list[str] = []
    email_result = run_git(project_root, ["log", "--format=%ae"])
    if email_result is not None and email_result.returncode == 0:
        emails = {line.strip() for line in email_result.stdout.splitlines() if line.strip()}
        if any(email.endswith("@MacBook-Pro.local") for email in emails):
            issues.append("git history still contains local-author metadata such as @MacBook-Pro.local")
    return issues


def release_readiness_payload(project_root: Path) -> dict[str, object]:
    missing_governance = public_governance_paths(project_root)
    local_paths, cloud_refs, secret_like = scan_public_release_content(project_root)
    history_issues = git_history_release_issues(project_root)
    missing_profiles, canaries = validate_canary_registry_coverage(project_root)
    canary_reports = [canary_verification_report(project_root, entry) for entry in canaries]
    canaries_ok = bool(canary_reports) and all(item["status"] == "ok" for item in canary_reports)
    issues: list[str] = []
    issues.extend(f"missing governance file: {item}" for item in missing_governance)
    issues.extend(f"tracked local path reference found in: {item}" for item in local_paths)
    issues.extend(f"tracked cloud-drive reference found in: {item}" for item in cloud_refs)
    issues.extend(f"tracked secret-like material found in: {item}" for item in secret_like)
    issues.extend(history_issues)
    issues.extend(f"missing canary profile coverage: {item}" for item in missing_profiles)
    if not canaries_ok:
        issues.append("one or more canary verification runs failed")
    status_result = run_git(project_root, ["status", "--short"]) if is_git_repository(project_root) else None
    clean_worktree = bool(status_result is None or (status_result.returncode == 0 and not status_result.stdout.strip()))
    if not clean_worktree:
        issues.append("working tree is not clean")
    recommended_strategy = ""
    next_steps: list[str] = []
    if history_issues:
        recommended_strategy = "fresh-public-repo"
        next_steps.extend(
            [
                "run `python3 scripts/sula.py release export-public --project-root . --output <clean-public-tree>`",
                "initialize a new public repository from that exported tree",
                "update site/sula.json with the published public repository URL and ref after the new repository exists",
            ]
        )
    elif not issues:
        recommended_strategy = "current-repository-is-publishable"
    if not missing_governance:
        next_steps.append("keep `python3 scripts/sula.py release readiness --project-root .` in the public-release gate")
    return {
        "project_root": str(project_root),
        "ready": not issues,
        "missing_governance_files": missing_governance,
        "local_path_refs": local_paths,
        "cloud_drive_refs": cloud_refs,
        "secret_like_refs": secret_like,
        "history_issues": history_issues,
        "missing_canary_profiles": missing_profiles,
        "canary_reports": canary_reports,
        "clean_worktree": clean_worktree,
        "recommended_strategy": recommended_strategy,
        "next_steps": next_steps,
        "issues": issues,
    }


def export_public_release_tree(project_root: Path, output_root: Path, *, overwrite: bool) -> dict[str, object]:
    if output_root.exists():
        if not overwrite:
            raise SystemExit(f"Output already exists: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    tracked = tracked_files_for_release(project_root)
    copied: list[str] = []
    for source in tracked:
        relative = source.relative_to(project_root)
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(relative.as_posix())
    manifest_lines = [
        "# Sula Public Export",
        "",
        f"- generated_on: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "- source_tree: tracked files exported from the private source repository",
        f"- file_count: {len(copied)}",
        "- public_release_strategy: fresh-public-repo",
        "",
        "This export intentionally omits git history so maintainers can create a fresh public repository from a clean tracked-file tree.",
        "",
        "## Suggested Initialization",
        "",
        "1. create a new empty public repository",
        "2. copy this exported tree into that repository root",
        "3. set an explicit public-safe git identity before the first commit",
        "4. run `git init`, `git add .`, and create the initial public commit",
        "5. update `site/sula.json` so `source_repository_url` and `source_ref` point at that published public repository",
        "",
    ]
    (output_root / "PUBLIC-EXPORT.md").write_text("\n".join(manifest_lines), encoding="utf-8")
    return {"output_root": str(output_root), "file_count": len(copied), "manifest": "PUBLIC-EXPORT.md"}


def handle_release_command(project_root: Path, args: argparse.Namespace) -> int:
    if args.release_command == "readiness":
        payload = release_readiness_payload(project_root)
        wrapped = {"command": "release.readiness", "status": "ok" if payload["ready"] else "failed", **payload}
        if json_output_requested(args):
            emit_json(wrapped)
            return 0 if payload["ready"] else 1
        print(f"Release readiness for {project_root}")
        print(f"  Ready: {'yes' if payload['ready'] else 'no'}")
        if payload["recommended_strategy"]:
            print(f"  Recommended strategy: {payload['recommended_strategy']}")
        for issue in payload["issues"]:
            print(f"  - {issue}")
        for step in payload["next_steps"]:
            print(f"  next: {step}")
        return 0 if payload["ready"] else 1
    if args.release_command == "export-public":
        output_root = Path(args.output).expanduser().resolve()
        payload = export_public_release_tree(project_root, output_root, overwrite=bool(args.overwrite))
        wrapped = {"command": "release.export-public", "status": "ok", **payload}
        if json_output_requested(args):
            emit_json(wrapped)
            return 0
        print(f"Exported clean public-release tree to {output_root}")
        print(f"  - files: {payload['file_count']}")
        print(f"  - manifest: {payload['manifest']}")
        return 0
    raise AssertionError("unreachable")


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
    apply_projection_state(config, report.actions)
    write_lockfile(config)
    finalize_adoption_traceability(config)
    generate_memory_digest(config, argparse.Namespace(output=None, stdout=False, json=False), emit_output=not json_mode)
    refresh_kernel_state(config, event_type="adopt.approved", summary="Applied initial Sula adoption.")
    if not json_mode:
        print("接入后校验：" if locale_family(config.interaction_locale) == "zh" else "Post-adoption validation:")
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
        if locale_family(config.interaction_locale) == "zh":
            print(f"{config.data['project']['name']} 的 Sula 接入已完成")
        else:
            print(f"Sula adoption completed for {config.data['project']['name']}")
    else:
        if locale_family(config.interaction_locale) == "zh":
            print("Sula 接入已完成，但在达到严格合规前仍需后续处理。")
        else:
            print("Sula adoption completed with follow-up required before strict compliance is clean.")
    return doctor_exit


def finalize_adoption_traceability(config: ProjectConfig) -> None:
    ensure_initial_status(config)
    ensure_promotion_file(config)
    ensure_adoption_record(config)


def initial_adoption_record_path(config: ProjectConfig, record_date: str) -> Path:
    return config.change_record_directory / f"{record_date}-adopt-sula-operating-system.md"


def current_truth_source_freshness_status(config: ProjectConfig) -> str:
    payload = project_status_payload(config)
    truth_sources = payload.get("truth_sources", {}) if isinstance(payload, dict) else {}
    if not isinstance(truth_sources, dict):
        return "n/a"
    if truth_sources.get("provider_errors") or truth_sources.get("local_copy_risk_count"):
        return "stale-risk"
    if truth_sources.get("provider_native") and not normalize_optional_text(truth_sources.get("last_provider_check_at", "")):
        return "needs-refresh"
    if truth_sources.get("artifact_families"):
        return "current"
    return "n/a"


def ensure_initial_status(config: ProjectConfig) -> None:
    status_path = config.root / config.data["paths"]["status_file"]
    if status_path.exists():
        text = status_path.read_text(encoding="utf-8")
        if not any(placeholder in text for placeholder in STATUS_PLACEHOLDERS):
            return
    today = date.today().isoformat()
    initial_record_path = initial_adoption_record_path(config, today)
    relative_record_path = os.path.relpath(initial_record_path, start=status_path.parent).replace(os.sep, "/")
    git_branch = detect_git_branch(config.root) if is_git_repository(config.root) else "n/a"
    git_commit = detect_git_commit(config.root)
    git_worktree = detect_git_worktree_state(config.root)
    source_freshness = current_truth_source_freshness_status(config)
    if locale_family(config.content_locale) == "zh":
        text = (
            "# 项目状态\n\n"
            f"- 最后更新: {today}\n\n"
            "## 摘要\n\n"
            f"- 当前仓库已经以 `{config.profile}` 配置档和 `{config.projection_mode}` 投影模式完成了初始 Sula 接入。\n"
            "- 仓库现在已经具备 `.sula/` 内核与当前投影模式对应的可见协作表面。\n\n"
            "## 健康状态\n\n"
            "- 状态: yellow\n"
            "- 原因: 接入已经完成，但团队仍应复核生成规则与被保留的项目自有文件。\n\n"
            "## 当前重点\n\n"
            "- 复核第一次 Sula 接入差异\n"
            "- 确认 manifest 事实与当前投影模式是否合适\n\n"
            "## 阻塞项\n\n"
            "- 无\n\n"
            "## 近期决策\n\n"
            f"- {today}: 批准以 `{config.profile}` 配置档完成首次 Sula 接入\n\n"
            "## 下次复盘\n\n"
            "- 负责人: 项目维护者\n"
            f"- 日期: {today}\n"
            "- 触发条件: 第一次 managed-file sync 之后，或项目规则进一步收紧之后\n\n"
            "## 交接\n\n"
            "- 可交接: yes\n"
            f"- 从这里开始: `{relative_record_path}`; `STATUS.md`\n"
            f"- 最新记录: `{relative_record_path}`\n"
            f"- 下一步动作: 查看 `{relative_record_path}`; 运行 `python3 scripts/sula.py sync --project-root . --dry-run`\n"
            "- 下一步负责人: 项目维护者\n"
            f"- 下一步截止: {today}\n"
            "- 完成定义: 结果 `已审阅首次 sync dry-run`; 产物 `STATUS.md`\n"
            "- 阻塞: 无\n"
            f"- 真相源: `STATUS.md`; `{relative_record_path}`\n"
            f"- 真相新鲜度: {source_freshness}\n"
            "- 验证命令: `python3 scripts/sula.py doctor --project-root . --strict`\n"
            "- 验证结果: pass\n"
            f"- 验证日期: {today}\n"
            f"- Git 分支: {git_branch}\n"
            f"- Git 提交: {git_commit}\n"
            f"- Git 工作区: {git_worktree}\n"
        )
    else:
        text = (
            "# STATUS\n\n"
            f"- last updated: {today}\n\n"
            "## Summary\n\n"
            f"- Initial Sula adoption is complete for this repository under the `{config.profile}` profile in `{config.projection_mode}` projection mode.\n"
            "- The repository now has the `.sula/` kernel plus the visible collaboration surface selected by the current projection mode.\n\n"
            "## Health\n\n"
            "- status: yellow\n"
            "- reason: adoption is complete, but the team should review generated rules and preserved project-owned files.\n\n"
            "## Current Focus\n\n"
            "- review the first Sula adoption diff\n"
            "- confirm manifest facts and whether the current projection mode is the right fit\n\n"
            "## Blockers\n\n"
            "- none\n\n"
            "## Recent Decisions\n\n"
            f"- {today}: approved initial Sula adoption under the `{config.profile}` profile\n\n"
            "## Next Review\n\n"
            "- owner: project maintainers\n"
            f"- date: {today}\n"
            "- trigger: review after the first managed-file sync or after tightening project-specific rules\n\n"
            "## Handoff\n\n"
            "- ready: yes\n"
            f"- start here: `{relative_record_path}`; `STATUS.md`\n"
            f"- latest record: `{relative_record_path}`\n"
            f"- next action: review `{relative_record_path}`; run `python3 scripts/sula.py sync --project-root . --dry-run`\n"
            "- next owner: project maintainers\n"
            f"- next due: {today}\n"
            "- done when: result `first sync dry run reviewed`; artifact `STATUS.md`\n"
            "- blockers: none\n"
            f"- source of truth: `STATUS.md`; `{relative_record_path}`\n"
            f"- source freshness: {source_freshness}\n"
            "- verification command: `python3 scripts/sula.py doctor --project-root . --strict`\n"
            "- verification result: pass\n"
            f"- verification date: {today}\n"
            f"- git branch: {git_branch}\n"
            f"- git commit: {git_commit}\n"
            f"- git working tree: {git_worktree}\n"
        )
    status_path.write_text(text, encoding="utf-8")


def ensure_adoption_record(config: ProjectConfig) -> None:
    today = date.today().isoformat()
    zh = locale_family(config.content_locale) == "zh"
    title = "接入 Sula 项目操作系统" if zh else "Adopt Sula operating system"
    slug = "adopt-sula-operating-system"
    record_path = config.change_record_directory / f"{today}-{slug}.md"
    if record_path.exists():
        return
    config.change_record_directory.mkdir(parents=True, exist_ok=True)
    branch = detect_git_branch(config.root)
    summary = (
        f"已按 `{config.profile}` 配置档和 `{config.projection_mode}` 投影模式接入 Sula，并生成当前模式所需的内核与可见投影。"
        if zh
        else f"Adopted Sula under the `{config.profile}` profile in `{config.projection_mode}` projection mode and generated the required kernel plus visible projections."
    )
    if zh:
        content = (
            f"# {title}\n\n"
            "## 元数据\n\n"
            f"- 日期: {today}\n"
            f"- 执行者: {config.data['project']['default_agent']}\n"
            f"- 分支: {branch}\n"
            "- 关联提交: 待补充 review commit\n"
            "- 状态: completed\n\n"
            "## 背景\n\n"
            f"{summary}\n\n"
            "## 分析\n\n"
            "- 仓库需要一个可复用的操作系统内核，而不是零散的临时规则。\n"
            "- 可见治理表面应该是可选投影，而不是默认重写整个仓库。\n\n"
            "## 选定方案\n\n"
            f"- 使用 `{config.profile}` 配置档初始化 Sula\n"
            f"- 按 `{config.projection_mode}` 投影模式渲染所需文件，并保留项目自有脚手架\n"
            "- 为状态与变更跟踪增加持久记忆结构\n\n"
            "## 执行\n\n"
            "- 创建项目 manifest 与 version lock\n"
            "- 初始化 `.sula/` 内核状态与投影登记\n"
            "- 渲染当前投影模式需要的规则、文档与脚手架文件\n"
            "- 生成第一版 memory digest 以支持快速接管\n\n"
            "## 验证\n\n"
            "- 在批准前审阅 adoption report\n"
            "- 在接入后运行 `sula doctor --strict`\n\n"
            "## 回退\n\n"
            "- 如果仓库不应由 Sula 管理，则回退接入提交\n"
            "- 保留项目自有真相，并在重试前重新评估 profile 匹配度\n\n"
            "## 数据副作用\n\n"
            "- 无运行时数据副作用\n"
            "- 仓库文档与治理文件被新增或更新\n\n"
            "## 后续\n\n"
            "- 审阅当前投影模式是否合适，并按需要升级或收缩可见投影\n"
            "- 后续共享升级前先运行 `sula sync --dry-run`\n\n"
            "## 架构边界检查\n\n"
            "- 最高规则影响: 仓库现在采用 Sula 作为可复用操作系统内核，并把可见治理文件当作可选投影处理\n"
        )
    else:
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
            "- The repository needed a reusable operating-system kernel instead of ad hoc rules.\n"
            "- The visible governance surface should remain optional projections instead of becoming a mandatory repo rewrite.\n\n"
            "## Chosen Plan\n\n"
            f"- initialize Sula with the `{config.profile}` profile\n"
            f"- apply the `{config.projection_mode}` projection mode and preserve project-owned scaffold files when they already exist\n"
            "- add durable memory structures for status and change tracking\n\n"
            "## Execution\n\n"
            "- created the project manifest and version lock\n"
            "- initialized the `.sula/` kernel and projection registry\n"
            "- rendered the rules, docs, and scaffolds required by the selected projection mode\n"
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
            "- review whether the current projection mode is the right fit and enable or disable packs intentionally\n"
            "- use `sula sync --dry-run` before future shared upgrades\n\n"
            "## Architecture Boundary Check\n\n"
            "- highest rule impact: the repository now adopts Sula as its reusable operating-system kernel while treating visible governance files as optional projections\n"
        )
    record_path.write_text(content, encoding="utf-8")
    update_change_records_index(config, record_path, today, title, summary)
    update_status_for_new_record(config, "change", record_path, today, title)


def print_adoption_usage(config: ProjectConfig) -> None:
    sula_command = f"python3 {SULA_ROOT / 'scripts' / 'sula.py'}"
    if locale_family(config.interaction_locale) == "zh":
        print("接入后可以这样使用 Sula：")
        print(f"  - 查看当前规则: {config.root / 'AGENTS.md'}")
        print(f"  - 校验仓库: {sula_command} doctor --project-root {config.root} --strict")
        print(f"  - 预览后续升级: {sula_command} sync --project-root {config.root} --dry-run")
        print(f"  - 预览移除: {sula_command} remove --project-root {config.root}")
        print(f"  - 添加非琐碎历史: {sula_command} record new --project-root {config.root} --title \"...\"")
        print(f"  - capture 临时上下文: {sula_command} memory capture --project-root {config.root} --title \"...\" --summary \"...\"")
        print(f"  - review / promote: {sula_command} memory review --project-root {config.root} --json")
        print(f"  - 提升文件: {config.promotion_file}")
        print(f"  - 重新生成记忆摘要: {sula_command} memory digest --project-root {config.root}")
    else:
        print("How to use Sula after adoption:")
        print(f"  - inspect current rules: {config.root / 'AGENTS.md'}")
        print(f"  - validate the repository: {sula_command} doctor --project-root {config.root} --strict")
        print(f"  - preview future upgrades: {sula_command} sync --project-root {config.root} --dry-run")
        print(f"  - preview removal: {sula_command} remove --project-root {config.root}")
        print(f"  - add non-trivial history: {sula_command} record new --project-root {config.root} --title \"...\"")
        print(f"  - capture temporary context: {sula_command} memory capture --project-root {config.root} --title \"...\" --summary \"...\"")
        print(f"  - review and promote memory: {sula_command} memory review --project-root {config.root} --json")
        print(f"  - durable promotion file: {config.promotion_file}")
        print(f"  - regenerate recall summary: {sula_command} memory digest --project-root {config.root}")


def normalize_projection_mode(raw: str | None, default: str = "detached") -> str:
    value = (raw or default).strip().lower()
    return value if value in PROJECTION_MODE_CHOICES else default


def default_projection_mode_for_new_manifest(profile: str) -> str:
    del profile
    return "governed"


def default_projection_mode_for_existing_consumer(profile: str) -> str:
    del profile
    return "governed"


def projection_pack_descriptions() -> dict[str, str]:
    return {
        "project-memory": "Minimal project-facing memory files such as README, AGENTS, STATUS, and CHANGE-RECORDS.",
        "record-templates": "Change, release, and incident record template scaffolds under docs/.",
        "document-design": "Formal document design rules for source-first planning, proposal, report, process, and training docs.",
        "ops-core": "Reusable operating docs such as team operating model, project memory, release checklist, and request template.",
        "profile-architecture": "Profile-specific architecture maps.",
        "profile-runbooks": "Profile-specific runbooks and operational guides.",
        "ai-tooling": "AI tool instruction projections such as CODEX, CLAUDE, GEMINI, Copilot, and Cursor rules. Depends on ops-core.",
    }


def profile_available_projection_packs(profile: str) -> list[str]:
    packs = ["project-memory", "record-templates"]
    if (core_managed_dir() / "docs" / "ops" / "document-design-principles.md.tmpl").exists():
        packs.append("document-design")
    if any(path.is_file() for path in (core_managed_dir() / "docs" / "ops").glob("*.tmpl")):
        packs.append("ops-core")
    if (profile_managed_dir(profile) / "docs" / "architecture").exists():
        packs.append("profile-architecture")
    if (profile_managed_dir(profile) / "docs" / "runbooks").exists():
        packs.append("profile-runbooks")
    if any(
        (core_managed_dir() / candidate).exists()
        for candidate in [
            "CODEX.md.tmpl",
            "CLAUDE.md.tmpl",
            "GEMINI.md.tmpl",
            ".github/copilot-instructions.md.tmpl",
            ".cursor/rules/project.mdc.tmpl",
        ]
    ):
        packs.append("ai-tooling")
    return packs


def default_projection_packs(profile: str, mode: str) -> list[str]:
    defaults = {
        "detached": ["project-memory", "record-templates"],
        "collaborative": ["project-memory", "record-templates", "document-design", "ops-core", "profile-architecture", "profile-runbooks"],
        "governed": [
            "project-memory",
            "record-templates",
            "document-design",
            "ops-core",
            "profile-architecture",
            "profile-runbooks",
            "ai-tooling",
        ],
    }
    available = set(profile_available_projection_packs(profile))
    return [pack for pack in defaults.get(normalize_projection_mode(mode), defaults["detached"]) if pack in available]


def projection_pack_dependencies(pack: str) -> list[str]:
    return {
        "ai-tooling": ["ops-core"],
    }.get(pack, [])


def normalize_projection_packs(profile: str, packs: list[object]) -> list[str]:
    available = set(profile_available_projection_packs(profile))
    ordered: list[str] = []
    seen: set[str] = set()

    def add_pack(pack: str) -> None:
        if not pack or pack in seen or pack not in available:
            return
        for dependency in projection_pack_dependencies(pack):
            add_pack(dependency)
        seen.add(pack)
        ordered.append(pack)

    for item in packs:
        add_pack(str(item).strip())
    return ordered


def projection_pack_for_action(action: RenderAction) -> str | None:
    relative = action.relative_path.as_posix()
    if relative in {"README.md", "AGENTS.md", "STATUS.md", "CHANGE-RECORDS.md"}:
        return "project-memory"
    if relative.startswith("docs/change-records/") or relative.startswith("docs/releases/") or relative.startswith("docs/incidents/"):
        return "record-templates"
    if relative == "docs/ops/document-design-principles.md":
        return "document-design"
    if relative in {
        "docs/README.md",
        "docs/ops/architecture-exception-register.md",
        "docs/ops/project-memory.md",
        "docs/ops/release-checklist.md",
        "docs/ops/request-template.md",
        "docs/ops/smoke-test-checklist.md",
        "docs/ops/team-operating-model.md",
    }:
        return "ops-core"
    if relative.startswith("docs/architecture/"):
        return "profile-architecture"
    if relative.startswith("docs/runbooks/"):
        return "profile-runbooks"
    if relative in {
        "CODEX.md",
        "CLAUDE.md",
        "GEMINI.md",
        ".github/copilot-instructions.md",
        ".cursor/rules/project.mdc",
    }:
        return "ai-tooling"
    return None


def projection_registry_path(config: ProjectConfig) -> Path:
    return config.root / ".sula" / "projections" / "registry.json"


def load_projection_registry(config: ProjectConfig) -> dict[str, object]:
    path = projection_registry_path(config)
    if not path.exists():
        return {"version": VERSION, "mode": config.projection_mode, "packs": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid projection registry JSON: {path} ({exc})")
    if not isinstance(data, dict) or not isinstance(data.get("packs", {}), dict):
        raise SystemExit(f"Malformed projection registry: {path}")
    return data


def save_projection_registry(config: ProjectConfig, registry: dict[str, object]) -> None:
    path = projection_registry_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def projection_registry_entries(actions: list[RenderAction]) -> dict[str, list[dict[str, object]]]:
    entries: dict[str, list[dict[str, object]]] = {}
    for action in actions:
        pack = projection_pack_for_action(action)
        if pack is None:
            continue
        entries.setdefault(pack, []).append(
            {
                "path": action.relative_path.as_posix(),
                "managed": action.overwrite,
                "origin": action.origin,
            }
        )
    for values in entries.values():
        values.sort(key=lambda item: (str(item["path"]), bool(item["managed"])))
    return entries


def remove_projection_path(path: Path, project_root: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
        remove_empty_parent_dirs(path.parent, project_root)


def sync_projection_registry(config: ProjectConfig, actions: list[RenderAction]) -> None:
    previous = load_projection_registry(config)
    previous_packs = previous.get("packs", {})
    current_packs = projection_registry_entries(actions)

    previous_managed_paths = {
        str(item.get("path", ""))
        for items in previous_packs.values()
        if isinstance(items, list)
        for item in items
        if isinstance(item, dict) and bool(item.get("managed")) and str(item.get("path", ""))
    }
    current_managed_paths = {
        str(item.get("path", ""))
        for items in current_packs.values()
        if isinstance(items, list)
        for item in items
        if bool(item.get("managed")) and str(item.get("path", ""))
    }
    for relative_path in sorted(previous_managed_paths - current_managed_paths):
        target = config.root / relative_path
        if target.exists() and not target.is_relative_to(config.root / ".sula"):
            remove_projection_path(target, config.root)

    save_projection_registry(
        config,
        {
            "version": VERSION,
            "mode": config.projection_mode,
            "packs": current_packs,
        },
    )


def collect_render_actions(config: ProjectConfig, *, include_scaffold: bool) -> list[RenderAction]:
    tokens = config.token_map()
    candidate_actions: list[RenderAction] = []
    candidate_actions.extend(plan_template_tree(core_managed_dir(), config.root, tokens, overwrite=True, origin="core"))
    candidate_actions.extend(
        plan_template_tree(
            profile_managed_dir(config.profile),
            config.root,
            tokens,
            overwrite=True,
            origin=f"profile:{config.profile}",
        )
    )
    if include_scaffold:
        candidate_actions.extend(
            plan_template_tree(
                core_scaffold_dir(),
                config.root,
                tokens,
                overwrite=False,
                origin="core-scaffold",
            )
        )
        candidate_actions.extend(
            plan_template_tree(
                profile_scaffold_dir(config.profile),
                config.root,
                tokens,
                overwrite=False,
                origin=f"scaffold:{config.profile}",
            )
        )
    enabled_packs = set(config.enabled_projection_packs)
    actions: list[RenderAction] = []
    for action in candidate_actions:
        pack = projection_pack_for_action(action)
        if pack is None or pack not in enabled_packs:
            continue
        if not include_scaffold and not action.overwrite:
            continue
        actions.append(action)
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
    for _ in range(3):
        updated = text
        for key, value in tokens.items():
            updated = updated.replace(f"{{{{{key}}}}}", value)
        if updated == text:
            break
        text = updated
    return localize_template_text(text, tokens.get("CONTENT_LOCALE", "en"))


def apply_actions(actions: list[RenderAction]) -> None:
    for action in actions:
        if action.status not in {"create", "update"}:
            continue
        action.output_path.parent.mkdir(parents=True, exist_ok=True)
        action.output_path.write_text(action.rendered_text, encoding="utf-8")


def apply_projection_state(config: ProjectConfig, actions: list[RenderAction]) -> None:
    apply_actions(actions)
    sync_projection_registry(config, collect_render_actions(config, include_scaffold=True))


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
    summary = (
        args.summary.strip()
        or ("补充这次决策或交付的关键信息。" if locale_family(config.content_locale) == "zh" else "Fill in the key decision or delivery summary.")
    )
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
    if locale_family(config.interaction_locale) == "zh":
        print(f"已在 {output_path} 创建 {args.kind} 记录")
    else:
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
        digest = hashlib.md5(value.encode("utf-8")).hexdigest()[:10]
        return f"item-{digest}"
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
    text = localize_template_text(text, config.content_locale)
    merged_context = dict(template_locale_tokens(config.content_locale))
    merged_context.update(context)
    for key, value in merged_context.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def local_record_template_path(config: ProjectConfig, kind: str) -> Path:
    return record_directory_for_kind(config, kind) / "_template.md"


def builtin_record_template(kind: str) -> str:
    if kind == "change":
        return """# {{TITLE}}

{{RECORD_METADATA_HEADING}}

{{RECORD_DATE_LINE}}
{{RECORD_EXECUTOR_LINE}}
{{RECORD_BRANCH_LINE}}
{{RECORD_RELATED_COMMITS_LINE}}
{{RECORD_STATUS_LINE}}

{{CHANGE_RECORD_BACKGROUND_HEADING}}

{{SUMMARY}}

{{CHANGE_RECORD_ANALYSIS_HEADING}}

{{CHANGE_RECORD_ANALYSIS_PLACEHOLDER}}

{{CHANGE_RECORD_CHOSEN_PLAN_HEADING}}

{{CHANGE_RECORD_CHOSEN_PLAN_PLACEHOLDER}}

{{CHANGE_RECORD_EXECUTION_HEADING}}

{{CHANGE_RECORD_EXECUTION_PLACEHOLDER}}

{{CHANGE_RECORD_VERIFICATION_HEADING}}

{{CHANGE_RECORD_VERIFICATION_PLACEHOLDER}}

{{CHANGE_RECORD_ROLLBACK_HEADING}}

{{CHANGE_RECORD_ROLLBACK_PLACEHOLDER}}

{{CHANGE_RECORD_DATA_SIDE_EFFECTS_HEADING}}

{{CHANGE_RECORD_DATA_SIDE_EFFECTS_PLACEHOLDER}}

{{CHANGE_RECORD_FOLLOW_UP_HEADING}}

{{CHANGE_RECORD_FOLLOW_UP_PLACEHOLDER}}

{{CHANGE_RECORD_ARCHITECTURE_BOUNDARY_HEADING}}

{{CHANGE_RECORD_ARCHITECTURE_BOUNDARY_LINE}}
"""
    if kind == "release":
        return """# {{TITLE}}

{{RECORD_METADATA_HEADING}}

{{RECORD_DATE_LINE}}
{{RECORD_EXECUTOR_LINE}}
{{RECORD_BRANCH_LINE}}
{{RECORD_STATUS_LINE}}

{{RELEASE_RECORD_SCOPE_HEADING}}

{{SUMMARY}}

{{RELEASE_RECORD_RISKS_HEADING}}

{{RELEASE_RECORD_RISKS_PLACEHOLDER}}

{{CHANGE_RECORD_VERIFICATION_HEADING}}

{{CHANGE_RECORD_VERIFICATION_PLACEHOLDER}}

{{CHANGE_RECORD_ROLLBACK_HEADING}}

{{CHANGE_RECORD_ROLLBACK_PLACEHOLDER}}

{{CHANGE_RECORD_FOLLOW_UP_HEADING}}

{{CHANGE_RECORD_FOLLOW_UP_PLACEHOLDER}}
"""
    if kind == "incident":
        return """# {{TITLE}}

{{RECORD_METADATA_HEADING}}

{{RECORD_DATE_LINE}}
{{RECORD_EXECUTOR_LINE}}
{{RECORD_BRANCH_LINE}}
{{RECORD_STATUS_LINE}}

{{INCIDENT_RECORD_SUMMARY_HEADING}}

{{SUMMARY}}

{{INCIDENT_RECORD_IMPACT_HEADING}}

{{INCIDENT_RECORD_IMPACT_PLACEHOLDER}}

{{INCIDENT_RECORD_TIMELINE_HEADING}}

{{INCIDENT_RECORD_TIMELINE_PLACEHOLDER}}

{{INCIDENT_RECORD_ROOT_CAUSE_HEADING}}

{{INCIDENT_RECORD_ROOT_CAUSE_PLACEHOLDER}}

{{INCIDENT_RECORD_RESOLUTION_HEADING}}

{{INCIDENT_RECORD_RESOLUTION_PLACEHOLDER}}

{{CHANGE_RECORD_FOLLOW_UP_HEADING}}

{{CHANGE_RECORD_FOLLOW_UP_PLACEHOLDER}}
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
    locale = config.content_locale
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = default_change_records_index(config)
    relative_link_path = os.path.relpath(record_path, start=index_path.parent).replace(os.sep, "/")
    separator = " - "
    entry = f"- {record_date}{separator}[{title}]({relative_link_path}){separator}{summary}"

    if "- _no records yet_" in text or "- _暂无记录_" in text:
        text = text.replace("- _no records yet_", entry).replace("- _暂无记录_", entry)
    else:
        span = markdown_section_span(text, "Index")
        if span is None:
            marker = f"## {localized_section_name('Index', locale)}"
            text = text.rstrip() + f"\n\n{marker}\n\n" + entry + "\n"
        else:
            _, start, end = span
            index_block = text[start:end].rstrip()
            new_block = index_block + ("\n\n" if index_block.strip() else "\n\n") + entry + "\n"
            text = text[:start] + new_block + text[end:]
    index_path.write_text(text.rstrip() + "\n", encoding="utf-8")


def default_change_records_index(config: ProjectConfig) -> str:
    if locale_family(config.content_locale) == "zh":
        return (
            f"# {config.data['project']['name']} 变更记录\n\n"
            "## 用途\n\n"
            "记录非琐碎变更、关键决策、验证方式与回退信息。\n\n"
            "## 规则\n\n"
            "- 保持索引简洁。\n"
            "- 详细记录放在 docs/change-records/ 下。\n\n"
            "## 索引\n\n"
            "- _暂无记录_\n\n"
            "## 详细记录\n\n"
            f"- 目录: `{config.change_record_directory.relative_to(config.root).as_posix()}`\n"
        )
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
    status_updated_date = date.today().isoformat()
    relative_link_path = os.path.relpath(record_path, start=status_path.parent).replace(os.sep, "/")
    locale = config.content_locale
    if kind == "change":
        bullet = (
            f"- {record_date}: 新增了 [{title}]({relative_link_path})"
            if locale_family(locale) == "zh"
            else f"- {record_date}: added [{title}]({relative_link_path})"
        )
    elif kind == "release":
        bullet = (
            f"- {record_date}: 新增了发布记录 [{title}]({relative_link_path})"
            if locale_family(locale) == "zh"
            else f"- {record_date}: added release record [{title}]({relative_link_path})"
        )
    else:
        bullet = (
            f"- {record_date}: 新增了事故记录 [{title}]({relative_link_path})"
            if locale_family(locale) == "zh"
            else f"- {record_date}: added incident record [{title}]({relative_link_path})"
        )
    latest_record_date, latest_record_path = latest_memory_record_reference(config)
    updated_label = localized_field_label("last updated", locale)
    text = STATUS_UPDATED_PATTERN.sub(f"- {updated_label}: {status_updated_date}", text, count=1)
    text, archived_items = append_bullet_to_section(
        text,
        "Recent Decisions",
        bullet,
        max_items=config.status_recent_decision_limit,
    )
    if latest_record_path is not None:
        relative_latest_path = os.path.relpath(latest_record_path, start=status_path.parent).replace(os.sep, "/")
        text = update_status_handoff_fields(
            text,
            locale=locale,
            updates={
                "start here": f"`{relative_latest_path}`; `STATUS.md`",
                "latest record": f"`{relative_latest_path}`",
                "source of truth": f"`STATUS.md`; `{relative_latest_path}`",
                "source freshness": current_truth_source_freshness_status(config),
                "git branch": detect_git_branch(config.root) if is_git_repository(config.root) else "n/a",
                "git commit": detect_git_commit(config.root),
                "git working tree": detect_git_worktree_state(config.root),
            },
        )
    status_path.write_text(text.rstrip() + "\n", encoding="utf-8")
    if archived_items:
        archive_status_section_items(config, "Recent Decisions", archived_items, archived_on=record_date)


def section_placeholder_bullets(section_name: str) -> list[str]:
    placeholders = {
        "Recent Decisions": ["- _add recent decisions_", "- _补充近期决策_"],
    }
    return placeholders.get(section_name, [])


def status_archive_heading(config: ProjectConfig) -> str:
    return "# 状态归档" if locale_family(config.content_locale) == "zh" else "# Status Archive"


def status_archive_intro(config: ProjectConfig) -> str:
    if locale_family(config.content_locale) == "zh":
        return "这个文件保存从 `STATUS.md` 当前态页移出的超限条目，避免状态页变成长日志。"
    return "This file stores overflow items moved out of `STATUS.md` so the current-state page does not turn into a long log."


def ensure_status_archive_file(config: ProjectConfig) -> Path:
    archive_path = config.status_archive_file
    if archive_path.exists():
        return archive_path
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(
        f"{status_archive_heading(config)}\n\n{status_archive_intro(config)}\n",
        encoding="utf-8",
    )
    return archive_path


def archive_status_section_items(config: ProjectConfig, section_name: str, items: list[str], *, archived_on: str) -> None:
    if not items:
        return
    archive_path = ensure_status_archive_file(config)
    localized_section = localized_section_name(section_name, config.content_locale)
    text = archive_path.read_text(encoding="utf-8")
    marker = f"## {localized_section}"
    entry_lines = [f"### {archived_on}", ""]
    entry_lines.extend(f"- {item}" for item in items)
    entry_block = "\n".join(entry_lines) + "\n"
    span = markdown_section_span(text, section_name)
    if span is None:
        text = text.rstrip() + f"\n\n{marker}\n\n" + entry_block
    else:
        _, start, end = span
        section_body = text[start:end].rstrip()
        new_body = section_body + ("\n\n" if section_body.strip() else "\n\n") + entry_block
        text = text[:start] + new_body + text[end:]
    archive_path.write_text(text.rstrip() + "\n", encoding="utf-8")


def trim_status_section_overflow(text: str, section_name: str, *, max_items: int | None) -> tuple[str, list[str]]:
    if max_items is None or max_items <= 0:
        return text, []
    span = markdown_section_span(text, section_name)
    if span is None:
        return text, []
    _, start, end = span
    section_body = text[start:end]
    items = markdown_bullet_items(section_body)
    items = [item for item in items if f"- {item}" not in section_placeholder_bullets(section_name)]
    if len(items) <= max_items:
        return text, []
    archived_items = items[:-max_items]
    kept_items = items[-max_items:]
    new_body = "\n\n" + "\n".join(f"- {item}" for item in kept_items) + "\n"
    return text[:start] + new_body + text[end:], archived_items


def normalize_status_current_state_sections(config: ProjectConfig) -> bool:
    status_path = config.root / config.data["paths"]["status_file"]
    if not status_path.exists():
        return False
    text = status_path.read_text(encoding="utf-8")
    changed = False
    archived_on = date.today().isoformat()
    for section_name, max_items in [
        ("Current Focus", config.status_current_focus_limit),
        ("Blockers", config.status_blocker_limit),
        ("Recent Decisions", config.status_recent_decision_limit),
    ]:
        text, archived_items = trim_status_section_overflow(text, section_name, max_items=max_items)
        if archived_items:
            archive_status_section_items(config, section_name, archived_items, archived_on=archived_on)
            changed = True
    if changed:
        status_path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return changed


def cmd_test(config: ProjectConfig, args: argparse.Namespace) -> int:
    """Run project tests with tiered scope: quick (default), module, or full."""
    if getattr(args, "list_modules", False):
        return _cmd_test_list_modules(config)

    if getattr(args, "full", False):
        return _cmd_test_run_full(config)

    module = getattr(args, "module", None)
    if module:
        return _cmd_test_run_module(config, module)

    return _cmd_test_quick(config)


def _cmd_test_quick(config: ProjectConfig) -> int:
    """Quick validation: check + doctor --strict."""
    print("=== Quick validation ===")
    check_ok = daily_check(config, emit_output=False) == 0
    doctor_ok = doctor(config, strict=True, json_mode=False) == 0
    if check_ok and doctor_ok:
        print("All quick checks passed.")
        return 0
    print("Quick checks failed. Run `sula test --full` for detailed diagnostics.")
    return 1


def _cmd_test_run_full(config: ProjectConfig) -> int:
    """Run the full test suite explicitly."""
    tests_dir = config.root / "tests"
    if not tests_dir.is_dir():
        print("No tests/ directory found.")
        return 1
    print("=== Full test suite ===")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-v"],
        cwd=config.root,
    )
    if result.returncode == 0:
        print("All tests passed.")
    else:
        print(f"Tests failed (exit code {result.returncode}).")
    return result.returncode


def _cmd_test_run_module(config: ProjectConfig, module: str) -> int:
    """Run tests matching a module prefix (e.g. 'orchestration', 'check')."""
    tests_dir = config.root / "tests"
    if not tests_dir.is_dir():
        print("No tests/ directory found.")
        return 1
    pattern = f"test_{module}"
    print(f"=== Tests matching '{pattern}' ===")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", f"*.py", "-k", pattern, "-v"],
        cwd=config.root,
    )
    if result.returncode == 0:
        print(f"All '{module}' tests passed.")
    else:
        print(f"Some '{module}' tests failed (exit code {result.returncode}).")
    return result.returncode


def _cmd_test_list_modules(config: ProjectConfig) -> int:
    """Scan test file and list available modules with test counts."""
    test_file = config.root / "tests" / "test_sula.py"
    if not test_file.exists():
        print("No test file found at tests/test_sula.py")
        return 1
    modules: dict[str, int] = {}
    total = 0
    for line in test_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s+def test_(\w+)", line)
        if m:
            total += 1
            name = m.group(1)
            parts = name.split("_")
            mod = parts[0] if parts else "other"
            modules[mod] = modules.get(mod, 0) + 1
    print(f"Available test modules ({total} tests total):")
    for mod, count in sorted(modules.items(), key=lambda x: -x[1]):
        print(f"  {mod:25s} {count} tests")
    print()
    print("Usage:")
    print("  sula test                    Quick validation (check + doctor)")
    print("  sula test --module <name>    Run one module's tests")
    print("  sula test --full             Run all tests")
    return 0


def cmd_report(config: ProjectConfig, args: argparse.Namespace) -> int:
    """Write a session report into STATUS.md Summary and regenerate derived state."""
    status_path = config.root / config.data["paths"]["status_file"]
    if not status_path.exists():
        print("STATUS.md not found.")
        return 1

    today = date.today().isoformat()
    text = status_path.read_text(encoding="utf-8")
    summary_text = args.summary.strip()
    if not summary_text:
        print("Summary text is empty.")
        return 1

    group_order: list[str] = []
    archived_items: list[str] = []

    span = markdown_section_span(text, "Summary")
    if span is None:
        health_span = markdown_section_span(text, "Health")
        insertion_point = health_span[2] if health_span else len(text)
        new_section = f"\n\n## Summary\n\n### {today}\n\n- {summary_text}\n"
        text = text[:insertion_point] + new_section + text[insertion_point:]
        group_order = [today]
    else:
        _, start, end = span
        summary_body = text[start:end]

        groups: dict[str, list[str]] = {}
        lines = summary_body.splitlines(keepends=False)
        current_heading: str | None = None
        current_items: list[str] = []

        for raw_line in lines:
            line = raw_line.rstrip()
            if line.startswith("### "):
                if current_heading is not None:
                    groups[current_heading] = current_items
                    group_order.append(current_heading)
                current_heading = line[4:].strip()
                current_items = []
            elif line.strip().startswith("- ") and current_heading is not None:
                current_items.append(line.strip()[2:])
        if current_heading is not None:
            groups[current_heading] = current_items
            group_order.append(current_heading)

        if today in groups:
            if summary_text not in groups[today]:
                groups[today].append(summary_text)
        else:
            group_order.insert(0, today)
            groups[today] = [summary_text]

        date_groups = [h for h in group_order if MEMORY_DATE_PATTERN.fullmatch(h)]
        non_date_groups = [h for h in group_order if not MEMORY_DATE_PATTERN.fullmatch(h)]
        max_date_groups = 30
        if len(date_groups) > max_date_groups:
            for heading in date_groups[: -max_date_groups]:
                for item in groups.get(heading, []):
                    archived_items.append(f"({heading}) {item}")
                del groups[heading]
            date_groups = date_groups[-max_date_groups:]
            group_order = date_groups + non_date_groups

        new_body_lines: list[str] = []
        for heading in group_order:
            new_body_lines.append(f"### {heading}")
            new_body_lines.append("")
            for item in groups.get(heading, []):
                new_body_lines.append(f"- {item}")
            new_body_lines.append("")
        new_body = "\n".join(new_body_lines)
        text = text[:start] + new_body + text[end:]

    text = update_status_handoff_fields(
        text,
        locale=config.interaction_locale,
        updates={
            "verification date": today,
            "git working tree": detect_git_worktree_state(config.root),
        },
    )

    status_path.write_text(text.rstrip() + "\n", encoding="utf-8")

    if archived_items:
        archive_status_section_items(config, "Summary", archived_items, archived_on=today)

    lightweight = bool(getattr(args, "lightweight", False))

    if not lightweight:
        digest_args = argparse.Namespace(output=None, stdout=False, json=json_output_requested(args))
        generate_memory_digest(config, digest_args, emit_output=True)

        refresh_kernel_state(
            config,
            event_type="report.created",
            summary=f"Session report written to STATUS.md under {today}.",
        )

    date_group_count = len(
        [h for h in group_order if MEMORY_DATE_PATTERN.fullmatch(h)]
    )
    if json_output_requested(args):
        emit_json(
            {
                "command": "report",
                "status": "ok",
                "project": project_payload(config),
                "summary_date": today,
                "date_group_count": date_group_count,
                "archived": len(archived_items),
                "lightweight": lightweight,
                "digest_path": config.digest_file.relative_to(config.root).as_posix(),
            }
        )
    else:
        zh = locale_family(config.interaction_locale) == "zh"
        if lightweight:
            print(f"STATUS.md {'updated' if not zh else '已更新'} (lightweight).")
        else:
            parts = [
                f"STATUS.md {'updated' if not zh else '已更新'} with 1 entry under {today}."
            ]
            if archived_items:
                parts.append(
                    f"Archived {len(archived_items)} old {'entries' if not zh else '条目'}."
                )
            parts.append(
                f"Digest regenerated at {config.digest_file.relative_to(config.root).as_posix()}."
            )
            print(" ".join(parts))

    return 0


def append_bullet_to_section(text: str, section_name: str, bullet: str, *, max_items: int | None = None) -> tuple[str, list[str]]:
    span = markdown_section_span(text, section_name)
    bullet_value = bullet[2:].strip() if bullet.startswith("- ") else bullet.strip()
    if span is None:
        marker = f"## {section_name}"
        items = [bullet_value]
        body = "\n".join(f"- {item}" for item in items)
        new_text = text.rstrip() + f"\n\n{marker}\n\n{body}\n"
        return trim_status_section_overflow(new_text, section_name, max_items=max_items)
    _, start, end = span
    section_body = text[start:end]
    items = markdown_bullet_items(section_body)
    items = [item for item in items if f"- {item}" not in section_placeholder_bullets(section_name)]
    if bullet_value in items:
        return text, []
    items.append(bullet_value)
    new_body = "\n\n" + "\n".join(f"- {item}" for item in items) + "\n"
    return trim_status_section_overflow(text[:start] + new_body + text[end:], section_name, max_items=max_items)


def update_status_handoff_fields(text: str, *, locale: str, updates: dict[str, str]) -> str:
    span = markdown_section_span(text, "Handoff")
    if span is None:
        return text
    _, start, end = span
    section_body = text[start:end]
    fields = markdown_key_values(section_body)
    fields.update({key: value for key, value in updates.items() if value})
    ordered_keys = [
        "ready",
        "start here",
        "latest record",
        "next action",
        "next owner",
        "next due",
        "done when",
        "blockers",
        "source of truth",
        "source freshness",
        "verification command",
        "verification result",
        "verification date",
        "git branch",
        "git commit",
        "git working tree",
    ]
    extra_keys = [key for key in fields if key not in ordered_keys]
    rendered_lines = []
    for key in ordered_keys + extra_keys:
        value = fields.get(key, "").strip()
        if not value:
            continue
        rendered_lines.append(f"- {localized_field_label(key, locale)}: {value}")
    if not rendered_lines:
        return text
    new_body = "\n\n" + "\n".join(rendered_lines) + "\n"
    return text[:start] + new_body + text[end:]


def sync_status_handoff_runtime_fields(config: ProjectConfig, *, bump_last_updated: bool) -> bool:
    status_path = config.root / config.data["paths"]["status_file"]
    if not status_path.exists():
        return False
    original_text = status_path.read_text(encoding="utf-8")
    text = original_text
    if bump_last_updated:
        updated_label = localized_field_label("last updated", config.content_locale)
        text = STATUS_UPDATED_PATTERN.sub(f"- {updated_label}: {date.today().isoformat()}", text, count=1)
    current_commit = ""
    if "Handoff" in markdown_sections(text):
        handoff_fields = markdown_key_values(markdown_sections(text)["Handoff"])
        current_commit = handoff_fields.get("git commit", "")
    text = update_status_handoff_fields(
        text,
        locale=config.content_locale,
        updates={
            "source freshness": current_truth_source_freshness_status(config),
            "git branch": detect_git_branch(config.root) if is_git_repository(config.root) else "n/a",
            "git commit": current_commit if current_commit == "any" else detect_git_commit(config.root),
            "git working tree": detect_git_worktree_state(config.root),
        },
    )
    if text == original_text:
        return False
    status_path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return True


def markdown_section_span(text: str, canonical_name: str) -> tuple[str, int, int] | None:
    lines = text.splitlines(keepends=True)
    offset = 0
    current_heading: str | None = None
    current_body_start = 0
    current_heading_text = ""
    for line in lines:
        if line.startswith("## "):
            if current_heading == canonical_name:
                return current_heading_text, current_body_start, offset
            current_heading_text = line.rstrip("\n")
            current_heading = canonical_section_name(line[3:].strip())
            current_body_start = offset + len(line)
        offset += len(line)
    if current_heading == canonical_name:
        return current_heading_text, current_body_start, len(text)
    return None


def generate_memory_digest(config: ProjectConfig, args: argparse.Namespace, *, emit_output: bool = True) -> int:
    normalize_status_current_state_sections(config)
    output_path = config.digest_file if not args.output else (config.root / args.output)
    digest = build_memory_digest(config, output_path)
    if args.stdout and emit_output:
        print(digest, end="")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest, encoding="utf-8")
    job = record_memory_job(
        config,
        job_type="memory.digest",
        status="ok",
        summary=f"Regenerated memory digest at `{output_path.relative_to(config.root).as_posix()}`.",
        details={"output_path": output_path.relative_to(config.root).as_posix()},
    )
    refresh_kernel_state(config, event_type="memory.digest", summary=f"Regenerated memory digest at `{output_path.relative_to(config.root).as_posix()}`.")
    if json_output_requested(args) and emit_output:
        emit_json(
            {
                "command": "memory.digest",
                "status": "ok",
                "project": project_payload(config),
                "output_path": output_path.relative_to(config.root).as_posix(),
                "job": job,
            }
        )
        return 0
    if emit_output:
        if locale_family(config.interaction_locale) == "zh":
            print(f"已将记忆摘要写入 {output_path}")
        else:
            print(f"Wrote memory digest to {output_path}")
    return 0


def build_memory_digest(config: ProjectConfig, output_path: Path) -> str:
    status_path = config.root / config.data["paths"]["status_file"]
    change_index_path = config.root / config.data["paths"]["change_records_file"]
    status_text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
    status_sections = markdown_sections(status_text)
    zh = locale_family(config.content_locale) == "zh"

    lines = [
        f"# {config.data['project']['name']} {'记忆摘要' if zh else 'Memory Digest'}",
        "",
        f"- {localized_field_label('generated by', config.content_locale)}: Sula {VERSION}",
        "- 真相源是项目文档与记录，而不是这份生成摘要" if zh else "- source of truth: project docs and records, not this generated digest",
        "",
        f"## {localized_section_name('Identity', config.content_locale)}",
        "",
        f"- {localized_field_label('project', config.content_locale)}: {config.data['project']['name']}",
        f"- {localized_field_label('profile', config.content_locale)}: {config.profile}",
        f"- {localized_field_label('description', config.content_locale)}: {config.data['project']['description']}",
        f"- {localized_field_label('highest rule', config.content_locale)}: `{config.data['rules']['highest_rule']}`",
        "",
        f"## {localized_section_name('Current State', config.content_locale)}",
        "",
    ]
    lines.extend(section_digest_lines("Summary", status_sections.get("Summary", localized_string("_missing_", config.content_locale)), locale=config.content_locale))
    lines.extend(section_digest_lines("Health", status_sections.get("Health", localized_string("_missing_", config.content_locale)), locale=config.content_locale))
    lines.extend(section_digest_lines("Current Focus", status_sections.get("Current Focus", localized_string("_missing_", config.content_locale)), locale=config.content_locale))
    lines.extend(section_digest_lines("Blockers", status_sections.get("Blockers", localized_string("_missing_", config.content_locale)), locale=config.content_locale))
    lines.extend(section_digest_lines("Recent Decisions", status_sections.get("Recent Decisions", localized_string("_missing_", config.content_locale)), locale=config.content_locale))
    lines.extend(section_digest_lines("Next Review", status_sections.get("Next Review", localized_string("_missing_", config.content_locale)), locale=config.content_locale))
    lines.extend(section_digest_lines("Handoff", status_sections.get("Handoff", localized_string("_missing_", config.content_locale)), locale=config.content_locale))

    lines.extend([f"## {localized_section_name('Recent Change Records', config.content_locale)}", ""])
    lines.extend(record_summary_lines(config.change_record_directory, output_path, limit=5, locale=config.content_locale))

    lines.extend([f"## {localized_section_name('Release History', config.content_locale)}", ""])
    lines.extend(record_summary_lines(config.release_record_directory, output_path, limit=3, locale=config.content_locale))

    lines.extend([f"## {localized_section_name('Incident History', config.content_locale)}", ""])
    lines.extend(record_summary_lines(config.incident_record_directory, output_path, limit=3, locale=config.content_locale))

    lines.extend([f"## {localized_section_name('Open Architecture Exceptions', config.content_locale)}", ""])
    lines.extend(exception_summary_lines(config, output_path))

    lines.extend([f"## {localized_section_name('Active Orchestration Tasks', config.content_locale)}", ""])
    if config.orchestration_enabled:
        try:
            tasks, task_issues = load_orchestration_tasks(config)
            open_tasks = [t for t in tasks if t.get("state") in {"open", "running"}]
            if open_tasks:
                for t in open_tasks[:5]:
                    title = t.get("title", "untitled")
                    tid = t.get("id", "")
                    state = t.get("state", "unknown")
                    lines.append(f"- [{title}] (state={state})")
                    for ac in t.get("acceptance_criteria", [])[:2]:
                        lines.append(f"  - acceptance: {ac}")
            else:
                lines.append(f"- {localized_string('none', config.content_locale)}")
        except Exception:
            lines.append(f"- {localized_string('none', config.content_locale)}")
        try:
            runs = read_orchestration_runs(config)
            pending_runs = [r for r in runs if r.get("status") not in {"accepted", "failed", "cancelled"}]
            if pending_runs:
                lines.append("")
                lines.append(f"### {localized_section_name('Pending Runs', config.content_locale)}")
                for r in pending_runs[:3]:
                    lines.append(f"- run `{r.get('run_id')}`: status={r.get('status')}, task={r.get('task_id')}")
        except Exception:
            pass
    else:
        lines.append(f"- {localized_string('orchestration disabled', config.content_locale)}")
    lines.append("")

    lines.extend(
        [
            f"## {localized_section_name('Key References', config.content_locale)}",
            "",
            f"- [Status]({relative_link(output_path, status_path)})",
            f"- [Change Record Index]({relative_link(output_path, change_index_path)})",
            f"- [Project Memory Guide]({relative_link(output_path, config.root / 'docs/ops/project-memory.md')})",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def section_digest_lines(title: str, body: str, *, locale: str) -> list[str]:
    cleaned = body.strip() or localized_string("_missing_", locale)
    return [f"### {localized_section_name(title, locale)}", "", cleaned, ""]


def record_summary_lines(directory: Path, output_path: Path, *, limit: int, locale: str) -> list[str]:
    files = list_record_files(directory)
    if not files:
        return [f"- {localized_string('none', locale)}", ""]
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
        return ["- 未找到登记册" if locale_family(config.content_locale) == "zh" else "- no register found", ""]
    text = path.read_text(encoding="utf-8")
    rows = []
    for raw_line in text.splitlines():
        if not raw_line.startswith("|"):
            continue
        if raw_line.startswith("| ID ") or raw_line.startswith("| ---") or "_none yet_" in raw_line:
            continue
        rows.append(raw_line)
    if not rows:
        return [f"- {localized_string('none', config.content_locale)}", ""]
    lines = [
        (
            f"- [exception register]({relative_link(output_path, path)}) 中有 {len(rows)} 条开放或历史条目"
            if locale_family(config.content_locale) == "zh"
            else f"- {len(rows)} open or historical entries in [exception register]({relative_link(output_path, path)})"
        ),
        "",
    ]
    return lines


def markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = canonical_section_name(line[3:].strip())
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


def inspect_doctor_state(config: ProjectConfig, *, strict: bool) -> dict[str, object]:
    missing_files: list[str] = []
    drifted_files: list[str] = []
    placeholder_files: list[str] = []
    lock_issues: list[str] = []
    warnings = collect_doctor_warnings(config)
    advisories: list[str] = []
    memory_errors, memory_warnings, memory_advisories = collect_memory_doctor_report(config)
    warnings.extend(memory_warnings)
    advisories.extend(memory_advisories)
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
    has_errors = bool(missing_files or drifted_files or placeholder_files or memory_errors or lock_issues or kernel_errors)
    passed = not has_errors and not (strict and warnings)
    return {
        "missing_files": missing_files,
        "drifted_files": drifted_files,
        "placeholder_files": placeholder_files,
        "memory_errors": memory_errors,
        "lock_issues": lock_issues,
        "kernel_errors": kernel_errors,
        "warnings": warnings,
        "advisories": advisories,
        "passed": passed,
        "has_errors": has_errors,
    }


def doctor(config: ProjectConfig, *, strict: bool, json_mode: bool = False, emit_output: bool = True) -> int:
    report = inspect_doctor_state(config, strict=strict)
    missing_files = report["missing_files"]
    drifted_files = report["drifted_files"]
    placeholder_files = report["placeholder_files"]
    memory_errors = report["memory_errors"]
    lock_issues = report["lock_issues"]
    kernel_errors = report["kernel_errors"]
    warnings = report["warnings"]
    advisories = report["advisories"]

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
    if emit_output and not json_mode and advisories:
        print("Advisories:")
        for item in advisories:
            print(f"  - {item}")

    passed = bool(report["passed"])
    if emit_output:
        flat_issues = flatten_daily_check_issues(report, [])
        automation_result = automation_observe_event(
            config,
            source_kind="sula-cli",
            event_kind="doctor.passed" if passed else "doctor.failed",
            title="Sula doctor strict" if strict else "Sula doctor",
            summary="Sula doctor passed." if passed else "Sula doctor failed.",
            identity_key=("doctor-strict:" if strict else "doctor:") + date.today().isoformat(),
            payload={"passed": passed, "strict": strict, "issues": flat_issues},
        )
        if not json_mode:
            print_sula_activity_feedback(config, automation_result)
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
                    advisories=advisories,
                    passed=passed,
                ),
            }
        )
        return 0 if passed else 1
    if passed:
        if emit_output:
            if locale_family(config.interaction_locale) == "zh":
                print(f"{config.data['project']['name']} 的 Sula doctor 校验通过")
            else:
                print(f"Sula doctor passed for {config.data['project']['name']}")
        return 0
    return 1


def normalize_generated_snapshot_text(text: str) -> str:
    lines = [line for line in text.splitlines() if not GENERATED_ON_PATTERN.fullmatch(line)]
    return "\n".join(lines).strip()


def collect_daily_check_drift_errors(config: ProjectConfig) -> list[str]:
    errors: list[str] = []
    repair_command = f"python3 scripts/sula.py memory digest --project-root {shlex.quote(str(config.root))}"

    generated_targets = [
        (config.root / ".sula" / "state" / "current.md", render_kernel_current_state(config)),
        (config.digest_file, build_memory_digest(config, config.digest_file)),
    ]
    for path, expected_text in generated_targets:
        if not path.exists():
            errors.append(f"missing generated state file: {path}. Rebuild with `{repair_command}`.")
            continue
        current_text = path.read_text(encoding="utf-8")
        if normalize_generated_snapshot_text(current_text) != normalize_generated_snapshot_text(expected_text):
            errors.append(f"{path}: generated state is out of sync with current source documents. Rebuild with `{repair_command}`.")
    return errors


def is_sula_check_automation_task(task: dict[str, object]) -> bool:
    labels = set(normalize_task_string_list(task.get("labels")))
    return normalize_optional_text(task.get("source_kind", "")) == "automation" and "sula-check" in labels


def sula_check_automation_task_ids(config: ProjectConfig) -> set[str]:
    ids: set[str] = set()
    for intent in load_automation_intents(config):
        labels = set(normalize_task_string_list(intent.get("labels")))
        if "sula-check" not in labels:
            continue
        task_id = normalize_optional_text(intent.get("task_id", ""))
        if task_id:
            ids.add(task_id)
    return ids


def collect_orchestration_check_errors(config: ProjectConfig) -> list[str]:
    """Check for open orchestration tasks and unclosed runs. Emit warnings, not hard errors."""
    errors: list[str] = []
    if not config.orchestration_enabled:
        return errors
    if not config.orchestration_tasks_path.exists():
        return errors
    try:
        tasks, task_issues = load_orchestration_tasks(config)
        ignored_task_ids = sula_check_automation_task_ids(config)
        for task in tasks:
            if is_sula_check_automation_task(task):
                task_id = normalize_optional_text(task.get("id", ""))
                if task_id:
                    ignored_task_ids.add(task_id)
        open_tasks = [
            t
            for t in tasks
            if t.get("state") in {"open", "running"}
            and t.get("eligible")
            and normalize_optional_text(t.get("id", "")) not in ignored_task_ids
        ]
        if open_tasks:
            task_ids = ", ".join(normalize_optional_text(t.get("id", "")) for t in open_tasks[:3])
            suffix = f": {task_ids}" if task_ids else ""
            errors.append(f"orchestration: {len(open_tasks)} open/eligible task(s) exist{suffix}. Close them with `orchestration close --accept`.")
        blocked = [
            t
            for t in tasks
            if t.get("blocked_reasons")
            and t.get("state") in {"open", "running"}
            and normalize_optional_text(t.get("id", "")) not in ignored_task_ids
        ]
        for t in blocked[:3]:
            reasons = "; ".join(str(r) for r in t.get("blocked_reasons", [])[:2])
            errors.append(f"orchestration: task `{t.get('id')}` blocked: {reasons}")
    except Exception:
        errors.append("orchestration: could not load task file")
    try:
        runs = read_orchestration_runs(config)
        ignored_task_ids = sula_check_automation_task_ids(config)
        pending_runs = [
            r
            for r in runs
            if r.get("status") in {"planned", "running", "human-review"}
            and normalize_optional_text(r.get("task_id", "")) not in ignored_task_ids
        ]
        if pending_runs:
            errors.append(f"orchestration: {len(pending_runs)} run(s) not yet accepted/closed.")
    except Exception:
        pass
    return errors


def flatten_daily_check_issues(report: dict[str, object], drift_errors: list[str]) -> list[str]:
    issues: list[str] = []
    issues.extend(str(item) for item in report["missing_files"])
    issues.extend(str(item) for item in report["drifted_files"])
    issues.extend(str(item) for item in report["placeholder_files"])
    issues.extend(str(item) for item in report["memory_errors"])
    issues.extend(str(item) for item in report["lock_issues"])
    issues.extend(str(item) for item in report["kernel_errors"])
    issues.extend(f"warning: {item}" for item in report["warnings"])
    issues.extend(f"advisory: {item}" for item in report["advisories"])
    issues.extend(drift_errors)
    return issues


def count_nonempty_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def build_daily_check_commands(config: ProjectConfig, report: dict[str, object], drift_errors: list[str]) -> list[str]:
    commands: list[str] = []
    project_root_arg = shlex.quote(str(config.root))
    if drift_errors:
        commands.append(f"python3 scripts/sula.py memory digest --project-root {project_root_arg}")
    if any("staged capture" in str(item) for item in report["memory_errors"]):
        commands.append(f"python3 scripts/sula.py memory review --project-root {project_root_arg} --json")
        commands.append(f"python3 scripts/sula.py memory clear --project-root {project_root_arg} --reviewed-captures")
    if report["missing_files"] or report["drifted_files"] or report["placeholder_files"] or report["lock_issues"]:
        commands.append(f"python3 scripts/sula.py sync --project-root {project_root_arg} --dry-run")
    commands.append(f"python3 scripts/sula.py check --project-root {project_root_arg}")

    deduped: list[str] = []
    seen: set[str] = set()
    for command in commands:
        if command in seen:
            continue
        seen.add(command)
        deduped.append(command)
    return deduped


def daily_check_payload(config: ProjectConfig, report: dict[str, object], drift_errors: list[str], *, passed: bool) -> dict[str, object]:
    status_path = config.root / config.data["paths"]["status_file"]
    status_text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
    return {
        "project": project_payload(config),
        "passed": passed,
        "status_updated": extract_status_updated_date(status_text),
        "event_log_entries": count_nonempty_lines(config.root / ".sula" / "events" / "log.jsonl"),
        "change_record_count": len(list_record_files(config.change_record_directory)),
        "derived_state_errors": drift_errors,
        "issues": flatten_daily_check_issues(report, drift_errors),
        "repair_commands": build_daily_check_commands(config, report, drift_errors),
        "doctor": doctor_payload(
            config,
            missing_files=report["missing_files"],
            drifted_files=report["drifted_files"],
            placeholder_files=report["placeholder_files"],
            memory_errors=report["memory_errors"],
            lock_issues=report["lock_issues"],
            kernel_errors=report["kernel_errors"],
            warnings=report["warnings"],
            advisories=report["advisories"],
            passed=bool(report["passed"]),
        ),
    }


def daily_check(config: ProjectConfig, *, json_mode: bool = False, emit_output: bool = True, skip_orchestration: bool = False) -> int:
    report = inspect_doctor_state(config, strict=True)
    drift_errors = collect_daily_check_drift_errors(config)
    if not skip_orchestration:
        drift_errors.extend(collect_orchestration_check_errors(config))
    passed = bool(report["passed"]) and not drift_errors
    payload = daily_check_payload(config, report, drift_errors, passed=passed)
    if emit_output:
        automation_result = automation_observe_event(
            config,
            source_kind="sula-cli",
            event_kind="check.passed" if passed else "check.failed",
            title="Sula check",
            summary="Sula check passed." if passed else "Sula check failed.",
            identity_key="check:" + date.today().isoformat(),
            payload={
                "passed": passed,
                "issues": payload["issues"],
                "repair_commands": payload["repair_commands"],
            },
        )
        if not json_mode:
            print_sula_activity_feedback(config, automation_result)

    if json_mode and emit_output:
        emit_json({"command": "check", "status": "ok" if passed else "failed", **payload})
        return 0 if passed else 1

    if not emit_output:
        return 0 if passed else 1

    if passed:
        print("SULA CHECK OK")
        print(f"project={config.data['project']['slug']}")
        print(f"status_updated={payload['status_updated'] or 'missing'}")
        print(f"event_log_entries={payload['event_log_entries']}")
        print(f"change_records={payload['change_record_count']}")
        advisories = payload["doctor"].get("advisories", [])
        if advisories:
            print("advisories:")
            for item in advisories:
                print(f"  - {item}")
        return 0

    print("SULA CHECK FAILED")
    print(f"project={config.data['project']['slug']}")
    print("issues:")
    for item in payload["issues"]:
        print(f"  - {item}")
    print("next:")
    for command in payload["repair_commands"]:
        print(f"  - {command}")
    return 1


def collect_doctor_warnings(config: ProjectConfig) -> list[str]:
    warnings: list[str] = []
    for section, key in EXISTENCE_WARNING_FIELDS:
        section_data = config.data.get(section, {})
        if not isinstance(section_data, dict) or key not in section_data:
            continue
        relative_value = str(section_data[key])
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
                source_ids: set[str] = set()
                duplicate_source_ids: set[str] = set()
                malformed_source_entry = False
                for item in registry:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("path"), str):
                        errors.append(f"source registry entry is malformed: {registry_path}")
                        malformed_source_entry = True
                        break
                    source_id = item["id"]
                    if source_id in source_ids:
                        duplicate_source_ids.add(source_id)
                    source_ids.add(source_id)
                if duplicate_source_ids:
                    duplicates = ", ".join(f"`{item}`" for item in sorted(duplicate_source_ids))
                    errors.append(f"{registry_path}: duplicate source ids detected {duplicates}")
                if malformed_source_entry:
                    registry = []
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


def collect_memory_doctor_report(config: ProjectConfig) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    advisories: list[str] = []

    status_path = config.root / config.data["paths"]["status_file"]
    if not status_path.exists():
        errors.append(f"missing status file: {status_path}")
    else:
        latest_record_date, latest_record_path = latest_memory_record_reference(config)
        status_errors, status_warnings, status_advisories = validate_status_file(
            status_path,
            config,
            latest_record_date=latest_record_date,
            latest_record_path=latest_record_path,
        )
        errors.extend(status_errors)
        warnings.extend(status_warnings)
        advisories.extend(status_advisories)

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
        required_sections=CHANGE_RECORD_REQUIRED_SECTIONS,
        required=True,
    )
    release_errors, release_warnings = validate_record_directory(
        config.release_record_directory,
        kind="release",
        required_sections=RELEASE_RECORD_REQUIRED_SECTIONS,
        required=False,
    )
    incident_errors, incident_warnings = validate_record_directory(
        config.incident_record_directory,
        kind="incident",
        required_sections=INCIDENT_RECORD_REQUIRED_SECTIONS,
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

    capture_errors, capture_warnings = validate_session_capture_store(config)
    errors.extend(capture_errors)
    warnings.extend(capture_warnings)

    job_errors, job_warnings = validate_memory_jobs_store(config)
    errors.extend(job_errors)
    warnings.extend(job_warnings)

    promotion_errors, promotion_warnings = validate_promotion_file(config)
    errors.extend(promotion_errors)
    warnings.extend(promotion_warnings)

    gitignore_path = config.root / ".gitignore"
    if gitignore_path.exists():
        gitignore_text = gitignore_path.read_text(encoding="utf-8")
        if "memory-digest.md" in gitignore_text:
            zh = locale_family(config.content_locale) == "zh"
            advisories.append(
                "`.gitignore` 包含 `**/.sula/memory-digest.md` => 删除该行，运行 `sula memory digest`，提交 digest，使新 clone 的 AI 立即可读项目状态"
                if zh
                else "`.gitignore` contains `**/.sula/memory-digest.md` => remove it, run `sula memory digest`, commit the digest so new clones have immediate AI handoff"
            )

    return errors, warnings, advisories


def validate_session_capture_store(config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    path = config.session_capture_store
    if not path.exists():
        return errors, warnings
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid session capture JSON at {path}:{line_number} ({exc})")
            break
        if not isinstance(item, dict):
            errors.append(f"session capture entry is malformed: {path}:{line_number}")
            break
        capture_id = normalize_optional_text(item.get("id", "")).strip()
        title = normalize_optional_text(item.get("title", "")).strip()
        summary = normalize_optional_text(item.get("summary", "")).strip()
        status = normalize_optional_text(item.get("status", "")).strip()
        captured_at = normalize_optional_text(item.get("captured_at", "")).strip()
        if not capture_id or not title or not summary:
            errors.append(f"session capture entry is missing required fields: {path}:{line_number}")
            break
        if status not in MEMORY_CAPTURE_STATUS_CHOICES:
            errors.append(f"{path}:{line_number}: unsupported session capture status `{status}`")
            break
        try:
            normalized_captured_at = normalize_optional_timestamp(captured_at)
        except SystemExit as exc:
            errors.append(f"{path}:{line_number}: {exc}")
            break
        if status == "staged":
            captured_date = datetime.fromisoformat(normalized_captured_at.replace("Z", "+00:00")).date()
            age_days = (date.today() - captured_date).days
            if age_days > config.session_retention_days:
                errors.append(
                    f"{path}:{line_number}: staged capture `{capture_id}` is {age_days} days old, over the {config.session_retention_days}-day review target"
                )
        if status == "promoted" and not normalize_optional_text(item.get("promotion_path", "")).strip():
            warnings.append(f"{path}:{line_number}: promoted capture `{capture_id}` is missing `promotion_path`")
    return errors, warnings


def validate_memory_jobs_store(config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    path = config.memory_jobs_history_path
    if not path.exists():
        return errors, warnings
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid memory job JSON at {path}:{line_number} ({exc})")
            break
        if not isinstance(item, dict) or not normalize_optional_text(item.get("id", "")).strip():
            errors.append(f"memory job entry is malformed: {path}:{line_number}")
            break
        if not normalize_optional_text(item.get("job_type", "")).strip():
            warnings.append(f"{path}:{line_number}: memory job is missing `job_type`")
    latest_path = config.memory_jobs_latest_path
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid memory latest-job JSON: {latest_path} ({exc})")
        else:
            if latest and (not isinstance(latest, dict) or not normalize_optional_text(latest.get("id", "")).strip()):
                errors.append(f"memory latest-job payload is malformed: {latest_path}")
    return errors, warnings


def validate_promotion_file(config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    path = config.promotion_file
    if not path.exists():
        promoted_exists = any(item.get("status") == "promoted" for item in read_session_captures(config))
        if promoted_exists:
            errors.append(f"missing promotion file: {path}")
        return errors, warnings
    text = path.read_text(encoding="utf-8")
    sections = markdown_sections(text)
    for section_name in ["Rules", "Tasks", "Decisions", "Risks"]:
        if section_name not in sections:
            errors.append(f"{path}: missing section `## {section_name}`")
    if not extract_markdown_title(text):
        errors.append(f"{path}: missing top-level title")
    return errors, warnings


def latest_memory_record_reference(config: ProjectConfig) -> tuple[str | None, Path | None]:
    latest_date: str | None = None
    latest_path: Path | None = None
    for directory in [config.change_record_directory, config.release_record_directory, config.incident_record_directory]:
        for record_path in list_record_files(directory):
            text = record_path.read_text(encoding="utf-8")
            record_date = detect_record_date(record_path, text)
            if not record_date:
                continue
            if latest_date is None or record_date > latest_date:
                latest_date = record_date
                latest_path = record_path
    return latest_date, latest_path


def contains_status_placeholder(value: str) -> bool:
    return any(placeholder in value for placeholder in STATUS_PLACEHOLDERS)


def normalize_status_reference_value(value: str) -> str:
    stripped = value.strip()
    link_match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", stripped)
    if link_match:
        stripped = link_match.group(2).strip()
    if stripped.startswith("`") and stripped.endswith("`") and len(stripped) >= 2:
        stripped = stripped[1:-1].strip()
    return stripped


def normalize_handoff_ready_value(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in {"yes", "true", "ready", "ok", "是", "已就绪"}:
        return "yes"
    if lowered in {"no", "false", "not ready", "否", "未就绪"}:
        return "no"
    return None


def normalize_git_worktree_value(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in {"n/a", "na", "none", "not-git"}:
        return "n/a"
    if lowered in {"clean", "dirty"}:
        return lowered
    return None


def normalize_source_freshness_value(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in {"n/a", "na"}:
        return "n/a"
    if lowered in {"current", "needs-refresh", "stale-risk"}:
        return lowered
    return None


def normalize_verification_result_value(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in {"pass", "passed", "ok", "green"}:
        return "pass"
    if lowered in {"fail", "failed", "red"}:
        return "fail"
    if lowered in {"n/a", "na"}:
        return "n/a"
    return None


def split_status_reference_values(value: str) -> list[str]:
    if ";" in value:
        return [part.strip() for part in value.split(";") if part.strip()]
    return [value.strip()] if value.strip() else []


NEXT_ACTION_REFERENCE_VERBS = {
    "open",
    "read",
    "review",
    "inspect",
    "follow",
    "edit",
    "打开",
    "阅读",
    "查看",
    "审阅",
    "检查",
    "编辑",
}

NEXT_ACTION_COMMAND_VERBS = {
    "run",
    "execute",
    "rerun",
    "运行",
    "执行",
    "重跑",
}

DONE_WHEN_RESULT_VERBS = {
    "result",
    "results",
    "status",
    "结果",
    "状态",
}

DONE_WHEN_ARTIFACT_VERBS = {
    "artifact",
    "artifacts",
    "file",
    "document",
    "doc",
    "产物",
    "文件",
    "文档",
}

DONE_WHEN_COMMAND_VERBS = {
    "command",
    "commands",
    "cmd",
    "命令",
}

STANDARD_DONE_WHEN_RESULTS = [
    "SULA CHECK OK",
    "doctor strict passed",
    "sync dry run reviewed",
    "record created",
    "handoff updated",
    "Sula 检查通过",
    "doctor strict 已通过",
    "已审阅 sync dry-run",
    "已创建记录",
    "已更新交接",
]
STANDARD_DONE_WHEN_RESULTS_NORMALIZED = {item.casefold() for item in STANDARD_DONE_WHEN_RESULTS}


def strip_wrapping_code_ticks(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("`") and stripped.endswith("`") and len(stripped) >= 2:
        return stripped[1:-1].strip()
    return stripped


def parse_structured_handoff_steps(value: str) -> tuple[list[tuple[str, str]], list[str]]:
    steps: list[tuple[str, str]] = []
    invalid_steps: list[str] = []
    for raw_step in split_status_reference_values(value):
        match = re.fullmatch(r"(.+?)\s+(`[^`]+`|\[[^\]]+\]\([^)]+\))", raw_step)
        if not match:
            invalid_steps.append(raw_step)
            continue
        verb = match.group(1).strip().casefold()
        target = match.group(2).strip()
        steps.append((verb, target))
    return steps, invalid_steps


def parse_handoff_next_action_steps(value: str) -> tuple[list[tuple[str, str]], list[str]]:
    return parse_structured_handoff_steps(value)


def parse_handoff_done_when_steps(value: str) -> tuple[list[tuple[str, str]], list[str]]:
    return parse_structured_handoff_steps(value)


def validate_status_reference_target(status_path: Path, reference_value: str) -> str | None:
    normalized_reference = normalize_status_reference_value(reference_value)
    if not normalized_reference:
        return f"{status_path}: status reference is empty"
    lowered = normalized_reference.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return None
    reference_path = Path(normalized_reference)
    if not reference_path.is_absolute():
        reference_path = (status_path.parent / reference_path).resolve()
    else:
        reference_path = reference_path.resolve()
    if not reference_path.exists():
        return f"{status_path}: status reference target is missing -> {normalized_reference}"
    return None


def validate_status_handoff_section(
    config: ProjectConfig,
    status_path: Path,
    handoff_text: str,
    *,
    latest_record_path: Path | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    advisories: list[str] = []
    fields = markdown_key_values(handoff_text)

    ready_value = normalize_handoff_ready_value(fields.get("ready", ""))
    if ready_value != "yes":
        errors.append(f"{status_path}: `## Handoff` must declare `ready: yes` before `check` can pass")

    required_fields = [
        "start here",
        "latest record",
        "next action",
        "next owner",
        "next due",
        "done when",
        "blockers",
        "source of truth",
        "source freshness",
        "verification command",
        "verification result",
        "verification date",
        "git branch",
        "git commit",
        "git working tree",
    ]
    fields_allow_na = {"source freshness", "verification result", "git branch", "git commit", "git working tree"}
    for field_name in required_fields:
        value = fields.get(field_name, "").strip()
        if not value:
            errors.append(f"{status_path}: `## Handoff` is missing `- {field_name}: ...`")
            continue
        if field_name == "blockers":
            if contains_status_placeholder(value):
                errors.append(f"{status_path}: `## Handoff` field `{field_name}` still contains placeholder text")
            continue
        if field_name in fields_allow_na and value.strip().lower() in {"n/a", "na"}:
            continue
        if line_is_empty_placeholder(value) or contains_status_placeholder(value):
            errors.append(f"{status_path}: `## Handoff` field `{field_name}` still contains placeholder text")

    latest_record_value = fields.get("latest record", "").strip()
    if latest_record_value:
        normalized_reference = normalize_status_reference_value(latest_record_value)
        if normalized_reference:
            reference_path = Path(normalized_reference)
            if not reference_path.is_absolute():
                reference_path = (status_path.parent / reference_path).resolve()
            else:
                reference_path = reference_path.resolve()
            if not reference_path.exists():
                errors.append(f"{status_path}: `## Handoff` latest record target is missing -> {normalized_reference}")
            elif latest_record_path is not None and reference_path != latest_record_path.resolve():
                errors.append(
                    f"{status_path}: `## Handoff` latest record points to {normalized_reference}, but the latest durable record is {latest_record_path}"
                )
    elif latest_record_path is not None:
        errors.append(f"{status_path}: `## Handoff` must reference the latest durable record {latest_record_path}")
    start_here_value = fields.get("start here", "").strip()
    start_here_references = split_status_reference_values(start_here_value)
    if not start_here_references:
        errors.append(f"{status_path}: `## Handoff` start here must list at least one file or URL reference")
    for reference_value in start_here_references:
        reference_error = validate_status_reference_target(status_path, reference_value)
        if reference_error:
            errors.append(reference_error.replace("status reference", "`## Handoff` start here reference"))
    next_action_value = fields.get("next action", "").strip()
    next_action_steps, invalid_next_action_steps = parse_handoff_next_action_steps(next_action_value)
    if invalid_next_action_steps:
        errors.append(
            f"{status_path}: `## Handoff` next action must use structured steps like `review <path>`; `run <command>`"
        )
    reference_step_count = 0
    command_step_count = 0
    for verb, target in next_action_steps:
        if verb in NEXT_ACTION_REFERENCE_VERBS:
            reference_step_count += 1
            reference_error = validate_status_reference_target(status_path, target)
            if reference_error:
                errors.append(reference_error.replace("status reference", "`## Handoff` next action reference"))
            continue
        if verb in NEXT_ACTION_COMMAND_VERBS:
            command_step_count += 1
            normalized_command = strip_wrapping_code_ticks(target)
            if not normalized_command or contains_status_placeholder(normalized_command):
                errors.append(f"{status_path}: `## Handoff` next action command is empty or still placeholder text")
            continue
        errors.append(f"{status_path}: `## Handoff` next action verb `{verb}` is not allowed")
    if next_action_value and not invalid_next_action_steps:
        if reference_step_count == 0:
            errors.append(f"{status_path}: `## Handoff` next action must include at least one file or URL reference step")
        if command_step_count == 0:
            errors.append(f"{status_path}: `## Handoff` next action must include at least one runnable command step")
    next_due_value = fields.get("next due", "").strip()
    if next_due_value and not MEMORY_DATE_PATTERN.fullmatch(next_due_value):
        errors.append(f"{status_path}: `## Handoff` next due must use YYYY-MM-DD")
    done_when_value = fields.get("done when", "").strip()
    done_when_steps, invalid_done_when_steps = parse_handoff_done_when_steps(done_when_value)
    if invalid_done_when_steps:
        errors.append(
            f"{status_path}: `## Handoff` done when must use structured steps like `result <status>`; `artifact <path>`"
        )
    done_when_result_count = 0
    done_when_artifact_count = 0
    for verb, target in done_when_steps:
        if verb in DONE_WHEN_RESULT_VERBS:
            done_when_result_count += 1
            normalized_result = strip_wrapping_code_ticks(target)
            if not normalized_result or contains_status_placeholder(normalized_result):
                errors.append(f"{status_path}: `## Handoff` done when result is empty or still placeholder text")
            elif normalized_result.casefold() not in STANDARD_DONE_WHEN_RESULTS_NORMALIZED:
                advisories.append(
                    f"{status_path}: `## Handoff` done when result `{normalized_result}` is custom; prefer a standard result such as {', '.join(STANDARD_DONE_WHEN_RESULTS[:5])}"
                )
            continue
        if verb in DONE_WHEN_ARTIFACT_VERBS:
            done_when_artifact_count += 1
            reference_error = validate_status_reference_target(status_path, target)
            if reference_error:
                errors.append(reference_error.replace("status reference", "`## Handoff` done when artifact"))
            continue
        if verb in DONE_WHEN_COMMAND_VERBS:
            normalized_command = strip_wrapping_code_ticks(target)
            if not normalized_command or contains_status_placeholder(normalized_command):
                errors.append(f"{status_path}: `## Handoff` done when command is empty or still placeholder text")
            continue
        errors.append(f"{status_path}: `## Handoff` done when verb `{verb}` is not allowed")
    if done_when_value and not invalid_done_when_steps and (done_when_result_count + done_when_artifact_count) == 0:
        errors.append(f"{status_path}: `## Handoff` done when must include at least one result or artifact step")
    source_of_truth_value = fields.get("source of truth", "").strip()
    for reference_value in split_status_reference_values(source_of_truth_value):
        reference_error = validate_status_reference_target(status_path, reference_value)
        if reference_error:
            errors.append(reference_error)
    source_freshness_value = normalize_source_freshness_value(fields.get("source freshness", ""))
    actual_source_freshness = current_truth_source_freshness_status(config)
    if source_freshness_value is None:
        errors.append(f"{status_path}: `## Handoff` has invalid `source freshness` value")
    elif source_freshness_value != actual_source_freshness:
        errors.append(
            f"{status_path}: `## Handoff` source freshness is {source_freshness_value}, but the current truth-source freshness is {actual_source_freshness}"
        )
    verification_date = fields.get("verification date", "").strip()
    if verification_date and not MEMORY_DATE_PATTERN.fullmatch(verification_date):
        errors.append(f"{status_path}: `## Handoff` verification date must use YYYY-MM-DD")
    verification_result = normalize_verification_result_value(fields.get("verification result", ""))
    if verification_result is None:
        errors.append(f"{status_path}: `## Handoff` has invalid `verification result` value")
    git_branch_value = fields.get("git branch", "").strip()
    git_commit_value = fields.get("git commit", "").strip()
    git_worktree_value = normalize_git_worktree_value(fields.get("git working tree", ""))
    actual_git_branch = detect_git_branch(config.root) if is_git_repository(config.root) else "n/a"
    actual_git_commit = detect_git_commit(config.root)
    actual_git_worktree = detect_git_worktree_state(config.root)
    if git_branch_value != actual_git_branch:
        errors.append(f"{status_path}: `## Handoff` git branch is {git_branch_value}, but the repo is on {actual_git_branch}")
    if not (
        git_commit_value == actual_git_commit
        or (actual_git_commit not in {"n/a", "no-commits"} and actual_git_commit.startswith(git_commit_value))
        or (git_commit_value not in {"n/a", "no-commits"} and git_commit_value.startswith(actual_git_commit))
        or git_commit_value == "any"
    ):
        errors.append(f"{status_path}: `## Handoff` git commit is {git_commit_value}, but the repo head is {actual_git_commit}")
    if git_worktree_value is None:
        errors.append(f"{status_path}: `## Handoff` has invalid `git working tree` value")
    elif git_worktree_value != actual_git_worktree:
        errors.append(f"{status_path}: `## Handoff` git working tree is {git_worktree_value}, but the repo is {actual_git_worktree}")
    if ready_value == "yes":
        blockers_value = fields.get("blockers", "").strip()
        if not line_is_empty_placeholder(blockers_value):
            errors.append(f"{status_path}: `## Handoff` cannot declare `ready: yes` while blockers are still present")
        if verification_result not in {"pass", "n/a"}:
            errors.append(f"{status_path}: `## Handoff` cannot declare `ready: yes` while verification result is not pass")
    return errors, advisories


def validate_status_file(
    status_path: Path,
    config: ProjectConfig,
    *,
    latest_record_date: str | None = None,
    latest_record_path: Path | None = None,
) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    advisories: list[str] = []
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
            if latest_record_date and raw_date < latest_record_date:
                latest_record_reference = str(latest_record_path) if latest_record_path is not None else latest_record_date
                errors.append(
                    f"{status_path}: last updated date {raw_date} is older than the latest durable record {latest_record_date} in {latest_record_reference}"
                )
            age_days = (date.today() - datetime.strptime(raw_date, "%Y-%m-%d").date()).days
            if age_days > config.status_max_age_days:
                warnings.append(
                    f"{status_path}: status is {age_days} days old, over the {config.status_max_age_days}-day freshness target"
                )
    current_focus = markdown_bullet_items(sections.get("Current Focus", ""))
    if config.status_current_focus_limit > 0 and len(current_focus) > config.status_current_focus_limit:
        errors.append(
            f"{status_path}: `## Current Focus` has {len(current_focus)} items, over the {config.status_current_focus_limit}-item current-state limit"
        )
    blockers = markdown_bullet_items(sections.get("Blockers", ""))
    if config.status_blocker_limit > 0 and len(blockers) > config.status_blocker_limit:
        errors.append(
            f"{status_path}: `## Blockers` has {len(blockers)} items, over the {config.status_blocker_limit}-item current-state limit"
        )
    recent_decisions = markdown_bullet_items(sections.get("Recent Decisions", ""))
    if config.status_recent_decision_limit > 0 and len(recent_decisions) > config.status_recent_decision_limit:
        errors.append(
            f"{status_path}: `## Recent Decisions` has {len(recent_decisions)} items, over the {config.status_recent_decision_limit}-item current-state limit"
        )

    for placeholder in STATUS_PLACEHOLDERS:
        if placeholder in text:
            warnings.append(f"{status_path}: placeholder content still present ({placeholder})")
            break

    if "Summary" in sections and is_git_repository(config.root):
        summary_body = sections["Summary"]
        most_recent_summary_date = ""
        for raw_line in summary_body.splitlines():
            line = raw_line.strip()
            if line.startswith("### "):
                candidate = line[4:].strip()
                if MEMORY_DATE_PATTERN.fullmatch(candidate) and candidate > most_recent_summary_date:
                    most_recent_summary_date = candidate
        last_commit_date = latest_git_commit_date(config.root)
        if most_recent_summary_date and last_commit_date and last_commit_date > most_recent_summary_date:
            errors.append(
                f"{status_path}: most recent Summary date group ({most_recent_summary_date}) is older than last git commit ({last_commit_date}). Run `sula report --summary \"...\"` to update."
            )

    if "Handoff" in sections:
        handoff_errors, handoff_advisories = validate_status_handoff_section(
            config,
            status_path,
            sections["Handoff"],
            latest_record_path=latest_record_path,
        )
        errors.extend(handoff_errors)
        advisories.extend(handoff_advisories)
    return errors, warnings, advisories


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
    required_sections: list[str],
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
        sections = markdown_sections(text)
        if not extract_markdown_title(text):
            errors.append(f"{path}: missing top-level title")
        for section_name in required_sections:
            if section_name not in sections:
                errors.append(f"{path}: missing required section `## {section_name}`")
        if "YYYY-MM-DD" in text or "_fill in" in text or "_补充" in text or "TBD" in text:
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
    (kernel_root / "state" / "session").mkdir(parents=True, exist_ok=True)
    (kernel_root / "state" / "jobs").mkdir(parents=True, exist_ok=True)
    ensure_session_capture_store(config)
    ensure_memory_jobs_store(config)

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
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
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
        f'content_locale = "{config.content_locale}"\n'
        f'interaction_locale = "{config.interaction_locale}"\n'
        f"adapters = [{adapters}]\n"
        f"git_enabled = {git_enabled}\n"
        'adapter_catalog = ".sula/adapters/catalog.json"\n'
        'bundle_catalog = ".sula/adapters/bundles.json"\n'
        'artifact_catalog = ".sula/artifacts/catalog.json"\n'
        'object_catalog = ".sula/objects/catalog.json"\n'
        'state_snapshot = ".sula/state/current.md"\n'
        'source_registry = ".sula/sources/registry.json"\n'
        'event_log = ".sula/events/log.jsonl"\n'
        'session_captures = ".sula/state/session/captures.jsonl"\n'
        'memory_jobs = ".sula/state/jobs/history.jsonl"\n'
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
            item["workspace_root"] = str(config.storage_setting("workspace_root", "."))
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
        ("session-promotions", "operating-memory", config.memory_setting("promotion_file", "docs/ops/session-promotions.md")),
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
    seen_ids: set[str] = set()
    for path in iter_discoverable_files(config.root):
        relative_path = path.relative_to(config.root).as_posix()
        entries.append(
            {
                "id": stable_source_registry_id(relative_path, seen_ids),
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


def normalize_safe_id_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def unicode_safe_slug(value: str) -> str:
    characters: list[str] = []
    pending_separator = False
    for char in value:
        if char.isalnum():
            characters.append(char)
            pending_separator = False
            continue
        if characters and not pending_separator:
            characters.append("-")
            pending_separator = True
    return "".join(characters).strip("-")


def sanitize_source_id(relative_path: str) -> str:
    normalized = normalize_safe_id_text(relative_path)
    if not normalized:
        return "root"
    if normalized.isascii():
        sanitized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
        return sanitized or "root"
    sanitized = unicode_safe_slug(normalized)
    if sanitized:
        return sanitized
    return f"item-{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:10]}"


def stable_source_registry_id(relative_path: str, seen_ids: set[str]) -> str:
    base_id = f"source:{sanitize_source_id(relative_path)}"
    if base_id not in seen_ids:
        seen_ids.add(base_id)
        return base_id
    digest = hashlib.sha1(normalize_safe_id_text(relative_path).encode("utf-8")).hexdigest()[:10]
    candidate = f"{base_id}-{digest}"
    suffix = 2
    while candidate in seen_ids:
        candidate = f"{base_id}-{digest}-{suffix}"
        suffix += 1
    seen_ids.add(candidate)
    return candidate


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
            "title": "当前项目状态" if locale_family(config.content_locale) == "zh" else "Current Project State",
            "summary": status_sections.get("Summary", localized_string("_missing_", config.content_locale)),
            "status": "current",
            "path": config.data["paths"]["status_file"],
            "source_paths": [config.data["paths"]["status_file"]],
            "adapters": ["generic-project", "memory"],
            "tags": ["state"],
            "date": status_updated,
        }
    )
    objects.append(
        {
            "id": "rule:manifest:highest-rule",
            "kind": "rule",
            "title": "Highest Rule",
            "summary": str(config.data["rules"]["highest_rule"]),
            "status": "active",
            "path": MANIFEST_PATH.as_posix(),
            "source_paths": [MANIFEST_PATH.as_posix()],
            "adapters": ["generic-project", "memory"],
            "tags": ["rule", "manifest"],
            "date": status_updated,
        }
    )
    objects.extend(build_status_objects(config, status_sections, status_updated))
    objects.extend(build_record_objects(config.root, config.change_record_directory, "change", ["generic-project", "memory"]))
    objects.extend(build_record_objects(config.root, config.release_record_directory, "release", ["generic-project", "memory"]))
    objects.extend(build_record_objects(config.root, config.incident_record_directory, "incident", ["generic-project", "memory"]))
    objects.extend(build_artifact_objects(config))
    objects.extend(build_session_capture_objects(config))
    objects.extend(build_memory_job_objects(config))
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
        source_adapters = source.get("adapters", ["generic-project"])
        objects.extend(build_discovered_source_objects(source_path, str(source["path"]), source_adapters))
        if bool(config.memory_setting("rule_registry", True)):
            objects.extend(build_rule_objects(str(source["path"]), source_path, source_adapters))
    return dedupe_objects(objects)


def build_artifact_objects(config: ProjectConfig) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    catalog = load_artifact_catalog(config)
    for artifact in catalog.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        source_paths = artifact_local_access_paths(config, artifact)
        display_path = artifact_display_path(artifact)
        truth_summary = artifact_truth_summary(config, artifact, catalog=catalog)
        objects.append(
            {
                "id": str(artifact.get("id", "")),
                "kind": str(artifact.get("kind", "artifact")),
                "title": str(artifact.get("title", Path(display_path).name if display_path else "artifact")),
                "summary": str(artifact.get("summary", "")),
                "status": str(artifact.get("status", "registered")),
                "path": display_path,
                "source_paths": source_paths,
                "adapters": dedupe_preserve_order(
                    [config.storage_provider, "generic-project", "docs"] + ([config.storage_provider] if config.storage_provider else [])
                ),
                "tags": artifact_search_tags(artifact),
                "date": normalize_optional_text(artifact.get("date", "")),
                "identity_key": artifact_entry_identity_key(artifact),
                "project_relative_path": normalize_optional_text(artifact.get("project_relative_path", "")),
                "provider_item_id": normalize_optional_text(artifact.get("provider_item_id", "")),
                "provider_item_kind": normalize_optional_text(artifact.get("provider_item_kind", "")),
                "provider_item_url": normalize_optional_text(artifact.get("provider_item_url", "")),
                "family_key": truth_summary["family_key"],
                "artifact_role": normalize_artifact_role(artifact.get("artifact_role", ""), default="workspace-source"),
                "source_of_truth": truth_summary["source_of_truth"],
                "truth_source_type": truth_summary["truth_source_type"],
                "truth_source_artifact_id": truth_summary["truth_source_artifact_id"],
                "truth_source_path": truth_summary["truth_source_path"],
                "provider_target_path": truth_summary["provider_target_path"],
                "provider_parent_relative_path": truth_summary["provider_parent_relative_path"],
                "collaboration_mode": truth_summary["collaboration_mode"],
                "last_refreshed_at": truth_summary["last_refreshed_at"],
                "last_provider_sync_at": truth_summary["last_provider_sync_at"],
                "local_copy_stale_risk": truth_summary["local_copy_stale_risk"],
                "freshness_status": truth_summary["freshness_status"],
                "missing_provider_metadata": truth_summary["missing_provider_metadata"],
                "family_roles": truth_summary["family_roles"],
                "minimal_register_action": truth_summary["minimal_register_action"],
                "provider_revision_id": truth_summary["provider_revision_id"],
                "provider_modified_at": truth_summary["provider_modified_at"],
                "provider_last_checked_at": truth_summary["provider_last_checked_at"],
                "provider_last_fetch_status": truth_summary["provider_last_fetch_status"],
                "provider_last_fetch_error": truth_summary["provider_last_fetch_error"],
                "provider_snapshot_path": truth_summary["provider_snapshot_path"],
                "truth_source_reason": truth_summary["truth_source_reason"],
            }
        )
    return objects


def build_session_capture_objects(config: ProjectConfig) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    relative_path = config.session_capture_store.relative_to(config.root).as_posix()
    for item in read_session_captures(config):
        capture_id = str(item.get("id", "")).strip()
        if not capture_id:
            continue
        status = normalize_optional_text(item.get("status", "staged")) or "staged"
        source_paths = [relative_path]
        source_path = normalize_optional_text(item.get("source_path", "")).strip()
        if source_path:
            source_paths.append(source_path)
        objects.append(
            {
                "id": capture_id,
                "kind": "session_capture",
                "title": normalize_optional_text(item.get("title", "")) or capture_id,
                "summary": normalize_optional_text(item.get("summary", "")),
                "status": status,
                "path": relative_path,
                "source_paths": dedupe_preserve_order(source_paths),
                "adapters": ["generic-project", "memory"],
                "tags": ["session-capture", normalize_optional_text(item.get("category", "note")) or "note"],
                "date": normalize_optional_text(item.get("captured_at", ""))[:10],
                "category": normalize_optional_text(item.get("category", "note")),
            }
        )
        if status == "promoted" and normalize_optional_text(item.get("promoted_to", "")):
            promotion_path = normalize_optional_text(item.get("promotion_path", "")).strip() or config.promotion_file.relative_to(config.root).as_posix()
            objects.append(
                {
                    "id": f"promotion:{capture_id}",
                    "kind": "promotion",
                    "title": f"Promotion of {normalize_optional_text(item.get('title', capture_id))}",
                    "summary": normalize_optional_text(item.get("promotion_summary", "")) or normalize_optional_text(item.get("summary", "")),
                    "status": "recorded",
                    "path": promotion_path,
                    "source_paths": [promotion_path, relative_path],
                    "adapters": ["generic-project", "memory", "docs"],
                    "tags": ["promotion", normalize_optional_text(item.get("promoted_to", ""))],
                    "date": normalize_optional_text(item.get("updated_at", ""))[:10],
                }
            )
    return objects


def build_memory_job_objects(config: ProjectConfig) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    relative_path = config.memory_jobs_history_path.relative_to(config.root).as_posix()
    for item in read_memory_jobs(config):
        job_id = normalize_optional_text(item.get("id", ""))
        if not job_id:
            continue
        objects.append(
            {
                "id": job_id,
                "kind": "job",
                "title": normalize_optional_text(item.get("job_type", "memory-job")),
                "summary": normalize_optional_text(item.get("summary", "")),
                "status": normalize_optional_text(item.get("status", "")) or "recorded",
                "path": relative_path,
                "source_paths": [relative_path],
                "adapters": ["generic-project", "memory"],
                "tags": ["job", "memory-job"],
                "date": normalize_optional_text(item.get("started_at", ""))[:10],
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
                    "summary": first_readme_paragraph(text) or ("记录的发布里程碑。" if contains_cjk(text) else "Recorded release milestone."),
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
                    "summary": first_readme_paragraph(text) or ("记录的事故与后续风险。" if contains_cjk(text) else "Recorded incident and follow-up risk."),
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
                "summary": (
                    f"{config.data['project']['name']} 的当前复盘负责人。"
                    if locale_family(config.content_locale) == "zh"
                    else f"Current review owner for {config.data['project']['name']}."
                ),
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
                "title": "下次复盘" if locale_family(config.content_locale) == "zh" else "Next Review",
                "summary": (
                    milestone_summary or ("下次复盘检查点。" if locale_family(config.content_locale) == "zh" else "Next review checkpoint.")
                ),
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
                "title": f"项目健康状态为 {health_status}" if locale_family(config.content_locale) == "zh" else f"Project health is {health_status}",
                "summary": health_reason or (f"健康状态被记录为 {health_status}。" if locale_family(config.content_locale) == "zh" else f"Health status reported as {health_status}."),
                "status": "watch",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["health", "status"],
                "date": status_updated,
            }
        )
    handoff_fields = markdown_key_values(status_sections.get("Handoff", ""))
    next_action = handoff_fields.get("next action", "")
    if next_action and not contains_status_placeholder(next_action):
        objects.append(
            {
                "id": f"task:handoff:{sanitize_source_id(next_action)}",
                "kind": "task",
                "title": truncate_title(next_action),
                "summary": next_action,
                "status": "open",
                "path": status_path,
                "source_paths": [status_path],
                "adapters": adapters,
                "tags": ["handoff", "next-action", "status"],
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


def build_rule_objects(relative_path: str, source_path: Path, adapters: list[str]) -> list[dict[str, object]]:
    if not source_path.exists() or source_path.is_dir():
        return []
    if source_path.suffix.lower() not in {".md", ".txt", ".rst"}:
        return []
    text = source_path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return []
    default_date = detect_source_date(source_path, text)
    sections = markdown_sections(text)
    rule_section_names = [
        "Highest Rule",
        "Working Rules",
        "Rules",
        "Maintenance Rule",
        "Maintenance Rules",
        "Design Rules",
        "Publication Hygiene",
    ]
    objects: list[dict[str, object]] = []
    for section_name in rule_section_names:
        section_text = sections.get(section_name, "")
        if not section_text.strip():
            continue
        bullet_items = markdown_bullet_items(section_text)
        if bullet_items:
            for item in bullet_items:
                objects.append(
                    {
                        "id": f"rule:{sanitize_source_id(relative_path)}:{sanitize_source_id(section_name)}:{sanitize_source_id(item)}",
                        "kind": "rule",
                        "title": truncate_title(item),
                        "summary": item,
                        "status": "active",
                        "path": relative_path,
                        "source_paths": [relative_path],
                        "adapters": dedupe_preserve_order(adapters + ["memory"]),
                        "tags": ["rule", "section-rule", sanitize_slug(section_name)],
                        "date": extract_inline_date(item) or default_date,
                    }
                )
            continue
        paragraph = first_readme_paragraph(section_text)
        if not paragraph:
            continue
        objects.append(
            {
                "id": f"rule:{sanitize_source_id(relative_path)}:{sanitize_source_id(section_name)}",
                "kind": "rule",
                "title": section_name,
                "summary": paragraph,
                "status": "active",
                "path": relative_path,
                "source_paths": [relative_path],
                "adapters": dedupe_preserve_order(adapters + ["memory"]),
                "tags": ["rule", "section-rule", sanitize_slug(section_name)],
                "date": default_date,
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
        "Rules": ("rule", "active", ["rule"]),
        "State Updates": ("state", "active", ["state", "promotion-section"]),
        "Workflow Artifacts": ("document", "active", ["workflow-artifact", "promotion-section"]),
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
        fields[canonical_field_name(key)] = value.strip()
    return fields


def line_is_empty_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in {"none", "n/a", "none.", "_none_", "_missing_", "无", "_缺失_"}


def truncate_title(value: str, limit: int = 80) -> str:
    collapsed = re.sub(r"\s+", " ", value).strip()
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 3].rstrip() + "..."


def looks_like_agreement(relative_path: str, title: str, text: str) -> bool:
    haystack = " ".join([relative_path.lower(), title.lower(), text[:500].lower()])
    return any(term in haystack for term in ["contract", "agreement", "msa", "statement of work", "sow", "合同", "协议"])


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
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        "# 当前状态快照" if zh else "# Current State Snapshot",
        "",
        f"- {localized_field_label('generated on', config.content_locale)}: {date.today().isoformat()}",
        f"- {localized_field_label('project', config.content_locale)}: {config.data['project']['name']}",
        f"- {localized_field_label('profile', config.content_locale)}: `{config.profile}`",
        "- 真相优先级: STATUS.md 与项目记录高于这份生成快照" if zh else "- source priority: STATUS.md and project records override this generated snapshot",
        "",
    ]
    for section_name in ["Summary", "Health", "Current Focus", "Blockers", "Recent Decisions", "Next Review", "Handoff"]:
        lines.append(f"## {localized_section_name(section_name, config.content_locale)}")
        lines.append("")
        lines.append((status_sections.get(section_name, localized_string("_missing_", config.content_locale)) or localized_string("_missing_", config.content_locale)).strip())
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
                "family_key": normalize_optional_text(item.get("family_key", "")),
                "artifact_role": normalize_optional_text(item.get("artifact_role", "")),
                "source_of_truth": normalize_optional_text(item.get("source_of_truth", "")),
                "truth_source_type": normalize_optional_text(item.get("truth_source_type", "")),
                "truth_source_artifact_id": normalize_optional_text(item.get("truth_source_artifact_id", "")),
                "truth_source_path": normalize_optional_text(item.get("truth_source_path", "")),
                "provider_target_path": normalize_optional_text(item.get("provider_target_path", "")),
                "provider_parent_relative_path": normalize_optional_text(item.get("provider_parent_relative_path", "")),
                "collaboration_mode": normalize_optional_text(item.get("collaboration_mode", "")),
                "last_refreshed_at": normalize_optional_text(item.get("last_refreshed_at", "")),
                "last_provider_sync_at": normalize_optional_text(item.get("last_provider_sync_at", "")),
                "local_copy_stale_risk": bool(item.get("local_copy_stale_risk")),
                "freshness_status": normalize_optional_text(item.get("freshness_status", "")),
                "missing_provider_metadata": item.get("missing_provider_metadata", []) if isinstance(item.get("missing_provider_metadata", []), list) else [],
                "minimal_register_action": normalize_optional_text(item.get("minimal_register_action", "")),
                "provider_revision_id": normalize_optional_text(item.get("provider_revision_id", "")),
                "provider_modified_at": normalize_optional_text(item.get("provider_modified_at", "")),
                "provider_last_checked_at": normalize_optional_text(item.get("provider_last_checked_at", "")),
                "provider_last_fetch_status": normalize_optional_text(item.get("provider_last_fetch_status", "")),
                "provider_last_fetch_error": normalize_optional_text(item.get("provider_last_fetch_error", "")),
                "provider_snapshot_path": normalize_optional_text(item.get("provider_snapshot_path", "")),
                "truth_source_reason": normalize_optional_text(item.get("truth_source_reason", "")),
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
    freshness_intent = detect_freshness_intent(args.q)
    effective_query = strip_freshness_intent_phrases(args.q) if freshness_intent else args.q
    route = determine_query_route(
        effective_query,
        kind=args.kind,
        timeline=args.timeline,
        freshness_intent=freshness_intent,
        routing_policy=normalize_optional_text(config.memory_setting("query_routing", "deterministic")),
    )
    refresh_report = None
    if freshness_intent:
        refresh_report = refresh_provider_artifact_batch(
            config,
            query=effective_query,
            all_collaborative=False,
            limit=max(args.limit, 5),
            force=True,
            event_type="artifact.refresh.intent",
            event_summary_prefix="Refreshed provider-native truth sources before query",
        )
    results = search_kernel(
        config,
        effective_query,
        kind=args.kind,
        adapter=args.adapter,
        status=args.status,
        path_prefix=args.path_prefix,
        since=args.since,
        until=args.until,
        timeline=args.timeline,
        limit=args.limit,
        freshness_intent=freshness_intent,
        route=route,
    )
    automation_result = automation_observe_event(
        config,
        source_kind="sula-cli",
        event_kind="query.freshness" if freshness_intent else "query.performed",
        title="Sula query",
        summary=f"Sula query returned {len(results)} result(s).",
        identity_key=f"query:{date.today().isoformat()}:{sanitize_slug(effective_query or 'empty')}",
        payload={"query": args.q, "effective_query": effective_query, "freshness_intent": freshness_intent, "refresh": refresh_report or {}},
    )
    if args.json:
        print(
            json.dumps(
                {
                    "query": args.q,
                    "effective_query": effective_query,
                    "route": route,
                    "freshness_intent_detected": freshness_intent,
                    "refresh": refresh_report,
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
    zh = locale_family(config.interaction_locale) == "zh"
    print_sula_activity_feedback(config, automation_result)
    print(f"{config.data['project']['name']} 的 Sula 查询结果: {args.q}" if zh else f"Sula query results for {config.data['project']['name']}: {args.q}")
    if not results:
        print("  没有结果。" if zh else "  No results.")
        return 0
    print(f"  路由: {route}" if zh else f"  Route: {route}")
    for result in results:
        date_prefix = f"{result['date']} " if result.get("date") else ""
        status_suffix = f" status={result['status']}" if result.get("status") else ""
        related_suffix = ""
        if result.get("related_kinds"):
            related_suffix = " related=" + ",".join(str(kind_name) for kind_name in result["related_kinds"])
        truth_suffix = f" truth={result['truth_source_type']}" if result.get("truth_source_type") else ""
        refresh_suffix = f" refreshed={result['last_refreshed_at']}" if result.get("last_refreshed_at") else ""
        stale_suffix = " local-copy-risk=true" if result.get("local_copy_stale_risk") else ""
        provider_path_suffix = f" provider-path={result['provider_target_path']}" if result.get("provider_target_path") else ""
        missing_suffix = ""
        if result.get("missing_provider_metadata"):
            missing_suffix = " missing=" + ",".join(str(value) for value in result["missing_provider_metadata"])
        route_suffix = f" route={result['route']}" if result.get("route") else ""
        print(
            "  - "
            f"{date_prefix}[{result['kind']}] score={result['score']}{status_suffix}{related_suffix}{truth_suffix}{refresh_suffix}{stale_suffix}{provider_path_suffix}{missing_suffix}{route_suffix} "
            f"{result['title']} :: {result['path']}"
        )
    return 0


def determine_query_route(
    query: str,
    *,
    kind: str | None,
    timeline: bool,
    freshness_intent: bool,
    routing_policy: str,
) -> str:
    if routing_policy == "literal":
        return "literal"
    if kind:
        return "kind"
    if freshness_intent:
        return "freshness"
    if timeline:
        return "timeline"
    token_set = set(tokenize_text(query))
    if token_set & {"rule", "rules", "policy", "policies", "constraint", "constraints", "governance", "guideline", "guidelines"}:
        return "rules"
    if token_set & {"status", "state", "health", "summary", "current", "progress"}:
        return "state"
    if token_set & {"change", "changes", "release", "incident", "history", "why", "decision"}:
        return "record"
    if token_set & {"task", "todo", "next", "deliver", "milestone", "plan", "workflow", "review", "spec"}:
        return "execution"
    return "general"


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
    freshness_intent: bool = False,
    route: str = "general",
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
    if sqlite_cache_path.exists() and not freshness_intent:
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
            freshness_intent=freshness_intent,
            route=route,
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
            allow_empty=timeline or freshness_intent,
            freshness_intent=freshness_intent,
            route=route,
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
            allow_empty=timeline or freshness_intent,
            freshness_intent=freshness_intent,
            route=route,
        )
        if result is not None:
            candidates.append(result)
    if freshness_intent:
        candidates = [item for item in candidates if candidate_is_freshness_relevant(item)]
    return finalize_query_results(
        candidates,
        timeline=timeline,
        limit=limit,
        explicit_kind=kind,
        normalized_query=normalized_query,
        query_tokens=query_tokens,
        route=route,
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
    freshness_intent: bool = False,
    route: str = "general",
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
    truth_source_type = normalize_optional_text(item.get("truth_source_type", ""))
    collaboration_mode = normalize_optional_text(item.get("collaboration_mode", ""))
    freshness_status = normalize_optional_text(item.get("freshness_status", ""))
    last_refreshed_at = normalize_optional_timestamp(item.get("last_refreshed_at", ""))
    last_provider_sync_at = normalize_optional_timestamp(item.get("last_provider_sync_at", ""))
    provider_revision_id = normalize_optional_text(item.get("provider_revision_id", ""))
    provider_modified_at = normalize_optional_text(item.get("provider_modified_at", ""))
    provider_last_checked_at = normalize_optional_text(item.get("provider_last_checked_at", ""))
    provider_last_fetch_status = normalize_optional_text(item.get("provider_last_fetch_status", ""))
    provider_last_fetch_error = normalize_optional_text(item.get("provider_last_fetch_error", ""))
    provider_snapshot_path = normalize_optional_text(item.get("provider_snapshot_path", ""))
    truth_source_reason = normalize_optional_text(item.get("truth_source_reason", ""))
    provider_target_path = normalize_optional_text(item.get("provider_target_path", ""))
    provider_parent_path = normalize_optional_text(item.get("provider_parent_relative_path", ""))
    missing_provider_metadata = item.get("missing_provider_metadata", [])
    local_copy_stale_risk = bool(item.get("local_copy_stale_risk"))
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
        [
            str(item.get("id", "")),
            candidate_kind,
            title,
            summary,
            path,
            provider_target_path,
            provider_parent_path,
            " ".join(tags),
            " ".join(adapters),
            candidate_status,
        ]
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
    if freshness_intent:
        if collaboration_mode == "multi-editor":
            score += 18
        if truth_source_type == "provider-native":
            score += 24
        if local_copy_stale_risk:
            score += 28
        if freshness_status == "provider-metadata-missing":
            score += 32
    score += route_score_bonus(route, candidate_kind)
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
        "family_key": normalize_optional_text(item.get("family_key", "")),
        "artifact_role": normalize_optional_text(item.get("artifact_role", "")),
        "source_of_truth": normalize_optional_text(item.get("source_of_truth", "")),
        "truth_source_type": truth_source_type,
        "truth_source_artifact_id": normalize_optional_text(item.get("truth_source_artifact_id", "")),
        "truth_source_path": normalize_optional_text(item.get("truth_source_path", "")),
        "provider_target_path": provider_target_path,
        "provider_parent_relative_path": provider_parent_path,
        "collaboration_mode": collaboration_mode,
        "last_refreshed_at": last_refreshed_at,
        "last_provider_sync_at": last_provider_sync_at,
        "local_copy_stale_risk": local_copy_stale_risk,
        "freshness_status": freshness_status,
        "missing_provider_metadata": missing_provider_metadata if isinstance(missing_provider_metadata, list) else [],
        "minimal_register_action": normalize_optional_text(item.get("minimal_register_action", "")),
        "provider_revision_id": provider_revision_id,
        "provider_modified_at": provider_modified_at,
        "provider_last_checked_at": provider_last_checked_at,
        "provider_last_fetch_status": provider_last_fetch_status,
        "provider_last_fetch_error": provider_last_fetch_error,
        "provider_snapshot_path": provider_snapshot_path,
        "truth_source_reason": truth_source_reason,
        "route": route,
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
    route: str,
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
        route=route,
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


def candidate_is_freshness_relevant(item: dict[str, object]) -> bool:
    return bool(
        normalize_optional_text(item.get("truth_source_type", "")) == "provider-native"
        or normalize_optional_text(item.get("collaboration_mode", "")) == "multi-editor"
        or normalize_optional_text(item.get("source_of_truth", "")) == "provider-native"
        or bool(item.get("missing_provider_metadata"))
    )


def compact_query_result_families(
    candidates: list[dict[str, object]],
    *,
    timeline: bool,
    limit: int,
    normalized_query: str,
    query_tokens: list[str],
    route: str,
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
        group_key = normalize_optional_text(item.get("family_key", "")) or path
        grouped.setdefault(group_key, []).append(item)

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
    finalized = combined[: max(1, limit)]
    for item in finalized:
        item.setdefault("route", route)
    return finalized


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


def route_score_bonus(route: str, kind: str) -> int:
    family = kind_family(kind)
    route_family_bonus = {
        "rules": {"governance": 18},
        "state": {"state": 18},
        "record": {"record": 18, "governance": 6},
        "execution": {"execution": 18},
        "freshness": {"source": 8, "record": 4, "state": 4},
        "timeline": {"record": 8, "event": 8},
    }
    return route_family_bonus.get(route, {}).get(family, 0)


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
        "session_capture": "state",
        "job": "state",
        "task": "execution",
        "milestone": "execution",
        "decision": "governance",
        "risk": "governance",
        "rule": "governance",
        "promotion": "governance",
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
        "session_capture": 6,
        "job": 5,
        "task": 6,
        "decision": 6,
        "risk": 6,
        "rule": 7,
        "promotion": 5,
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
        "session_capture": 2,
        "job": 3,
        "task": 4,
        "decision": 5,
        "risk": 6,
        "rule": 7,
        "promotion": 8,
        "agreement": 9,
        "milestone": 10,
        "person": 11,
        "change": 12,
        "release": 13,
        "incident": 14,
        "event": 15,
        "document": 16,
        "code": 17,
        "config": 18,
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
                family_key TEXT,
                artifact_role TEXT,
                source_of_truth TEXT,
                truth_source_type TEXT,
                truth_source_artifact_id TEXT,
                truth_source_path TEXT,
                provider_target_path TEXT,
                provider_parent_relative_path TEXT,
                collaboration_mode TEXT,
                last_refreshed_at TEXT,
                last_provider_sync_at TEXT,
                stale_local_copy_risk INTEGER NOT NULL,
                freshness_status TEXT,
                missing_provider_metadata_json TEXT,
                minimal_register_action TEXT,
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
                    doc_id, entity_type, kind, title, summary, path, status, date_value, tags_text, adapters_text,
                    family_key, artifact_role, source_of_truth, truth_source_type, truth_source_artifact_id, truth_source_path,
                    provider_target_path, provider_parent_relative_path,
                    collaboration_mode, last_refreshed_at, last_provider_sync_at, stale_local_copy_risk, freshness_status,
                    missing_provider_metadata_json, minimal_register_action, searchable_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    str(item.get("family_key", "")),
                    str(item.get("artifact_role", "")),
                    str(item.get("source_of_truth", "")),
                    str(item.get("truth_source_type", "")),
                    str(item.get("truth_source_artifact_id", "")),
                    str(item.get("truth_source_path", "")),
                    str(item.get("provider_target_path", "")),
                    str(item.get("provider_parent_relative_path", "")),
                    str(item.get("collaboration_mode", "")),
                    str(item.get("last_refreshed_at", "") or ""),
                    str(item.get("last_provider_sync_at", "") or ""),
                    1 if item.get("local_copy_stale_risk") else 0,
                    str(item.get("freshness_status", "")),
                    json.dumps(item.get("missing_provider_metadata", []), ensure_ascii=True),
                    str(item.get("minimal_register_action", "")),
                    " ".join(
                        [
                            str(item.get("id", "")),
                            str(item.get("kind", "")),
                            str(item.get("title", "")),
                            str(item.get("summary", "")),
                            str(item.get("path", "")),
                            str(item.get("provider_target_path", "")),
                            " ".join(str(tag) for tag in item.get("tags", [])),
                            " ".join(str(adapter) for adapter in item.get("adapters", [])),
                            str(item.get("status", "")),
                            str(item.get("date", "")),
                        ]
                    ).lower(),
                ),
            )
        for index, item in enumerate(events, start=1):
            cursor.execute(
                """
                INSERT INTO documents (
                    doc_id, entity_type, kind, title, summary, path, status, date_value, tags_text, adapters_text,
                    family_key, artifact_role, source_of_truth, truth_source_type, truth_source_artifact_id, truth_source_path,
                    provider_target_path, provider_parent_relative_path,
                    collaboration_mode, last_refreshed_at, last_provider_sync_at, stale_local_copy_risk, freshness_status,
                    missing_provider_metadata_json, minimal_register_action, searchable_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"event:{index}:{item.get('timestamp', '')}:{item.get('event_type', '')}",
                    "event",
                    "event",
                    str(item.get("event_type", "")),
                    str(item.get("summary", "")),
                    ".sula/events/log.jsonl",
                    "recorded",
                    str(item.get("timestamp", "")),
                    "event kernel",
                    "generic-project memory",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    0,
                    "",
                    "[]",
                    "",
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
    freshness_intent: bool = False,
    route: str = "general",
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
        "SELECT doc_id, entity_type, kind, title, summary, path, status, date_value, family_key, artifact_role, source_of_truth, "
        "truth_source_type, truth_source_artifact_id, truth_source_path, provider_target_path, provider_parent_relative_path, "
        "collaboration_mode, last_refreshed_at, last_provider_sync_at, stale_local_copy_risk, freshness_status, "
        "missing_provider_metadata_json, minimal_register_action "
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
                "family_key": row[8],
                "artifact_role": row[9],
                "source_of_truth": row[10],
                "truth_source_type": row[11],
                "truth_source_artifact_id": row[12],
                "truth_source_path": row[13],
                "provider_target_path": row[14],
                "provider_parent_relative_path": row[15],
                "collaboration_mode": row[16],
                "last_refreshed_at": row[17],
                "last_provider_sync_at": row[18],
                "local_copy_stale_risk": bool(row[19]),
                "freshness_status": row[20],
                "missing_provider_metadata": json.loads(row[21] or "[]"),
                "minimal_register_action": row[22],
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
                allow_empty=timeline or freshness_intent,
                freshness_intent=freshness_intent,
                route=route,
            )
            if result is not None:
                results.append(result)
    if freshness_intent:
        results = [item for item in results if candidate_is_freshness_relevant(item)]
    return finalize_query_results(
        results,
        timeline=timeline,
        limit=limit,
        explicit_kind=kind,
        normalized_query=normalized_query,
        query_tokens=query_tokens,
        route=route,
    )


def tokenize_text(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


def normalize_optional_text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_optional_timestamp(value: object) -> str:
    text = normalize_optional_text(value).strip()
    if not text:
        return ""
    if MEMORY_DATE_PATTERN.fullmatch(text):
        return f"{text}T00:00:00Z"
    candidate = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SystemExit(f"Invalid ISO timestamp: {text}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_artifact_role(value: object, *, default: str | None = None) -> str:
    raw = normalize_optional_text(value).strip().lower().replace("_", "-")
    aliases = {
        "workspace": "workspace-source",
        "provider-native": "provider-native-source",
        "derivative": "exported-derivative",
    }
    normalized = aliases.get(raw, raw)
    if not normalized:
        return default or ""
    if normalized not in ARTIFACT_ROLE_CHOICES:
        raise SystemExit(f"Unsupported artifact role: {value}")
    return normalized


def normalize_source_of_truth(value: object, *, default: str = "auto") -> str:
    raw = normalize_optional_text(value).strip().lower().replace("_", "-")
    aliases = {
        "workspace-source": "workspace",
        "provider-native-source": "provider-native",
        "provider": "provider-native",
    }
    normalized = aliases.get(raw, raw)
    if not normalized:
        return default
    if normalized not in SOURCE_OF_TRUTH_CHOICES:
        raise SystemExit(f"Unsupported source_of_truth value: {value}")
    return normalized


def normalize_collaboration_mode(value: object, *, default: str = "single-editor") -> str:
    normalized = normalize_optional_text(value).strip().lower().replace("_", "-")
    if not normalized:
        return default
    if normalized not in COLLABORATION_MODE_CHOICES:
        raise SystemExit(f"Unsupported collaboration_mode value: {value}")
    return normalized


def provider_metadata_is_missing(value: object) -> bool:
    normalized = normalize_optional_text(value).strip().lower()
    return not normalized or normalized in NON_PATH_SENTINELS or normalized == "unrecorded"


def detect_freshness_intent(text: str) -> bool:
    lowered = text.strip().lower()
    return any(phrase in lowered for phrase in FRESHNESS_INTENT_PHRASES)


def strip_freshness_intent_phrases(text: str) -> str:
    cleaned = text
    for phrase in sorted(FRESHNESS_INTENT_PHRASES, key=len, reverse=True):
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def project_status(config: ProjectConfig, args: argparse.Namespace) -> int:
    if getattr(args, "refresh_provider", False):
        refresh_provider_artifact_batch(
            config,
            all_collaborative=True,
            limit=200,
            force=True,
            event_type="artifact.refresh.status",
            event_summary_prefix="Refreshed provider-native truth sources before status summary",
        )
    payload = project_status_payload(config)
    truth_risks = [
        f"{item.get('title', '')}: {item.get('freshness_status', '')}"
        for item in payload["truth_sources"]["artifacts_at_risk"]
        if isinstance(item, dict)
    ]
    automation_result = automation_observe_event(
        config,
        source_kind="sula-cli",
        event_kind="status.truth-risk" if truth_risks else "status.viewed",
        title="Sula status",
        summary="Sula status found truth-source risks." if truth_risks else "Sula status viewed.",
        identity_key="status:" + date.today().isoformat(),
        payload={"risks": truth_risks, "summary": payload.get("summary", "")},
    )
    if json_output_requested(args):
        emit_json({"command": "status", "status": "ok", "project": project_payload(config), "state": payload, "automation": automation_status_payload(config)})
        return 0
    print_sula_activity_feedback(config, automation_result)
    if locale_family(config.interaction_locale) == "zh":
        print(f"{config.data['project']['name']} 的 Sula 状态")
        print(f"  配置档: {config.profile}")
        print(f"  工作流: {config.workflow_pack} ({config.workflow_stage})")
        print(f"  存储: {config.storage_provider} [{config.storage_sync_mode}]")
        print(f"  摘要: {payload['summary']}")
        print(f"  健康状态: {payload['health']}")
        print(f"  开放任务: {payload['counts']['open_tasks']}")
        print(f"  开放风险: {payload['counts']['open_risks']}")
        print(f"  规则对象: {payload['counts']['rules']}")
        print(f"  文件产物: {payload['counts']['artifacts']}")
        print(
            "  记忆: "
            f"staged={payload['memory']['counts']['staged']} "
            f"promoted={payload['memory']['counts']['promoted']} "
            f"routing={payload['memory']['query_routing']}"
        )
        print(
            "  事实源: "
            f"provider-native={payload['truth_sources']['provider_native']} "
            f"workspace={payload['truth_sources']['workspace']} "
            f"risk={payload['truth_sources']['local_copy_risk_count']}"
        )
    else:
        print(f"Sula status for {config.data['project']['name']}")
        print(f"  Profile: {config.profile}")
        print(f"  Workflow: {config.workflow_pack} ({config.workflow_stage})")
        print(f"  Storage: {config.storage_provider} [{config.storage_sync_mode}]")
        print(f"  Summary: {payload['summary']}")
        print(f"  Health: {payload['health']}")
        print(f"  Open tasks: {payload['counts']['open_tasks']}")
        print(f"  Open risks: {payload['counts']['open_risks']}")
        print(f"  Rule objects: {payload['counts']['rules']}")
        print(f"  Artifacts: {payload['counts']['artifacts']}")
        print(
            "  Memory: "
            f"staged={payload['memory']['counts']['staged']} "
            f"promoted={payload['memory']['counts']['promoted']} "
            f"routing={payload['memory']['query_routing']}"
        )
        print(
            "  Truth sources: "
            f"provider-native={payload['truth_sources']['provider_native']} "
            f"workspace={payload['truth_sources']['workspace']} "
            f"risk={payload['truth_sources']['local_copy_risk_count']}"
        )
    if payload["memory"]["recent_promotions"]:
        print("  最近提升:" if locale_family(config.interaction_locale) == "zh" else "  Recent promotions:")
        for item in payload["memory"]["recent_promotions"]:
            print(
                f"    - {item.get('updated_at', item.get('captured_at', ''))} {item.get('promoted_to', '')}: {item.get('title', '')}"
            )
    if payload["memory"]["last_job"]:
        last_job = payload["memory"]["last_job"]
        print(
            ("  最近记忆任务: " if locale_family(config.interaction_locale) == "zh" else "  Last memory job: ")
            + f"{last_job.get('started_at', '')} {last_job.get('job_type', '')} [{last_job.get('status', '')}]"
        )
    if payload["memory"]["last_failed_job"]:
        failed_job = payload["memory"]["last_failed_job"]
        print(
            ("  最近失败记忆任务: " if locale_family(config.interaction_locale) == "zh" else "  Last failed memory job: ")
            + f"{failed_job.get('started_at', '')} {failed_job.get('job_type', '')} :: {failed_job.get('summary', '')}"
        )
    if payload["truth_sources"]["artifacts_at_risk"]:
        print("  事实源风险:" if locale_family(config.interaction_locale) == "zh" else "  Truth-source risks:")
        for item in payload["truth_sources"]["artifacts_at_risk"]:
            missing_suffix = ""
            if item.get("missing_provider_metadata"):
                missing_suffix = " missing=" + ",".join(str(value) for value in item["missing_provider_metadata"])
            provider_path_suffix = f" provider-path={item['provider_target_path']}" if item.get("provider_target_path") else ""
            print(
                f"    - {item['title']} truth={item['truth_source_type']} refreshed={item['last_refreshed_at']}{provider_path_suffix}{missing_suffix}"
            )
    if payload["truth_sources"]["provider_errors"]:
        print("  Provider 刷新错误:" if locale_family(config.interaction_locale) == "zh" else "  Provider refresh errors:")
        for item in payload["truth_sources"]["provider_errors"]:
            print(
                f"    - {item['title']} status={item.get('provider_last_fetch_status', '')} error={item.get('provider_last_fetch_error', '')}"
            )
    if payload["recent_events"]:
        print("  近期事件:" if locale_family(config.interaction_locale) == "zh" else "  Recent events:")
        for item in payload["recent_events"]:
            print(f"    - {item['timestamp']} {item['event_type']}: {item['summary']}")
    orch = orchestration_status_payload(config)
    tasks_info = orch.get("tasks", {})
    runs_info = orch.get("runs", {})
    if tasks_info.get("total", 0) > 0:
        t_label = "编排" if locale_family(config.interaction_locale) == "zh" else "  Orchestration"
        print(f"{t_label}: {tasks_info['total']} tasks, {tasks_info['eligible']} eligible, {tasks_info['blocked']} blocked")
        print(f"    Runs: {runs_info.get('total', 0)} total")
        run_counts = runs_info.get("counts", {})
        if isinstance(run_counts, dict):
            statuses = {k: v for k, v in run_counts.items() if v > 0}
            if statuses:
                print(f"    Run states: {', '.join(f'{k}={v}' for k, v in sorted(statuses.items()))}")
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
    artifact_summaries = []
    for item in artifact_catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        summary = artifact_truth_summary(config, item, catalog=artifact_catalog)
        artifact_summaries.append(
            {
                "id": normalize_optional_text(item.get("id", "")),
                "title": normalize_optional_text(item.get("title", "")),
                "kind": normalize_optional_text(item.get("kind", "")),
                "display_path": artifact_display_path(item),
                **summary,
            }
        )
    recent_events = read_kernel_events(kernel_root / "events" / "log.jsonl")[-5:]
    open_tasks = [item for item in objects if isinstance(item, dict) and item.get("kind") == "task" and item.get("status") in {"open", "planned"}]
    open_risks = [item for item in objects if isinstance(item, dict) and item.get("kind") == "risk" and item.get("status") in {"open", "watch", "incident"}]
    milestones = [item for item in objects if isinstance(item, dict) and item.get("kind") == "milestone"]
    rule_objects = [item for item in objects if isinstance(item, dict) and item.get("kind") == "rule"]
    memory_summary = memory_state_summary(config)
    unique_family_summaries: dict[str, dict[str, object]] = {}
    for item in artifact_summaries:
        family_key = normalize_optional_text(item.get("family_key", "")) or normalize_optional_text(item.get("id", ""))
        if family_key in unique_family_summaries:
            continue
        unique_family_summaries[family_key] = item
    truth_source_rows = list(unique_family_summaries.values())
    provider_native_count = sum(1 for item in truth_source_rows if item.get("truth_source_type") == "provider-native")
    workspace_count = sum(1 for item in truth_source_rows if item.get("truth_source_type") == "workspace")
    derivative_count = sum(1 for item in truth_source_rows if item.get("truth_source_type") == "exported-derivative")
    local_copy_risk = [item for item in truth_source_rows if item.get("local_copy_stale_risk") or item.get("missing_provider_metadata")]
    provider_errors = [
        item
        for item in truth_source_rows
        if normalize_optional_text(item.get("provider_last_fetch_status", ""))
        and normalize_optional_text(item.get("provider_last_fetch_status", "")) != "ok"
    ]
    return {
        "summary": state_sections.get("Summary", "_missing_"),
        "health": state_sections.get("Health", "_missing_"),
        "current_focus": markdown_bullet_items(state_sections.get("Current Focus", "")),
        "blockers": markdown_bullet_items(state_sections.get("Blockers", "")),
        "recent_decisions": markdown_bullet_items(state_sections.get("Recent Decisions", "")),
        "next_review": markdown_key_values(state_sections.get("Next Review", "")),
        "handoff": markdown_key_values(state_sections.get("Handoff", "")),
        "workflow": {
            "pack": config.workflow_pack,
            "stage": config.workflow_stage,
            "artifacts_root": config.artifacts_root.relative_to(config.root).as_posix() if config.artifacts_root.is_relative_to(config.root) else str(config.artifacts_root),
            "docs_root": config.workflow_docs_root.relative_to(config.root).as_posix() if config.workflow_docs_root.is_relative_to(config.root) else str(config.workflow_docs_root),
            "execution_mode": config.workflow_execution_mode,
            "design_gate": config.workflow_design_gate,
            "plan_gate": config.workflow_plan_gate,
            "review_policy": config.workflow_review_policy,
            "workspace_isolation": config.workflow_workspace_isolation,
            "testing_policy": config.workflow_testing_policy,
            "closeout_policy": config.workflow_closeout_policy,
        },
        "automation": automation_status_payload(config),
        "orchestration": orchestration_status_payload(config),
        "agent_behavior": agent_behavior_payload(config),
        "storage": {
            "provider": config.storage_provider,
            "sync_mode": config.storage_sync_mode,
            "workspace_root": str(config.storage_workspace_root),
            "provider_root_url": config.provider_root_url,
            "provider_root_id": config.provider_root_id,
            "google_oauth_store_path": config.project_google_oauth_file.relative_to(config.root).as_posix()
            if config.storage_provider == "google-drive"
            else "",
        },
        "counts": {
            "open_tasks": len(open_tasks),
            "open_risks": len(open_risks),
            "milestones": len(milestones),
            "artifacts": len(artifact_catalog.get("artifacts", [])),
            "sources": len(load_json_file(kernel_root / "sources" / "registry.json", default=[])),
            "rules": len(rule_objects),
        },
        "memory": memory_summary,
        "truth_sources": {
            "artifact_families": len(truth_source_rows),
            "collaborative_artifacts": sum(1 for item in truth_source_rows if item.get("collaboration_mode") == "multi-editor"),
            "provider_native": provider_native_count,
            "workspace": workspace_count,
            "exported_derivative": derivative_count,
            "last_refreshed_at": max((normalize_optional_text(item.get("last_refreshed_at", "")) for item in truth_source_rows), default=""),
            "last_provider_sync_at": max((normalize_optional_text(item.get("last_provider_sync_at", "")) for item in truth_source_rows), default=""),
            "last_provider_check_at": max((normalize_optional_text(item.get("provider_last_checked_at", "")) for item in truth_source_rows), default=""),
            "local_copy_risk_count": len(local_copy_risk),
            "artifacts_at_risk": local_copy_risk[:5],
            "provider_errors": provider_errors[:5],
        },
        "recent_events": recent_events,
    }


def normalize_project_relative_path(raw: str | None) -> str:
    if raw is None:
        return ""
    candidate = raw.strip().replace("\\", "/")
    if not candidate:
        return ""
    path = PurePosixPath(candidate)
    if path.is_absolute():
        raise SystemExit(f"Project-relative artifact path must not be absolute: {raw}")
    parts = [part for part in path.parts if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise SystemExit(f"Invalid project-relative artifact path: {raw}")
    return PurePosixPath(*parts).as_posix()


def resolve_artifact_registration_path(config: ProjectConfig, raw_path: str | None) -> tuple[Path | None, str]:
    if raw_path is None or not raw_path.strip():
        return (None, "")
    candidate = Path(raw_path.strip()).expanduser()
    path = candidate.resolve() if candidate.is_absolute() else (config.root / candidate).resolve()
    if not path.exists():
        raise SystemExit(f"Artifact path does not exist: {path}")
    if not path.is_relative_to(config.root):
        raise SystemExit(f"Artifact path must stay inside the project root: {path}")
    return (path, path.relative_to(config.root).as_posix())


def normalize_artifact_derived_from(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def default_provider_item_kind(config: ProjectConfig, *, has_local_path: bool) -> str:
    if not has_local_path:
        return ""
    if config.storage_provider == "google-drive":
        return "drive-file"
    return ""


def artifact_primary_path(
    *,
    path: str,
    project_relative_path: str,
    provider_item_id: str,
    provider_item_kind: str,
) -> str:
    if path:
        return path
    if project_relative_path:
        return project_relative_path
    if provider_item_id:
        kind = provider_item_kind or "provider-item"
        return f"{kind}:{provider_item_id}"
    return ""


def artifact_identity_key_for_values(
    *,
    storage_provider: str,
    provider_root_id: str,
    path: str,
    project_relative_path: str,
    provider_item_id: str,
    provider_item_kind: str,
) -> str:
    if provider_item_id:
        kind = provider_item_kind or "provider-item"
        root_id = provider_root_id or "unrecorded"
        return f"provider|{storage_provider}|{root_id}|{kind}|{provider_item_id}"
    if path:
        return f"path|{path}"
    if project_relative_path:
        root_id = provider_root_id or "unrecorded"
        return f"project|{storage_provider}|{root_id}|{project_relative_path}"
    return f"ad-hoc|{storage_provider}|untitled"


def artifact_entry_identity_key(entry: dict[str, object]) -> str:
    return artifact_identity_key_for_values(
        storage_provider=normalize_optional_text(entry.get("storage_provider", "")),
        provider_root_id=normalize_optional_text(entry.get("provider_root_id", "")),
        path=normalize_optional_text(entry.get("path", "")),
        project_relative_path=normalize_optional_text(entry.get("project_relative_path", "")),
        provider_item_id=normalize_optional_text(entry.get("provider_item_id", "")),
        provider_item_kind=normalize_optional_text(entry.get("provider_item_kind", "")),
    )


def artifact_entries_match(existing: dict[str, object], incoming: dict[str, object]) -> bool:
    existing_provider_id = normalize_optional_text(existing.get("provider_item_id", ""))
    incoming_provider_id = normalize_optional_text(incoming.get("provider_item_id", ""))
    if existing_provider_id and incoming_provider_id:
        existing_provider = normalize_optional_text(existing.get("storage_provider", ""))
        incoming_provider = normalize_optional_text(incoming.get("storage_provider", ""))
        existing_root = normalize_optional_text(existing.get("provider_root_id", ""))
        incoming_root = normalize_optional_text(incoming.get("provider_root_id", ""))
        if existing_provider == incoming_provider and existing_root == incoming_root and existing_provider_id == incoming_provider_id:
            return True
    for key in ("path", "project_relative_path"):
        existing_value = normalize_optional_text(existing.get(key, ""))
        incoming_value = normalize_optional_text(incoming.get(key, ""))
        if existing_value and incoming_value and existing_value == incoming_value:
            return True
    return artifact_entry_identity_key(existing) == artifact_entry_identity_key(incoming)


def artifact_local_access_paths(config: ProjectConfig, entry: dict[str, object]) -> list[str]:
    explicit_paths = entry.get("local_access_paths", [])
    if isinstance(explicit_paths, list):
        normalized = [normalize_project_relative_path(str(value)) for value in explicit_paths if str(value).strip()]
        if normalized:
            return normalized
    path = normalize_optional_text(entry.get("path", ""))
    if path:
        candidate = config.root / path
        if candidate.exists():
            return [path]
    return []


def artifact_display_path(entry: dict[str, object]) -> str:
    path = normalize_optional_text(entry.get("path", ""))
    if path:
        return path
    project_relative_path = normalize_optional_text(entry.get("project_relative_path", ""))
    if project_relative_path:
        return project_relative_path
    provider_item_id = normalize_optional_text(entry.get("provider_item_id", ""))
    if provider_item_id:
        kind = normalize_optional_text(entry.get("provider_item_kind", "")) or "provider-item"
        return f"{kind}:{provider_item_id}"
    return ""


def artifact_search_tags(entry: dict[str, object]) -> list[str]:
    tags = [
        "artifact",
        normalize_optional_text(entry.get("slot", "")),
        normalize_optional_text(entry.get("workflow_pack", "")),
        normalize_optional_text(entry.get("family_key", "")),
        normalize_optional_text(entry.get("artifact_role", "")),
        normalize_optional_text(entry.get("source_of_truth", "")),
        normalize_optional_text(entry.get("collaboration_mode", "")),
        normalize_optional_text(entry.get("last_refreshed_at", "")),
        normalize_optional_text(entry.get("last_provider_sync_at", "")),
        normalize_optional_text(entry.get("provider_item_kind", "")),
        normalize_optional_text(entry.get("provider_item_id", "")),
        normalize_optional_text(entry.get("project_relative_path", "")),
        normalize_optional_text(entry.get("provider_item_url", "")),
        normalize_optional_text(entry.get("provider_revision_id", "")),
        normalize_optional_text(entry.get("provider_modified_at", "")),
        normalize_optional_text(entry.get("provider_last_fetch_status", "")),
    ]
    derived_from = entry.get("derived_from", [])
    if isinstance(derived_from, list):
        tags.extend(normalize_optional_text(value) for value in derived_from)
    return [tag for tag in tags if tag]


def resolve_required_project_source_path(config: ProjectConfig, raw_path: str) -> tuple[Path, str]:
    path, relative_path = resolve_artifact_registration_path(config, raw_path)
    if path is None or not relative_path:
        raise SystemExit("A project source path is required.")
    return (path, relative_path)


def find_registered_artifact_by_source_path(config: ProjectConfig, relative_path: str) -> dict[str, object] | None:
    normalized = normalize_project_relative_path(relative_path)
    catalog = load_artifact_catalog(config)
    for item in catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        candidates = {
            normalize_optional_text(item.get("path", "")),
            normalize_optional_text(item.get("project_relative_path", "")),
        }
        local_access_paths = item.get("local_access_paths", [])
        if isinstance(local_access_paths, list):
            candidates.update(normalize_project_relative_path(str(value)) for value in local_access_paths if str(value).strip())
        if normalized in {value for value in candidates if value}:
            return item
    return None


def find_registered_artifact_by_id(config: ProjectConfig, artifact_id: str) -> dict[str, object] | None:
    normalized_id = normalize_optional_text(artifact_id)
    if not normalized_id:
        return None
    catalog = load_artifact_catalog(config)
    for item in catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        if normalize_optional_text(item.get("id", "")) == normalized_id:
            return item
    return None


def family_key_from_path(storage_provider: str, provider_root_id: str, relative_path: str) -> str:
    normalized = normalize_project_relative_path(relative_path) if relative_path else ""
    if not normalized:
        return ""
    pure = PurePosixPath(normalized)
    family_path = pure.with_suffix("").as_posix() if pure.suffix else pure.as_posix()
    root_id = provider_root_id or "unrecorded"
    return f"family|{storage_provider}|{root_id}|{family_path}"


def infer_artifact_role(
    *,
    path: str,
    project_relative_path: str,
    local_access_paths: list[str],
    provider_item_id: str,
    provider_item_kind: str,
    derived_from: list[str],
) -> str:
    provider_kind = provider_item_kind.strip().lower()
    if provider_item_id.strip() and provider_kind in PROVIDER_NATIVE_ITEM_KINDS:
        return "provider-native-source"
    candidate_paths = [path, project_relative_path, *local_access_paths]
    suffix = ""
    for candidate in candidate_paths:
        if candidate:
            suffix = PurePosixPath(candidate).suffix.lower()
            if suffix:
                break
    if derived_from and suffix in EXPORT_DERIVATIVE_SUFFIXES:
        return "exported-derivative"
    return "workspace-source"


def artifact_family_entries(catalog: dict[str, object], family_key: str) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for item in catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        if normalize_optional_text(item.get("family_key", "")) == family_key:
            entries.append(item)
    return entries


def choose_family_entry(entries: list[dict[str, object]], preferred_role: str | None = None) -> dict[str, object] | None:
    if not entries:
        return None
    role_order = {
        "provider-native-source": 3,
        "workspace-source": 2,
        "exported-derivative": 1,
    }
    if preferred_role is not None:
        preferred = [item for item in entries if normalize_artifact_role(item.get("artifact_role", "")) == preferred_role]
        if preferred:
            entries = preferred
    return max(
        entries,
        key=lambda item: (
            role_order.get(normalize_artifact_role(item.get("artifact_role", "")), 0),
            normalize_optional_timestamp(item.get("last_provider_sync_at", "")),
            normalize_optional_timestamp(item.get("last_refreshed_at", "")),
            normalize_optional_text(item.get("date", "")),
            normalize_optional_text(item.get("title", "")),
        ),
    )


def artifact_missing_provider_metadata(config: ProjectConfig, entry: dict[str, object]) -> list[str]:
    missing: list[str] = []
    storage_provider = normalize_optional_text(entry.get("storage_provider", "")) or config.storage_provider
    if storage_provider != "google-drive":
        return missing
    if provider_metadata_is_missing(entry.get("provider_root_url", config.provider_root_url)):
        missing.append("provider_root_url")
    if provider_metadata_is_missing(entry.get("provider_root_id", config.provider_root_id)):
        missing.append("provider_root_id")
    if provider_metadata_is_missing(entry.get("provider_item_id", "")):
        missing.append("provider_item_id")
    provider_item_kind = normalize_optional_text(entry.get("provider_item_kind", "")).strip().lower()
    if provider_metadata_is_missing(provider_item_kind) or provider_item_kind not in PROVIDER_NATIVE_ITEM_KINDS:
        missing.append("provider_item_kind")
    if provider_metadata_is_missing(entry.get("provider_item_url", "")):
        missing.append("provider_item_url")
    return missing


def artifact_truth_summary(
    config: ProjectConfig,
    entry: dict[str, object],
    *,
    catalog: dict[str, object] | None = None,
) -> dict[str, object]:
    resolved_catalog = catalog or load_artifact_catalog(config)
    family_key = normalize_optional_text(entry.get("family_key", "")) or artifact_entry_identity_key(entry)
    family_entries = artifact_family_entries(resolved_catalog, family_key) or [entry]
    collaboration_mode = "single-editor"
    if any(normalize_collaboration_mode(item.get("collaboration_mode", "")) == "multi-editor" for item in family_entries):
        collaboration_mode = "multi-editor"
    source_of_truth = "auto"
    for item in family_entries:
        candidate = normalize_source_of_truth(item.get("source_of_truth", ""), default="auto")
        if candidate != "auto":
            source_of_truth = candidate
            break
    provider_entries = [item for item in family_entries if normalize_artifact_role(item.get("artifact_role", "")) == "provider-native-source"]
    workspace_entries = [item for item in family_entries if normalize_artifact_role(item.get("artifact_role", "")) == "workspace-source"]
    derivative_entries = [item for item in family_entries if normalize_artifact_role(item.get("artifact_role", "")) == "exported-derivative"]
    if source_of_truth == "provider-native" or (source_of_truth == "auto" and collaboration_mode == "multi-editor"):
        truth_source_type = "provider-native"
    elif source_of_truth == "workspace":
        truth_source_type = "workspace"
    elif workspace_entries:
        truth_source_type = "workspace"
    elif provider_entries:
        truth_source_type = "provider-native"
    else:
        truth_source_type = "exported-derivative"
    truth_entry = None
    if truth_source_type == "provider-native":
        truth_entry = choose_family_entry(provider_entries, preferred_role="provider-native-source")
    elif truth_source_type == "workspace":
        truth_entry = choose_family_entry(workspace_entries, preferred_role="workspace-source")
    if truth_entry is None:
        fallback_entries = derivative_entries or family_entries
        truth_entry = choose_family_entry(fallback_entries)
    family_last_refreshed_at = max(
        (normalize_optional_timestamp(item.get("last_refreshed_at", "")) for item in family_entries),
        default="",
    )
    local_copy_last_refreshed_at = max(
        (artifact_local_observed_at(config, item) for item in [*workspace_entries, *derivative_entries]),
        default="",
    )
    family_last_provider_sync_at = max(
        (
            normalize_optional_timestamp(item.get("provider_modified_at", ""))
            or normalize_optional_timestamp(item.get("last_provider_sync_at", ""))
            for item in family_entries
        ),
        default="",
    )
    local_copy_stale_risk = False
    if truth_source_type == "provider-native" and (workspace_entries or derivative_entries):
        if family_last_provider_sync_at and (
            not local_copy_last_refreshed_at or local_copy_last_refreshed_at < family_last_provider_sync_at
        ):
            local_copy_stale_risk = True
        elif collaboration_mode == "multi-editor" and not family_last_provider_sync_at:
            local_copy_stale_risk = True
    missing_provider_metadata = artifact_missing_provider_metadata(config, truth_entry or entry) if truth_source_type == "provider-native" else []
    if truth_source_type == "provider-native" and missing_provider_metadata:
        freshness_status = "provider-metadata-missing"
    elif truth_source_type == "provider-native":
        freshness_status = "provider-native-current" if not local_copy_stale_risk else "local-copy-may-be-stale"
    elif truth_source_type == "workspace":
        freshness_status = "workspace-current"
    else:
        freshness_status = "derivative-only"
    truth_role = normalize_artifact_role(truth_entry.get("artifact_role", ""), default="workspace-source") if truth_entry else "workspace-source"
    truth_display_path = artifact_display_path(truth_entry) if isinstance(truth_entry, dict) else artifact_display_path(entry)
    truth_project_relative_path = normalize_optional_text(truth_entry.get("project_relative_path", "")) if isinstance(truth_entry, dict) else ""
    return {
        "family_key": family_key,
        "family_member_count": len(family_entries),
        "family_roles": sorted(
            {
                normalize_artifact_role(item.get("artifact_role", ""), default="workspace-source")
                for item in family_entries
                if normalize_optional_text(item.get("id", ""))
            }
        ),
        "collaboration_mode": collaboration_mode,
        "source_of_truth": source_of_truth,
        "truth_source_type": truth_source_type,
        "truth_source_artifact_id": normalize_optional_text(truth_entry.get("id", "")) if isinstance(truth_entry, dict) else "",
        "truth_source_role": truth_role,
        "truth_source_path": truth_display_path,
        "provider_target_path": truth_project_relative_path if truth_source_type == "provider-native" else "",
        "provider_parent_relative_path": provider_parent_relative_path(truth_project_relative_path) if truth_source_type == "provider-native" else "",
        "last_refreshed_at": family_last_refreshed_at,
        "last_provider_sync_at": family_last_provider_sync_at,
        "local_copy_stale_risk": local_copy_stale_risk,
        "freshness_status": freshness_status,
        "missing_provider_metadata": missing_provider_metadata,
        "refresh_strategy": "provider-native-fetch" if truth_source_type == "provider-native" and not missing_provider_metadata else (
            "register-provider-metadata" if missing_provider_metadata else "workspace-read"
        ),
        "provider_revision_id": normalize_optional_text(truth_entry.get("provider_revision_id", "")) if isinstance(truth_entry, dict) else "",
        "provider_modified_at": normalize_optional_text(truth_entry.get("provider_modified_at", "")) if isinstance(truth_entry, dict) else "",
        "provider_last_checked_at": normalize_optional_text(truth_entry.get("provider_last_checked_at", "")) if isinstance(truth_entry, dict) else "",
        "provider_last_fetch_status": normalize_optional_text(truth_entry.get("provider_last_fetch_status", "")) if isinstance(truth_entry, dict) else "",
        "provider_last_fetch_error": normalize_optional_text(truth_entry.get("provider_last_fetch_error", "")) if isinstance(truth_entry, dict) else "",
        "provider_snapshot_path": normalize_optional_text(truth_entry.get("provider_snapshot_path", "")) if isinstance(truth_entry, dict) else "",
        "truth_source_reason": normalize_optional_text(truth_entry.get("truth_source_reason", "")) if isinstance(truth_entry, dict) else "",
        "minimal_register_action": (
            "Re-register this artifact and fill provider_root_url, provider_root_id, provider_item_id, provider_item_kind, and provider_item_url."
            if missing_provider_metadata
            else ""
        ),
    }


def default_freshness_policy(*, collaboration_mode: str, source_of_truth: str, artifact_role: str) -> str:
    if artifact_role == "provider-native-source" or (collaboration_mode == "multi-editor" and source_of_truth == "provider-native"):
        return "always-refresh-on-intent"
    return "ttl"


def default_freshness_ttl_seconds(*, collaboration_mode: str, source_of_truth: str, artifact_role: str) -> int:
    if artifact_role == "provider-native-source" or (collaboration_mode == "multi-editor" and source_of_truth == "provider-native"):
        return 300
    return 3600


def local_snapshot_revision_id_for_paths(config: ProjectConfig, local_access_paths: list[str]) -> str:
    fingerprints: list[str] = []
    for relative_path in local_access_paths:
        candidate = config.root / relative_path
        if not candidate.exists() or not candidate.is_file():
            continue
        stat = candidate.stat()
        fingerprints.append(f"{relative_path}:{stat.st_size}:{stat.st_mtime_ns}")
    if not fingerprints:
        return ""
    joined = "|".join(sorted(fingerprints))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:20]


def artifact_local_observed_at(config: ProjectConfig, entry: dict[str, object]) -> str:
    observed: list[str] = []
    for relative_path in artifact_local_access_paths(config, entry):
        candidate = config.root / relative_path
        if not candidate.exists() or not candidate.is_file():
            continue
        observed.append(datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    last_refreshed_at = normalize_optional_timestamp(entry.get("last_refreshed_at", ""))
    if last_refreshed_at:
        observed.append(last_refreshed_at)
    return max(observed, default="")


def provider_snapshot_cache_path(config: ProjectConfig, artifact_id: str) -> Path:
    safe_id = sanitize_source_id(artifact_id)
    return config.provider_snapshot_root / f"{safe_id}.json"


def write_provider_snapshot_cache(
    config: ProjectConfig,
    *,
    artifact_id: str,
    snapshot: ProviderSnapshot,
    refreshed_at: str,
) -> str:
    cache_path = provider_snapshot_cache_path(config, artifact_id)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": VERSION,
        "refreshed_at": refreshed_at,
        "provider": snapshot.provider,
        "provider_item_id": snapshot.provider_item_id,
        "provider_item_kind": snapshot.provider_item_kind,
        "provider_item_url": snapshot.provider_item_url,
        "provider_title": snapshot.provider_title,
        "provider_revision_id": snapshot.provider_revision_id,
        "provider_modified_at": snapshot.provider_modified_at,
        "provider_etag": snapshot.provider_etag,
        "truth_source_reason": snapshot.truth_source_reason,
        "normalized_content": snapshot.normalized_content,
        "raw_metadata": snapshot.raw_metadata,
    }
    cache_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return cache_path.relative_to(config.root).as_posix()


def artifact_search_haystack(item: dict[str, object]) -> str:
    return " ".join(
        [
            normalize_optional_text(item.get("id", "")),
            normalize_optional_text(item.get("kind", "")),
            normalize_optional_text(item.get("title", "")),
            normalize_optional_text(item.get("slot", "")),
            artifact_display_path(item),
            normalize_optional_text(item.get("project_relative_path", "")),
            normalize_optional_text(item.get("provider_item_id", "")),
            normalize_optional_text(item.get("provider_item_kind", "")),
            normalize_optional_text(item.get("provider_item_url", "")),
            normalize_optional_text(item.get("summary", "")),
            normalize_optional_text(item.get("family_key", "")),
            normalize_optional_text(item.get("collaboration_mode", "")),
            normalize_optional_text(item.get("source_of_truth", "")),
        ]
    ).lower()


def artifact_refresh_due(config: ProjectConfig, entry: dict[str, object], *, force: bool) -> bool:
    if force:
        return True
    policy = normalize_optional_text(entry.get("freshness_policy", "")).strip().lower() or "ttl"
    ttl_seconds_raw = normalize_optional_text(entry.get("freshness_ttl_seconds", ""))
    try:
        ttl_seconds = int(ttl_seconds_raw or "0")
    except ValueError:
        ttl_seconds = 0
    if policy == "always-refresh-on-intent":
        return True
    if ttl_seconds <= 0:
        return True
    checked_at = normalize_optional_timestamp(entry.get("provider_last_checked_at", ""))
    if not checked_at:
        return True
    checked_dt = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
    now_dt = datetime.now(timezone.utc)
    return (now_dt - checked_dt).total_seconds() >= ttl_seconds


def resolve_artifact_refresh_candidates(
    config: ProjectConfig,
    *,
    artifact_id: str | None = None,
    family_key: str | None = None,
    query: str | None = None,
    all_collaborative: bool = False,
    limit: int = 5,
) -> list[dict[str, object]]:
    catalog = load_artifact_catalog(config)
    candidates: list[dict[str, object]] = []
    if artifact_id:
        item = find_registered_artifact_by_id(config, artifact_id)
        if item is not None:
            candidates.append(item)
    elif family_key:
        candidates.extend(artifact_family_entries(catalog, family_key))
    else:
        effective_query = (query or "").strip().lower()
        for item in catalog.get("artifacts", []):
            if not isinstance(item, dict):
                continue
            summary = artifact_truth_summary(config, item, catalog=catalog)
            if summary["truth_source_type"] != "provider-native":
                continue
            if all_collaborative and summary["collaboration_mode"] != "multi-editor":
                continue
            if effective_query and effective_query not in artifact_search_haystack(item):
                continue
            candidates.append(item)
    unique: dict[str, dict[str, object]] = {}
    for item in candidates:
        summary = artifact_truth_summary(config, item, catalog=catalog)
        if summary["truth_source_type"] != "provider-native":
            continue
        key = summary["family_key"]
        existing = unique.get(key)
        if existing is None:
            unique[key] = item
            continue
        existing_summary = artifact_truth_summary(config, existing, catalog=catalog)
        if summary["collaboration_mode"] == "multi-editor" and existing_summary["collaboration_mode"] != "multi-editor":
            unique[key] = item
    ordered = list(unique.values())
    ordered.sort(
        key=lambda item: (
            artifact_truth_summary(config, item, catalog=catalog)["collaboration_mode"] == "multi-editor",
            artifact_truth_summary(config, item, catalog=catalog)["local_copy_stale_risk"],
            normalize_optional_text(item.get("last_provider_sync_at", "")),
            normalize_optional_text(item.get("title", "")),
        ),
        reverse=True,
    )
    return ordered[: max(1, limit)]


def refresh_provider_artifact_entry(
    config: ProjectConfig,
    *,
    entry: dict[str, object],
    force: bool,
) -> dict[str, object]:
    catalog = load_artifact_catalog(config)
    truth = artifact_truth_summary(config, entry, catalog=catalog)
    truth_artifact_id = normalize_optional_text(truth.get("truth_source_artifact_id", ""))
    provider_entry = None
    if truth_artifact_id:
        for item in catalog.get("artifacts", []):
            if not isinstance(item, dict):
                continue
            if normalize_optional_text(item.get("id", "")) == truth_artifact_id:
                provider_entry = item
                break
    if provider_entry is None:
        provider_entry = choose_family_entry(artifact_family_entries(catalog, truth["family_key"]), preferred_role="provider-native-source")
    if provider_entry is None:
        return {
            "artifact_id": normalize_optional_text(entry.get("id", "")),
            "family_key": truth["family_key"],
            "status": "skipped",
            "reason": "no-provider-native-entry",
        }
    missing = artifact_missing_provider_metadata(config, provider_entry)
    if missing:
        now_timestamp = current_utc_timestamp()
        provider_entry["provider_last_checked_at"] = now_timestamp
        provider_entry["provider_last_fetch_status"] = "provider-metadata-incomplete"
        provider_entry["provider_last_fetch_error"] = ",".join(missing)
        write_artifact_catalog(config, catalog)
        return {
            "artifact_id": normalize_optional_text(provider_entry.get("id", "")),
            "family_key": truth["family_key"],
            "status": "blocked",
            "reason": "provider-metadata-incomplete",
            "missing_provider_metadata": missing,
        }
    if not artifact_refresh_due(config, provider_entry, force=force):
        return {
            "artifact_id": normalize_optional_text(provider_entry.get("id", "")),
            "family_key": truth["family_key"],
            "status": "skipped",
            "reason": "freshness-ttl-not-expired",
        }
    refreshed_at = current_utc_timestamp()
    try:
        adapter = create_provider_adapter(
            normalize_optional_text(provider_entry.get("storage_provider", "")) or config.storage_provider,
            oauth_store_path=config.project_google_oauth_file,
        )
        snapshot = adapter.fetch_item(
            provider_item_id=normalize_optional_text(provider_entry.get("provider_item_id", "")),
            provider_item_kind=normalize_optional_text(provider_entry.get("provider_item_kind", "")),
            provider_item_url=normalize_optional_text(provider_entry.get("provider_item_url", "")),
        )
    except ProviderAdapterError as exc:
        provider_entry["provider_last_checked_at"] = refreshed_at
        provider_entry["provider_last_fetch_status"] = exc.code
        provider_entry["provider_last_fetch_error"] = exc.message
        write_artifact_catalog(config, catalog)
        return {
            "artifact_id": normalize_optional_text(provider_entry.get("id", "")),
            "family_key": truth["family_key"],
            "status": "error",
            "reason": exc.code,
            "message": exc.message,
            "retryable": exc.retryable,
        }
    provider_entry["title"] = normalize_optional_text(provider_entry.get("title", "")) or snapshot.provider_title
    provider_entry["provider_item_url"] = snapshot.provider_item_url or normalize_optional_text(provider_entry.get("provider_item_url", ""))
    provider_entry["last_refreshed_at"] = refreshed_at
    provider_entry["last_provider_sync_at"] = snapshot.provider_modified_at or refreshed_at
    provider_entry["provider_revision_id"] = snapshot.provider_revision_id
    provider_entry["provider_modified_at"] = snapshot.provider_modified_at
    provider_entry["provider_etag"] = snapshot.provider_etag
    provider_entry["provider_last_checked_at"] = refreshed_at
    provider_entry["provider_last_fetch_status"] = "ok"
    provider_entry["provider_last_fetch_error"] = ""
    provider_entry["truth_source_reason"] = snapshot.truth_source_reason
    cache_path = write_provider_snapshot_cache(
        config,
        artifact_id=normalize_optional_text(provider_entry.get("id", "")),
        snapshot=snapshot,
        refreshed_at=refreshed_at,
    )
    provider_entry["provider_snapshot_path"] = cache_path
    write_artifact_catalog(config, catalog)
    return {
        "artifact_id": normalize_optional_text(provider_entry.get("id", "")),
        "family_key": truth["family_key"],
        "status": "ok",
        "reason": "provider-refreshed",
        "provider_revision_id": snapshot.provider_revision_id,
        "provider_modified_at": snapshot.provider_modified_at,
        "provider_snapshot_path": cache_path,
    }


def refresh_provider_artifact_batch(
    config: ProjectConfig,
    *,
    artifact_id: str | None = None,
    family_key: str | None = None,
    query: str | None = None,
    all_collaborative: bool = False,
    limit: int = 5,
    force: bool = False,
    event_type: str = "artifact.refresh",
    event_summary_prefix: str = "Refreshed provider-native artifact truth sources",
) -> dict[str, object]:
    candidates = resolve_artifact_refresh_candidates(
        config,
        artifact_id=artifact_id,
        family_key=family_key,
        query=query,
        all_collaborative=all_collaborative,
        limit=limit,
    )
    results = [refresh_provider_artifact_entry(config, entry=item, force=force) for item in candidates]
    refresh_kernel_state(
        config,
        event_type=event_type,
        summary=f"{event_summary_prefix} ({sum(1 for item in results if item.get('status') == 'ok')} ok, {len(results)} attempted).",
    )
    return {
        "attempted": len(candidates),
        "ok": sum(1 for item in results if item.get("status") == "ok"),
        "blocked": sum(1 for item in results if item.get("status") == "blocked"),
        "errors": sum(1 for item in results if item.get("status") == "error"),
        "skipped": sum(1 for item in results if item.get("status") == "skipped"),
        "results": results,
    }


def provider_import_spec(provider_item_kind: str) -> dict[str, object]:
    spec = PROVIDER_IMPORT_KIND_SPECS.get(provider_item_kind.lower())
    if spec is None:
        raise SystemExit(f"Unsupported provider import kind: {provider_item_kind}")
    return spec


def provider_import_target_format(provider_item_kind: str, explicit_target_format: str | None) -> str:
    spec = provider_import_spec(provider_item_kind)
    requested = normalize_optional_text(explicit_target_format).lower()
    if requested:
        if requested not in spec["allowed_target_formats"]:
            allowed = ", ".join(spec["allowed_target_formats"])
            raise SystemExit(f"{provider_item_kind} import only supports bridge formats: {allowed}")
        return requested
    return str(spec["default_target_format"])


def provider_import_mime_type(provider_item_kind: str, target_format: str) -> str:
    spec = provider_import_spec(provider_item_kind)
    mime_types = spec.get("mime_types", {})
    if isinstance(mime_types, dict):
        value = mime_types.get(target_format)
        if isinstance(value, str) and value:
            return value
    return "application/octet-stream"


def provider_import_plan_path(config: ProjectConfig, *, record_date: str, slug: str, provider_item_kind: str) -> Path:
    provider_slug = sanitize_slug(provider_item_kind) or "provider-item"
    target_dir = config.provider_import_root
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"{record_date}-{slug}-{provider_slug}-import.json"


def provider_parent_relative_path(project_relative_path: str) -> str:
    normalized = normalize_project_relative_path(project_relative_path) if project_relative_path else ""
    if not normalized:
        return ""
    parent = PurePosixPath(normalized).parent.as_posix()
    return "" if parent == "." else parent


def slot_relative_provider_path(*, slot: str, date_value: str, title: str, slug: str | None = None) -> str:
    slot_prefix = normalize_project_relative_path(slot or "delivery")
    basename_slug = sanitize_slug(slug or title) or "item"
    basename = f"{date_value}-{basename_slug}" if date_value else basename_slug
    return PurePosixPath(slot_prefix, basename).as_posix()


def provider_relative_path_from_local_candidate(config: ProjectConfig, *, candidate: str, slot: str) -> str:
    normalized = normalize_project_relative_path(candidate)
    pure = PurePosixPath(normalized)
    if pure.suffix:
        normalized = pure.with_suffix("").as_posix()
    artifacts_prefix = ""
    if config.artifacts_root.is_relative_to(config.root):
        artifacts_prefix = config.artifacts_root.relative_to(config.root).as_posix()
    if artifacts_prefix and (normalized == artifacts_prefix or normalized.startswith(f"{artifacts_prefix}/")):
        trimmed = normalized[len(artifacts_prefix) :].lstrip("/")
        return normalize_project_relative_path(trimmed) if trimmed else ""
    slot_prefix = normalize_project_relative_path(slot) if slot else ""
    if slot_prefix and (normalized == slot_prefix or normalized.startswith(f"{slot_prefix}/")):
        return normalized
    return ""


def artifact_provider_relative_path(
    config: ProjectConfig,
    entry: dict[str, object] | None,
    *,
    slot: str,
    date_value: str,
    title: str,
    slug: str | None = None,
    fallback_path: str,
    explicit_project_relative_path: str = "",
) -> str:
    explicit = normalize_project_relative_path(explicit_project_relative_path)
    if explicit:
        return explicit
    if isinstance(entry, dict):
        entry_project_relative_path = normalize_optional_text(entry.get("project_relative_path", ""))
        if entry_project_relative_path:
            candidate = provider_relative_path_from_local_candidate(config, candidate=entry_project_relative_path, slot=slot)
            if candidate:
                return candidate
            return normalize_project_relative_path(entry_project_relative_path)
        entry_path = normalize_optional_text(entry.get("path", ""))
        if entry_path:
            candidate = provider_relative_path_from_local_candidate(config, candidate=entry_path, slot=slot)
            if candidate:
                return candidate
    if fallback_path:
        candidate = provider_relative_path_from_local_candidate(config, candidate=fallback_path, slot=slot)
        if candidate:
            return candidate
    return slot_relative_provider_path(slot=slot, date_value=date_value, title=title, slug=slug)


def artifact_register_command_preview(
    config: ProjectConfig,
    *,
    artifact_kind: str,
    title: str,
    slot: str,
    date_value: str,
    summary: str,
    project_relative_path: str,
    provider_item_kind: str,
    derived_from: list[str],
    source_of_truth: str = "auto",
    collaboration_mode: str = "single-editor",
) -> str:
    command: list[str] = [
        "python3",
        "scripts/sula.py",
        "artifact",
        "register",
        "--project-root",
        str(config.root),
        "--kind",
        artifact_kind,
        "--title",
        title,
        "--slot",
        slot,
        "--project-relative-path",
        project_relative_path,
        "--provider-item-id",
        "<provider-item-id>",
        "--provider-item-kind",
        provider_item_kind,
        "--provider-item-url",
        "<provider-item-url>",
    ]
    if date_value:
        command.extend(["--date", date_value])
    if summary.strip():
        command.extend(["--summary", summary.strip()])
    if source_of_truth != "auto":
        command.extend(["--source-of-truth", source_of_truth])
    if collaboration_mode != "single-editor":
        command.extend(["--collaboration-mode", collaboration_mode])
    for derived in derived_from:
        if derived:
            command.extend(["--derived-from", derived])
    return " ".join(command)


def resolve_artifact_import_source(
    config: ProjectConfig,
    *,
    source_path: str | None,
    artifact_id: str | None,
) -> tuple[Path, str, dict[str, object] | None]:
    if bool(source_path) == bool(artifact_id):
        raise SystemExit("Provider import planning requires exactly one of --source-path or --artifact-id.")
    if source_path:
        path, relative_path = resolve_required_project_source_path(config, source_path)
        return (path, relative_path, find_registered_artifact_by_source_path(config, relative_path))
    artifact = find_registered_artifact_by_id(config, str(artifact_id))
    if artifact is None:
        raise SystemExit(f"Unknown artifact id: {artifact_id}")
    local_paths = artifact_local_access_paths(config, artifact)
    if not local_paths:
        raise SystemExit(f"Artifact `{artifact_id}` does not have a local project file that can be imported.")
    relative_path = local_paths[0]
    return (config.root / relative_path, relative_path, artifact)


def markdown_inline_html(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", lambda match: f"<code>{match.group(1)}</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", lambda match: f"<strong>{match.group(1)}</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", lambda match: f"<em>{match.group(1)}</em>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        escaped,
    )
    return escaped


def is_markdown_table_block(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index].strip()
    separator = lines[index + 1].strip()
    return "|" in header and bool(re.match(r"^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$", separator))


def parse_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def render_markdown_table(lines: list[str], start_index: int) -> tuple[str, int]:
    header_cells = parse_markdown_table_row(lines[start_index])
    body_rows: list[list[str]] = []
    index = start_index + 2
    while index < len(lines):
        candidate = lines[index].rstrip()
        if not candidate.strip() or "|" not in candidate:
            break
        body_rows.append(parse_markdown_table_row(candidate))
        index += 1
    header_html = "".join(f"<th>{markdown_inline_html(cell)}</th>" for cell in header_cells)
    body_html = []
    for row in body_rows:
        cells = "".join(f"<td>{markdown_inline_html(cell)}</td>" for cell in row)
        body_html.append(f"<tr>{cells}</tr>")
    table_html = ["<table>", f"<thead><tr>{header_html}</tr></thead>"]
    if body_html:
        table_html.append("<tbody>")
        table_html.extend(body_html)
        table_html.append("</tbody>")
    table_html.append("</table>")
    return ("\n".join(table_html), index)


def render_markdown_body_to_html(text: str) -> str:
    lines = text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip("\n")
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            blocks.append(f"<h{level}>{markdown_inline_html(heading_match.group(2).strip())}</h{level}>")
            index += 1
            continue
        if is_markdown_table_block(lines, index):
            table_html, index = render_markdown_table(lines, index)
            blocks.append(table_html)
            continue
        if stripped.startswith("```"):
            fence = stripped[:3]
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(fence):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            code_html = html.escape("\n".join(code_lines))
            blocks.append(f"<pre><code>{code_html}</code></pre>")
            continue
        if re.match(r"^[-*]\s+", stripped):
            items: list[str] = []
            while index < len(lines):
                candidate = lines[index].strip()
                if not re.match(r"^[-*]\s+", candidate):
                    break
                items.append(re.sub(r"^[-*]\s+", "", candidate))
                index += 1
            blocks.append("<ul>" + "".join(f"<li>{markdown_inline_html(item)}</li>" for item in items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while index < len(lines):
                candidate = lines[index].strip()
                if not re.match(r"^\d+\.\s+", candidate):
                    break
                items.append(re.sub(r"^\d+\.\s+", "", candidate))
                index += 1
            blocks.append("<ol>" + "".join(f"<li>{markdown_inline_html(item)}</li>" for item in items) + "</ol>")
            continue
        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            quote_html = "".join(f"<p>{markdown_inline_html(item)}</p>" for item in quote_lines if item)
            blocks.append(f"<blockquote>{quote_html}</blockquote>")
            continue
        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or re.match(r"^(#{1,6})\s+", candidate) or candidate.startswith("```") or candidate.startswith(">"):
                break
            if is_markdown_table_block(lines, index) or re.match(r"^[-*]\s+", candidate) or re.match(r"^\d+\.\s+", candidate):
                break
            paragraph_lines.append(candidate)
            index += 1
        blocks.append(f"<p>{markdown_inline_html(' '.join(paragraph_lines))}</p>")
    return "\n".join(blocks)


def wrap_html_document(title: str, body_html: str) -> str:
    safe_title = html.escape(title)
    return (
        "<!doctype html>\n"
        "<html>\n"
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{safe_title}</title>\n"
        "  <style>\n"
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; line-height: 1.6; color: #1f2937; }\n"
        "    table { border-collapse: collapse; width: 100%; margin: 16px 0; }\n"
        "    th, td { border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; vertical-align: top; }\n"
        "    th { background: #f8fafc; }\n"
        "    code, pre { font-family: 'SFMono-Regular', Menlo, monospace; }\n"
        "    pre { background: #f8fafc; padding: 12px; overflow-x: auto; }\n"
        "    blockquote { border-left: 4px solid #cbd5e1; margin: 16px 0; padding-left: 16px; color: #475569; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"{body_html}\n"
        "</body>\n"
        "</html>\n"
    )


def render_source_document_to_html(source_path: Path, *, title: str) -> str:
    suffix = source_path.suffix.lower()
    text = source_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".html":
        return text
    if suffix == ".md":
        return wrap_html_document(title, render_markdown_body_to_html(text))
    if suffix == ".txt":
        paragraphs = [segment.strip() for segment in text.split("\n\n") if segment.strip()]
        body_html = "\n".join(f"<p>{markdown_inline_html(paragraph.replace(chr(10), ' '))}</p>" for paragraph in paragraphs)
        return wrap_html_document(title, body_html or "<p></p>")
    raise SystemExit(f"Unsupported document source format for materialization: {source_path.suffix or source_path.name}")


def convert_html_to_docx(html_text: str, output_path: Path) -> None:
    write_simple_docx(output_path, html_blocks_for_docx(html_text))


class DocxHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, str]] = []
        self.current_style = "Normal"
        self.current_parts: list[str] = []
        self.preformatted = False
        self.in_table_cell = False
        self.table_cell_parts: list[str] = []
        self.table_row_cells: list[str] = []

    def push_text(self, text: str) -> None:
        if not text:
            return
        if self.in_table_cell:
            self.table_cell_parts.append(text)
            return
        self.current_parts.append(text)

    def flush_block(self) -> None:
        raw_text = "".join(self.current_parts)
        if self.preformatted:
            text = raw_text.strip("\n")
        else:
            text = re.sub(r"[ \t\r\f\v]+", " ", raw_text)
            text = re.sub(r" *\n *", "\n", text)
            text = text.strip()
        if text:
            self.blocks.append({"style": self.current_style, "text": text})
        self.current_parts = []
        self.current_style = "Normal"

    def start_block(self, style: str) -> None:
        self.flush_block()
        self.current_style = style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"p", "div"}:
            self.start_block("Normal")
        elif tag == "blockquote":
            self.start_block("Quote")
        elif tag == "pre":
            self.start_block("Code")
            self.preformatted = True
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.start_block("Heading1" if tag == "h1" else "Heading2")
        elif tag == "li":
            self.start_block("ListParagraph")
            self.push_text("- ")
        elif tag == "br":
            self.push_text("\n")
        elif tag == "tr":
            self.table_row_cells = []
        elif tag in {"td", "th"}:
            self.in_table_cell = True
            self.table_cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "blockquote", "li"}:
            self.flush_block()
        elif tag == "pre":
            self.flush_block()
            self.preformatted = False
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.flush_block()
        elif tag in {"td", "th"}:
            cell_text = re.sub(r"\s+", " ", "".join(self.table_cell_parts)).strip()
            self.table_row_cells.append(cell_text)
            self.table_cell_parts = []
            self.in_table_cell = False
        elif tag == "tr":
            row_text = " | ".join(cell for cell in self.table_row_cells if cell)
            if row_text:
                self.start_block("TableParagraph")
                self.push_text(row_text)
                self.flush_block()
            self.table_row_cells = []
        elif tag == "body":
            self.flush_block()

    def handle_data(self, data: str) -> None:
        if self.preformatted:
            self.push_text(data)
            return
        self.push_text(re.sub(r"\s+", " ", data))


def html_blocks_for_docx(html_text: str) -> list[dict[str, str]]:
    parser = DocxHtmlParser()
    parser.feed(html_text)
    parser.close()
    parser.flush_block()
    if parser.blocks:
        return parser.blocks
    plain_text = re.sub(r"<[^>]+>", " ", html_text)
    normalized = re.sub(r"\s+", " ", plain_text).strip()
    return [{"style": "Normal", "text": normalized or " "}]


def docx_runs_xml(text: str) -> str:
    segments = text.split("\n")
    xml_parts: list[str] = []
    for index, segment in enumerate(segments):
        xml_parts.append(
            '<w:r><w:t xml:space="preserve">'
            + html.escape(segment or " ", quote=False)
            + "</w:t></w:r>"
        )
        if index < len(segments) - 1:
            xml_parts.append("<w:r><w:br/></w:r>")
    return "".join(xml_parts)


def docx_paragraph_xml(text: str, *, style: str) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}{docx_runs_xml(text)}</w:p>"


def docx_styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="TableParagraph"><w:name w:val="Table Paragraph"/></w:style>'
        "</w:styles>"
    )


def write_simple_docx(output_path: Path, blocks: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    paragraphs = "".join(
        docx_paragraph_xml(
            block.get("text", "") or " ",
            style=normalize_optional_text(block.get("style", "")) or "Normal",
        )
        for block in blocks
    ) or docx_paragraph_xml(" ", style="Normal")
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 wp14">'
        f"<w:body>{paragraphs}<w:sectPr/></w:body>"
        "</w:document>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )
    package_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    document_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", package_rels_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", document_rels_xml)
        archive.writestr("word/styles.xml", docx_styles_xml())


def json_tabular_rows(data: object) -> list[list[object]]:
    if isinstance(data, dict) and "rows" in data:
        data = data["rows"]
    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        headers: list[str] = []
        seen: set[str] = set()
        for item in data:
            assert isinstance(item, dict)
            for key in item:
                if key not in seen:
                    seen.add(key)
                    headers.append(str(key))
        rows: list[list[object]] = [headers]
        for item in data:
            assert isinstance(item, dict)
            rows.append([item.get(header, "") for header in headers])
        return rows
    if isinstance(data, list) and all(isinstance(item, list) for item in data):
        return [[cell for cell in row] for row in data if isinstance(row, list)]
    raise SystemExit("JSON spreadsheet materialization expects an array of objects, an array of arrays, or an object with a `rows` array.")


def load_tabular_rows(source_path: Path) -> list[list[object]]:
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        with source_path.open("r", encoding="utf-8", newline="") as handle:
            return [row for row in csv.reader(handle)]
    if suffix == ".tsv":
        with source_path.open("r", encoding="utf-8", newline="") as handle:
            return [row for row in csv.reader(handle, delimiter="\t")]
    if suffix == ".json":
        data = json.loads(source_path.read_text(encoding="utf-8"))
        return json_tabular_rows(data)
    raise SystemExit(f"Unsupported spreadsheet source format for materialization: {source_path.suffix or source_path.name}")


def excel_column_name(index: int) -> str:
    label = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(65 + remainder) + label
    return label or "A"


def sanitize_sheet_name(value: str) -> str:
    cleaned = re.sub(r"[:\\\\/?*\\[\\]]", "-", value).strip()
    return (cleaned or "Sheet1")[:31]


def xlsx_cell_xml(reference: str, value: object) -> str:
    if isinstance(value, bool):
        string_value = "TRUE" if value else "FALSE"
        return f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">{html.escape(string_value)}</t></is></c>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{reference}"><v>{value}</v></c>'
    text_value = html.escape("" if value is None else str(value))
    return f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">{text_value}</t></is></c>'


def write_simple_xlsx(output_path: Path, rows: list[list[object]], *, sheet_name: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_sheet_name = sanitize_sheet_name(sheet_name)
    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row, start=1):
            reference = f"{excel_column_name(column_index)}{row_index}"
            cells.append(xlsx_cell_xml(reference, value))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{html.escape(safe_sheet_name, quote=True)}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    package_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", package_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def materialize_source_file(source_path: Path, *, target_format: str, output_path: Path, title: str, sheet_name: str) -> None:
    if target_format == "html":
        output_path.write_text(render_source_document_to_html(source_path, title=title), encoding="utf-8")
        return
    if target_format == "docx":
        convert_html_to_docx(render_source_document_to_html(source_path, title=title), output_path)
        return
    if target_format == "xlsx":
        rows = load_tabular_rows(source_path)
        write_simple_xlsx(output_path, rows, sheet_name=sheet_name)
        return
    raise SystemExit(f"Unsupported target materialization format: {target_format}")


def materialized_artifact_summary(
    config: ProjectConfig,
    *,
    target_format: str,
    source_relative_path: str,
    explicit_summary: str,
) -> str:
    if explicit_summary.strip():
        return explicit_summary.strip()
    if locale_family(config.content_locale) == "zh":
        return f"由 `{source_relative_path}` 物化生成的 {target_format} 成品。"
    return f"Materialized {target_format} artifact derived from `{source_relative_path}`."


def materialize_or_register_bridge_artifact(
    config: ProjectConfig,
    *,
    source_path: Path,
    source_relative_path: str,
    source_entry: dict[str, object] | None,
    target_format: str,
    artifact_kind: str,
    title: str,
    slug: str,
    slot: str,
    record_date: str,
    summary: str,
    sheet_name: str,
    allow_existing_output: bool,
) -> tuple[dict[str, object], Path, bool]:
    target_dir = config.artifacts_root / slot
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{record_date}-{slug}.{target_format}"
    output_relative = output_path.relative_to(config.root).as_posix()
    existing_registered = find_registered_artifact_by_source_path(config, output_relative)
    if output_path.exists() and not allow_existing_output:
        raise SystemExit(f"Materialized artifact already exists: {output_path}")
    created = False
    if not output_path.exists():
        materialize_source_file(
            source_path,
            target_format=target_format,
            output_path=output_path,
            title=title,
            sheet_name=sheet_name,
        )
        created = True
    if existing_registered is not None:
        return (existing_registered, output_path, created)
    derived_from = [normalize_optional_text(source_entry.get("id", ""))] if isinstance(source_entry, dict) and source_entry.get("id") else []
    entry = register_artifact_entry(
        config,
        path=output_relative,
        artifact_kind=artifact_kind,
        title=title,
        slot=slot,
        summary=summary,
        date_value=record_date,
        project_relative_path=output_relative,
        local_access_paths=[output_relative],
        provider_item_id="",
        provider_item_kind=default_provider_item_kind(config, has_local_path=True),
        provider_item_url="",
        derived_from=derived_from,
        source_of_truth="workspace",
        collaboration_mode=normalize_collaboration_mode(source_entry.get("collaboration_mode", ""), default="single-editor")
        if isinstance(source_entry, dict)
        else "single-editor",
        artifact_role="exported-derivative",
        last_refreshed_at=current_utc_timestamp(),
        last_provider_sync_at=normalize_optional_timestamp(source_entry.get("last_provider_sync_at", "")) if isinstance(source_entry, dict) else "",
    )
    return (entry, output_path, created)


def artifact_materialize(config: ProjectConfig, args: argparse.Namespace) -> int:
    ensure_artifact_catalog(config)
    source_path, source_relative_path = resolve_required_project_source_path(config, args.source_path)
    source_entry = find_registered_artifact_by_source_path(config, source_relative_path)
    target_format = args.target_format.lower()
    default_kind = normalize_optional_text(source_entry.get("kind", "")) if isinstance(source_entry, dict) else ""
    artifact_kind = (args.kind or default_kind or "deliverable").lower()
    slot = artifact_slot_for_kind(config, artifact_kind, args.slot)
    source_entry_date = normalize_optional_text(source_entry.get("date", "")) if isinstance(source_entry, dict) else ""
    record_date = normalize_record_date(args.date) if args.date else source_entry_date or date.today().isoformat()
    title = args.title or (normalize_optional_text(source_entry.get("title", "")) if isinstance(source_entry, dict) else "") or source_path.stem
    slug = sanitize_slug(args.slug or title)
    summary = materialized_artifact_summary(
        config,
        target_format=target_format,
        source_relative_path=source_relative_path,
        explicit_summary=args.summary,
    )
    entry, output_path, _created = materialize_or_register_bridge_artifact(
        config,
        source_path=source_path,
        source_relative_path=source_relative_path,
        source_entry=source_entry,
        target_format=target_format,
        artifact_kind=artifact_kind,
        title=title,
        slug=slug,
        slot=slot,
        record_date=record_date,
        summary=summary,
        sheet_name=args.sheet_name,
        allow_existing_output=False,
    )
    refresh_kernel_state(config, event_type="artifact.materialize", summary=f"Materialized {target_format} artifact `{title}` from `{source_relative_path}`.")
    payload = {
        "command": "artifact.materialize",
        "status": "ok",
        "project": project_payload(config),
        "source_path": source_relative_path,
        "target_format": target_format,
        "artifact": entry,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    if locale_family(config.interaction_locale) == "zh":
        print(f"已从 {source_relative_path} 生成 {target_format} 文件 {output_path.relative_to(config.root).as_posix()}")
    else:
        print(f"Materialized {target_format} artifact from {source_relative_path} to {output_path.relative_to(config.root).as_posix()}")
    return 0


def artifact_import_plan(config: ProjectConfig, args: argparse.Namespace) -> int:
    ensure_artifact_catalog(config)
    provider_item_kind = args.provider_item_kind.lower()
    spec = provider_import_spec(provider_item_kind)
    provider = normalize_optional_text(args.provider).lower() or str(spec["provider"])
    if provider != spec["provider"]:
        raise SystemExit(f"{provider_item_kind} import planning currently supports provider `{spec['provider']}` only.")
    source_path, source_relative_path, source_entry = resolve_artifact_import_source(
        config,
        source_path=getattr(args, "source_path", None),
        artifact_id=getattr(args, "artifact_id", None),
    )
    target_format = provider_import_target_format(provider_item_kind, getattr(args, "target_format", None))
    default_kind = normalize_optional_text(source_entry.get("kind", "")) if isinstance(source_entry, dict) else ""
    artifact_kind = (args.kind or default_kind or "deliverable").lower()
    slot = artifact_slot_for_kind(config, artifact_kind, args.slot)
    source_entry_date = normalize_optional_text(source_entry.get("date", "")) if isinstance(source_entry, dict) else ""
    detected_source_date = detect_source_date(source_path, source_summary(source_path)) or ""
    record_date = normalize_record_date(args.date) if args.date else source_entry_date or detected_source_date or date.today().isoformat()
    title = args.title or (normalize_optional_text(source_entry.get("title", "")) if isinstance(source_entry, dict) else "") or source_path.stem
    slug = sanitize_slug(args.slug or title)
    source_suffix = source_path.suffix.lower()
    source_suffixes = set(spec["source_suffixes"])
    if source_suffix not in source_suffixes:
        supported = ", ".join(sorted(source_suffixes))
        raise SystemExit(f"{provider_item_kind} import planning supports source files with these suffixes: {supported}")
    bridge_entry: dict[str, object]
    bridge_created = False
    if source_suffix == f".{target_format}":
        if isinstance(source_entry, dict):
            bridge_entry = source_entry
        else:
            summary = args.summary.strip() or source_summary(source_path)
            bridge_entry = register_artifact_entry(
                config,
                path=source_relative_path,
                artifact_kind=artifact_kind,
                title=title,
                slot=slot,
                summary=summary,
                date_value=record_date,
                project_relative_path=source_relative_path,
                local_access_paths=[source_relative_path],
                provider_item_id="",
                provider_item_kind=default_provider_item_kind(config, has_local_path=True),
                provider_item_url="",
                derived_from=[],
                source_of_truth="workspace",
                collaboration_mode="single-editor",
                artifact_role="workspace-source",
                last_refreshed_at=current_utc_timestamp(),
                last_provider_sync_at="",
            )
    else:
        summary = materialized_artifact_summary(
            config,
            target_format=target_format,
            source_relative_path=source_relative_path,
            explicit_summary=args.summary,
        )
        bridge_entry, _bridge_output_path, bridge_created = materialize_or_register_bridge_artifact(
            config,
            source_path=source_path,
            source_relative_path=source_relative_path,
            source_entry=source_entry,
            target_format=target_format,
            artifact_kind=artifact_kind,
            title=title,
            slug=slug,
            slot=slot,
            record_date=record_date,
            summary=summary,
            sheet_name=args.sheet_name,
            allow_existing_output=True,
        )
    bridge_path = artifact_display_path(bridge_entry)
    project_relative_path = artifact_provider_relative_path(
        config,
        bridge_entry,
        slot=slot,
        date_value=record_date,
        title=title,
        slug=slug,
        fallback_path=bridge_path,
        explicit_project_relative_path=getattr(args, "project_relative_path", ""),
    )
    provider_parent_path = provider_parent_relative_path(project_relative_path)
    bridge_collaboration_mode = normalize_collaboration_mode(
        bridge_entry.get("collaboration_mode", "") if isinstance(bridge_entry, dict) else "",
        default="single-editor",
    )
    bridge_source_of_truth = normalize_source_of_truth(
        bridge_entry.get("source_of_truth", "") if isinstance(bridge_entry, dict) else "",
        default="auto",
    )
    bridge_artifact_id = normalize_optional_text(bridge_entry.get("id", ""))
    derived_from = [bridge_artifact_id] if bridge_artifact_id else []
    provider_root_id = config.provider_root_id if config.storage_provider == provider else ""
    provider_root_url = config.provider_root_url if config.storage_provider == provider else ""
    register_summary = normalize_optional_text(bridge_entry.get("summary", "")) or (args.summary.strip() if args.summary.strip() else source_summary(source_path))
    register_after_import = {
        "kind": artifact_kind,
        "title": title,
        "slot": slot,
        "date": record_date,
        "summary": register_summary,
        "project_relative_path": project_relative_path,
        "provider_item_kind": provider_item_kind,
        "provider_item_id": "<provider-item-id>",
        "provider_item_url": "<provider-item-url>",
        "derived_from": derived_from,
        "source_of_truth": "provider-native" if bridge_collaboration_mode == "multi-editor" else bridge_source_of_truth,
        "collaboration_mode": bridge_collaboration_mode,
    }
    plan = {
        "version": VERSION,
        "generated_on": date.today().isoformat(),
        "command": "artifact.import-plan",
        "project": project_payload(config),
        "provider_import": {
            "provider": provider,
            "provider_item_kind": provider_item_kind,
            "operation": "import-file",
            "title": title,
            "source_artifact_id": normalize_optional_text(source_entry.get("id", "")) if isinstance(source_entry, dict) else "",
            "artifact_kind": artifact_kind,
            "workflow_slot": slot,
            "bridge_format": target_format,
            "bridge_mime_type": provider_import_mime_type(provider_item_kind, target_format),
            "bridge_artifact_id": bridge_artifact_id,
            "bridge_path": bridge_path,
            "source_path": source_relative_path,
            "project_relative_path": project_relative_path,
            "provider_parent_relative_path": provider_parent_path,
            "provider_root_id": provider_root_id,
            "provider_root_url": provider_root_url,
            "register_after_import": register_after_import,
        },
    }
    plan_path = provider_import_plan_path(config, record_date=record_date, slug=slug, provider_item_kind=provider_item_kind)
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    refresh_kernel_state(config, event_type="artifact.import-plan", summary=f"Prepared {provider_item_kind} import plan `{title}`.")
    register_command = artifact_register_command_preview(
        config,
        artifact_kind=artifact_kind,
        title=title,
        slot=slot,
        date_value=record_date,
        summary=register_summary,
        project_relative_path=project_relative_path,
        provider_item_kind=provider_item_kind,
        derived_from=derived_from,
        source_of_truth="provider-native" if bridge_collaboration_mode == "multi-editor" else bridge_source_of_truth,
        collaboration_mode=bridge_collaboration_mode,
    )
    payload = {
        "command": "artifact.import-plan",
        "status": "ok",
        "project": project_payload(config),
        "provider_import": plan["provider_import"],
        "plan_path": plan_path.relative_to(config.root).as_posix(),
        "bridge_artifact": bridge_entry,
        "bridge_created": bridge_created,
        "register_command_preview": register_command,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    if locale_family(config.interaction_locale) == "zh":
        print(f"已生成 {provider_item_kind} 导入计划 {plan_path.relative_to(config.root).as_posix()}")
        print(f"  - 桥接文件: {bridge_path}")
        print(f"  - 后续登记命令: {register_command}")
    else:
        print(f"Prepared {provider_item_kind} import plan at {plan_path.relative_to(config.root).as_posix()}")
        print(f"  - bridge artifact: {bridge_path}")
        print(f"  - follow-up register command: {register_command}")
    return 0


def handle_workflow_command(config: ProjectConfig, args: argparse.Namespace) -> int:
    if args.workflow_command == "assess":
        return workflow_assess(config, args)
    if args.workflow_command == "scaffold":
        return workflow_scaffold(config, args)
    if args.workflow_command == "branch":
        return workflow_branch(config, args)
    if args.workflow_command == "close":
        return workflow_close(config, args)
    if args.workflow_command == "start":
        return workflow_start(config, args)
    raise AssertionError("unreachable")


def workflow_start(config: ProjectConfig, args: argparse.Namespace) -> int:
    """Composite command: assess -> scaffold -> branch -> intake in one step."""
    title = args.title or args.task
    assessment = workflow_assessment_payload(config, args.task)
    task_profile = assessment["task_profile"]
    recommended = assessment["recommended"]
    scaffolds = recommended["scaffolds"]
    created_scaffolds: dict[str, str] = {}

    for kind in scaffolds:
        scaffold_args = argparse.Namespace(
            kind=kind, title=title, slug=None, date=None, summary="",
            json=False, project_root=str(config.root),
        )
        try:
            workflow_scaffold(config, scaffold_args)
            slug = sanitize_slug(title)
            record_date = normalize_record_date(None)
            subdir = workflow_document_subdir(kind)
            relative_path = f"docs/workflows/{subdir}/{record_date}-{slug}.md"
            created_scaffolds[kind] = relative_path
        except SystemExit as exc:
            if "already exists" in str(exc):
                created_scaffolds[kind] = "already exists"
            else:
                raise

    branch_result: dict[str, str] = {}
    if not args.skip_branch and recommended.get("workspace_isolation") in ("branch", "worktree"):
        branch_payload = workflow_branch_payload(config, args.task, None, None)
        branch_args = argparse.Namespace(
            task=args.task, slug=None, create=True, base_branch=None,
            worktree_root=None, json=False, project_root=str(config.root),
        )
        try:
            workflow_branch(config, branch_args)
            branch_result = {
                "branch_name": branch_payload["branch_name"],
                "isolation": branch_payload["isolation"],
                "worktree_path": branch_payload.get("worktree_path", ""),
            }
        except SystemExit:
            branch_result = {"status": "error"}

    identity_key = f"workflow-start-{date.today().isoformat()}-{sanitize_slug(title)}"
    acceptance = list(args.acceptance) if args.acceptance else [
        f"Complete all scaffolded workflow documents: {', '.join(scaffolds) or 'none required'}"
    ]
    if scaffolds:
        validation = list(args.validation) if args.validation else ["validate scaffold documents exist"]
    else:
        validation = list(args.validation) if args.validation else []

    task_payload, code = capture_orchestration_task(
        config,
        source_kind="workflow-start",
        source_url="",
        identity_key=identity_key,
        event_kind="workflow-start",
        title=title,
        description=args.task,
        acceptance=acceptance,
        validation=validation,
        labels=args.label,
        risk_hints=[],
        priority=args.priority or "normal",
        error_on_duplicate=False,
    )
    task_id = task_payload.get("task", {}).get("id", "") or task_payload.get("trigger", {}).get("task_id", "")

    payload: dict[str, object] = {
        "command": "workflow.start",
        "status": "ok",
        "project": project_payload(config),
        "task_id": task_id,
        "task_title": title,
        "task_description": args.task,
        "assessment": {
            "multi_step": task_profile["multi_step"],
            "complex": task_profile["complex"],
        },
        "scaffolds_required": scaffolds,
        "scaffolds_created": created_scaffolds,
        "branch": branch_result,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0

    complexity = "complex" if task_profile["complex"] else "multi-step" if task_profile["multi_step"] else "simple"
    print(f"Workflow start for {config.data['project']['name']}")
    print(f"  Task: {title}")
    print(f"  Complexity: {complexity}")
    print(f"  Task ID: {task_id}")
    if created_scaffolds:
        print(f"  Scaffolds: {', '.join(f'{k}={v}' for k, v in created_scaffolds.items())}")
    if branch_result.get("branch_name"):
        print(f"  Branch: {branch_result['branch_name']} ({branch_result['isolation']})")
    print(f"  Next: work on the task, then run `sula orchestration close --task-id {task_id}`")
    return 0


def workflow_task_profile(task: str) -> dict[str, object]:
    normalized = normalize_optional_text(task)
    if not normalized:
        return {"task": "", "multi_step": False, "complex": False, "parallel_hint": False}
    lowered = normalized.lower()
    multi_step_markers = [
        " and ",
        " then ",
        "refactor",
        "migrate",
        "introduce",
        "design",
        "rollout",
        "audit",
        "schema",
        "workflow",
        "integration",
        "并且",
        "然后",
        "重构",
        "迁移",
        "设计",
        "上线",
        "审计",
        "流程",
        "集成",
    ]
    complex_markers = [
        "architecture",
        "contract",
        "adapter",
        "parallel",
        "platform",
        "policy",
        "design",
        "schema",
        "migration",
        "工作流",
        "架构",
        "协议",
        "适配",
        "并行",
        "策略",
        "迁移",
    ]
    parallel_markers = ["parallel", "subagent", "multi-agent", "并行", "多代理", "多 agent"]
    word_count = len(normalized.replace("，", " ").replace(",", " ").split())
    multi_step = word_count >= 10 or any(marker in lowered for marker in multi_step_markers)
    complex_task = multi_step or any(marker in lowered for marker in complex_markers)
    parallel_hint = any(marker in lowered for marker in parallel_markers)
    return {
        "task": normalized,
        "multi_step": multi_step,
        "complex": complex_task,
        "parallel_hint": parallel_hint,
    }


def workflow_assessment_payload(config: ProjectConfig, task: str) -> dict[str, object]:
    task_profile = workflow_task_profile(task)
    requires_spec = config.workflow_design_gate == "always" or (
        config.workflow_design_gate == "complex-only" and bool(task_profile["complex"])
    )
    requires_plan = config.workflow_plan_gate == "always" or (
        config.workflow_plan_gate == "multi-step" and bool(task_profile["multi_step"])
    )
    requires_review = (
        config.workflow_review_policy == "strict"
        or (config.workflow_review_policy == "task-checkpoints" and bool(task_profile["multi_step"]))
        or (config.workflow_review_policy == "batch" and bool(task_profile["task"]))
    )
    recommended_scaffolds: list[str] = []
    if requires_spec:
        recommended_scaffolds.append("spec")
    if requires_plan:
        recommended_scaffolds.append("plan")
    if requires_review:
        recommended_scaffolds.append("review")
    recommended_commands = [
        f'python3 scripts/sula.py workflow scaffold --project-root {shlex.quote(str(config.root))} --kind {kind} --title "<title>"'
        for kind in recommended_scaffolds
    ]
    effective_execution_mode = (
        "subagent-parallel"
        if config.workflow_execution_mode == "subagent-parallel" or bool(task_profile["parallel_hint"])
        else config.workflow_execution_mode
    )
    return {
        "task_profile": task_profile,
        "recommended": {
            "execution_mode": effective_execution_mode,
            "workspace_isolation": config.workflow_workspace_isolation,
            "testing_policy": config.workflow_testing_policy,
            "closeout_policy": config.workflow_closeout_policy,
            "requires_spec": requires_spec,
            "requires_plan": requires_plan,
            "requires_review": requires_review,
            "scaffolds": recommended_scaffolds,
            "commands": recommended_commands,
        },
    }


def workflow_assess(config: ProjectConfig, args: argparse.Namespace) -> int:
    assessment = workflow_assessment_payload(config, getattr(args, "task", "") or "")
    payload = {
        "command": "workflow.assess",
        "status": "ok",
        "project": project_payload(config),
        "workflow": {
            "pack": config.workflow_pack,
            "stage": config.workflow_stage,
            "docs_root": config.workflow_docs_root.relative_to(config.root).as_posix()
            if config.workflow_docs_root.is_relative_to(config.root)
            else str(config.workflow_docs_root),
            "execution_mode": config.workflow_execution_mode,
            "design_gate": config.workflow_design_gate,
            "plan_gate": config.workflow_plan_gate,
            "review_policy": config.workflow_review_policy,
            "workspace_isolation": config.workflow_workspace_isolation,
            "testing_policy": config.workflow_testing_policy,
            "closeout_policy": config.workflow_closeout_policy,
        },
        "assessment": assessment,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Workflow assessment for {config.data['project']['name']}")
    print(f"  Pack: {config.workflow_pack} ({config.workflow_stage})")
    print(f"  Execution mode: {assessment['recommended']['execution_mode']}")
    print(f"  Docs root: {payload['workflow']['docs_root']}")
    print(f"  Scaffolds: {', '.join(assessment['recommended']['scaffolds']) if assessment['recommended']['scaffolds'] else 'none'}")
    if assessment["recommended"]["commands"]:
        print("  Next commands:")
        for command in assessment["recommended"]["commands"]:
            print(f"    - {command}")
    return 0


def workflow_document_subdir(kind: str) -> str:
    mapping = {"spec": "specs", "plan": "plans", "review": "reviews"}
    return mapping[kind]


def workflow_scaffold_summary(config: ProjectConfig, kind: str, title: str, explicit_summary: str) -> str:
    if explicit_summary.strip():
        return explicit_summary.strip()
    zh = locale_family(config.content_locale) == "zh"
    labels = {
        "spec": "规格说明" if zh else "implementation spec",
        "plan": "执行计划" if zh else "execution plan",
        "review": "审查记录" if zh else "review record",
    }
    return (
        f"{config.data['project']['name']} 的 {labels[kind]}：{title}"
        if zh
        else f"{labels[kind]} for {config.data['project']['name']}: {title}"
    )


def workflow_scaffold(config: ProjectConfig, args: argparse.Namespace) -> int:
    ensure_artifact_catalog(config)
    kind = args.kind
    record_date = normalize_record_date(args.date)
    slug = sanitize_slug(args.slug or args.title)
    slot = artifact_slot_for_kind(config, kind)
    relative_path = (
        config.workflow_docs_root.relative_to(config.root) / workflow_document_subdir(kind) / f"{record_date}-{slug}.md"
        if config.workflow_docs_root.is_relative_to(config.root)
        else Path("docs/workflows") / workflow_document_subdir(kind) / f"{record_date}-{slug}.md"
    )
    output_path = config.root / relative_path
    if output_path.exists():
        raise SystemExit(f"Workflow document already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = workflow_scaffold_summary(config, kind, args.title, args.summary)
    output_path.write_text(render_workflow_template(config, kind, args.title, summary, record_date, slot), encoding="utf-8")
    entry = register_artifact_entry(
        config,
        path=relative_path.as_posix(),
        artifact_kind=kind,
        title=args.title,
        slot=slot,
        summary=summary,
        date_value=record_date,
        project_relative_path=relative_path.as_posix(),
        local_access_paths=[relative_path.as_posix()],
        provider_item_id="",
        provider_item_kind=default_provider_item_kind(config, has_local_path=True),
        provider_item_url="",
        derived_from=[],
        source_of_truth="workspace",
        collaboration_mode="single-editor",
        artifact_role="workspace-source",
        last_refreshed_at=current_utc_timestamp(),
        last_provider_sync_at="",
    )
    sync_status_handoff_runtime_fields(config, bump_last_updated=True)
    refresh_kernel_state(config, event_type="workflow.scaffold", summary=f"Created workflow {kind} `{args.title}`.")
    payload = {
        "command": "workflow.scaffold",
        "status": "ok",
        "project": project_payload(config),
        "workflow_document": {
            "kind": kind,
            "path": relative_path.as_posix(),
            "slot": slot,
            "summary": summary,
        },
        "artifact": entry,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Created workflow {kind} at {output_path}")
    return 0


def workflow_branch_payload(config: ProjectConfig, task: str, slug_override: str | None, base_branch_override: str | None) -> dict[str, object]:
    task_slug = sanitize_slug(slug_override or task)
    prefix = str(config.data["repository"]["working_branch_prefix"])
    branch_name = f"{prefix}{task_slug}" if prefix else task_slug
    base_branch = base_branch_override or normalize_optional_text(config.data["repository"]["primary_branch"]) or detect_primary_branch(config.root)
    if base_branch in NON_PATH_SENTINELS:
        base_branch = detect_primary_branch(config.root)
    isolation = config.workflow_workspace_isolation
    worktree_root = config.root.parent / f"{config.root.name}-{task_slug}"
    payload = {
        "task": task,
        "slug": task_slug,
        "isolation": isolation,
        "branch_name": branch_name,
        "base_branch": base_branch,
        "current_branch": detect_git_branch(config.root) if is_git_repository(config.root) else "n/a",
        "worktree_path": str(worktree_root),
        "create_command": "",
    }
    if isolation == "branch":
        payload["create_command"] = f"git switch -c {branch_name} {base_branch}"
    elif isolation == "worktree":
        payload["create_command"] = f"git worktree add {shlex.quote(str(worktree_root))} -b {branch_name} {base_branch}"
    return payload


def workflow_branch(config: ProjectConfig, args: argparse.Namespace) -> int:
    payload = workflow_branch_payload(config, args.task, args.slug, args.base_branch)
    if args.worktree_root:
        payload["worktree_path"] = str(Path(args.worktree_root).expanduser().resolve())
        if payload["isolation"] == "worktree":
            payload["create_command"] = f"git worktree add {shlex.quote(payload['worktree_path'])} -b {payload['branch_name']} {payload['base_branch']}"
    status = "planned"
    created_root = ""
    if args.create:
        if payload["isolation"] == "none":
            status = "noop"
        elif not is_git_repository(config.root):
            raise SystemExit("workflow branch creation requires a git repository")
        elif payload["isolation"] == "branch":
            completed = run_git(config.root, ["switch", "-c", str(payload["branch_name"]), str(payload["base_branch"])])
            if completed is None or completed.returncode != 0:
                raise SystemExit(completed.stderr.strip() if completed is not None else "git is not available")
            status = "created"
        elif payload["isolation"] == "worktree":
            worktree_path = Path(str(payload["worktree_path"]))
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            completed = run_git(
                config.root,
                ["worktree", "add", str(worktree_path), "-b", str(payload["branch_name"]), str(payload["base_branch"])],
            )
            if completed is None or completed.returncode != 0:
                raise SystemExit(completed.stderr.strip() if completed is not None else "git is not available")
            status = "created"
            created_root = str(worktree_path)
    if args.create and status == "created" and sync_status_handoff_runtime_fields(config, bump_last_updated=True):
        refresh_kernel_state(config, event_type="workflow.branch", summary=f"Created workflow branch `{payload['branch_name']}`.")
    wrapped = {
        "command": "workflow.branch",
        "status": status,
        "project": project_payload(config),
        "workflow_branch": {
            **payload,
            "created_root": created_root,
        },
    }
    if json_output_requested(args):
        emit_json(wrapped)
        return 0
    print(f"Workflow branch for {config.data['project']['name']}")
    print(f"  Isolation: {payload['isolation']}")
    print(f"  Branch: {payload['branch_name']}")
    if payload["isolation"] == "worktree":
        print(f"  Worktree: {payload['worktree_path']}")
    print(f"  Status: {status}")
    return 0


def workflow_artifact_matches_slug(config: ProjectConfig, item: dict[str, object], slug: str, kind: str) -> bool:
    if normalize_optional_text(item.get("kind", "")) != kind:
        return False
    path = normalize_optional_text(item.get("path", ""))
    docs_root = config.workflow_docs_root.relative_to(config.root).as_posix() if config.workflow_docs_root.is_relative_to(config.root) else "docs/workflows"
    return path.startswith(f"{docs_root}/") and slug in path


def workflow_close(config: ProjectConfig, args: argparse.Namespace) -> int:
    assessment = workflow_assessment_payload(config, args.task)
    slug = sanitize_slug(args.slug or args.task)
    catalog = load_artifact_catalog(config)
    required_kinds = list(assessment["recommended"]["scaffolds"])
    matched: dict[str, dict[str, object]] = {}
    for kind in required_kinds:
        for item in catalog.get("artifacts", []):
            if isinstance(item, dict) and workflow_artifact_matches_slug(config, item, slug, kind):
                matched[kind] = item
                break
    missing = [kind for kind in required_kinds if kind not in matched]
    if sync_status_handoff_runtime_fields(config, bump_last_updated=False):
        refresh_kernel_state(config)
    generate_memory_digest(
        config,
        argparse.Namespace(output=None, stdout=False, json=False),
        emit_output=False,
    )
    doctor_code = doctor(config, strict=bool(args.doctor_strict), emit_output=False)
    check_code = daily_check(config, emit_output=False)
    branch_name = detect_git_branch(config.root) if is_git_repository(config.root) else "n/a"
    clean = is_clean_git_worktree(config.root) if is_git_repository(config.root) else True
    primary_branch = normalize_optional_text(config.data["repository"]["primary_branch"]) or detect_primary_branch(config.root)
    blocked_reasons: list[str] = []
    if missing:
        blocked_reasons.append(f"missing workflow documents: {', '.join(missing)}")
    if check_code != 0:
        blocked_reasons.append("sula check is failing")
    if args.doctor_strict and doctor_code != 0:
        blocked_reasons.append("doctor --strict is failing")
    if config.workflow_workspace_isolation in {"branch", "worktree"} and is_git_repository(config.root) and branch_name == primary_branch:
        blocked_reasons.append(f"still on protected branch `{primary_branch}`")
    if blocked_reasons:
        status = "blocked"
    elif is_git_repository(config.root) and not clean:
        status = "pr-needed"
    else:
        status = "merge-ready"
    payload = {
        "command": "workflow.close",
        "status": status,
        "project": project_payload(config),
        "task": args.task,
        "slug": slug,
        "required_documents": required_kinds,
        "matched_documents": {
            kind: normalize_optional_text(item.get("path", ""))
            for kind, item in matched.items()
        },
        "missing_documents": missing,
        "git": {
            "is_repository": is_git_repository(config.root),
            "current_branch": branch_name,
            "primary_branch": primary_branch,
            "clean_worktree": clean,
        },
        "checks": {
            "check_passed": check_code == 0,
            "doctor_strict_required": bool(args.doctor_strict),
            "doctor_strict_passed": doctor_code == 0,
        },
        "issues": blocked_reasons,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0 if status != "blocked" else 1
    print(f"Workflow close for {config.data['project']['name']}")
    print(f"  Status: {status}")
    if blocked_reasons:
        for item in blocked_reasons:
            print(f"  - {item}")
    return 0 if status != "blocked" else 1


def handle_orchestration_command(config: ProjectConfig, args: argparse.Namespace) -> int:
    if args.orchestration_command == "status":
        return orchestration_status(config, args)
    if args.orchestration_command == "tasks":
        return orchestration_tasks(config, args)
    if args.orchestration_command == "timeline":
        return orchestration_timeline(config, args)
    if args.orchestration_command == "intake":
        return orchestration_intake(config, args)
    if args.orchestration_command == "trigger":
        return orchestration_trigger(config, args)
    if args.orchestration_command == "run":
        return orchestration_run(config, args)
    if args.orchestration_command == "close":
        return orchestration_close(config, args)
    if args.orchestration_command == "cancel":
        return orchestration_cancel(config, args)
    if args.orchestration_command == "stop-all":
        return orchestration_stop_all(config, args)
    if args.orchestration_command == "doctor":
        return orchestration_doctor(config, args)
    raise AssertionError("unreachable")


def orchestration_relative_path(config: ProjectConfig, path: Path) -> str:
    return path.relative_to(config.root).as_posix() if path.is_relative_to(config.root) else str(path)


def orchestration_config_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "enabled": config.orchestration_enabled,
        "mode": config.orchestration_mode,
        "task_source": config.orchestration_task_source,
        "runner": config.orchestration_runner,
        "runner_command": config.orchestration_runner_command,
        "runner_endpoint": config.orchestration_runner_endpoint,
        "runner_token_env": config.orchestration_runner_token_env,
        "tasks_path": orchestration_relative_path(config, config.orchestration_tasks_path),
        "provider_task_item_id": config.orchestration_provider_task_item_id,
        "provider_task_item_kind": config.orchestration_provider_task_item_kind,
        "provider_task_item_url": config.orchestration_provider_task_item_url,
        "workspace_root": orchestration_relative_path(config, config.orchestration_workspace_root),
        "workspace_mode": config.orchestration_workspace_mode,
        "trust_profile": config.orchestration_trust_profile,
        "allow_project_root_runner": config.orchestration_allow_project_root_runner,
        "max_concurrent_runs": config.orchestration_max_concurrent_runs,
        "max_retry_count": config.orchestration_max_retry_count,
        "max_run_minutes": config.orchestration_max_run_minutes,
        "daily_budget_minutes": config.orchestration_daily_budget_minutes,
        "unattended_risk_ceiling": config.orchestration_unattended_risk_ceiling,
        "require_human_approval_for": config.orchestration_require_human_approval_for,
        "status_surface": config.orchestration_status_surface,
        "verification_adapters": config.orchestration_verification_adapters,
        "remote_verification_policy": config.orchestration_remote_verification_policy,
        "agent_behavior": agent_behavior_payload(config),
    }


def orchestration_runs_path(config: ProjectConfig) -> Path:
    return config.orchestration_state_root / "runs.jsonl"


def orchestration_latest_path(config: ProjectConfig) -> Path:
    return config.orchestration_state_root / "latest.json"


def orchestration_tasks_snapshot_path(config: ProjectConfig) -> Path:
    return config.orchestration_state_root / "tasks.json"


def orchestration_budgets_path(config: ProjectConfig) -> Path:
    return config.orchestration_state_root / "budgets.json"


def orchestration_events_path(config: ProjectConfig) -> Path:
    return config.orchestration_events_path


def orchestration_active_path(config: ProjectConfig) -> Path:
    return config.orchestration_active_path


def orchestration_triggers_path(config: ProjectConfig) -> Path:
    return config.orchestration_state_root / "triggers.jsonl"


def orchestration_promotion_candidates_path(config: ProjectConfig) -> Path:
    return config.orchestration_state_root / "promotion-candidates.jsonl"


def automation_events_path(config: ProjectConfig) -> Path:
    return config.automation_state_root / "events.jsonl"


def automation_intents_path(config: ProjectConfig) -> Path:
    return config.automation_state_root / "intents.jsonl"


def automation_latest_path(config: ProjectConfig) -> Path:
    return config.automation_state_root / "latest.json"


def read_jsonl_objects(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def append_jsonl_object(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def write_jsonl_objects(path: Path, payloads: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(payload, ensure_ascii=True) + "\n" for payload in payloads),
        encoding="utf-8",
    )


def read_orchestration_runs(config: ProjectConfig) -> list[dict[str, object]]:
    path = orchestration_runs_path(config)
    return read_jsonl_objects(path)


def append_orchestration_run(config: ProjectConfig, run: dict[str, object]) -> None:
    append_jsonl_object(orchestration_runs_path(config), run)


def write_orchestration_latest(config: ProjectConfig, payload: dict[str, object]) -> None:
    config.orchestration_state_root.mkdir(parents=True, exist_ok=True)
    orchestration_latest_path(config).write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_orchestration_active(config: ProjectConfig) -> dict[str, object]:
    payload = load_json_file(orchestration_active_path(config), default={})
    return payload if isinstance(payload, dict) else {}


def visible_orchestration_active(payload: dict[str, object]) -> dict[str, object]:
    active_event = payload.get("active", {}) if isinstance(payload, dict) else {}
    if not isinstance(active_event, dict):
        return {}
    state = normalize_optional_text(active_event.get("state", "")).lower()
    if state not in ORCHESTRATION_VISIBLE_ACTIVE_STATES:
        return {}
    return payload


def write_orchestration_active(config: ProjectConfig, payload: dict[str, object]) -> None:
    config.orchestration_state_root.mkdir(parents=True, exist_ok=True)
    orchestration_active_path(config).write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def append_orchestration_event(config: ProjectConfig, event: dict[str, object]) -> None:
    append_jsonl_object(orchestration_events_path(config), event)


def role_status_line(role: str, role_payload: dict[str, object], state: str = "pending") -> str:
    provider = normalize_optional_text(role_payload.get("provider", "unknown")) or "unknown"
    model = normalize_optional_text(role_payload.get("model", "unknown")) or "unknown"
    effort = normalize_optional_text(role_payload.get("reasoning_effort", ""))
    access = "write-enabled" if bool(role_payload.get("write_access", False)) else "read-only"
    parts = [f"{role.title()}: {provider}:{model}"]
    if effort:
        parts.append(effort)
    parts.extend([access, state])
    return " / ".join(parts)


def runner_effort_for_role(config: ProjectConfig, role_payload: dict[str, object]) -> str:
    """Return the runner-native effort label for a routed role."""
    effort = normalize_optional_text(role_payload.get("reasoning_effort", ""))
    if not effort:
        return "unknown"
    command = config.orchestration_runner_command
    if command:
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        for index, part in enumerate(parts):
            if part == "--effort" and index + 1 < len(parts):
                return parts[index + 1]
            if part.startswith("--effort="):
                return part.split("=", 1)[1]
    provider = normalize_optional_text(role_payload.get("provider", ""))
    if effort == "xhigh" and ("claude" in command or provider in {"claudecode", "deepseek"}):
        return "max"
    return effort


def role_compact_label(
    config: ProjectConfig,
    role_payload: dict[str, object],
    *,
    provider_default: str = "unknown",
    include_runner_effort: bool = False,
) -> str:
    provider = normalize_optional_text(role_payload.get("provider", "")) or provider_default
    if provider == "host":
        provider = "codex"
    model = normalize_optional_text(role_payload.get("model", "")) or "unknown"
    effort = normalize_optional_text(role_payload.get("reasoning_effort", "")) or "unknown"
    if include_runner_effort:
        return f"{provider}/{model}/{effort}/{runner_effort_for_role(config, role_payload)}"
    return f"{provider}/{model}/{effort}"


def short_orchestration_run_id(run_id: str) -> str:
    match = re.search(r"T(\d{4})", run_id)
    if match:
        return match.group(1)
    return run_id[-6:] if run_id else "none"


def parse_sula_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def latest_orchestration_execution_run(config: ProjectConfig) -> dict[str, object]:
    runs = read_orchestration_runs(config)
    if runs:
        def run_key(run: dict[str, object]) -> datetime:
            return parse_sula_timestamp(normalize_optional_text(run.get("started_at", ""))) or datetime.min.replace(tzinfo=timezone.utc)

        return max(runs, key=run_key)
    latest = load_json_file(orchestration_latest_path(config), default={})
    if isinstance(latest, dict) and isinstance(latest.get("latest_run"), dict):
        return latest["latest_run"]
    return {}


def orchestration_tasks_done_label(tasks: list[dict[str, object]], run: dict[str, object]) -> str:
    status = normalize_optional_text(run.get("status", "")).lower()
    latest_task_id = normalize_optional_text(run.get("task_id", ""))
    terminal = {"accepted", "completed", "complete", "closed", "human-review", "succeeded", "success"}
    if tasks:
        done = 0
        for task in tasks:
            task_state = normalize_optional_text(task.get("state", task.get("status", ""))).lower()
            task_id = normalize_optional_text(task.get("id", task.get("task_id", "")))
            if task_state in terminal or (latest_task_id and task_id == latest_task_id and status in terminal):
                done += 1
        return f"{done}/{len(tasks)} done"
    return f"{1 if status in terminal else 0}/1 done"


def orchestration_elapsed_label(run: dict[str, object]) -> str:
    metrics = run.get("metrics", {})
    if isinstance(metrics, dict) and isinstance(metrics.get("runtime_minutes"), (int, float)) and metrics.get("runtime_minutes", 0) > 0:
        return f"{int(metrics.get('runtime_minutes', 0))}m"
    started = parse_sula_timestamp(normalize_optional_text(run.get("started_at", "")))
    ended = parse_sula_timestamp(normalize_optional_text(run.get("ended_at", "")))
    if started and ended:
        seconds = max(0, int((ended - started).total_seconds()))
        return f"{seconds}s" if seconds < 60 else f"{seconds // 60}m"
    return "0s"


def orchestration_cost_label(run: dict[str, object]) -> str:
    metrics = run.get("metrics", {})
    cost = metrics.get("cost_usd") if isinstance(metrics, dict) else 0
    return f"${float(cost or 0):.3f}"


def orchestration_last_event_label(run: dict[str, object]) -> str:
    blocked = run.get("blocked_reasons")
    if isinstance(blocked, list) and blocked:
        return normalize_optional_text(blocked[-1])
    evidence = run.get("validation_evidence")
    if isinstance(evidence, list) and evidence:
        latest = evidence[-1]
        if isinstance(latest, dict):
            return normalize_optional_text(latest.get("summary", latest.get("kind", ""))) or "evidence recorded"
    events = run.get("runner_events")
    if isinstance(events, list) and events:
        latest = events[-1]
        if isinstance(latest, dict):
            return normalize_optional_text(latest.get("event", "")) or "runner event"
    return normalize_optional_text(run.get("status", "")) or "idle"


def orchestration_next_label(status: str) -> str:
    normalized = status.lower()
    if normalized == "idle":
        return "none"
    if normalized == "accepted":
        return "done"
    if normalized in {"running", "active"}:
        return "wait"
    if normalized in {"blocked", "failed", "error"}:
        return "repair"
    if normalized in {"queued", "pending", "planned"}:
        return "run"
    return "review"


def orchestration_compact_status_line(config: ProjectConfig, *, ctx: str = "unknown") -> str:
    tasks, _issues = load_orchestration_tasks(config)
    run = latest_orchestration_execution_run(config)
    run_status = normalize_optional_text(run.get("status", "")) or "idle"
    status = run_status if run_status.lower() in ORCHESTRATION_VISIBLE_ACTIVE_STATES else "idle"
    reviewer = agent_routing_role_payload(config, "reviewer")
    planner = agent_routing_role_payload(config, "planner")
    main_role = reviewer or planner
    executor = agent_routing_role_payload(config, "executor")
    workspace = normalize_optional_text(run.get("workspace_mode", "")) or config.orchestration_workspace_mode
    last_prefix = "Last run" if status == "idle" and normalize_optional_text(run.get("run_id", "")) else "Run"
    return (
        f"Sula: {status} | {last_prefix}: {short_orchestration_run_id(normalize_optional_text(run.get('run_id', '')))}"
        f"{'/' + run_status if last_prefix == 'Last run' else ''} | "
        f"Tasks: {orchestration_tasks_done_label(tasks, run)} | Risk: {normalize_optional_text(run.get('risk', 'unknown')) or 'unknown'} | "
        f"Main: {role_compact_label(config, main_role, provider_default='codex')} | Ctx: {ctx} | "
        f"Executor: {role_compact_label(config, executor, include_runner_effort=True)} | Workspace: {workspace or 'unknown'} | "
        f"Elapsed: {orchestration_elapsed_label(run)} | Cost: {orchestration_cost_label(run)} | "
        f"Last: {orchestration_last_event_label(run)} | Next: {orchestration_next_label(status)}"
    )


def build_orchestration_stage_event(
    config: ProjectConfig,
    *,
    run: dict[str, object],
    task: dict[str, object] | None,
    stage: str,
    role: str,
    state: str,
    summary: str,
    next_action: str,
    routing_cycle: int = 1,
) -> dict[str, object]:
    role_payload = agent_routing_role_payload(config, role)
    now = current_utc_timestamp()
    identity = "|".join(
        [
            normalize_optional_text(run.get("run_id", "")),
            normalize_optional_text(task.get("id", "")) if task else normalize_optional_text(run.get("task_id", "")),
            stage,
            role,
            now,
        ]
    )
    workspace = normalize_optional_text(run.get("workspace_path", ""))
    return {
        "event_id": f"evt:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}",
        "timestamp": now,
        "run_id": normalize_optional_text(run.get("run_id", "")),
        "task_id": normalize_optional_text(task.get("id", "")) if task else normalize_optional_text(run.get("task_id", "")),
        "task_title": normalize_optional_text(task.get("title", "")) if task else "",
        "stage": stage,
        "role": role,
        "provider": normalize_optional_text(role_payload.get("provider", "unknown")) or "unknown",
        "model": normalize_optional_text(role_payload.get("model", "unknown")) or "unknown",
        "reasoning_effort": normalize_optional_text(role_payload.get("reasoning_effort", "")),
        "state": state,
        "summary": summary,
        "next_action": next_action,
        "write_access": bool(role_payload.get("write_access", False)),
        "workspace": workspace,
        "routing_cycle": routing_cycle,
        "cost_estimate": {
            "tokens_input": 0,
            "tokens_output": 0,
            "cost_usd": None,
        },
    }


def record_orchestration_stage(
    config: ProjectConfig,
    *,
    run: dict[str, object],
    task: dict[str, object] | None,
    stage: str,
    role: str,
    state: str,
    summary: str,
    next_action: str,
    routing_cycle: int = 1,
) -> dict[str, object]:
    event = build_orchestration_stage_event(
        config,
        run=run,
        task=task,
        stage=stage,
        role=role,
        state=state,
        summary=summary,
        next_action=next_action,
        routing_cycle=routing_cycle,
    )
    append_orchestration_event(config, event)
    write_orchestration_active(
        config,
        {
            "version": VERSION,
            "updated_at": current_utc_timestamp(),
            "active": event,
            "agent_routing": agent_routing_config_payload(config),
        },
    )
    return event


def write_orchestration_task_snapshot(config: ProjectConfig, tasks: list[dict[str, object]], issues: list[str]) -> None:
    config.orchestration_state_root.mkdir(parents=True, exist_ok=True)
    orchestration_tasks_snapshot_path(config).write_text(
        json.dumps(
            {
                "version": VERSION,
                "updated_at": current_utc_timestamp(),
                "task_source": config.orchestration_task_source,
                "tasks_path": orchestration_relative_path(config, config.orchestration_tasks_path),
                "issues": issues,
                "tasks": tasks,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )


def append_orchestration_trigger(config: ProjectConfig, trigger: dict[str, object]) -> None:
    append_jsonl_object(orchestration_triggers_path(config), trigger)


def append_orchestration_promotion_candidate(config: ProjectConfig, candidate: dict[str, object]) -> None:
    append_jsonl_object(orchestration_promotion_candidates_path(config), candidate)


def count_jsonl_records(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def automation_intent_to_raw_task(config: ProjectConfig, intent: dict[str, object]) -> dict[str, object]:
    return {
        "id": normalize_optional_text(intent.get("task_id", "")) or f"automation:{sanitize_slug(normalize_optional_text(intent.get('identity_key', 'intent')))}",
        "source_kind": "automation",
        "source_url": normalize_optional_text(intent.get("source_url", "")),
        "identifier": normalize_optional_text(intent.get("identity_key", "")),
        "title": normalize_optional_text(intent.get("title", "")) or "Review Sula automation intent",
        "description": normalize_optional_text(intent.get("description", "")),
        "state": normalize_optional_text(intent.get("state", "open")) or "open",
        "priority": normalize_optional_text(intent.get("priority", "normal")) or "normal",
        "labels": normalize_task_string_list(intent.get("labels")),
        "blocked_by": normalize_task_string_list(intent.get("blocked_by")),
        "project_slug": config.data["project"]["slug"],
        "acceptance_criteria": normalize_task_string_list(intent.get("acceptance_criteria")),
        "validation_requirements": normalize_task_string_list(intent.get("validation_requirements")),
        "risk": normalize_optional_text(intent.get("risk", "")),
        "risk_hints": normalize_task_string_list(intent.get("risk_hints")),
        "created_at": normalize_optional_text(intent.get("created_at", "")),
        "updated_at": normalize_optional_text(intent.get("updated_at", "")),
    }


def load_automation_intents(config: ProjectConfig) -> list[dict[str, object]]:
    return read_jsonl_objects(automation_intents_path(config))


def load_automation_intent_tasks(config: ProjectConfig) -> tuple[list[dict[str, object]], list[str]]:
    if not config.automation_enabled or not config.automation_auto_plan:
        return [], []
    raw_tasks = [
        automation_intent_to_raw_task(config, intent)
        for intent in load_automation_intents(config)
        if normalize_orchestration_task_state(intent.get("state", "open")) in {"open", "running"}
    ]
    tasks = [normalize_orchestration_task(config, item, index) for index, item in enumerate(raw_tasks)]
    return tasks, []


def automation_status_payload(config: ProjectConfig) -> dict[str, object]:
    events = read_jsonl_objects(automation_events_path(config))
    intents = load_automation_intents(config)
    runs = read_orchestration_runs(config)
    automation_run_ids = {
        normalize_optional_text(intent.get("last_run_id", ""))
        for intent in intents
        if normalize_optional_text(intent.get("last_run_id", ""))
    }
    pending_intents = [
        intent
        for intent in intents
        if normalize_optional_text(intent.get("state", "open")) == "open"
    ]
    return {
        "config": automation_config_payload(config),
        "events": {
            "total": len(events),
            "events_path": orchestration_relative_path(config, automation_events_path(config)),
            "latest": events[-1] if events else {},
        },
        "intents": {
            "total": len(intents),
            "pending": len(pending_intents),
            "intents_path": orchestration_relative_path(config, automation_intents_path(config)),
            "latest": intents[-1] if intents else {},
        },
        "runs": {
            "linked": sum(1 for run in runs if normalize_optional_text(run.get("run_id", "")) in automation_run_ids),
        },
    }


def automation_identity_key(source_kind: str, event_kind: str, identity_key: str, title: str) -> str:
    raw = normalize_optional_text(identity_key) or f"{event_kind}:{title}"
    return f"{source_kind}:{event_kind}:{raw}"


def automation_classify_event(config: ProjectConfig, event: dict[str, object]) -> dict[str, object] | None:
    event_kind = normalize_optional_text(event.get("event_kind", ""))
    payload = event.get("payload", {})
    payload = payload if isinstance(payload, dict) else {}
    identity_key = normalize_optional_text(event.get("identity_key", ""))
    now = current_utc_timestamp()
    base = {
        "version": VERSION,
        "created_at": now,
        "updated_at": now,
        "event_id": normalize_optional_text(event.get("event_id", "")),
        "source_kind": normalize_optional_text(event.get("source_kind", "")),
        "source_url": normalize_optional_text(event.get("source_url", "")),
        "identity_key": identity_key,
        "task_id": f"automation:{sanitize_slug(identity_key)}",
        "state": "open",
        "priority": "normal",
        "risk": "low",
        "labels": ["automation"],
        "blocked_by": [],
    }
    if event_kind == "check.failed":
        issues = normalize_task_string_list(payload.get("issues"))
        repair_commands = normalize_task_string_list(payload.get("repair_commands"))
        return {
            **base,
            "title": "Repair failed Sula check",
            "description": "\n".join(issues[:10]),
            "acceptance_criteria": ["Sula check passes"],
            "validation_requirements": repair_commands or ["python3 scripts/sula.py check --project-root . passes"],
            "labels": ["automation", "sula-check"],
        }
    if event_kind == "doctor.failed":
        issues = normalize_task_string_list(payload.get("issues"))
        return {
            **base,
            "title": "Repair failed Sula doctor",
            "description": "\n".join(issues[:10]),
            "acceptance_criteria": ["Sula doctor strict passes"],
            "validation_requirements": ["python3 scripts/sula.py doctor --project-root . --strict passes"],
            "labels": ["automation", "sula-doctor"],
        }
    if event_kind in {"query.freshness", "artifact.locate.freshness"}:
        refresh = payload.get("refresh", {})
        errors = refresh.get("errors", []) if isinstance(refresh, dict) else []
        if not errors:
            return None
        return {
            **base,
            "title": "Review provider freshness refresh errors",
            "description": "\n".join(normalize_task_string_list(errors)[:10]),
            "acceptance_criteria": ["Provider freshness errors are resolved or documented"],
            "validation_requirements": ["rerun the freshness query or artifact locate command"],
            "labels": ["automation", "provider-refresh"],
        }
    if event_kind == "status.truth-risk":
        risks = normalize_task_string_list(payload.get("risks"))
        return {
            **base,
            "title": "Review Sula status truth-source risks",
            "description": "\n".join(risks[:10]),
            "acceptance_criteria": ["Truth-source risks are resolved or documented"],
            "validation_requirements": ["python3 scripts/sula.py status --project-root . --json shows expected truth-source state"],
            "labels": ["automation", "status", "truth-source"],
        }
    if event_kind.endswith(".failed"):
        return {
            **base,
            "title": f"Review failed Sula command: {normalize_optional_text(event.get('title', 'command'))}",
            "description": normalize_optional_text(event.get("summary", "")),
            "acceptance_criteria": ["The failed command is understood and resolved"],
            "validation_requirements": ["rerun the failed command successfully or document the blocker"],
            "labels": ["automation", "sula-command"],
            "risk": "medium",
        }
    return None


def automation_write_latest(config: ProjectConfig, payload: dict[str, object]) -> None:
    config.automation_state_root.mkdir(parents=True, exist_ok=True)
    automation_latest_path(config).write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def automation_append_intent(config: ProjectConfig, intent: dict[str, object]) -> tuple[dict[str, object], bool]:
    intents = load_automation_intents(config)
    task_id = normalize_optional_text(intent.get("task_id", ""))
    for existing in intents:
        if normalize_optional_text(existing.get("task_id", "")) == task_id:
            return existing, False
    append_jsonl_object(automation_intents_path(config), intent)
    return intent, True


def automation_resolve_recovered_intents(config: ProjectConfig, event: dict[str, object]) -> list[dict[str, object]]:
    event_kind = normalize_optional_text(event.get("event_kind", ""))
    label = ""
    if event_kind == "check.passed":
        label = "sula-check"
    elif event_kind == "doctor.passed":
        label = "sula-doctor"
    if not label:
        return []
    intents = load_automation_intents(config)
    if not intents:
        return []
    now = current_utc_timestamp()
    resolved: list[dict[str, object]] = []
    updated: list[dict[str, object]] = []
    changed = False
    for intent in intents:
        item = dict(intent)
        labels = normalize_task_string_list(item.get("labels"))
        state = normalize_orchestration_task_state(item.get("state", "open"))
        if label in labels and state in {"open", "running"}:
            item["state"] = "accepted"
            item["updated_at"] = now
            item["resolved_at"] = now
            item["resolution_event_id"] = normalize_optional_text(event.get("event_id", ""))
            item["resolution_reason"] = f"{event_kind} recovered"
            resolved.append(item)
            changed = True
        updated.append(item)
    if changed:
        write_jsonl_objects(automation_intents_path(config), updated)
    return resolved


def automation_dispatch_intent(config: ProjectConfig, intent: dict[str, object]) -> dict[str, object]:
    task = normalize_orchestration_task(config, automation_intent_to_raw_task(config, intent), 0)
    reasons: list[str] = []
    if config.automation_mode != "execute" or not config.automation_auto_dispatch:
        reasons.append("automation dispatch is not enabled")
    if not config.orchestration_enabled:
        reasons.append("orchestration is disabled")
    if risk_rank(normalize_optional_text(task.get("risk", "high"))) > risk_rank(config.automation_risk_ceiling):
        reasons.append(f"task risk `{task.get('risk')}` exceeds automation risk ceiling `{config.automation_risk_ceiling}`")
    approval_categories = approval_categories_for_task(task)
    blocked_categories = [item for item in approval_categories if item in config.automation_approval_required_for]
    if blocked_categories:
        reasons.append("human approval is required for: " + ", ".join(blocked_categories))
    if task.get("blocked_reasons"):
        reasons.extend(str(item) for item in task.get("blocked_reasons", []))
    if reasons:
        return {"status": "queued", "dispatch_blocked_reasons": reasons}
    run_payload, run_code = create_orchestration_run_payload(config, normalize_optional_text(task.get("id", "")))
    run = run_payload.get("run", {}) if isinstance(run_payload, dict) else {}
    return {
        "status": "dispatched" if run_code == 0 else "dispatch-failed",
        "run_status": run_payload.get("status", "blocked") if isinstance(run_payload, dict) else "blocked",
        "run_id": normalize_optional_text(run.get("run_id", "")) if isinstance(run, dict) else "",
    }


def automation_observe_event(
    config: ProjectConfig,
    *,
    source_kind: str,
    event_kind: str,
    title: str,
    summary: str,
    identity_key: str = "",
    source_url: str = "",
    payload: dict[str, object] | None = None,
) -> dict[str, object] | None:
    source = normalize_optional_text(source_kind).strip().lower()
    if not config.automation_enabled or source not in config.automation_event_sources:
        return None
    now = current_utc_timestamp()
    identity = automation_identity_key(source, event_kind, identity_key, title)
    event = {
        "version": VERSION,
        "event_id": f"event:{hashlib.sha256((identity + now).encode('utf-8')).hexdigest()[:16]}",
        "created_at": now,
        "source_kind": source,
        "source_url": normalize_optional_text(source_url),
        "event_kind": event_kind,
        "identity_key": identity,
        "title": title,
        "summary": summary,
        "payload": payload or {},
    }
    append_jsonl_object(automation_events_path(config), event)
    result: dict[str, object] = {"event": event, "intent": {}, "dispatch": {}, "resolved_intents": []}
    resolved_intents = automation_resolve_recovered_intents(config, event)
    if resolved_intents:
        result["resolved_intents"] = resolved_intents
    if config.automation_mode != "observe" and config.automation_auto_intake:
        intent = automation_classify_event(config, event)
        if intent:
            stored_intent, created = automation_append_intent(config, intent)
            result["intent"] = {**stored_intent, "created": created}
            if created:
                dispatch = automation_dispatch_intent(config, stored_intent)
                result["dispatch"] = dispatch
                if dispatch.get("run_id"):
                    stored_intent["last_run_id"] = normalize_optional_text(dispatch.get("run_id", ""))
    automation_write_latest(
        config,
        {
            "version": VERSION,
            "updated_at": now,
            "latest_event": event,
            "latest_intent": result.get("intent", {}),
            "latest_dispatch": result.get("dispatch", {}),
        },
    )
    return result


def print_sula_activity_feedback(config: ProjectConfig, result: dict[str, object] | None) -> None:
    if not result:
        return
    zh = locale_family(config.interaction_locale) == "zh"
    event = result.get("event", {})
    intent = result.get("intent", {})
    dispatch = result.get("dispatch", {})
    resolved = result.get("resolved_intents", [])
    if isinstance(event, dict) and event:
        if zh:
            print(f"Sula 反馈: 已记录 `{event.get('event_kind', 'event')}` 事件。")
        else:
            print(f"Sula activity: recorded `{event.get('event_kind', 'event')}`.")
    if isinstance(intent, dict) and intent:
        state = normalize_optional_text(intent.get("state", "open")) or "open"
        title = normalize_optional_text(intent.get("title", "intent")) or "intent"
        created = bool(intent.get("created"))
        if zh:
            verb = "新增" if created else "复用"
            print(f"Sula 反馈: 已{verb}意图 `{title}`，状态 `{state}`。")
        else:
            verb = "created" if created else "reused"
            print(f"Sula activity: {verb} intent `{title}` with state `{state}`.")
    if isinstance(dispatch, dict) and dispatch:
        status = normalize_optional_text(dispatch.get("status", "")) or "queued"
        run_id = normalize_optional_text(dispatch.get("run_id", ""))
        if zh:
            suffix = f"，run `{run_id}`" if run_id else ""
            print(f"Sula 反馈: 自动派发状态 `{status}`{suffix}。")
        else:
            suffix = f", run `{run_id}`" if run_id else ""
            print(f"Sula activity: automatic dispatch `{status}`{suffix}.")
    if isinstance(resolved, list) and resolved:
        if zh:
            print(f"Sula 反馈: 已关闭 {len(resolved)} 个恢复后的自动化意图。")
        else:
            print(f"Sula activity: resolved {len(resolved)} recovered automation intent(s).")


def risk_rank(risk: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(risk, 3)


def normalize_task_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_agent_routing_role(role: str, raw: dict[str, object] | None) -> dict[str, object]:
    defaults = default_agent_routing_roles().get(role, {})
    source = raw if isinstance(raw, dict) else {}
    provider = normalize_optional_text(source.get("provider", defaults.get("provider", ""))) or normalize_optional_text(defaults.get("provider", ""))
    model = normalize_optional_text(source.get("model", defaults.get("model", ""))) or normalize_optional_text(defaults.get("model", ""))
    reasoning_effort = normalize_optional_text(source.get("reasoning_effort", defaults.get("reasoning_effort", "")))
    workspace_mode = normalize_workflow_choice(
        source.get("workspace_mode", defaults.get("workspace_mode", "none")),
        ORCHESTRATION_WORKSPACE_MODE_CHOICES,
        normalize_optional_text(defaults.get("workspace_mode", "none")) or "none",
    )
    return {
        "provider": provider,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "write_access": bool(source.get("write_access", defaults.get("write_access", False))),
        "workspace_mode": workspace_mode,
    }


def normalize_agent_routing_roles(raw_roles: dict[str, object]) -> dict[str, dict[str, object]]:
    roles: dict[str, dict[str, object]] = {}
    for role in AGENT_ROUTING_ROLE_CHOICES:
        raw = raw_roles.get(role, {}) if isinstance(raw_roles, dict) else {}
        roles[role] = normalize_agent_routing_role(role, raw if isinstance(raw, dict) else {})
    return roles


def agent_routing_role_payload(config: ProjectConfig, role: str) -> dict[str, object]:
    return config.agent_routing_roles.get(role, normalize_agent_routing_role(role, {}))


def normalize_orchestration_task_state(raw: object) -> str:
    state = normalize_optional_text(raw).strip().lower()
    if state in {"todo", "open", "ready", "planned", "backlog"}:
        return "open"
    if state in {"blocked", "needs-info", "waiting"}:
        return "blocked"
    if state in {"running", "in-progress", "active"}:
        return "running"
    if state in {"done", "closed", "accepted", "complete", "completed"}:
        return "accepted"
    if state in {"failed", "rejected"}:
        return "failed"
    return state or "open"


def approval_categories_for_task(task: dict[str, object]) -> list[str]:
    haystack = " ".join(
        [
            normalize_optional_text(task.get("title", "")),
            normalize_optional_text(task.get("description", "")),
            " ".join(normalize_task_string_list(task.get("labels"))),
            " ".join(normalize_task_string_list(task.get("risk_hints"))),
        ]
    ).lower()
    categories: list[str] = []
    markers = {
        "release": ["release", "deploy", "rollout", "发布", "上线"],
        "security": ["security", "secret", "auth", "permission", "credential", "安全", "密钥", "认证", "权限"],
        "provider-write": ["provider-write", "google drive write", "write provider", "写入 provider", "写入 google"],
        "destructive": ["delete", "remove", "drop", "reset", "destructive", "删除", "清空", "重置"],
    }
    for category, terms in markers.items():
        if any(term in haystack for term in terms):
            categories.append(category)
    return categories


def classify_orchestration_task_risk(task: dict[str, object]) -> str:
    explicit = normalize_optional_text(task.get("risk", "")).strip().lower()
    if explicit in ORCHESTRATION_RISK_CHOICES:
        return explicit
    haystack = " ".join(
        [
            normalize_optional_text(task.get("title", "")),
            normalize_optional_text(task.get("description", "")),
            " ".join(normalize_task_string_list(task.get("labels"))),
            " ".join(normalize_task_string_list(task.get("risk_hints"))),
        ]
    ).lower()
    if approval_categories_for_task(task) or any(term in haystack for term in ["migration", "schema", "data mutation", "release", "security"]):
        return "high"
    if any(term in haystack for term in ["code", "refactor", "integration", "adapter", "sync", "runner", "代码", "重构", "集成", "适配"]):
        return "medium"
    return "low"


def normalize_orchestration_task(config: ProjectConfig, raw: dict[str, object], index: int) -> dict[str, object]:
    identifier = normalize_optional_text(raw.get("identifier", "")) or normalize_optional_text(raw.get("id", "")) or f"local-{index + 1}"
    task_id = normalize_optional_text(raw.get("id", "")) or f"local:{sanitize_slug(identifier)}"
    state = normalize_orchestration_task_state(raw.get("state", "open"))
    task = {
        "id": task_id,
        "source_kind": normalize_optional_text(raw.get("source_kind", "local-task")) or "local-task",
        "source_url": normalize_optional_text(raw.get("source_url", "")),
        "identifier": identifier,
        "title": normalize_optional_text(raw.get("title", "")) or identifier,
        "description": normalize_optional_text(raw.get("description", "")),
        "state": state,
        "priority": normalize_optional_text(raw.get("priority", "normal")) or "normal",
        "labels": normalize_task_string_list(raw.get("labels")),
        "blocked_by": normalize_task_string_list(raw.get("blocked_by")),
        "project_slug": normalize_optional_text(raw.get("project_slug", config.data["project"]["slug"])),
        "acceptance_criteria": normalize_task_string_list(raw.get("acceptance_criteria")),
        "validation_requirements": normalize_task_string_list(raw.get("validation_requirements")),
        "risk": normalize_optional_text(raw.get("risk", "")),
        "risk_hints": normalize_task_string_list(raw.get("risk_hints")),
        "created_at": normalize_optional_text(raw.get("created_at", "")),
        "updated_at": normalize_optional_text(raw.get("updated_at", "")),
        "provider": normalize_optional_text(raw.get("provider", "")),
        "provider_item_id": normalize_optional_text(raw.get("provider_item_id", "")),
        "provider_item_kind": normalize_optional_text(raw.get("provider_item_kind", "")),
        "provider_item_url": normalize_optional_text(raw.get("provider_item_url", "")),
        "provider_title": normalize_optional_text(raw.get("provider_title", "")),
        "provider_modified_at": normalize_optional_text(raw.get("provider_modified_at", "")),
    }
    risk = classify_orchestration_task_risk(task)
    approval_categories = approval_categories_for_task(task)
    blocked_reasons: list[str] = []
    if state == "blocked":
        blocked_reasons.append("task source marks this task blocked")
    if state not in {"open", "running"}:
        blocked_reasons.append(f"task state is terminal or not dispatchable: {state}")
    if task["blocked_by"]:
        blocked_reasons.append("task has unresolved blockers")
    if not task["acceptance_criteria"]:
        blocked_reasons.append("missing acceptance criteria")
    if risk_rank(risk) > risk_rank(config.orchestration_unattended_risk_ceiling):
        blocked_reasons.append(f"risk `{risk}` exceeds unattended ceiling `{config.orchestration_unattended_risk_ceiling}`")
    required_approvals = [item for item in approval_categories if item in config.orchestration_require_human_approval_for]
    if required_approvals:
        blocked_reasons.append("requires human approval for: " + ", ".join(required_approvals))
    task["risk"] = risk
    task["approval_categories"] = approval_categories
    task["eligible"] = not blocked_reasons
    task["blocked_reasons"] = blocked_reasons
    return task


def load_local_orchestration_tasks(config: ProjectConfig) -> tuple[list[dict[str, object]], list[str]]:
    issues: list[str] = []
    path = config.orchestration_tasks_path
    if not path.exists():
        return [], []
    if not path.is_relative_to(config.root):
        return [], [f"local task file must stay inside project root: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"invalid local task JSON: {orchestration_relative_path(config, path)} ({exc})"]
    raw_tasks = data.get("tasks", []) if isinstance(data, dict) else data
    if not isinstance(raw_tasks, list):
        return [], ["local task file must contain a JSON array or an object with a `tasks` array"]
    tasks: list[dict[str, object]] = []
    for index, item in enumerate(raw_tasks):
        if not isinstance(item, dict):
            issues.append(f"skipped non-object task at index {index}")
            continue
        tasks.append(normalize_orchestration_task(config, item, index))
    return tasks, issues


PROVIDER_TASK_LINE_PATTERN = re.compile(r"^-\s*\[(?P<mark>[ xX])\]\s*(?P<body>.+)$")


def parse_provider_task_metadata(raw: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for part in raw.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        normalized_key = key.strip().lower().replace("-", "_")
        if normalized_key:
            metadata[normalized_key] = value.strip()
    return metadata


def provider_task_list(value: str) -> list[str]:
    if not value.strip():
        return []
    return [item.strip() for item in re.split(r"\s*[,|]\s*", value) if item.strip()]


def provider_task_document_line_to_task(config: ProjectConfig, line: str, index: int, path: Path) -> dict[str, object] | None:
    match = PROVIDER_TASK_LINE_PATTERN.match(line.strip())
    if not match:
        return None
    body = match.group("body").strip()
    title = body
    metadata: dict[str, str] = {}
    if "::" in body:
        title, raw_metadata = body.split("::", 1)
        metadata = parse_provider_task_metadata(raw_metadata)
    title = title.strip()
    identifier = metadata.get("id") or f"provider-task-{index + 1}-{sanitize_slug(title)}"
    state = metadata.get("state") or ("accepted" if match.group("mark").lower() == "x" else "open")
    return {
        "id": f"provider-task-document:{sanitize_slug(identifier)}",
        "source_kind": "provider-task-document",
        "source_url": orchestration_relative_path(config, path),
        "identifier": identifier,
        "title": title,
        "description": metadata.get("description", ""),
        "state": state,
        "priority": metadata.get("priority", "normal"),
        "labels": provider_task_list(metadata.get("labels", "")),
        "blocked_by": provider_task_list(metadata.get("blocked_by", "")),
        "project_slug": config.data["project"]["slug"],
        "acceptance_criteria": provider_task_list(metadata.get("acceptance", "")),
        "validation_requirements": provider_task_list(metadata.get("validation", "")),
        "risk_hints": provider_task_list(metadata.get("risk_hints", metadata.get("risk", ""))),
        "created_at": metadata.get("created_at", ""),
        "updated_at": metadata.get("updated_at", ""),
    }


def load_provider_task_document_tasks(config: ProjectConfig) -> tuple[list[dict[str, object]], list[str]]:
    issues: list[str] = []
    path = config.orchestration_tasks_path
    if not path.exists():
        return [], [f"provider task document does not exist: {orchestration_relative_path(config, path)}"]
    if not path.is_relative_to(config.root):
        return [], [f"provider task document must stay inside project root: {path}"]
    text = path.read_text(encoding="utf-8")
    raw_tasks: list[dict[str, object]] = []
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return [], [f"invalid provider task JSON: {orchestration_relative_path(config, path)} ({exc})"]
        source_tasks = data.get("tasks", []) if isinstance(data, dict) else data
        if not isinstance(source_tasks, list):
            return [], ["provider task JSON must contain a JSON array or an object with a `tasks` array"]
        for index, item in enumerate(source_tasks):
            if not isinstance(item, dict):
                issues.append(f"skipped non-object provider task at index {index}")
                continue
            raw = dict(item)
            raw["source_kind"] = normalize_optional_text(raw.get("source_kind", "")) or "provider-task-document"
            raw["source_url"] = normalize_optional_text(raw.get("source_url", "")) or orchestration_relative_path(config, path)
            raw_tasks.append(raw)
    else:
        for index, line in enumerate(text.splitlines()):
            task = provider_task_document_line_to_task(config, line, index, path)
            if task is not None:
                raw_tasks.append(task)
    tasks = [normalize_orchestration_task(config, item, index) for index, item in enumerate(raw_tasks)]
    if not tasks:
        issues.append(f"provider task document contains no task checklist items: {orchestration_relative_path(config, path)}")
    return tasks, issues


def provider_api_task_to_raw(config: ProjectConfig, snapshot: ProviderTaskListSnapshot, item: dict[str, object], index: int) -> dict[str, object]:
    raw = dict(item)
    identifier = normalize_optional_text(raw.get("identifier", "")) or normalize_optional_text(raw.get("id", "")) or f"provider-api-{index + 1}"
    raw["source_kind"] = "provider-api"
    raw["source_url"] = normalize_optional_text(raw.get("source_url", "")) or snapshot.provider_item_url
    raw["identifier"] = identifier
    raw["id"] = normalize_optional_text(raw.get("id", "")) or f"provider-api:{sanitize_slug(identifier)}"
    raw["project_slug"] = normalize_optional_text(raw.get("project_slug", "")) or config.data["project"]["slug"]
    raw["provider"] = snapshot.provider
    raw["provider_item_id"] = snapshot.provider_item_id
    raw["provider_item_kind"] = snapshot.provider_item_kind
    raw["provider_item_url"] = snapshot.provider_item_url
    raw["provider_title"] = snapshot.provider_title
    raw["provider_modified_at"] = snapshot.provider_modified_at
    return raw


def load_provider_api_tasks(config: ProjectConfig) -> tuple[list[dict[str, object]], list[str]]:
    provider_item_id = config.orchestration_provider_task_item_id
    provider_item_kind = config.orchestration_provider_task_item_kind
    provider_item_url = config.orchestration_provider_task_item_url
    missing = []
    if not provider_item_id:
        missing.append("orchestration.provider_task_item_id")
    if not provider_item_kind:
        missing.append("orchestration.provider_task_item_kind")
    if missing:
        return [], ["provider-api task source missing required fields: " + ", ".join(missing)]
    try:
        adapter = create_provider_adapter(config.storage_provider, oauth_store_path=config.project_google_oauth_file)
        snapshot = adapter.fetch_tasks(
            provider_item_id=provider_item_id,
            provider_item_kind=provider_item_kind,
            provider_item_url=provider_item_url,
        )
    except ProviderAdapterError as exc:
        return [], [f"provider-api task fetch failed: {exc.code}: {exc.message}"]
    raw_tasks = [provider_api_task_to_raw(config, snapshot, item, index) for index, item in enumerate(snapshot.tasks) if isinstance(item, dict)]
    tasks = [normalize_orchestration_task(config, item, index) for index, item in enumerate(raw_tasks)]
    issues: list[str] = []
    if not tasks:
        issues.append(f"provider-api task source returned no tasks: {provider_item_kind}:{provider_item_id}")
    return tasks, issues


def load_local_orchestration_task_file(config: ProjectConfig) -> dict[str, object]:
    path = config.orchestration_tasks_path
    if path.exists():
        if not path.is_relative_to(config.root):
            raise SystemExit(f"local task file must stay inside project root: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid local task JSON: {orchestration_relative_path(config, path)} ({exc})")
        if isinstance(data, list):
            return {"version": VERSION, "tasks": data}
        if isinstance(data, dict):
            tasks = data.get("tasks", [])
            if not isinstance(tasks, list):
                raise SystemExit("local task file must contain a `tasks` array")
            return data
        raise SystemExit("local task file must be a JSON array or object")
    return {"version": VERSION, "tasks": []}


def write_local_orchestration_task_file(config: ProjectConfig, data: dict[str, object]) -> None:
    path = config.orchestration_tasks_path
    if not path.is_relative_to(config.root):
        raise SystemExit(f"local task file must stay inside project root: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = normalize_optional_text(data.get("version", VERSION)) or VERSION
    data["updated_at"] = current_utc_timestamp()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_orchestration_tasks(config: ProjectConfig) -> tuple[list[dict[str, object]], list[str]]:
    automation_tasks, automation_issues = load_automation_intent_tasks(config)
    source_tasks: list[dict[str, object]]
    source_issues: list[str]
    if config.orchestration_task_source == "local":
        source_tasks, source_issues = load_local_orchestration_tasks(config)
    elif config.orchestration_task_source == "provider-task-document":
        source_tasks, source_issues = load_provider_task_document_tasks(config)
    elif config.orchestration_task_source == "provider-api":
        source_tasks, source_issues = load_provider_api_tasks(config)
    else:
        source_tasks, source_issues = [], [f"unsupported task source: {config.orchestration_task_source}"]
    seen: set[str] = set()
    combined: list[dict[str, object]] = []
    for task in [*source_tasks, *automation_tasks]:
        task_id = normalize_optional_text(task.get("id", ""))
        if task_id and task_id in seen:
            continue
        if task_id:
            seen.add(task_id)
        combined.append(task)
    return combined, [*source_issues, *automation_issues]


def orchestration_budget_payload(config: ProjectConfig, runs: list[dict[str, object]]) -> dict[str, object]:
    today = date.today().isoformat()
    used_minutes = 0
    for run in runs:
        started_at = normalize_optional_text(run.get("started_at", ""))
        if started_at[:10] != today:
            continue
        metrics = run.get("metrics", {})
        if isinstance(metrics, dict):
            try:
                used_minutes += int(metrics.get("runtime_minutes", 0))
            except (TypeError, ValueError):
                continue
    remaining = max(0, config.orchestration_daily_budget_minutes - used_minutes)
    return {
        "date": today,
        "daily_budget_minutes": config.orchestration_daily_budget_minutes,
        "used_minutes": used_minutes,
        "remaining_minutes": remaining,
        "exhausted": remaining <= 0,
    }


def orchestration_status_payload(config: ProjectConfig) -> dict[str, object]:
    tasks, task_issues = load_orchestration_tasks(config)
    write_orchestration_task_snapshot(config, tasks, task_issues)
    runs = read_orchestration_runs(config)
    latest = load_json_file(orchestration_latest_path(config), default={})
    raw_active = load_orchestration_active(config)
    active = visible_orchestration_active(raw_active)
    counts = {status: 0 for status in ORCHESTRATION_RUN_STATUSES}
    for run in runs:
        status = normalize_optional_text(run.get("status", ""))
        if status in counts:
            counts[status] += 1
    task_counts = {
        "total": len(tasks),
        "eligible": sum(1 for task in tasks if bool(task.get("eligible"))),
        "blocked": sum(1 for task in tasks if task.get("blocked_reasons")),
    }
    budget = orchestration_budget_payload(config, runs)
    budget_path = orchestration_budgets_path(config)
    budget_path.parent.mkdir(parents=True, exist_ok=True)
    budget_path.write_text(json.dumps(budget, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {
        "config": orchestration_config_payload(config),
        "tasks": {
            **task_counts,
            "issues": task_issues,
            "snapshot_path": orchestration_relative_path(config, orchestration_tasks_snapshot_path(config)),
        },
        "runs": {
            "total": len(runs),
            "counts": counts,
            "latest": latest if isinstance(latest, dict) else {},
            "runs_path": orchestration_relative_path(config, orchestration_runs_path(config)),
        },
        "active": active,
        "last_active": raw_active,
        "events": {
            "total": count_jsonl_records(orchestration_events_path(config)),
            "events_path": orchestration_relative_path(config, orchestration_events_path(config)),
        },
        "triggers": {
            "total": count_jsonl_records(orchestration_triggers_path(config)),
            "triggers_path": orchestration_relative_path(config, orchestration_triggers_path(config)),
        },
        "promotion_candidates": {
            "total": count_jsonl_records(orchestration_promotion_candidates_path(config)),
            "promotion_candidates_path": orchestration_relative_path(config, orchestration_promotion_candidates_path(config)),
        },
        "budget": budget,
    }


def orchestration_policy_issues(config: ProjectConfig) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if config.orchestration_workspace_root.exists() and not config.orchestration_workspace_root.is_dir():
        errors.append(f"workspace_root is not a directory: {config.orchestration_workspace_root}")
    if not config.orchestration_workspace_root.is_relative_to(config.root):
        errors.append(f"workspace_root must stay inside project root: {config.orchestration_workspace_root}")
    if config.orchestration_tasks_path.exists() and not config.orchestration_tasks_path.is_relative_to(config.root):
        errors.append(f"tasks_path must stay inside project root: {config.orchestration_tasks_path}")
    if config.orchestration_enabled and config.orchestration_runner == "shell-command" and not config.orchestration_runner_command:
        errors.append("runner `shell-command` requires orchestration.runner_command")
    if config.orchestration_enabled and config.orchestration_runner == "codex-sdk" and not config.orchestration_runner_command:
        errors.append("runner `codex-sdk` requires orchestration.runner_command")
    if config.orchestration_enabled and config.orchestration_runner == "codex-app-server" and not config.orchestration_runner_endpoint:
        errors.append("runner `codex-app-server` requires orchestration.runner_endpoint")
    if config.orchestration_enabled and config.orchestration_task_source == "provider-api":
        if not config.orchestration_provider_task_item_id:
            errors.append("task_source `provider-api` requires orchestration.provider_task_item_id")
        if not config.orchestration_provider_task_item_kind:
            errors.append("task_source `provider-api` requires orchestration.provider_task_item_kind")
    if (
        config.orchestration_enabled
        and config.orchestration_runner in {"shell-command", "codex-sdk", "codex-app-server"}
        and config.orchestration_workspace_mode == "none"
        and not config.orchestration_allow_project_root_runner
    ):
        errors.append(f"runner `{config.orchestration_runner}` with workspace_mode `none` requires allow_project_root_runner = true")
    if not config.orchestration_enabled:
        warnings.append("orchestration is disabled; task listing is available, but runs will be blocked")
    return errors, warnings


def orchestration_doctor(config: ProjectConfig, args: argparse.Namespace) -> int:
    errors, warnings = orchestration_policy_issues(config)
    tasks, task_issues = load_orchestration_tasks(config)
    warnings.extend(task_issues)
    payload = {
        "command": "orchestration.doctor",
        "status": "ok" if not errors else "failed",
        "project": project_payload(config),
        "orchestration": orchestration_config_payload(config),
        "task_count": len(tasks),
        "errors": errors,
        "warnings": warnings,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0 if not errors else 1
    print(f"Orchestration doctor for {config.data['project']['name']}")
    print(f"  Status: {payload['status']}")
    for item in errors:
        print(f"  error: {item}")
    for item in warnings:
        print(f"  warning: {item}")
    return 0 if not errors else 1


def orchestration_status(config: ProjectConfig, args: argparse.Namespace) -> int:
    if bool(getattr(args, "watch", False)):
        try:
            while True:
                code = orchestration_status(config, argparse.Namespace(json=False, watch=False, compact=bool(getattr(args, "compact", False))))
                if load_orchestration_active(config).get("active", {}).get("state") in {"accepted", "failed", "blocked", "cancelled"}:
                    return code
                print("")
                sys.stdout.flush()
                import time

                time.sleep(2)
        except KeyboardInterrupt:
            return 130
    payload = {
        "command": "orchestration.status",
        "status": "ok",
        "project": project_payload(config),
        "orchestration": orchestration_status_payload(config),
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    if bool(getattr(args, "compact", False)):
        print(orchestration_compact_status_line(config))
        return 0
    state = payload["orchestration"]
    print(f"Orchestration status for {config.data['project']['name']}")
    print(f"  Enabled: {state['config']['enabled']}")
    print(f"  Task source: {state['config']['task_source']} ({state['config']['tasks_path']})")
    print(f"  Runner: {state['config']['runner']}")
    print(f"  Tasks: {state['tasks']['total']} total / {state['tasks']['eligible']} eligible / {state['tasks']['blocked']} blocked")
    print(f"  Runs: {state['runs']['total']}")
    print(f"  Budget minutes: {state['budget']['used_minutes']} used / {state['budget']['daily_budget_minutes']} daily")
    active = state.get("active", {})
    active_event = active.get("active", {}) if isinstance(active, dict) else {}
    if isinstance(active_event, dict) and active_event:
        print("  Active execution:")
        print(f"    Task: {active_event.get('task_title') or active_event.get('task_id') or 'unknown'}")
        print(f"    Stage: {active_event.get('stage', 'unknown')} / role={active_event.get('role', 'unknown')} / state={active_event.get('state', 'unknown')}")
        print(f"    Model: {active_event.get('provider', 'unknown')}:{active_event.get('model', 'unknown')}")
        print(f"    Cycle: {active_event.get('routing_cycle', 1)} of {config.agent_routing_max_review_cycles}")
        print(f"    Next: {active_event.get('next_action', '') or 'n/a'}")
    else:
        print("  Active execution: none")
    return 0


def orchestration_tasks(config: ProjectConfig, args: argparse.Namespace) -> int:
    tasks, issues = load_orchestration_tasks(config)
    write_orchestration_task_snapshot(config, tasks, issues)
    payload = {
        "command": "orchestration.tasks",
        "status": "ok",
        "project": project_payload(config),
        "task_source": config.orchestration_task_source,
        "tasks_path": orchestration_relative_path(config, config.orchestration_tasks_path),
        "issues": issues,
        "tasks": tasks,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Orchestration tasks for {config.data['project']['name']}")
    for task in tasks:
        print(f"  - {task['id']}: {task['title']} [{task['state']}/{task['risk']}]")
        for reason in task.get("blocked_reasons", []):
            print(f"    blocked: {reason}")
    if not tasks:
        print("  No tasks.")
    for issue in issues:
        print(f"  warning: {issue}")
    return 0


def orchestration_timeline(config: ProjectConfig, args: argparse.Namespace) -> int:
    limit = max(1, int(getattr(args, "limit", 20)))
    events = read_jsonl_objects(orchestration_events_path(config))
    selected = events[-limit:]
    payload = {
        "command": "orchestration.timeline",
        "status": "ok",
        "project": project_payload(config),
        "events_path": orchestration_relative_path(config, orchestration_events_path(config)),
        "events": selected,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Orchestration timeline for {config.data['project']['name']}")
    if not selected:
        print("  No orchestration events.")
        return 0
    for event in selected:
        print(
            "  - "
            + f"{event.get('timestamp', '')}: "
            + f"{event.get('stage', 'unknown')}/{event.get('role', 'unknown')} "
            + f"{event.get('state', 'unknown')} "
            + f"({event.get('provider', 'unknown')}:{event.get('model', 'unknown')})"
        )
        next_action = normalize_optional_text(event.get("next_action", ""))
        if next_action:
            print(f"    next: {next_action}")
    return 0


def load_agent_provider_config(config: ProjectConfig) -> tuple[dict[str, object], list[str], list[str]]:
    path = config.agent_provider_config_path
    warnings: list[str] = []
    errors: list[str] = []
    if not path.exists():
        return {"providers": {}}, [f"local provider config not found: {orchestration_relative_path(config, path)}"], []
    if not path.is_relative_to(config.root):
        return {"providers": {}}, [], [f"agent provider config must stay inside project root: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"providers": {}}, [], [f"invalid local provider config JSON: {exc}"]
    if not isinstance(payload, dict):
        return {"providers": {}}, [], ["local provider config must be a JSON object"]
    providers = payload.get("providers", {})
    if not isinstance(providers, dict):
        return {"providers": {}}, [], ["local provider config `providers` must be an object"]
    for provider_name, provider in providers.items():
        if not isinstance(provider, dict):
            errors.append(f"provider `{provider_name}` must be an object")
            continue
        for forbidden in ["api_key", "token", "secret", "password", "credential"]:
            if forbidden in provider:
                errors.append(f"provider `{provider_name}` must not store raw `{forbidden}`; use env var names instead")
        allowed_roles = provider.get("allowed_roles", [])
        if allowed_roles and not isinstance(allowed_roles, list):
            errors.append(f"provider `{provider_name}` allowed_roles must be an array")
    return payload, warnings, errors


def agent_provider_readiness(config: ProjectConfig) -> dict[str, object]:
    payload, warnings, errors = load_agent_provider_config(config)
    providers = payload.get("providers", {}) if isinstance(payload, dict) else {}
    provider_status: dict[str, object] = {}
    if isinstance(providers, dict):
        for provider_name, provider in providers.items():
            if not isinstance(provider, dict):
                continue
            endpoint_env = normalize_optional_text(provider.get("endpoint_env", ""))
            api_key_env = normalize_optional_text(provider.get("api_key_env", ""))
            allowed_roles = normalize_task_string_list(provider.get("allowed_roles"))
            provider_status[provider_name] = {
                "kind": normalize_optional_text(provider.get("kind", "")) or "unknown",
                "endpoint_env": endpoint_env,
                "endpoint_configured": bool(endpoint_env and os.environ.get(endpoint_env)),
                "api_key_env": api_key_env,
                "api_key_configured": bool(api_key_env and os.environ.get(api_key_env)),
                "allowed_roles": allowed_roles,
            }
    roles = config.agent_routing_roles
    role_status: dict[str, object] = {}
    for role_name, role_payload in roles.items():
        provider_name = normalize_optional_text(role_payload.get("provider", ""))
        provider = provider_status.get(provider_name, {})
        provider_known = provider_name in {"host", "local", "human", "unknown"} or bool(provider)
        allowed_roles = normalize_task_string_list(provider.get("allowed_roles") if isinstance(provider, dict) else [])
        role_allowed = not allowed_roles or role_name in allowed_roles
        missing_credentials = []
        if isinstance(provider, dict) and provider:
            if provider.get("api_key_env") and not provider.get("api_key_configured"):
                missing_credentials.append(provider.get("api_key_env"))
        role_status[role_name] = {
            **role_payload,
            "provider_known": provider_known,
            "role_allowed_by_provider": role_allowed,
            "missing_credential_env": missing_credentials,
            "ready": provider_known and role_allowed and not missing_credentials,
        }
    return {
        "config_path": orchestration_relative_path(config, config.agent_provider_config_path),
        "warnings": warnings,
        "errors": errors,
        "providers": provider_status,
        "roles": role_status,
    }


def agent_routing_executor_is_remembered(config: ProjectConfig) -> bool:
    executor = agent_routing_role_payload(config, "executor")
    provider = normalize_optional_text(executor.get("provider", ""))
    model = normalize_optional_text(executor.get("model", ""))
    has_runner = (
        config.orchestration_runner == "shell-command"
        and bool(config.orchestration_runner_command)
    ) or (
        config.orchestration_runner == "codex-sdk"
        and bool(config.orchestration_runner_command)
    ) or (
        config.orchestration_runner == "codex-app-server"
        and bool(config.orchestration_runner_endpoint)
    )
    has_executor = provider not in {"", "local"} or model not in {"", "configured-runner"}
    return bool(has_runner and has_executor)


def agent_routing_remembered_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "remembered": agent_routing_executor_is_remembered(config),
        "runner": {
            "kind": config.orchestration_runner,
            "command": config.orchestration_runner_command,
            "endpoint": config.orchestration_runner_endpoint,
            "workspace_mode": config.orchestration_workspace_mode,
        },
        "executor": agent_routing_role_payload(config, "executor"),
    }


def prompt_agent_routing_value(label: str, default: str, *, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default:
            return default
        if not required:
            return ""
        print(f"{label} is required.")


def prompt_agent_routing_bool(label: str, default: bool) -> bool:
    default_text = "Y/n" if default else "y/N"
    while True:
        value = input(f"{label} [{default_text}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes", "true", "1"}:
            return True
        if value in {"n", "no", "false", "0"}:
            return False
        print("Please answer yes or no.")


def upsert_local_agent_provider(
    config: ProjectConfig,
    *,
    provider_name: str,
    provider_kind: str,
    endpoint_env: str,
    api_key_env: str,
) -> None:
    if provider_name in {"host", "local", "human", "unknown"}:
        return
    payload, warnings, errors = load_agent_provider_config(config)
    if errors:
        raise SystemExit("Cannot update local provider config: " + "; ".join(errors))
    providers = payload.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise SystemExit("Cannot update local provider config: providers must be an object")
    existing = providers.get(provider_name, {})
    if not isinstance(existing, dict):
        existing = {}
    updated = {
        "kind": provider_kind or normalize_optional_text(existing.get("kind", "")) or "cli",
        "allowed_roles": ["executor"],
    }
    if endpoint_env or existing.get("endpoint_env"):
        updated["endpoint_env"] = endpoint_env or normalize_optional_text(existing.get("endpoint_env", ""))
    if api_key_env or existing.get("api_key_env"):
        updated["api_key_env"] = api_key_env or normalize_optional_text(existing.get("api_key_env", ""))
    providers[provider_name] = updated
    config.agent_provider_config_path.parent.mkdir(parents=True, exist_ok=True)
    config.agent_provider_config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def agent_routing_configure_payload(project_root: Path, config: ProjectConfig, args: argparse.Namespace) -> tuple[dict[str, object], int]:
    has_cli_values = any(
        normalize_optional_text(getattr(args, name, ""))
        for name in ["runner", "runner_command", "runner_endpoint", "provider", "model", "reasoning_effort", "workspace_mode", "endpoint_env", "api_key_env"]
    ) or getattr(args, "write_access", None) is not None
    remembered = agent_routing_executor_is_remembered(config)
    if remembered and not bool(getattr(args, "replace", False)) and not has_cli_values:
        payload = {
            "command": "agent-routing.configure",
            "status": "remembered",
            "project": project_payload(config),
            "routing": agent_routing_remembered_payload(config),
            "next_action": "Use --replace or pass new values to change the remembered executor route.",
        }
        return payload, 0
    if not has_cli_values and not sys.stdin.isatty():
        payload = {
            "command": "agent-routing.configure",
            "status": "needs-input",
            "project": project_payload(config),
            "routing": agent_routing_remembered_payload(config),
            "errors": [
                "agent-routing configure needs a TTY for first-time setup, or pass --runner, --runner-command, --provider, and --model"
            ],
        }
        return payload, 1

    current_executor = agent_routing_role_payload(config, "executor")
    runner = normalize_optional_text(getattr(args, "runner", "")) or config.orchestration_runner
    runner_command = normalize_optional_text(getattr(args, "runner_command", "")) or config.orchestration_runner_command
    runner_endpoint = normalize_optional_text(getattr(args, "runner_endpoint", "")) or config.orchestration_runner_endpoint
    provider = normalize_optional_text(getattr(args, "provider", "")) or normalize_optional_text(current_executor.get("provider", "")) or "local"
    model = normalize_optional_text(getattr(args, "model", "")) or normalize_optional_text(current_executor.get("model", "")) or "configured-runner"
    reasoning_effort = normalize_optional_text(getattr(args, "reasoning_effort", "")) or normalize_optional_text(current_executor.get("reasoning_effort", ""))
    workspace_mode = normalize_optional_text(getattr(args, "workspace_mode", "")) or config.orchestration_workspace_mode
    write_access = getattr(args, "write_access", None)
    if write_access is None:
        write_access = bool(current_executor.get("write_access", False))

    if not has_cli_values and sys.stdin.isatty():
        print("Configure Sula executor routing. Press Enter to keep the default shown.")
        runner = prompt_agent_routing_value("Runner", "shell-command" if config.orchestration_runner == "dry-run" else runner, required=True)
        runner_command = prompt_agent_routing_value("Runner command", runner_command, required=runner in {"shell-command", "codex-sdk"})
        if runner == "codex-app-server":
            runner_endpoint = prompt_agent_routing_value("Runner endpoint", runner_endpoint, required=True)
        provider = prompt_agent_routing_value("Executor provider", provider if provider != "local" else "claudecode", required=True)
        model = prompt_agent_routing_value("Executor model", model if model != "configured-runner" else "deepseek", required=True)
        reasoning_effort = prompt_agent_routing_value("Executor reasoning effort", reasoning_effort, required=False)
        workspace_mode = prompt_agent_routing_value("Workspace mode", workspace_mode if workspace_mode != "none" else "copy", required=True)
        write_access = prompt_agent_routing_bool("Allow executor write access", True)
    if runner not in ORCHESTRATION_RUNNER_CHOICES:
        return {
            "command": "agent-routing.configure",
            "status": "failed",
            "project": project_payload(config),
            "errors": [f"unsupported runner: {runner}"],
        }, 1
    if workspace_mode not in ORCHESTRATION_WORKSPACE_MODE_CHOICES:
        return {
            "command": "agent-routing.configure",
            "status": "failed",
            "project": project_payload(config),
            "errors": [f"unsupported workspace mode: {workspace_mode}"],
        }, 1
    errors = []
    if runner in {"shell-command", "codex-sdk"} and not runner_command:
        errors.append(f"runner `{runner}` requires --runner-command")
    if runner == "codex-app-server" and not runner_endpoint:
        errors.append("runner `codex-app-server` requires --runner-endpoint")
    if not provider:
        errors.append("--provider is required")
    if not model:
        errors.append("--model is required")
    if errors:
        return {
            "command": "agent-routing.configure",
            "status": "failed",
            "project": project_payload(config),
            "errors": errors,
        }, 1

    data = json.loads(json.dumps(config.data))
    orchestration = data.setdefault("orchestration", {})
    orchestration["runner"] = runner
    orchestration["runner_command"] = runner_command if runner in {"shell-command", "codex-sdk"} else ""
    orchestration["runner_endpoint"] = runner_endpoint if runner == "codex-app-server" else ""
    orchestration["workspace_mode"] = workspace_mode
    if runner in {"shell-command", "codex-sdk", "codex-app-server"} and workspace_mode == "none":
        orchestration["allow_project_root_runner"] = True
    agent_routing = data.setdefault("agent_routing", default_agent_routing_config())
    roles = agent_routing.setdefault("roles", default_agent_routing_roles())
    executor = roles.setdefault("executor", default_agent_routing_roles()["executor"])
    executor["provider"] = provider
    executor["model"] = model
    executor["reasoning_effort"] = reasoning_effort
    executor["write_access"] = bool(write_access)
    executor["workspace_mode"] = workspace_mode
    updated_config = write_manifest_data(project_root, data)
    upsert_local_agent_provider(
        updated_config,
        provider_name=provider,
        provider_kind=normalize_optional_text(getattr(args, "provider_kind", "")) or "cli",
        endpoint_env=normalize_optional_text(getattr(args, "endpoint_env", "")),
        api_key_env=normalize_optional_text(getattr(args, "api_key_env", "")),
    )
    final_config = load_manifest(project_root)
    payload = {
        "command": "agent-routing.configure",
        "status": "ok",
        "project": project_payload(final_config),
        "routing": agent_routing_remembered_payload(final_config),
        "provider_readiness": agent_provider_readiness(final_config),
        "next_action": "Run `python3 scripts/sula.py session start --project-root .` to see the remembered executor route.",
    }
    return payload, 0


def agent_routing_configure(project_root: Path, config: ProjectConfig, args: argparse.Namespace) -> int:
    payload, code = agent_routing_configure_payload(project_root, config, args)
    if json_output_requested(args):
        emit_json(payload)
        return code
    print(f"Agent routing configure for {config.data['project']['name']}")
    print(f"  Status: {payload['status']}")
    if payload["status"] == "remembered":
        remembered = payload["routing"]
        print("  Reusing remembered executor route.")
        print(f"  Runner: {remembered['runner']['kind']} / {remembered['runner']['command'] or remembered['runner']['endpoint']}")
        executor = remembered["executor"]
        print(f"  Executor: {executor.get('provider', 'unknown')}:{executor.get('model', 'unknown')}")
    elif payload["status"] == "ok":
        remembered = payload["routing"]
        print("  Remembered executor route.")
        print(f"  Runner: {remembered['runner']['kind']} / {remembered['runner']['command'] or remembered['runner']['endpoint']}")
        executor = remembered["executor"]
        print(f"  Executor: {executor.get('provider', 'unknown')}:{executor.get('model', 'unknown')}")
    for item in payload.get("errors", []):
        print(f"  error: {item}")
    next_action = normalize_optional_text(payload.get("next_action", ""))
    if next_action:
        print(f"  Next: {next_action}")
    return code


def agent_routing_status_payload(config: ProjectConfig, *, host_metadata: dict[str, str] | None = None) -> dict[str, object]:
    active = load_orchestration_active(config)
    readiness = agent_provider_readiness(config)
    return {
        "config": agent_routing_config_payload(config),
        "host": host_metadata or session_host_metadata(),
        "provider_readiness": readiness,
        "active": active,
    }


def agent_routing_status(config: ProjectConfig, args: argparse.Namespace) -> int:
    payload = {
        "command": "agent-routing.status",
        "status": "ok",
        "project": project_payload(config),
        "agent_routing": agent_routing_status_payload(config),
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Agent routing status for {config.data['project']['name']}")
    routing = payload["agent_routing"]
    config_payload = routing["config"]
    print(f"  Enabled: {config_payload['enabled']}")
    print(f"  Mode: {config_payload['mode']}")
    print(f"  Visibility: {config_payload['visibility']}")
    print(f"  Budget policy: {config_payload['default_budget_policy']} / breach={config_payload['budget_breach_behavior']}")
    host = routing["host"]
    print(f"  Host: {host.get('agent', 'unknown')} / {host.get('provider', 'unknown')}:{host.get('model', 'unknown')}")
    roles = routing["provider_readiness"]["roles"]
    for role_name in AGENT_ROUTING_ROLE_CHOICES:
        role = roles.get(role_name, {})
        if isinstance(role, dict):
            ready = "ready" if role.get("ready") else "not-ready"
            print(f"  {role_name}: {role.get('provider', 'unknown')}:{role.get('model', 'unknown')} ({ready})")
    return 0


def agent_routing_doctor(config: ProjectConfig, args: argparse.Namespace) -> int:
    readiness = agent_provider_readiness(config)
    errors = list(readiness.get("errors", [])) if isinstance(readiness.get("errors", []), list) else []
    warnings = list(readiness.get("warnings", [])) if isinstance(readiness.get("warnings", []), list) else []
    roles = readiness.get("roles", {})
    if isinstance(roles, dict):
        for role_name, role in roles.items():
            if not isinstance(role, dict):
                continue
            if not role.get("provider_known"):
                errors.append(f"role `{role_name}` provider is not configured: {role.get('provider', '')}")
            if not role.get("role_allowed_by_provider"):
                errors.append(f"role `{role_name}` is not allowed by provider `{role.get('provider', '')}`")
            missing = normalize_task_string_list(role.get("missing_credential_env"))
            if missing:
                warnings.append(f"role `{role_name}` missing credential env: {', '.join(missing)}")
    payload = {
        "command": "agent-routing.doctor",
        "status": "ok" if not errors else "failed",
        "project": project_payload(config),
        "agent_routing": agent_routing_config_payload(config),
        "provider_readiness": readiness,
        "errors": errors,
        "warnings": warnings,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0 if not errors else 1
    print(f"Agent routing doctor for {config.data['project']['name']}")
    print(f"  Status: {payload['status']}")
    for item in errors:
        print(f"  error: {item}")
    for item in warnings:
        print(f"  warning: {item}")
    return 0 if not errors else 1


def session_host_metadata(args: argparse.Namespace | None = None) -> dict[str, str]:
    return {
        "agent": normalize_optional_text(getattr(args, "host_agent", "")) or os.environ.get("SULA_HOST_AGENT", "").strip() or "unknown",
        "provider": normalize_optional_text(getattr(args, "host_provider", "")) or os.environ.get("SULA_HOST_PROVIDER", "").strip() or "unknown",
        "model": normalize_optional_text(getattr(args, "host_model", "")) or os.environ.get("SULA_HOST_MODEL", "").strip() or "unknown",
    }


def session_start(config: ProjectConfig, args: argparse.Namespace) -> int:
    tasks, issues = load_orchestration_tasks(config)
    raw_active = load_orchestration_active(config)
    active = visible_orchestration_active(raw_active)
    host = session_host_metadata(args)
    routing = agent_routing_status_payload(config, host_metadata=host)
    open_tasks = [task for task in tasks if task.get("state") in {"open", "running"}]
    blocked_tasks = [task for task in tasks if task.get("blocked_reasons")]
    payload = {
        "command": "session.start",
        "status": "ok",
        "project": project_payload(config),
        "memory_digest": orchestration_relative_path(config, config.digest_file),
        "host": host,
        "agent_routing": routing,
        "orchestration": {
            "task_count": len(tasks),
            "open_tasks": open_tasks[:10],
            "blocked_task_count": len(blocked_tasks),
            "issues": issues,
            "active": active,
            "last_active": raw_active,
        },
        "next_action": "Review active execution, then follow STATUS.md Handoff or the user's current request.",
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Sula session start for {config.data['project']['name']}")
    print(f"  Memory digest: {payload['memory_digest']}")
    print(f"  Host: {host['agent']} / {host['provider']}:{host['model']}")
    print(f"  Agent routing: {routing['config']['mode']} ({'enabled' if routing['config']['enabled'] else 'disabled'})")
    for role_name in ["planner", "executor", "verifier", "reviewer"]:
        print("  " + role_status_line(role_name, config.agent_routing_roles[role_name]))
    active_event = active.get("active", {}) if isinstance(active, dict) else {}
    if isinstance(active_event, dict) and active_event:
        print("  Active execution:")
        print(f"    Task: {active_event.get('task_title') or active_event.get('task_id') or 'unknown'}")
        print(f"    Stage: {active_event.get('stage', 'unknown')} / role={active_event.get('role', 'unknown')} / state={active_event.get('state', 'unknown')}")
        print(f"    Model: {active_event.get('provider', 'unknown')}:{active_event.get('model', 'unknown')}")
        print(f"    Next: {active_event.get('next_action', '') or 'n/a'}")
    else:
        print("  Active execution: none")
    print(f"  Tasks: {len(tasks)} total / {len(open_tasks)} open / {len(blocked_tasks)} blocked")
    for task in open_tasks[:5]:
        print(f"    - {task['id']}: {task['title']} [{task['state']}/{task['risk']}]")
    if issues:
        for issue in issues:
            print(f"  warning: {issue}")
    print(f"  Next: {payload['next_action']}")
    return 0


def orchestration_intake(config: ProjectConfig, args: argparse.Namespace) -> int:
    payload, code = capture_orchestration_task(
        config,
        source_kind="cli-intent",
        source_url="",
        identity_key=normalize_optional_text(args.identifier) or f"cli-{date.today().isoformat()}-{sanitize_slug(args.title)}",
        event_kind="cli-intent",
        title=args.title,
        description=args.description,
        acceptance=args.acceptance,
        validation=args.validation,
        labels=args.label,
        risk_hints=args.risk_hint,
        priority=args.priority,
        error_on_duplicate=True,
    )
    if json_output_requested(args):
        emit_json(payload)
        return code
    normalized = payload["task"]
    print(f"Captured orchestration task {normalized['id']}: {normalized['title']}")
    if normalized.get("blocked_reasons"):
        for item in normalized["blocked_reasons"]:
            print(f"  blocked: {item}")
    return code


def capture_orchestration_task(
    config: ProjectConfig,
    *,
    source_kind: str,
    source_url: str,
    identity_key: str,
    event_kind: str,
    title: str,
    description: str,
    acceptance: list[str],
    validation: list[str],
    labels: list[str],
    risk_hints: list[str],
    priority: str,
    error_on_duplicate: bool,
) -> tuple[dict[str, object], int]:
    task_file = load_local_orchestration_task_file(config)
    raw_tasks = task_file.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise SystemExit("local task file must contain a `tasks` array")
    identifier = normalize_optional_text(identity_key) or f"{source_kind}-{date.today().isoformat()}-{sanitize_slug(title)}"
    prefix = "cli" if source_kind == "cli-intent" else f"trigger:{sanitize_slug(source_kind)}"
    task_id = f"{prefix}:{sanitize_slug(identifier)}"
    existing_ids = {
        normalize_optional_text(item.get("id", ""))
        for item in raw_tasks
        if isinstance(item, dict)
    }
    if task_id in existing_ids:
        if error_on_duplicate:
            raise SystemExit(f"orchestration task already exists: {task_id}")
        for index, item in enumerate(raw_tasks):
            if isinstance(item, dict) and normalize_optional_text(item.get("id", "")) == task_id:
                normalized = normalize_orchestration_task(config, item, index)
                payload = {
                    "command": "orchestration.trigger",
                    "status": "duplicate",
                    "project": project_payload(config),
                    "tasks_path": orchestration_relative_path(config, config.orchestration_tasks_path),
                    "task": normalized,
                    "trigger": {
                        "source_kind": source_kind,
                        "source_url": source_url,
                        "identity_key": identifier,
                        "event_kind": event_kind,
                        "deduped": True,
                    },
                }
                return payload, 0
    now = current_utc_timestamp()
    task = {
        "id": task_id,
        "source_kind": source_kind,
        "source_url": normalize_optional_text(source_url),
        "identifier": identifier,
        "title": title,
        "description": normalize_optional_text(description),
        "state": "open",
        "priority": normalize_optional_text(priority) or "normal",
        "labels": normalize_task_string_list(labels),
        "blocked_by": [],
        "project_slug": config.data["project"]["slug"],
        "acceptance_criteria": normalize_task_string_list(acceptance),
        "validation_requirements": normalize_task_string_list(validation),
        "risk_hints": normalize_task_string_list(risk_hints),
        "trigger_event_kind": event_kind,
        "created_at": now,
        "updated_at": now,
    }
    raw_tasks.append(task)
    task_file["tasks"] = raw_tasks
    write_local_orchestration_task_file(config, task_file)
    normalized = normalize_orchestration_task(config, task, len(raw_tasks) - 1)
    write_orchestration_task_snapshot(config, [normalized], [])
    trigger = {
        "version": VERSION,
        "created_at": now,
        "source_kind": source_kind,
        "source_url": normalize_optional_text(source_url),
        "identity_key": identifier,
        "event_kind": event_kind,
        "task_id": normalized["id"],
        "title": normalized["title"],
        "deduped": False,
    }
    append_orchestration_trigger(config, trigger)
    refresh_kernel_state(config, event_type="orchestration.intake", summary=f"Captured orchestration task `{title}`.")
    payload = {
        "command": "orchestration.intake" if source_kind == "cli-intent" else "orchestration.trigger",
        "status": "ok",
        "project": project_payload(config),
        "tasks_path": orchestration_relative_path(config, config.orchestration_tasks_path),
        "task": normalized,
        "trigger": trigger,
    }
    return payload, 0


def orchestration_trigger(config: ProjectConfig, args: argparse.Namespace) -> int:
    payload, code = capture_orchestration_task(
        config,
        source_kind=args.source_kind,
        source_url=args.source_url,
        identity_key=args.identity_key,
        event_kind=args.event_kind,
        title=args.title,
        description=args.description,
        acceptance=args.acceptance,
        validation=args.validation,
        labels=args.label,
        risk_hints=args.risk_hint,
        priority=args.priority,
        error_on_duplicate=False,
    )
    run_payload: dict[str, object] | None = None
    run_code = 0
    if args.run and payload.get("task"):
        task = payload["task"]
        if isinstance(task, dict):
            run_payload, run_code = create_orchestration_run_payload(config, normalize_optional_text(task.get("id", "")))
            payload["run"] = run_payload.get("run", {}) if isinstance(run_payload, dict) else {}
            payload["run_status"] = run_payload.get("status", "blocked") if isinstance(run_payload, dict) else "blocked"
    if json_output_requested(args):
        emit_json(payload)
        return run_code if args.run else code
    task = payload["task"]
    if isinstance(task, dict):
        print(f"Triggered orchestration task {task['id']}: {task['title']}")
    if args.run:
        print(f"  Run status: {payload.get('run_status', 'blocked')}")
    return run_code if args.run else code


def orchestration_workspace_for_task(config: ProjectConfig, task: dict[str, object]) -> tuple[str, list[str]]:
    if config.orchestration_workspace_mode == "none":
        return "", []
    root = config.orchestration_workspace_root
    if not root.is_relative_to(config.root):
        return "", [f"workspace root escapes project root: {root}"]
    key = sanitize_slug(normalize_optional_text(task.get("identifier", "")) or normalize_optional_text(task.get("id", "")))
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        return "", [f"workspace path escapes configured workspace root: {path}"]
    return str(path), []


def orchestration_find_task(config: ProjectConfig, task_id: str) -> tuple[dict[str, object] | None, list[str]]:
    tasks, issues = load_orchestration_tasks(config)
    for task in tasks:
        if normalize_optional_text(task.get("id", "")) == task_id or normalize_optional_text(task.get("identifier", "")) == task_id:
            if normalize_optional_text(task.get("source_kind", "")) == "automation":
                return task, []
            return task, issues
    return None, issues


def agent_quality_checklist_payload(config: ProjectConfig) -> dict[str, object]:
    return {
        "quality_policy": config.agent_quality_policy,
        "assumptions": "surface uncertain assumptions before non-trivial implementation"
        if config.agent_assumption_policy != "off"
        else "no explicit assumption requirement",
        "simplicity": "prefer the smallest durable design that satisfies the task"
        if config.agent_complexity_policy == "simplicity-first"
        else "follow project default complexity policy",
        "diff_scope": "change only lines required by the task"
        if config.agent_diff_scope_policy == "surgical"
        else config.agent_diff_scope_policy,
        "success_criteria": "define or preserve acceptance criteria and report them at closeout"
        if config.agent_success_criteria_policy == "required"
        else config.agent_success_criteria_policy,
        "verification_required": config.agent_require_verification,
        "drive_by_refactors_forbidden": config.agent_forbid_drive_by_refactors,
    }


def build_orchestration_run_record(
    config: ProjectConfig,
    task: dict[str, object] | None,
    *,
    task_id: str,
    status: str,
    blocked_reasons: list[str],
    workspace_path: str = "",
) -> dict[str, object]:
    now = current_utc_timestamp()
    task_identifier = normalize_optional_text(task.get("identifier", task_id)) if task else task_id
    run_id = f"run-{now.replace(':', '').replace('-', '').replace('Z', '')}-{sanitize_slug(task_identifier)}"
    return {
        "run_id": run_id,
        "task_id": normalize_optional_text(task.get("id", task_id)) if task else task_id,
        "task_identifier": task_identifier,
        "task_source": config.orchestration_task_source,
        "runner": config.orchestration_runner,
        "workspace_mode": config.orchestration_workspace_mode,
        "workspace_path": workspace_path,
        "agent_routing": agent_routing_config_payload(config),
        "routing_mode": config.agent_routing_mode if config.agent_routing_enabled else "off",
        "routing_cycle": 1,
        "active_role": "executor",
        "agent_behavior": agent_behavior_payload(config),
        "quality_checklist": agent_quality_checklist_payload(config),
        "risk": normalize_optional_text(task.get("risk", "blocked")) if task else "blocked",
        "started_at": now,
        "ended_at": now,
        "status": status,
        "blocked_reasons": blocked_reasons,
        "metrics": {
            "runtime_minutes": 0,
            "token_count": 0,
            "cost_usd": 0,
        },
        "touched_files": [],
        "validation_evidence": [],
        "final_disposition": status,
        "links": [],
        "reusable_lessons": [],
        "runner_events": [],
    }


def orchestration_file_snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not root.exists() or not root.is_dir():
        return snapshot
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in KERNEL_SKIP_DIRS for part in relative.parts):
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
        snapshot[relative.as_posix()] = digest
    return snapshot


def compare_orchestration_snapshots(before: dict[str, str], after: dict[str, str]) -> list[str]:
    paths = sorted(set(before) | set(after))
    changed: list[str] = []
    for path in paths:
        if before.get(path) != after.get(path):
            changed.append(path)
    return changed


def redact_runner_text(text: str) -> str:
    redacted = text
    redacted = re.sub(r"(?i)(api[_-]?key|token|secret|password|credential)(\\s*[=:]\\s*)\\S+", r"\\1\\2[REDACTED]", redacted)
    return redacted[:8000]


def prepare_orchestration_runner_workspace(
    config: ProjectConfig,
    task: dict[str, object] | None,
) -> tuple[Path, list[str], dict[str, object]]:
    mode = config.orchestration_workspace_mode
    record: dict[str, object] = {
        "mode": mode,
        "prepared": False,
        "cleanup_policy": "preserve",
        "root_mutation_allowed": config.orchestration_allow_project_root_runner,
    }
    if task is None:
        return config.root, ["task is required before preparing a runner workspace"], record
    workspace_path_text, workspace_errors = orchestration_workspace_for_task(config, task)
    if workspace_errors:
        return config.root, workspace_errors, record
    if mode == "none":
        if config.orchestration_runner in {"shell-command", "codex-sdk", "codex-app-server"} and not config.orchestration_allow_project_root_runner:
            return config.root, [f"workspace_mode `none` cannot run {config.orchestration_runner} without allow_project_root_runner = true"], record
        record["prepared"] = True
        record["path"] = str(config.root)
        return config.root, [], record
    if mode == "copy":
        workspace_path = Path(workspace_path_text)
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        workspace_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(config.root, workspace_path, ignore=shutil.ignore_patterns(*sorted(KERNEL_SKIP_DIRS)))
        record["prepared"] = True
        record["path"] = str(workspace_path)
        return workspace_path, [], record
    return config.root, [f"workspace_mode `{mode}` is not implemented for runner `{config.orchestration_runner}`"], record


def run_shell_command_adapter(config: ProjectConfig, run: dict[str, object], task: dict[str, object] | None) -> dict[str, object]:
    command = config.orchestration_runner_command
    if not command:
        run["status"] = "blocked"
        run["blocked_reasons"] = [*normalize_task_string_list(run.get("blocked_reasons")), "runner_command is required for shell-command runner"]
        return run
    workspace, workspace_errors, workspace_record = prepare_orchestration_runner_workspace(config, task)
    run["workspace_path"] = str(workspace)
    run["workspace"] = workspace_record
    if workspace_errors:
        run["status"] = "blocked"
        run["blocked_reasons"] = [*normalize_task_string_list(run.get("blocked_reasons")), *workspace_errors]
        return run
    before = orchestration_file_snapshot(workspace)
    start = datetime.now(timezone.utc)
    run["runner_events"] = [
        {
            "event": "start",
            "created_at": current_utc_timestamp(),
            "runner": "shell-command",
            "cwd": str(workspace),
        }
    ]
    env = os.environ.copy()
    role_payload = agent_routing_role_payload(config, "executor")
    env.update(
        {
            "SULA_RUN_ID": normalize_optional_text(run.get("run_id", "")),
            "SULA_TASK_ID": normalize_optional_text(run.get("task_id", "")),
            "SULA_TASK_TITLE": normalize_optional_text(task.get("title", "")) if task else "",
            "SULA_AGENT_QUALITY_POLICY": config.agent_quality_policy,
            "SULA_AGENT_ROLE": "executor",
            "SULA_MODEL_PROVIDER": normalize_optional_text(role_payload.get("provider", "")),
            "SULA_MODEL_NAME": normalize_optional_text(role_payload.get("model", "")),
            "SULA_MODEL_REASONING_EFFORT": normalize_optional_text(role_payload.get("reasoning_effort", "")),
            "SULA_RUNNER_EFFORT": runner_effort_for_role(config, role_payload),
            "SULA_ROUTING_CYCLE": str(run.get("routing_cycle", 1)),
        }
    )
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=max(1, config.orchestration_max_run_minutes) * 60,
        )
        stdout = redact_runner_text(completed.stdout or "")
        stderr = redact_runner_text(completed.stderr or "")
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = redact_runner_text(exc.stdout if isinstance(exc.stdout, str) else "")
        stderr = redact_runner_text(exc.stderr if isinstance(exc.stderr, str) else "")
        returncode = 124
        timed_out = True
    response_payload = None
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                response_payload = parsed
        except json.JSONDecodeError:
            response_payload = None
    return apply_agent_runner_response(
        config,
        run,
        runner_name="shell-command",
        workspace=workspace,
        before=before,
        start=start,
        returncode=returncode,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        response_payload=response_payload,
    )


def codex_runner_request_payload(config: ProjectConfig, run: dict[str, object], task: dict[str, object] | None, workspace: Path) -> dict[str, object]:
    role = normalize_optional_text(run.get("active_role", "executor")) or "executor"
    role_payload = agent_routing_role_payload(config, role)
    return {
        "version": VERSION,
        "project": project_payload(config),
        "run": run,
        "task": task or {},
        "workspace_path": str(workspace),
        "quality_checklist": agent_quality_checklist_payload(config),
        "agent_routing": agent_routing_config_payload(config),
        "role": role,
        "model_hint": {
            "role": role,
            "provider": normalize_optional_text(role_payload.get("provider", "")),
            "model": normalize_optional_text(role_payload.get("model", "")),
            "reasoning_effort": normalize_optional_text(role_payload.get("reasoning_effort", "")),
            "runner_effort": runner_effort_for_role(config, role_payload),
        },
        "write_access": bool(role_payload.get("write_access", False)),
        "routing_cycle": int(run.get("routing_cycle", 1) or 1),
    }


def apply_agent_runner_response(
    config: ProjectConfig,
    run: dict[str, object],
    *,
    runner_name: str,
    workspace: Path,
    before: dict[str, str],
    start: datetime,
    returncode: int,
    timed_out: bool,
    stdout: str,
    stderr: str,
    response_payload: dict[str, object] | None,
) -> dict[str, object]:
    end = datetime.now(timezone.utc)
    runtime_minutes = max(0, int((end - start).total_seconds() // 60))
    touched_files = compare_orchestration_snapshots(before, orchestration_file_snapshot(workspace))
    explicit_status = normalize_optional_text((response_payload or {}).get("status", "")).strip()
    status = explicit_status if explicit_status in ORCHESTRATION_RUN_STATUSES else ("failed" if timed_out or returncode != 0 else "human-review")
    evidence_summary = normalize_optional_text((response_payload or {}).get("summary", "")).strip()
    if not evidence_summary:
        evidence_summary = (
            f"{runner_name} completed with exit code {returncode}; acceptance criteria require review"
            if status == "human-review"
            else f"{runner_name} failed with exit code {returncode}"
        )
    response_touched = normalize_task_string_list((response_payload or {}).get("touched_files", []))
    run["status"] = status
    run["ended_at"] = current_utc_timestamp()
    run["metrics"] = {
        **({"runtime_minutes": runtime_minutes, "token_count": 0, "cost_usd": 0}),
        **({k: v for k, v in (response_payload or {}).get("metrics", {}).items()} if isinstance((response_payload or {}).get("metrics", {}), dict) else {}),
    }
    run["touched_files"] = sorted(set([*touched_files, *response_touched]))
    response_evidence = (response_payload or {}).get("validation_evidence", [])
    validation_evidence = [item for item in run.get("validation_evidence", []) if isinstance(item, dict)]
    if isinstance(response_evidence, list):
        validation_evidence.extend(item for item in response_evidence if isinstance(item, dict))
    validation_evidence.append(
        {
            "kind": runner_name,
            "summary": evidence_summary,
            "created_at": current_utc_timestamp(),
            "returncode": returncode,
            "timed_out": timed_out,
            "stdout": stdout,
            "stderr": stderr,
        }
    )
    run["validation_evidence"] = validation_evidence
    response_links = normalize_task_string_list((response_payload or {}).get("links", []))
    if response_links:
        run["links"] = sorted(set([*normalize_task_string_list(run.get("links")), *response_links]))
    run["runner_events"] = [
        *[item for item in run.get("runner_events", []) if isinstance(item, dict)],
        {
            "event": "finish",
            "created_at": current_utc_timestamp(),
            "runner": runner_name,
            "returncode": returncode,
            "status": status,
            "touched_file_count": len(run["touched_files"]),
        },
    ]
    run["final_disposition"] = status
    return run


def run_codex_sdk_adapter(config: ProjectConfig, run: dict[str, object], task: dict[str, object] | None) -> dict[str, object]:
    command = config.orchestration_runner_command
    if not command:
        run["status"] = "blocked"
        run["blocked_reasons"] = [*normalize_task_string_list(run.get("blocked_reasons")), "runner_command is required for codex-sdk runner"]
        return run
    workspace, workspace_errors, workspace_record = prepare_orchestration_runner_workspace(config, task)
    run["workspace_path"] = str(workspace)
    run["workspace"] = workspace_record
    if workspace_errors:
        run["status"] = "blocked"
        run["blocked_reasons"] = [*normalize_task_string_list(run.get("blocked_reasons")), *workspace_errors]
        return run
    before = orchestration_file_snapshot(workspace)
    start = datetime.now(timezone.utc)
    run["runner_events"] = [
        *[item for item in run.get("runner_events", []) if isinstance(item, dict)],
        {"event": "start", "created_at": current_utc_timestamp(), "runner": "codex-sdk", "cwd": str(workspace)},
    ]
    request_payload = codex_runner_request_payload(config, run, task, workspace)
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            input=json.dumps(request_payload, ensure_ascii=True),
            capture_output=True,
            text=True,
            timeout=max(1, config.orchestration_max_run_minutes) * 60,
        )
        stdout = redact_runner_text(completed.stdout or "")
        stderr = redact_runner_text(completed.stderr or "")
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = redact_runner_text(exc.stdout if isinstance(exc.stdout, str) else "")
        stderr = redact_runner_text(exc.stderr if isinstance(exc.stderr, str) else "")
        returncode = 124
        timed_out = True
    response_payload = None
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                response_payload = parsed
        except json.JSONDecodeError:
            response_payload = None
    return apply_agent_runner_response(
        config,
        run,
        runner_name="codex-sdk",
        workspace=workspace,
        before=before,
        start=start,
        returncode=returncode,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        response_payload=response_payload,
    )


def run_codex_app_server_adapter(config: ProjectConfig, run: dict[str, object], task: dict[str, object] | None) -> dict[str, object]:
    endpoint = config.orchestration_runner_endpoint
    if not endpoint:
        run["status"] = "blocked"
        run["blocked_reasons"] = [*normalize_task_string_list(run.get("blocked_reasons")), "runner_endpoint is required for codex-app-server runner"]
        return run
    workspace, workspace_errors, workspace_record = prepare_orchestration_runner_workspace(config, task)
    run["workspace_path"] = str(workspace)
    run["workspace"] = workspace_record
    if workspace_errors:
        run["status"] = "blocked"
        run["blocked_reasons"] = [*normalize_task_string_list(run.get("blocked_reasons")), *workspace_errors]
        return run
    before = orchestration_file_snapshot(workspace)
    start = datetime.now(timezone.utc)
    run["runner_events"] = [
        *[item for item in run.get("runner_events", []) if isinstance(item, dict)],
        {"event": "start", "created_at": current_utc_timestamp(), "runner": "codex-app-server", "endpoint": endpoint},
    ]
    request_payload = codex_runner_request_payload(config, run, task, workspace)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token_env = config.orchestration_runner_token_env
    if token_env and os.environ.get(token_env):
        headers["Authorization"] = f"Bearer {os.environ[token_env]}"
    req = request.Request(endpoint, data=json.dumps(request_payload, ensure_ascii=True).encode("utf-8"), headers=headers, method="POST")
    response_payload: dict[str, object] | None = None
    stdout = ""
    stderr = ""
    returncode = 0
    timed_out = False
    try:
        with request.urlopen(req, timeout=max(1, config.orchestration_max_run_minutes) * 60) as response:
            stdout = redact_runner_text(response.read().decode("utf-8"))
            parsed = json.loads(stdout or "{}")
            if isinstance(parsed, dict):
                response_payload = parsed
    except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        returncode = 1
        stderr = redact_runner_text(str(exc))
    return apply_agent_runner_response(
        config,
        run,
        runner_name="codex-app-server",
        workspace=workspace,
        before=before,
        start=start,
        returncode=returncode,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        response_payload=response_payload,
    )


def create_orchestration_run_payload(config: ProjectConfig, task_id: str) -> tuple[dict[str, object], int]:
    task, task_issues = orchestration_find_task(config, task_id)
    blocked_reasons = list(task_issues)
    if not config.orchestration_enabled:
        blocked_reasons.append("orchestration is disabled in the manifest")
    if task is None:
        blocked_reasons.append(f"task not found: {task_id}")
    elif task.get("blocked_reasons"):
        blocked_reasons.extend(str(item) for item in task.get("blocked_reasons", []))
    runs = read_orchestration_runs(config)
    budget = orchestration_budget_payload(config, runs)
    if budget["exhausted"]:
        blocked_reasons.append("daily orchestration budget is exhausted")
    workspace_path = ""
    if task is not None:
        workspace_path, workspace_errors = orchestration_workspace_for_task(config, task)
        blocked_reasons.extend(workspace_errors)
    status = "blocked" if blocked_reasons else "human-review"
    evidence = []
    if not blocked_reasons:
        if config.orchestration_runner == "dry-run":
            evidence.append(
                {
                    "kind": "dry-run",
                    "summary": "Dry-run runner exercised scheduling, policy, workspace, and record persistence without mutating project files.",
                    "created_at": current_utc_timestamp(),
                }
            )
    run = build_orchestration_run_record(
        config,
        task,
        task_id=task_id,
        status=status,
        blocked_reasons=blocked_reasons,
        workspace_path=workspace_path,
    )
    if blocked_reasons:
        record_orchestration_stage(
            config,
            run=run,
            task=task,
            stage="blocked",
            role="host",
            state="blocked",
            summary="Orchestration run is blocked before execution.",
            next_action="Resolve blocked reasons, then rerun orchestration.",
        )
    else:
        record_orchestration_stage(
            config,
            run=run,
            task=task,
            stage="plan",
            role="planner",
            state="completed",
            summary="Planner role resolved task intent, acceptance criteria, and runner route.",
            next_action="Dispatch executor through the configured runner boundary.",
        )
        run["runner_events"] = [
            *[item for item in run.get("runner_events", []) if isinstance(item, dict)],
            {
                "event": "route",
                "created_at": current_utc_timestamp(),
                "mode": config.agent_routing_mode if config.agent_routing_enabled else "off",
                "planner": agent_routing_role_payload(config, "planner"),
                "executor": agent_routing_role_payload(config, "executor"),
                "verifier": agent_routing_role_payload(config, "verifier"),
                "reviewer": agent_routing_role_payload(config, "reviewer"),
            },
        ]
        record_orchestration_stage(
            config,
            run=run,
            task=task,
            stage="execute",
            role="executor",
            state="running" if config.orchestration_runner != "dry-run" else "completed",
            summary=(
                "Executor is running through the configured runner boundary."
                if config.orchestration_runner != "dry-run"
                else "Dry-run executor recorded scheduling without mutating files."
            ),
            next_action="Run verifier checks after executor returns.",
        )
    run["validation_evidence"] = evidence
    if not blocked_reasons and config.orchestration_runner == "shell-command":
        run = run_shell_command_adapter(config, run, task)
        status = normalize_optional_text(run.get("status", status)) or status
    if not blocked_reasons and config.orchestration_runner == "codex-sdk":
        run = run_codex_sdk_adapter(config, run, task)
        status = normalize_optional_text(run.get("status", status)) or status
    if not blocked_reasons and config.orchestration_runner == "codex-app-server":
        run = run_codex_app_server_adapter(config, run, task)
        status = normalize_optional_text(run.get("status", status)) or status
    if not blocked_reasons:
        record_orchestration_stage(
            config,
            run=run,
            task=task,
            stage="verify",
            role="verifier",
            state="completed" if normalize_task_string_list(run.get("validation_evidence")) or run.get("validation_evidence") else "pending",
            summary="Verifier evidence has been collected for closeout review.",
            next_action="Reviewer should compare evidence, touched files, and acceptance criteria.",
        )
        review_state = "accepted" if normalize_optional_text(run.get("status", "")) == "accepted" else "human-review"
        record_orchestration_stage(
            config,
            run=run,
            task=task,
            stage="review",
            role="reviewer",
            state=review_state,
            summary="Reviewer gate is ready; model review does not replace verification evidence.",
            next_action="Accept with orchestration close when evidence satisfies the task.",
        )
    append_orchestration_run(config, run)
    latest = {
        "version": VERSION,
        "updated_at": current_utc_timestamp(),
        "latest_run": run,
        "budget": orchestration_budget_payload(config, [*runs, run]),
    }
    write_orchestration_latest(config, latest)
    payload = {
        "command": "orchestration.run",
        "status": status,
        "project": project_payload(config),
        "run": run,
    }
    return payload, 0 if status not in {"blocked", "failed", "cancelled"} else 1


def orchestration_run(config: ProjectConfig, args: argparse.Namespace) -> int:
    payload, code = create_orchestration_run_payload(config, args.task_id)
    if json_output_requested(args):
        emit_json(payload)
        return code
    run = payload["run"]
    print(f"Orchestration run {run['run_id']}: {payload['status']}")
    for item in run.get("blocked_reasons", []):
        print(f"  - {item}")
    return code


def normalize_orchestration_evidence(values: list[str]) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for value in values:
        summary = normalize_optional_text(value).strip()
        if not summary:
            continue
        evidence.append(
            {
                "kind": "operator-evidence",
                "summary": summary,
                "created_at": current_utc_timestamp(),
            }
        )
    return evidence


def is_orchestration_url(value: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*://", value.strip(), flags=re.IGNORECASE))


def is_orchestration_pull_request_url(value: str) -> bool:
    lowered = value.strip().lower()
    return bool(
        re.search(r"https?://[^/]*github\.com/[^/]+/[^/]+/pull/\d+", lowered)
        or re.search(r"https?://[^/]*gitlab\.[^/]+/.+/-/merge_requests/\d+", lowered)
        or re.search(r"https?://[^/]*bitbucket\.[^/]+/.+/pull-requests/\d+", lowered)
    )


def is_orchestration_provider_url(value: str) -> bool:
    lowered = value.strip().lower()
    return any(
        marker in lowered
        for marker in [
            "docs.google.com/document/",
            "docs.google.com/spreadsheets/",
            "drive.google.com/",
        ]
    )


def remote_verification_attempt_allowed(config: ProjectConfig) -> bool:
    return config.orchestration_remote_verification_policy != "reference-only"


def remote_verification_required(config: ProjectConfig) -> bool:
    return config.orchestration_remote_verification_policy == "required"


def pr_reference_parts(value: str) -> dict[str, str]:
    match = re.search(r"https?://[^/]*github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)", value.strip(), flags=re.IGNORECASE)
    if match:
        return {
            "provider": "github",
            "owner": match.group("owner"),
            "repo": match.group("repo"),
            "number": match.group("number"),
        }
    match = re.search(r"https?://(?P<host>[^/]*gitlab\.[^/]+)/(?P<project>.+)/-/merge_requests/(?P<number>\d+)", value.strip(), flags=re.IGNORECASE)
    if match:
        return {
            "provider": "gitlab",
            "host": match.group("host"),
            "project": match.group("project"),
            "number": match.group("number"),
        }
    match = re.search(r"https?://(?P<host>[^/]*bitbucket\.[^/]+)/(?P<project>.+)/pull-requests/(?P<number>\d+)", value.strip(), flags=re.IGNORECASE)
    if match:
        return {
            "provider": "bitbucket",
            "host": match.group("host"),
            "project": match.group("project"),
            "number": match.group("number"),
        }
    return {}


def load_remote_verification_fixture(env_name: str, keys: list[str]) -> dict[str, object] | None:
    fixture_dir_raw = os.environ.get(env_name, "").strip()
    if not fixture_dir_raw:
        return None
    fixture_dir = Path(fixture_dir_raw)
    candidates: list[Path] = []
    for key in keys:
        if not key:
            continue
        candidates.append(fixture_dir / f"{sanitize_slug(key)}.json")
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "remote_status": "fixture-invalid-json",
                "remote_verified": False,
                "remote_message": f"invalid fixture JSON: {candidate}",
            }
        if not isinstance(data, dict):
            return {
                "remote_status": "fixture-invalid-payload",
                "remote_verified": False,
                "remote_message": f"fixture payload must be a JSON object: {candidate}",
            }
        return data
    return None


def normalize_pr_checks_summary(payload: dict[str, object]) -> dict[str, object]:
    raw = payload.get("checks_summary", payload.get("checks", {}))
    if isinstance(raw, dict):
        state = normalize_optional_text(raw.get("state", raw.get("status", ""))).lower()
        counts_raw = raw.get("counts", {})
        counts = counts_raw if isinstance(counts_raw, dict) else {}
        total = int(raw.get("total", counts.get("total", 0)) or 0)
        passed = int(raw.get("passed", counts.get("passed", counts.get("success", 0))) or 0)
        failed = int(raw.get("failed", counts.get("failed", counts.get("failure", 0))) or 0)
        pending = int(raw.get("pending", counts.get("pending", counts.get("queued", 0))) or 0)
        action_required = int(raw.get("action_required", raw.get("actionRequired", counts.get("action_required", 0))) or 0)
    elif isinstance(raw, list):
        normalized_states = [normalize_optional_text(item.get("state", item.get("status", ""))).lower() for item in raw if isinstance(item, dict)]
        total = len(normalized_states)
        passed = sum(1 for item in normalized_states if item in {"success", "passed", "pass", "ok", "completed"})
        failed = sum(1 for item in normalized_states if item in {"failed", "failure", "error", "cancelled"})
        pending = sum(1 for item in normalized_states if item in {"pending", "queued", "in_progress", "running", "waiting"})
        action_required = sum(1 for item in normalized_states if item in {"action_required", "required"})
        state = ""
    else:
        total = passed = failed = pending = action_required = 0
        state = ""
    if not state:
        if failed:
            state = "failed"
        elif action_required:
            state = "action_required"
        elif pending:
            state = "pending"
        elif total and passed >= total:
            state = "passed"
        else:
            state = "unknown"
    return {
        "state": state,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "action_required": action_required,
    }


def normalize_pr_review_summary(payload: dict[str, object], *, review_decision: str) -> dict[str, object]:
    raw = payload.get("review_summary", payload)
    if not isinstance(raw, dict):
        raw = {}
    unresolved = int(raw.get("unresolved_threads_count", raw.get("unresolved_review_threads_count", payload.get("unresolved_review_threads_count", 0))) or 0)
    comments = int(raw.get("comments_requiring_action_count", raw.get("review_comments_requiring_action_count", payload.get("review_comments_requiring_action_count", 0))) or 0)
    decision = normalize_optional_text(raw.get("review_decision", review_decision)).lower()
    if not decision:
        decision = "unknown"
    return {
        "review_decision": decision,
        "unresolved_threads_count": unresolved,
        "comments_requiring_action_count": comments,
        "requires_action": unresolved > 0 or comments > 0 or decision in {"changes_requested", "review_required", "action_required"},
    }


def pr_closeout_state(*, state: str, merged: bool, checks_summary: dict[str, object], review_summary: dict[str, object]) -> str:
    if merged:
        return "merged"
    if review_summary.get("requires_action"):
        return "action-required"
    if checks_summary.get("failed") or checks_summary.get("state") == "failed":
        return "failed"
    if checks_summary.get("pending") or checks_summary.get("state") == "pending":
        return "pending"
    if normalize_optional_text(state).lower() == "closed":
        return "closed"
    if checks_summary.get("state") == "passed":
        return "passing"
    return "unknown"


def verify_pull_request_reference(config: ProjectConfig, link: str) -> dict[str, object]:
    del config
    parts = pr_reference_parts(link)
    provider = parts.get("provider", "unknown")
    fixture_keys = [
        link,
        f"{provider}-{parts.get('owner', parts.get('host', ''))}-{parts.get('repo', parts.get('project', ''))}-{parts.get('number', '')}",
        hashlib.sha256(link.encode("utf-8")).hexdigest(),
    ]
    fixture = load_remote_verification_fixture("SULA_PR_VERIFICATION_FIXTURE_DIR", fixture_keys)
    if fixture is not None:
        state = normalize_optional_text(fixture.get("state", ""))
        merged = bool(fixture.get("merged", False))
        review_decision = normalize_optional_text(fixture.get("review_decision", fixture.get("reviewDecision", "")))
        checks_summary = normalize_pr_checks_summary(fixture)
        review_summary = normalize_pr_review_summary(fixture, review_decision=review_decision)
        verified = bool(fixture.get("remote_verified", fixture.get("verified", False))) or merged or state.lower() in {"open", "closed", "merged"}
        return {
            "remote_status": "ok" if verified else "fixture-unverified",
            "remote_verified": verified,
            "remote_provider": provider,
            "remote_state": state,
            "merged": merged,
            "review_decision": review_decision,
            "checks_summary": checks_summary,
            "review_summary": review_summary,
            "ci_state": checks_summary["state"],
            "unresolved_review_threads_count": review_summary["unresolved_threads_count"],
            "review_comments_requiring_action_count": review_summary["comments_requiring_action_count"],
            "closeout_state": pr_closeout_state(state=state, merged=merged, checks_summary=checks_summary, review_summary=review_summary),
            "remote_source": "fixture",
        }
    if provider == "github":
        token = os.environ.get("SULA_GITHUB_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
        if not token:
            return {"remote_status": "not-configured", "remote_verified": False, "remote_provider": provider}
        api_url = f"https://api.github.com/repos/{parse.quote(parts['owner'])}/{parse.quote(parts['repo'])}/pulls/{parse.quote(parts['number'])}"
        req = request.Request(api_url, headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"})
        try:
            with request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            return {"remote_status": "error", "remote_verified": False, "remote_provider": provider, "remote_message": str(exc)}
        if not isinstance(payload, dict):
            return {"remote_status": "invalid-response", "remote_verified": False, "remote_provider": provider}
        checks_summary = normalize_pr_checks_summary(payload)
        review_summary = normalize_pr_review_summary(payload, review_decision=normalize_optional_text(payload.get("review_decision", "")))
        return {
            "remote_status": "ok",
            "remote_verified": True,
            "remote_provider": provider,
            "remote_state": normalize_optional_text(payload.get("state", "")),
            "merged": bool(payload.get("merged", False)),
            "review_decision": normalize_optional_text(payload.get("review_decision", "")),
            "checks_summary": checks_summary,
            "review_summary": review_summary,
            "ci_state": checks_summary["state"],
            "unresolved_review_threads_count": review_summary["unresolved_threads_count"],
            "review_comments_requiring_action_count": review_summary["comments_requiring_action_count"],
            "closeout_state": pr_closeout_state(state=normalize_optional_text(payload.get("state", "")), merged=bool(payload.get("merged", False)), checks_summary=checks_summary, review_summary=review_summary),
            "remote_source": "github-api",
        }
    return {"remote_status": "not-configured", "remote_verified": False, "remote_provider": provider}


def verify_provider_reference(config: ProjectConfig, artifact: dict[str, object] | None, link: str) -> dict[str, object]:
    provider_item_id = normalize_optional_text(artifact.get("provider_item_id", "")) if artifact else ""
    provider_item_kind = normalize_optional_text(artifact.get("provider_item_kind", "")) if artifact else ""
    provider_item_url = normalize_optional_text(artifact.get("provider_item_url", "")) if artifact else link
    storage_provider = normalize_optional_text(artifact.get("storage_provider", "")) if artifact else config.storage_provider
    if not provider_item_id or not provider_item_kind:
        return {"remote_status": "not-configured", "remote_verified": False}
    has_fixture = bool(os.environ.get("SULA_PROVIDER_FIXTURE_DIR", "").strip())
    has_google_token = bool(os.environ.get("SULA_GOOGLE_ACCESS_TOKEN", "").strip()) or config.project_google_oauth_file.exists()
    if not has_fixture and not has_google_token and config.orchestration_remote_verification_policy != "required":
        return {"remote_status": "not-configured", "remote_verified": False}
    try:
        adapter = create_provider_adapter(storage_provider or config.storage_provider, oauth_store_path=config.project_google_oauth_file)
        snapshot = adapter.fetch_item(
            provider_item_id=provider_item_id,
            provider_item_kind=provider_item_kind,
            provider_item_url=provider_item_url,
        )
    except ProviderAdapterError as exc:
        return {
            "remote_status": exc.code,
            "remote_verified": False,
            "remote_message": exc.message,
            "retryable": exc.retryable,
        }
    return {
        "remote_status": "ok",
        "remote_verified": True,
        "remote_provider": snapshot.provider,
        "provider_title": snapshot.provider_title,
        "provider_modified_at": snapshot.provider_modified_at,
        "provider_revision_id": snapshot.provider_revision_id,
        "remote_source": snapshot.truth_source_reason,
    }


def artifact_match_tokens(entry: dict[str, object]) -> set[str]:
    tokens = {
        normalize_optional_text(entry.get("id", "")),
        normalize_optional_text(entry.get("identity_key", "")),
        normalize_optional_text(entry.get("provider_item_id", "")),
        normalize_optional_text(entry.get("provider_item_url", "")),
        normalize_optional_text(entry.get("project_relative_path", "")),
        normalize_optional_text(entry.get("path", "")),
        normalize_optional_text(artifact_display_path(entry)),
    }
    local_access_paths = entry.get("local_access_paths", [])
    if isinstance(local_access_paths, list):
        tokens.update(normalize_optional_text(item) for item in local_access_paths)
    normalized_tokens: set[str] = set()
    for token in tokens:
        cleaned = normalize_optional_text(token).strip()
        if not cleaned:
            continue
        normalized_tokens.add(cleaned)
        if not is_orchestration_url(cleaned):
            try:
                normalized_tokens.add(normalize_project_relative_path(cleaned))
            except SystemExit:
                pass
    return normalized_tokens


def resolve_orchestration_verification_link(
    config: ProjectConfig,
    catalog: dict[str, object],
    raw_link: str,
) -> dict[str, object]:
    link = normalize_optional_text(raw_link).strip()
    adapters = set(config.orchestration_verification_adapters)
    is_url = is_orchestration_url(link)
    normalized_path = ""
    if link and not is_url:
        try:
            normalized_path = normalize_project_relative_path(link)
        except SystemExit:
            normalized_path = ""
    check: dict[str, object] = {
        "input": link,
        "link": link,
        "kind": "unknown",
        "adapter": "none",
        "resolved": False,
        "exists": False,
        "verification_state": "unresolved",
    }
    artifacts = [item for item in catalog.get("artifacts", []) if isinstance(item, dict)]
    if "artifact-catalog" in adapters or "provider-metadata" in adapters:
        for artifact in artifacts:
            tokens = artifact_match_tokens(artifact)
            if link not in tokens and (not normalized_path or normalized_path not in tokens):
                continue
            provider_item_id = normalize_optional_text(artifact.get("provider_item_id", ""))
            provider_item_url = normalize_optional_text(artifact.get("provider_item_url", ""))
            provider_item_kind = normalize_optional_text(artifact.get("provider_item_kind", ""))
            has_provider_metadata = bool(provider_item_id or provider_item_url or provider_item_kind)
            adapter = "provider-metadata" if has_provider_metadata and "provider-metadata" in adapters else "artifact-catalog"
            check.update(
                {
                    "kind": "provider-artifact" if has_provider_metadata else "artifact",
                    "adapter": adapter,
                    "resolved": True,
                    "exists": True,
                    "verification_state": "catalog-matched",
                    "artifact_id": normalize_optional_text(artifact.get("id", "")),
                    "artifact_path": normalize_optional_text(artifact_display_path(artifact)),
                    "provider_item_id": provider_item_id,
                    "provider_item_kind": provider_item_kind,
                    "provider_item_url": provider_item_url,
                }
            )
            if has_provider_metadata and "provider-metadata" in adapters:
                remote = verify_provider_reference(config, artifact, link) if remote_verification_attempt_allowed(config) else {"remote_status": "reference-only", "remote_verified": False}
                check.update(
                    {
                        **remote,
                        "remote_verification_required": remote_verification_required(config),
                    }
                )
            return check
    if normalized_path and "local-file" in adapters and (config.root / normalized_path).exists():
        check.update(
            {
                "kind": "local-file",
                "adapter": "local-file",
                "resolved": True,
                "exists": True,
                "verification_state": "file-exists",
                "path": normalized_path,
            }
        )
        return check
    if is_url and is_orchestration_pull_request_url(link) and "pull-request-url" in adapters:
        remote = verify_pull_request_reference(config, link) if remote_verification_attempt_allowed(config) else {"remote_status": "reference-only", "remote_verified": False}
        check.update(
            {
                "kind": "pull-request-url",
                "adapter": "pull-request-url",
                "resolved": True,
                "exists": True,
                "verification_state": "reference-only" if not remote.get("remote_verified") else "remote-verified",
                **remote,
                "remote_verification_required": remote_verification_required(config),
            }
        )
        return check
    if is_url and is_orchestration_provider_url(link) and "provider-metadata" in adapters:
        remote = {"remote_status": "not-configured", "remote_verified": False}
        check.update(
            {
                "kind": "provider-item-url",
                "adapter": "provider-metadata",
                "resolved": True,
                "exists": True,
                "verification_state": "reference-only",
                **remote,
                "remote_verification_required": remote_verification_required(config),
            }
        )
        return check
    if is_url and "url" in adapters:
        check.update(
            {
                "kind": "url",
                "adapter": "url",
                "resolved": True,
                "exists": True,
                "verification_state": "reference-only",
            }
        )
        return check
    if normalized_path:
        check.update({"kind": "local-file", "adapter": "local-file", "path": normalized_path})
    elif is_url:
        check.update({"kind": "url", "adapter": "url"})
    return check


def evaluate_orchestration_closeout(
    config: ProjectConfig,
    run: dict[str, object],
    task: dict[str, object] | None,
    evidence: list[object],
    touched_files: list[str],
    links: list[str],
    lessons: list[str],
) -> dict[str, object]:
    non_dry_run_evidence = [
        item
        for item in evidence
        if isinstance(item, dict) and normalize_optional_text(item.get("kind", "")) != "dry-run"
    ]
    workspace_path = Path(normalize_optional_text(run.get("workspace_path", "")) or str(config.root))
    touched_file_checks: list[dict[str, object]] = []
    for item in touched_files:
        normalized = normalize_project_relative_path(item)
        if not normalized:
            continue
        candidate_roots = [workspace_path, config.root] if workspace_path != config.root else [config.root]
        exists = any((root / normalized).exists() for root in candidate_roots)
        touched_file_checks.append({"path": normalized, "exists": exists})
    catalog = load_artifact_catalog(config)
    verification_checks: list[dict[str, object]] = []
    for item in links:
        link = normalize_optional_text(item)
        if not link:
            continue
        verification_checks.append(resolve_orchestration_verification_link(config, catalog, link))
    evidence_summaries = " ".join(
        normalize_optional_text(item.get("summary", ""))
        for item in non_dry_run_evidence
        if isinstance(item, dict)
    ).lower()
    sula_check_requested = "sula check" in evidence_summaries
    sula_check_passed = None
    if sula_check_requested:
        try:
            fresh_digest = build_memory_digest(config, config.digest_file)
            if config.digest_file:
                config.digest_file.write_text(fresh_digest, encoding="utf-8")
        except Exception:
            pass
        sula_check_passed = daily_check(config, emit_output=False, skip_orchestration=True) == 0
    return {
        "has_closeout_evidence": bool(non_dry_run_evidence),
        "has_touched_file_summary": bool(touched_files),
        "has_links": bool(links),
        "has_promotion_candidates": bool(lessons),
        "touched_file_checks": touched_file_checks,
        "missing_touched_files": [item["path"] for item in touched_file_checks if not item["exists"]],
        "verification_adapters": config.orchestration_verification_adapters,
        "remote_verification_policy": config.orchestration_remote_verification_policy,
        "verification_checks": verification_checks,
        "link_checks": verification_checks,
        "unresolved_links": [item["link"] for item in verification_checks if not item["resolved"]],
        "unverified_remote_links": [
            item["link"]
            for item in verification_checks
            if item.get("remote_verification_required") and not item.get("remote_verified")
        ],
        "sula_check_requested": sula_check_requested,
        "sula_check_passed": sula_check_passed,
        "verification_required": config.agent_require_verification,
        "success_criteria_policy": config.agent_success_criteria_policy,
    }


def orchestration_close(config: ProjectConfig, args: argparse.Namespace) -> int:
    runs = read_orchestration_runs(config)
    target_index = -1
    for index, run in enumerate(runs):
        if normalize_optional_text(run.get("run_id", "")) == args.run_id:
            target_index = index
    issues: list[str] = []
    if target_index < 0:
        issues.append(f"run not found: {args.run_id}")
        payload = {
            "command": "orchestration.close",
            "status": "blocked",
            "project": project_payload(config),
            "run_id": args.run_id,
            "issues": issues,
        }
        if json_output_requested(args):
            emit_json(payload)
            return 1
        print(f"Orchestration close {args.run_id}: blocked")
        for item in issues:
            print(f"  - {item}")
        return 1

    run = dict(runs[target_index])
    task, task_issues = orchestration_find_task(config, normalize_optional_text(run.get("task_id", "")))
    existing_evidence = run.get("validation_evidence", [])
    if not isinstance(existing_evidence, list):
        existing_evidence = []
    new_evidence = normalize_orchestration_evidence(args.evidence)
    all_evidence = [*existing_evidence, *new_evidence]
    touched_files = normalize_task_string_list(run.get("touched_files"))
    for item in normalize_task_string_list(args.touched_file):
        touched_files.append(normalize_project_relative_path(item))
    links = normalize_task_string_list(run.get("links"))
    links.extend(normalize_task_string_list(args.link))
    lessons = normalize_task_string_list(run.get("reusable_lessons"))
    lessons.extend(normalize_task_string_list(args.lesson))

    closeout_evidence = [
        item
        for item in all_evidence
        if isinstance(item, dict) and normalize_optional_text(item.get("kind", "")) != "dry-run"
    ]
    closeout_evaluation = evaluate_orchestration_closeout(config, run, task, all_evidence, touched_files, links, lessons)
    if not closeout_evidence:
        issues.append("accepted closeout requires validation evidence beyond dry-run scheduling")
    if args.accept and task_issues:
        issues.extend(f"task source issue during closeout: {item}" for item in task_issues)
    if args.accept and closeout_evaluation["missing_touched_files"]:
        issues.append(
            "accepted closeout references touched files that cannot be found: "
            + ", ".join(str(item) for item in closeout_evaluation["missing_touched_files"])
        )
    if args.accept and closeout_evaluation["unresolved_links"]:
        issues.append(
            "accepted closeout references links or artifacts that cannot be resolved: "
            + ", ".join(str(item) for item in closeout_evaluation["unresolved_links"])
        )
    if args.accept and closeout_evaluation["unverified_remote_links"]:
        issues.append(
            "accepted closeout requires remote verification for: "
            + ", ".join(str(item) for item in closeout_evaluation["unverified_remote_links"])
        )
    if args.accept and closeout_evaluation["sula_check_requested"] and closeout_evaluation["sula_check_passed"] is False:
        issues.append("accepted closeout requires `sula check` to pass because it was declared as validation evidence")
    if args.accept and normalize_optional_text(run.get("status", "")) in {"blocked", "failed", "cancelled"}:
        issues.append(f"cannot accept run in `{run.get('status')}` status")
    if issues:
        close_status = "blocked"
    elif args.accept:
        close_status = "accepted"
    else:
        close_status = "human-review"

    run["validation_evidence"] = all_evidence
    run["touched_files"] = sorted(set(touched_files))
    run["links"] = sorted(set(links))
    run["reusable_lessons"] = sorted(set(lessons))
    run["status"] = close_status if close_status != "blocked" else run.get("status", "human-review")
    run["final_disposition"] = close_status
    run["closed_at"] = current_utc_timestamp()
    run["closeout_issues"] = issues
    run["closeout_evaluation"] = closeout_evaluation
    runs[target_index] = run
    rewrite_orchestration_runs(config, runs)
    for lesson in lessons:
        append_orchestration_promotion_candidate(
            config,
            {
                "version": VERSION,
                "created_at": current_utc_timestamp(),
                "run_id": normalize_optional_text(run.get("run_id", "")),
                "task_id": normalize_optional_text(run.get("task_id", "")),
                "candidate_kind": "lesson",
                "target": "memory-or-feedback-review",
                "status": "proposed",
                "summary": lesson,
            },
        )
    latest = {
        "version": VERSION,
        "updated_at": current_utc_timestamp(),
        "latest_run": run,
        "budget": orchestration_budget_payload(config, runs),
    }
    write_orchestration_latest(config, latest)
    if close_status in {"accepted", "blocked"}:
        record_orchestration_stage(
            config,
            run=run,
            task=task,
            stage="closeout",
            role="acceptor",
            state=close_status,
            summary="Orchestration closeout evaluated operator evidence and policy gates.",
            next_action="Run Sula report/check before committing when this work unit is ready." if close_status == "accepted" else "Resolve closeout issues, then retry.",
        )
    payload = {
        "command": "orchestration.close",
        "status": close_status,
        "project": project_payload(config),
        "run": run,
        "issues": issues,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0 if close_status != "blocked" else 1
    print(f"Orchestration close {args.run_id}: {close_status}")
    for item in issues:
        print(f"  - {item}")
    if issues:
        suggestions: list[str] = []
        for issue in issues:
            lowered = issue.lower()
            if "missing touched files" in lowered or "unresolved links" in lowered:
                suggestions.append("Verify touched files and links exist, then retry with `--touched-file ... --link ...`")
            if "sula check" in lowered:
                suggestions.append("Run `sula check` and fix errors, then retry close")
            if "remote verification" in lowered or "unverified remote" in lowered:
                suggestions.append("Either set `remote_verification_policy = \"reference-only\"` in manifest, or resolve the remote links")
            if "blocked" in lowered or "cannot be found" in lowered:
                suggestions.append("Resolve blocked reasons listed above and retry with `--accept`")
        if suggestions:
            unique: list[str] = []
            for s in suggestions:
                if s not in unique:
                    unique.append(s)
            print("  Suggested next actions:")
            for s in unique:
                print(f"    - {s}")
    return 0 if close_status != "blocked" else 1


def rewrite_orchestration_runs(config: ProjectConfig, runs: list[dict[str, object]]) -> None:
    config.orchestration_state_root.mkdir(parents=True, exist_ok=True)
    orchestration_runs_path(config).write_text(
        "".join(json.dumps(run, ensure_ascii=True) + "\n" for run in runs),
        encoding="utf-8",
    )


def orchestration_cancel(config: ProjectConfig, args: argparse.Namespace) -> int:
    runs = read_orchestration_runs(config)
    changed = False
    now = current_utc_timestamp()
    for run in runs:
        if normalize_optional_text(run.get("run_id", "")) != args.run_id:
            continue
        if normalize_optional_text(run.get("status", "")) in {"accepted", "failed", "cancelled", "blocked", "human-review"}:
            continue
        run["status"] = "cancelled"
        run["ended_at"] = now
        run["final_disposition"] = "cancelled"
        record_orchestration_stage(
            config,
            run=run,
            task=None,
            stage="cancel",
            role="host",
            state="cancelled",
            summary="Run was cancelled by operator command.",
            next_action="Inspect timeline and start a new run if needed.",
        )
        changed = True
    if changed:
        rewrite_orchestration_runs(config, runs)
    payload = {
        "command": "orchestration.cancel",
        "status": "cancelled" if changed else "noop",
        "project": project_payload(config),
        "run_id": args.run_id,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Orchestration cancel {args.run_id}: {payload['status']}")
    return 0


def orchestration_stop_all(config: ProjectConfig, args: argparse.Namespace) -> int:
    runs = read_orchestration_runs(config)
    now = current_utc_timestamp()
    cancelled: list[str] = []
    for run in runs:
        if normalize_optional_text(run.get("status", "")) not in {"planned", "running"}:
            continue
        run["status"] = "cancelled"
        run["ended_at"] = now
        run["final_disposition"] = "cancelled"
        cancelled.append(normalize_optional_text(run.get("run_id", "")))
    if cancelled:
        rewrite_orchestration_runs(config, runs)
    payload = {
        "command": "orchestration.stop-all",
        "status": "ok",
        "project": project_payload(config),
        "cancelled_run_ids": cancelled,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Orchestration stop-all cancelled {len(cancelled)} runs")
    return 0


def handle_artifact_command(config: ProjectConfig, args: argparse.Namespace) -> int:
    if args.artifact_command == "create":
        return artifact_create(config, args)
    if args.artifact_command == "register":
        return artifact_register(config, args)
    if args.artifact_command == "materialize":
        return artifact_materialize(config, args)
    if args.artifact_command == "import-plan":
        return artifact_import_plan(config, args)
    if args.artifact_command == "locate":
        return artifact_locate(config, args)
    if args.artifact_command == "refresh":
        return artifact_refresh(config, args)
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
    summary = (
        args.summary.strip()
        or (
            f"{config.data['project']['name']} 的 {artifact_kind} 文件"
            if locale_family(config.content_locale) == "zh"
            else f"{artifact_kind} artifact for {config.data['project']['name']}"
        )
    )
    output_path.write_text(render_artifact_template(config, artifact_kind, args.title, summary, record_date, slot), encoding="utf-8")
    entry = register_artifact_entry(
        config,
        path=output_path.relative_to(config.root).as_posix(),
        artifact_kind=artifact_kind,
        title=args.title,
        slot=slot,
        summary=summary,
        date_value=record_date,
        project_relative_path=output_path.relative_to(config.root).as_posix(),
        local_access_paths=[output_path.relative_to(config.root).as_posix()],
        provider_item_id="",
        provider_item_kind=default_provider_item_kind(config, has_local_path=True),
        provider_item_url="",
        derived_from=[],
        source_of_truth="workspace",
        collaboration_mode="single-editor",
        artifact_role="workspace-source",
        last_refreshed_at=current_utc_timestamp(),
        last_provider_sync_at="",
    )
    refresh_kernel_state(config, event_type="artifact.create", summary=f"Created {artifact_kind} artifact `{args.title}`.")
    if json_output_requested(args):
        emit_json({"command": "artifact.create", "status": "ok", "project": project_payload(config), "artifact": entry})
        return 0
    if locale_family(config.interaction_locale) == "zh":
        print(f"已在 {output_path} 创建 {artifact_kind} 文件")
    else:
        print(f"Created {artifact_kind} artifact at {output_path}")
    return 0


def artifact_register(config: ProjectConfig, args: argparse.Namespace) -> int:
    ensure_artifact_catalog(config)
    path, relative_path = resolve_artifact_registration_path(config, args.path)
    requested_project_relative_path = normalize_project_relative_path(args.project_relative_path)
    provider_item_id = normalize_optional_text(args.provider_item_id).strip()
    provider_item_kind = normalize_optional_text(args.provider_item_kind).strip()
    provider_item_url = normalize_optional_text(args.provider_item_url).strip()
    if not relative_path and not requested_project_relative_path and not provider_item_id:
        raise SystemExit("Artifact registration requires --path, --project-relative-path, or --provider-item-id.")
    slot = artifact_slot_for_kind(config, args.kind.lower(), args.slot)
    summary_text = ""
    date_value = ""
    if path is not None:
        summary_text = source_summary(path)
        date_value = detect_source_date(path, summary_text) or ""
    if args.summary.strip():
        summary_text = args.summary.strip()
    if args.date:
        date_value = normalize_record_date(args.date)
    provisional_display_path = artifact_primary_path(
        path=relative_path,
        project_relative_path=requested_project_relative_path or relative_path,
        provider_item_id=provider_item_id,
        provider_item_kind=provider_item_kind,
    )
    default_title = path.name if path is not None else (PurePosixPath(provisional_display_path).name if provisional_display_path else provider_item_id or args.kind.lower())
    resolved_title = args.title or default_title
    project_relative_path = requested_project_relative_path or relative_path
    if provider_item_id and not requested_project_relative_path:
        project_relative_path = artifact_provider_relative_path(
            config,
            {"path": relative_path} if relative_path else None,
            slot=slot,
            date_value=date_value,
            title=resolved_title,
            fallback_path=relative_path,
        )
    display_path = artifact_primary_path(
        path=relative_path,
        project_relative_path=project_relative_path,
        provider_item_id=provider_item_id,
        provider_item_kind=provider_item_kind,
    )
    entry = register_artifact_entry(
        config,
        path=display_path,
        artifact_kind=args.kind.lower(),
        title=resolved_title,
        slot=slot,
        summary=summary_text or f"{args.kind.lower()} artifact for {config.data['project']['name']}",
        date_value=date_value,
        project_relative_path=project_relative_path,
        local_access_paths=[relative_path] if relative_path else [],
        provider_item_id=provider_item_id,
        provider_item_kind=provider_item_kind or default_provider_item_kind(config, has_local_path=path is not None),
        provider_item_url=provider_item_url,
        derived_from=normalize_artifact_derived_from(args.derived_from),
        source_of_truth=getattr(args, "source_of_truth", None),
        collaboration_mode=getattr(args, "collaboration_mode", None),
        artifact_role=getattr(args, "artifact_role", None),
        last_refreshed_at=getattr(args, "last_refreshed_at", None),
        last_provider_sync_at=getattr(args, "last_provider_sync_at", None),
    )
    refresh_kernel_state(config, event_type="artifact.register", summary=f"Registered artifact `{entry['title']}`.")
    if json_output_requested(args):
        emit_json({"command": "artifact.register", "status": "ok", "project": project_payload(config), "artifact": entry})
        return 0
    if locale_family(config.interaction_locale) == "zh":
        print(f"已登记文件 {artifact_display_path(entry)}")
    else:
        print(f"Registered artifact {artifact_display_path(entry)}")
    return 0


def artifact_locate(config: ProjectConfig, args: argparse.Namespace) -> int:
    refresh_report = None
    freshness_intent = detect_freshness_intent(args.q)
    effective_query = strip_freshness_intent_phrases(args.q) if freshness_intent else args.q
    if freshness_intent:
        refresh_report = refresh_provider_artifact_batch(
            config,
            query=effective_query,
            all_collaborative=False,
            limit=max(args.limit, 5),
            force=True,
            event_type="artifact.refresh.intent",
            event_summary_prefix="Refreshed provider-native truth sources before artifact locate",
        )
    catalog = load_artifact_catalog(config)
    results: list[dict[str, object]] = []
    query = effective_query.strip().lower()
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
                artifact_display_path(item),
                str(item.get("project_relative_path", "")),
                str(item.get("provider_item_id", "")),
                str(item.get("provider_item_kind", "")),
                str(item.get("provider_item_url", "")),
                str(item.get("summary", "")),
            ]
        ).lower()
        if query and query not in haystack:
            continue
        result = dict(item)
        result["display_path"] = artifact_display_path(item)
        result.update(artifact_truth_summary(config, item, catalog=catalog))
        if freshness_intent and not candidate_is_freshness_relevant(result):
            continue
        results.append(result)
    if freshness_intent:
        results.sort(
            key=lambda item: (
                bool(item.get("local_copy_stale_risk")),
                normalize_optional_text(item.get("freshness_status", "")) == "provider-metadata-missing",
                normalize_optional_text(item.get("truth_source_type", "")) == "provider-native",
                normalize_optional_text(item.get("last_provider_sync_at", "")),
                normalize_optional_text(item.get("date", "")),
                normalize_optional_text(item.get("display_path", "")),
            ),
            reverse=True,
        )
    else:
        results.sort(key=lambda item: (str(item.get("date", "")), str(item.get("kind", "")), str(item.get("display_path", ""))), reverse=True)
    results = results[: max(1, args.limit)]
    automation_result = automation_observe_event(
        config,
        source_kind="sula-cli",
        event_kind="artifact.locate.freshness" if freshness_intent else "artifact.locate",
        title="Sula artifact locate",
        summary=f"Artifact locate returned {len(results)} result(s).",
        identity_key=f"artifact-locate:{date.today().isoformat()}:{sanitize_slug(effective_query or 'empty')}",
        payload={"query": args.q, "effective_query": effective_query, "freshness_intent": freshness_intent, "refresh": refresh_report or {}},
    )
    if json_output_requested(args):
        emit_json(
            {
                "command": "artifact.locate",
                "status": "ok",
                "project": project_payload(config),
                "freshness_intent_detected": freshness_intent,
                "effective_query": effective_query,
                "refresh": refresh_report,
                "results": results,
            }
        )
        return 0
    print_sula_activity_feedback(config, automation_result)
    print(f"{config.data['project']['name']} 的文件产物：" if locale_family(config.interaction_locale) == "zh" else f"Artifacts for {config.data['project']['name']}:")
    if not results:
        print("  暂无文件。" if locale_family(config.interaction_locale) == "zh" else "  No artifacts.")
        return 0
    for item in results:
        truth_suffix = f" truth={item['truth_source_type']}" if item.get("truth_source_type") else ""
        refresh_suffix = f" refreshed={item['last_refreshed_at']}" if item.get("last_refreshed_at") else ""
        stale_suffix = " local-copy-risk=true" if item.get("local_copy_stale_risk") else ""
        provider_path_suffix = f" provider-path={item['provider_target_path']}" if item.get("provider_target_path") else ""
        missing_suffix = ""
        if item.get("missing_provider_metadata"):
            missing_suffix = " missing=" + ",".join(str(value) for value in item["missing_provider_metadata"])
        print(
            f"  - [{item['kind']}] {item['title']} :: {item['display_path']} ({item['slot']})"
            f"{truth_suffix}{refresh_suffix}{stale_suffix}{provider_path_suffix}{missing_suffix}"
        )
    return 0


def artifact_refresh(config: ProjectConfig, args: argparse.Namespace) -> int:
    query_value = None
    if getattr(args, "q", None):
        query_value = strip_freshness_intent_phrases(args.q) if detect_freshness_intent(args.q) else args.q
    refresh_report = refresh_provider_artifact_batch(
        config,
        artifact_id=getattr(args, "artifact_id", None),
        family_key=getattr(args, "family_key", None),
        query=query_value,
        all_collaborative=bool(getattr(args, "all_collaborative", False)),
        limit=args.limit,
        force=bool(getattr(args, "force", False)),
        event_type="artifact.refresh.command",
        event_summary_prefix="Refreshed provider-native artifact truth sources by explicit command",
    )
    automation_result = automation_observe_event(
        config,
        source_kind="sula-cli",
        event_kind="artifact.refresh",
        title="Sula artifact refresh",
        summary="Artifact refresh completed.",
        identity_key=f"artifact-refresh:{date.today().isoformat()}:{sanitize_slug(query_value or getattr(args, 'artifact_id', '') or getattr(args, 'family_key', '') or 'all')}",
        payload={"refresh": refresh_report},
    )
    payload = {
        "command": "artifact.refresh",
        "status": "ok",
        "project": project_payload(config),
        "refresh": refresh_report,
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print_sula_activity_feedback(config, automation_result)
    if locale_family(config.interaction_locale) == "zh":
        print(f"已尝试刷新 {refresh_report['attempted']} 个 provider 文件族，成功 {refresh_report['ok']} 个。")
    else:
        print(f"Attempted provider refresh for {refresh_report['attempted']} artifact families, {refresh_report['ok']} succeeded.")
    for item in refresh_report["results"]:
        reason_suffix = f" ({item.get('reason', '')})" if item.get("reason") else ""
        print(f"  - {item.get('artifact_id', item.get('family_key', 'unknown'))}: {item.get('status', 'unknown')}{reason_suffix}")
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
    project_relative_path: str,
    local_access_paths: list[str],
    provider_item_id: str,
    provider_item_kind: str,
    provider_item_url: str,
    derived_from: list[str],
    source_of_truth: str | None = None,
    collaboration_mode: str | None = None,
    artifact_role: str | None = None,
    last_refreshed_at: str | None = None,
    last_provider_sync_at: str | None = None,
    provider_revision_id: str | None = None,
    provider_modified_at: str | None = None,
    provider_etag: str | None = None,
    provider_last_checked_at: str | None = None,
    provider_last_fetch_status: str | None = None,
    provider_last_fetch_error: str | None = None,
    provider_snapshot_path: str | None = None,
    freshness_policy: str | None = None,
    freshness_ttl_seconds: int | None = None,
    truth_source_reason: str | None = None,
) -> dict[str, object]:
    catalog = load_artifact_catalog(config)
    project_relative = normalize_project_relative_path(project_relative_path) if project_relative_path else ""
    normalized_local_access_paths = [normalize_project_relative_path(item) for item in local_access_paths if item]
    normalized_path = path.strip()
    identity_key = artifact_identity_key_for_values(
        storage_provider=config.storage_provider,
        provider_root_id=config.provider_root_id,
        path=normalized_path,
        project_relative_path=project_relative,
        provider_item_id=provider_item_id.strip(),
        provider_item_kind=provider_item_kind.strip(),
    )
    artifact_id = f"artifact:{sanitize_source_id(identity_key)}"
    incoming_match = {
        "path": normalized_path,
        "project_relative_path": project_relative,
        "provider_item_id": provider_item_id.strip(),
        "provider_item_kind": provider_item_kind.strip(),
        "storage_provider": config.storage_provider,
        "provider_root_id": config.provider_root_id,
        "identity_key": identity_key,
    }
    artifacts: list[dict[str, object]] = []
    matched_existing: dict[str, object] | None = None
    for item in catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        if matched_existing is None and artifact_entries_match(item, incoming_match):
            matched_existing = item
            continue
        artifacts.append(item)
    resolved_role = normalize_artifact_role(
        artifact_role if artifact_role is not None else matched_existing.get("artifact_role", "") if isinstance(matched_existing, dict) else "",
        default="",
    ) or infer_artifact_role(
        path=normalized_path,
        project_relative_path=project_relative,
        local_access_paths=normalized_local_access_paths,
        provider_item_id=provider_item_id.strip(),
        provider_item_kind=provider_item_kind.strip(),
        derived_from=derived_from,
    )
    resolved_source_of_truth = normalize_source_of_truth(
        source_of_truth if source_of_truth is not None else matched_existing.get("source_of_truth", "") if isinstance(matched_existing, dict) else "",
        default="auto",
    )
    resolved_collaboration_mode = normalize_collaboration_mode(
        collaboration_mode if collaboration_mode is not None else matched_existing.get("collaboration_mode", "") if isinstance(matched_existing, dict) else "",
        default="single-editor",
    )
    resolved_last_refreshed_at = normalize_optional_timestamp(
        last_refreshed_at if last_refreshed_at is not None else matched_existing.get("last_refreshed_at", "") if isinstance(matched_existing, dict) else ""
    ) or current_utc_timestamp()
    resolved_last_provider_sync_at = normalize_optional_timestamp(
        last_provider_sync_at if last_provider_sync_at is not None else matched_existing.get("last_provider_sync_at", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_modified_at = normalize_optional_timestamp(
        provider_modified_at if provider_modified_at is not None else matched_existing.get("provider_modified_at", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_last_checked_at = normalize_optional_timestamp(
        provider_last_checked_at if provider_last_checked_at is not None else matched_existing.get("provider_last_checked_at", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_revision_id = normalize_optional_text(
        provider_revision_id if provider_revision_id is not None else matched_existing.get("provider_revision_id", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_etag = normalize_optional_text(
        provider_etag if provider_etag is not None else matched_existing.get("provider_etag", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_last_fetch_status = normalize_optional_text(
        provider_last_fetch_status if provider_last_fetch_status is not None else matched_existing.get("provider_last_fetch_status", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_last_fetch_error = normalize_optional_text(
        provider_last_fetch_error if provider_last_fetch_error is not None else matched_existing.get("provider_last_fetch_error", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_provider_snapshot_path = normalize_optional_text(
        provider_snapshot_path if provider_snapshot_path is not None else matched_existing.get("provider_snapshot_path", "") if isinstance(matched_existing, dict) else ""
    )
    resolved_freshness_policy = normalize_optional_text(
        freshness_policy if freshness_policy is not None else matched_existing.get("freshness_policy", "") if isinstance(matched_existing, dict) else ""
    ) or default_freshness_policy(
        collaboration_mode=resolved_collaboration_mode,
        source_of_truth=resolved_source_of_truth,
        artifact_role=resolved_role,
    )
    resolved_freshness_ttl_seconds = (
        freshness_ttl_seconds
        if freshness_ttl_seconds is not None
        else int(matched_existing.get("freshness_ttl_seconds", 0) or 0) if isinstance(matched_existing, dict) else 0
    ) or default_freshness_ttl_seconds(
        collaboration_mode=resolved_collaboration_mode,
        source_of_truth=resolved_source_of_truth,
        artifact_role=resolved_role,
    )
    resolved_truth_source_reason = normalize_optional_text(
        truth_source_reason if truth_source_reason is not None else matched_existing.get("truth_source_reason", "") if isinstance(matched_existing, dict) else ""
    )
    family_key = ""
    for derived_id in derived_from:
        parent = find_registered_artifact_by_id(config, derived_id)
        if parent is None:
            continue
        family_key = normalize_optional_text(parent.get("family_key", "")) or normalize_optional_text(parent.get("identity_key", ""))
        if family_key:
            break
    if not family_key and isinstance(matched_existing, dict):
        family_key = normalize_optional_text(matched_existing.get("family_key", ""))
    if not family_key and project_relative:
        family_key = family_key_from_path(config.storage_provider, config.provider_root_id, project_relative)
    if not family_key and normalized_local_access_paths:
        family_key = family_key_from_path(config.storage_provider, config.provider_root_id, normalized_local_access_paths[0])
    if not family_key:
        family_key = identity_key
    entry: dict[str, object] = {
        "id": artifact_id,
        "kind": artifact_kind,
        "title": title,
        "slot": slot,
        "path": normalized_path,
        "summary": summary,
        "date": date_value or "",
        "status": "active",
        "workflow_pack": config.workflow_pack,
        "storage_provider": config.storage_provider,
        "storage_sync_mode": config.storage_sync_mode,
        "provider_root_url": config.provider_root_url,
        "provider_root_id": config.provider_root_id,
        "project_relative_path": project_relative,
        "local_access_paths": normalized_local_access_paths,
        "provider_item_id": provider_item_id.strip(),
        "provider_item_kind": provider_item_kind.strip(),
        "provider_item_url": provider_item_url.strip(),
        "derived_from": derived_from,
        "identity_key": identity_key,
        "family_key": family_key,
        "artifact_role": resolved_role,
        "source_of_truth": resolved_source_of_truth,
        "collaboration_mode": resolved_collaboration_mode,
        "last_refreshed_at": resolved_last_refreshed_at,
        "last_provider_sync_at": resolved_last_provider_sync_at,
        "provider_revision_id": resolved_provider_revision_id,
        "provider_modified_at": resolved_provider_modified_at,
        "provider_etag": resolved_provider_etag,
        "provider_last_checked_at": resolved_provider_last_checked_at,
        "provider_last_fetch_status": resolved_provider_last_fetch_status,
        "provider_last_fetch_error": resolved_provider_last_fetch_error,
        "provider_snapshot_path": resolved_provider_snapshot_path,
        "freshness_policy": resolved_freshness_policy,
        "freshness_ttl_seconds": resolved_freshness_ttl_seconds,
        "local_snapshot_revision_id": local_snapshot_revision_id_for_paths(config, normalized_local_access_paths),
        "truth_source_reason": resolved_truth_source_reason,
    }
    if matched_existing is not None:
        entry["id"] = str(matched_existing.get("id", artifact_id))
    artifacts.append(entry)
    artifacts.sort(key=lambda item: (str(item.get("date", "")), str(item.get("path", ""))))
    catalog["version"] = VERSION
    catalog["artifacts"] = artifacts
    write_artifact_catalog(config, catalog)
    return entry


def infer_document_genre(artifact_kind: str, title: str) -> str:
    lowered_kind = artifact_kind.strip().lower()
    if lowered_kind in DOCUMENT_GENRE_BY_KIND:
        return DOCUMENT_GENRE_BY_KIND[lowered_kind]
    haystack = f"{artifact_kind} {title}".casefold()
    for genre, keywords in DOCUMENT_TITLE_GENRE_KEYWORDS.items():
        if any(keyword.casefold() in haystack for keyword in keywords):
            return genre
    return ""


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [header_line, separator_line]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def artifact_metadata_lines(
    config: ProjectConfig,
    *,
    artifact_kind: str,
    record_date: str,
    slot: str,
    document_genre: str = "",
    bundle_name: str = "",
) -> list[str]:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        "## 元数据" if zh else "## Metadata",
        "",
        f"- {'日期' if zh else 'date'}: {record_date}",
        f"- {'类型' if zh else 'kind'}: {artifact_kind}",
        f"- {'项目' if zh else 'project'}: {config.data['project']['name']}",
        f"- {'工作流包' if zh else 'workflow pack'}: {config.workflow_pack}",
        f"- {'工作流槽位' if zh else 'workflow slot'}: {slot}",
        f"- {'存储提供方' if zh else 'storage provider'}: {config.storage_provider}",
    ]
    if document_genre:
        lines.append(f"- {'文档体裁' if zh else 'document genre'}: {document_genre}")
    if bundle_name:
        lines.append(f"- {'结构模板' if zh else 'document bundle'}: {bundle_name}")
    return lines


def summary_section_lines(summary: str, *, zh: bool) -> list[str]:
    return [
        "## 摘要" if zh else "## Summary",
        "",
        summary,
    ]


def schedule_mermaid_lines(title: str, record_date: str, *, zh: bool) -> list[str]:
    try:
        start_date = date.fromisoformat(record_date)
    except ValueError:
        start_date = date.today()
    second = (start_date + timedelta(days=3)).isoformat()
    third = (start_date + timedelta(days=6)).isoformat()
    return [
        "```mermaid",
        "gantt",
        f"    title {title}",
        "    dateFormat  YYYY-MM-DD",
        f"    section {'对方' if zh else 'Counterparty'}",
        f"    {'需求确认' if zh else 'Requirements alignment'} :cp_align, {start_date.isoformat()}, 3d",
        f"    {'素材与审批' if zh else 'Assets and approvals'} :cp_assets, {second}, 3d",
        f"    section {'我方' if zh else 'Internal'}",
        f"    {'排期固化' if zh else 'Schedule lock'} :internal_lock, {start_date.isoformat()}, 2d",
        f"    {'执行与跟进' if zh else 'Execution follow-through'} :internal_execute, {third}, 4d",
        "```",
    ]


def render_schedule_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
    bundle_name: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind=artifact_kind,
            record_date=record_date,
            slot=slot,
            document_genre="schedule",
            bundle_name=bundle_name,
        ),
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 月度总览" if zh else "## Monthly Overview",
        "",
        *markdown_table(
            ["阶段", "时间范围", "负责人", "关键里程碑", "依赖", "状态"] if zh else ["Phase", "Date Range", "Owner", "Milestone", "Dependency", "Status"],
            [
                ["启动与对齐", f"{record_date} -> {record_date}", "_负责人_", "_确认目标与边界_", "_无_", "_未开始_"] if zh else [f"Kickoff and alignment", f"{record_date} -> {record_date}", "_owner_", "_confirm goals and boundaries_", "_none_", "_not started_"],
                ["执行准备", "YYYY-MM-DD -> YYYY-MM-DD", "_负责人_", "_锁定资源、口径与审批_", "_启动确认_", "_未开始_"] if zh else [f"Execution preparation", "YYYY-MM-DD -> YYYY-MM-DD", "_owner_", "_lock resources, narrative, and approvals_", "_kickoff alignment_", "_not started_"],
                ["执行与复盘", "YYYY-MM-DD -> YYYY-MM-DD", "_负责人_", "_完成交付与复盘_", "_准备完成_", "_未开始_"] if zh else [f"Execution and review", "YYYY-MM-DD -> YYYY-MM-DD", "_owner_", "_complete delivery and review_", "_preparation complete_", "_not started_"],
            ],
        ),
        "",
        "## 角色拆分甘特图" if zh else "## Role-split Gantt",
        "",
        *markdown_table(
            ["角色", "开始", "结束", "关键动作", "依赖", "输出"] if zh else ["Role", "Start", "End", "Key Action", "Dependency", "Output"],
            [
                ["对方", record_date, "YYYY-MM-DD", "_确认需求、提供素材、完成审批_", "_项目启动_", "_确认后的输入_"] if zh else ["Counterparty", record_date, "YYYY-MM-DD", "_align requirements, provide assets, close approvals_", "_project kickoff_", "_approved inputs_"],
                ["我方", record_date, "YYYY-MM-DD", "_固化排期、推进执行、组织复盘_", "_对方输入齐备_", "_交付与复盘纪要_"] if zh else ["Internal", record_date, "YYYY-MM-DD", "_lock schedule, drive execution, run review_", "_counterparty inputs ready_", "_delivery and review note_"],
            ],
        ),
        "",
        *schedule_mermaid_lines(title, record_date, zh=zh),
        "",
        "## 同仁动作表" if zh else "## Counterparty Action Table",
        "",
        *markdown_table(
            ["日期", "角色", "动作", "依赖", "交付物", "状态"] if zh else ["Date", "Role", "Action", "Dependency", "Deliverable", "Status"],
            [
                [record_date, "_对接人_", "_确认目标、范围与关键约束_", "_项目启动_", "_确认口径_", "_未开始_"] if zh else [record_date, "_lead_", "_confirm goals, scope, and key constraints_", "_project kickoff_", "_aligned brief_", "_not started_"],
                ["YYYY-MM-DD", "_审批人_", "_完成素材、预算或法务审批_", "_确认口径_", "_审批结果_", "_未开始_"] if zh else ["YYYY-MM-DD", "_approver_", "_complete asset, budget, or legal approvals_", "_aligned brief_", "_approval result_", "_not started_"],
            ],
        ),
        "",
        "## 我方动作表" if zh else "## Internal Action Table",
        "",
        *markdown_table(
            ["日期", "角色", "动作", "依赖", "交付物", "状态"] if zh else ["Date", "Role", "Action", "Dependency", "Deliverable", "Status"],
            [
                [record_date, "_项目经理_", "_固化排期、节奏与责任人_", "_目标已确认_", "_可执行排期_", "_未开始_"] if zh else [record_date, "_project manager_", "_lock schedule, pace, and ownership_", "_goals aligned_", "_executable schedule_", "_not started_"],
                ["YYYY-MM-DD", "_执行负责人_", "_推进执行、收口风险并同步进展_", "_排期已锁定_", "_进展同步_", "_未开始_"] if zh else ["YYYY-MM-DD", "_execution owner_", "_drive execution, close risks, and share progress_", "_schedule locked_", "_progress update_", "_not started_"],
            ],
        ),
        "",
        "## 角色责任矩阵" if zh else "## Responsibility Matrix",
        "",
        *markdown_table(
            ["工作项", "负责 R", "签核 A", "协作 C", "知会 I", "完成定义"] if zh else ["Work Item", "Responsible R", "Accountable A", "Consulted C", "Informed I", "Done Definition"],
            [
                ["目标与范围确认", "_我方 PM_", "_对方负责人_", "_核心执行人_", "_相关干系人_", "_目标、边界、日期确认_"] if zh else ["Goal and scope alignment", "_internal PM_", "_counterparty lead_", "_core executors_", "_stakeholders_", "_goals, boundaries, and dates confirmed_"],
                ["执行推进", "_执行负责人_", "_我方 PM_", "_对方接口人_", "_相关干系人_", "_节点完成且风险同步_"] if zh else ["Execution delivery", "_execution owner_", "_internal PM_", "_counterparty contact_", "_stakeholders_", "_milestones completed and risks synced_"],
            ],
        ),
        "",
    ]
    return "\n".join(lines)


def render_proposal_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
    bundle_name: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind=artifact_kind,
            record_date=record_date,
            slot=slot,
            document_genre="proposal",
            bundle_name=bundle_name,
        ),
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 执行摘要" if zh else "## Executive Summary",
        "",
        "- _用一段话写清问题、目标与建议方案_"
        if zh
        else "- _summarize the problem, target outcome, and recommended approach in one paragraph_",
        "",
        "## 目标与范围" if zh else "## Objectives And Scope",
        "",
        *markdown_table(
            ["项", "内容"] if zh else ["Item", "Details"],
            [
                ["业务目标", "_写清业务目标_"] if zh else ["Business objective", "_describe the business objective_"],
                ["交付范围", "_写清本次包含内容_"] if zh else ["In scope", "_define what this proposal includes_"],
                ["不在范围", "_写清明确不做的部分_"] if zh else ["Out of scope", "_define what is explicitly excluded_"],
            ],
        ),
        "",
        "## 现状与约束" if zh else "## Current State And Constraints",
        "",
        "- _说明当前状态、关键约束、必须兼容的前提_"
        if zh
        else "- _capture the current state, critical constraints, and non-negotiable requirements_",
        "",
        "## 建议方案" if zh else "## Proposed Approach",
        "",
        "1. _方案骨架_"
        if zh
        else "1. _approach outline_",
        "2. _关键工作包_"
        if zh
        else "2. _major work packages_",
        "3. _成功判定_"
        if zh
        else "3. _success criteria_",
        "",
        "## 里程碑与工作计划" if zh else "## Milestones And Work Plan",
        "",
        *markdown_table(
            ["里程碑", "时间", "负责人", "完成定义"] if zh else ["Milestone", "Timing", "Owner", "Done Definition"],
            [
                ["方案确认", record_date, "_负责人_", "_方案获批_"] if zh else ["Proposal approval", record_date, "_owner_", "_proposal approved_"],
                ["执行准备", "YYYY-MM-DD", "_负责人_", "_资源与依赖齐备_"] if zh else ["Execution readiness", "YYYY-MM-DD", "_owner_", "_resources and dependencies ready_"],
                ["结果验收", "YYYY-MM-DD", "_负责人_", "_验收通过_"] if zh else ["Outcome acceptance", "YYYY-MM-DD", "_owner_", "_acceptance complete_"],
            ],
        ),
        "",
        "## 责任矩阵" if zh else "## Responsibility Matrix",
        "",
        *markdown_table(
            ["工作包", "负责 R", "签核 A", "协作 C", "知会 I"] if zh else ["Work Package", "Responsible R", "Accountable A", "Consulted C", "Informed I"],
            [
                ["方案定稿", "_负责人_", "_决策人_", "_顾问_", "_相关方_"] if zh else ["Finalize proposal", "_owner_", "_decision maker_", "_advisors_", "_stakeholders_"],
                ["执行落地", "_执行人_", "_负责人_", "_接口人_", "_相关方_"] if zh else ["Execution", "_executor_", "_owner_", "_counterparts_", "_stakeholders_"],
            ],
        ),
        "",
        "## 风险与待决策事项" if zh else "## Risks And Decisions",
        "",
        "- _列出关键风险、依赖和需要拍板的问题_"
        if zh
        else "- _list the main risks, dependencies, and open decisions_",
        "",
    ]
    return "\n".join(lines)


def render_report_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
    bundle_name: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind=artifact_kind,
            record_date=record_date,
            slot=slot,
            document_genre="report",
            bundle_name=bundle_name,
        ),
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 执行摘要" if zh else "## Executive Summary",
        "",
        "- _先给出结论，再给证据和动作_"
        if zh
        else "- _lead with the conclusion, then support it with evidence and actions_",
        "",
        "## 背景与范围" if zh else "## Background And Scope",
        "",
        "- _说明本次汇报覆盖的周期、对象和范围_"
        if zh
        else "- _define the reporting period, audience, and scope_",
        "",
        "## 方法与证据" if zh else "## Method And Evidence",
        "",
        *markdown_table(
            ["来源", "内容", "可信度"] if zh else ["Source", "Evidence", "Confidence"],
            [
                ["_数据源 / 访谈 / 观察_", "_写清证据内容_", "_高 / 中 / 低_"] if zh else ["_data / interviews / observation_", "_describe the evidence_", "_high / medium / low_"],
            ],
        ),
        "",
        "## 关键发现" if zh else "## Key Findings",
        "",
        "1. _发现一_"
        if zh
        else "1. _finding one_",
        "2. _发现二_"
        if zh
        else "2. _finding two_",
        "3. _发现三_"
        if zh
        else "3. _finding three_",
        "",
        "## 进展与风险" if zh else "## Progress And Risks",
        "",
        *markdown_table(
            ["主题", "当前状态", "风险", "缓解动作"] if zh else ["Theme", "Current Status", "Risk", "Mitigation"],
            [
                ["_主题_", "_写状态_", "_写风险_", "_写缓解动作_"] if zh else ["_theme_", "_state current status_", "_state risk_", "_state mitigation_"],
            ],
        ),
        "",
        "## 决策与请求" if zh else "## Decisions And Requests",
        "",
        "- _写需要确认的决策、支持或资源_"
        if zh
        else "- _capture the decisions, support, or resources needed_",
        "",
        "## 下一步动作" if zh else "## Next Actions",
        "",
        *markdown_table(
            ["动作", "负责人", "截止日期", "完成定义"] if zh else ["Action", "Owner", "Due Date", "Done Definition"],
            [
                ["_下一步动作_", "_负责人_", "YYYY-MM-DD", "_写完成定义_"] if zh else ["_next action_", "_owner_", "YYYY-MM-DD", "_define done_"],
            ],
        ),
        "",
    ]
    return "\n".join(lines)


def render_process_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
    bundle_name: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind=artifact_kind,
            record_date=record_date,
            slot=slot,
            document_genre="process",
            bundle_name=bundle_name,
        ),
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 目的与适用范围" if zh else "## Purpose And Scope",
        "",
        "- _说明这个流程解决什么问题，适用于哪些场景_"
        if zh
        else "- _define what this process solves and when it applies_",
        "",
        "## 角色与输入" if zh else "## Roles And Inputs",
        "",
        *markdown_table(
            ["角色", "职责", "关键输入"] if zh else ["Role", "Responsibility", "Key Inputs"],
            [
                ["_角色_", "_职责_", "_输入_"] if zh else ["_role_", "_responsibility_", "_input_"],
            ],
        ),
        "",
        "## 流程步骤" if zh else "## Workflow Steps",
        "",
        *markdown_table(
            ["步骤", "触发条件", "动作", "输出"] if zh else ["Step", "Trigger", "Action", "Output"],
            [
                ["1", "_触发条件_", "_执行动作_", "_输出_"] if zh else ["1", "_trigger_", "_action_", "_output_"],
                ["2", "_触发条件_", "_执行动作_", "_输出_"] if zh else ["2", "_trigger_", "_action_", "_output_"],
                ["3", "_触发条件_", "_执行动作_", "_输出_"] if zh else ["3", "_trigger_", "_action_", "_output_"],
            ],
        ),
        "",
        "## 控制点与例外处理" if zh else "## Controls And Exceptions",
        "",
        "- _写清审批点、升级条件、失败回退和异常路径_"
        if zh
        else "- _document approvals, escalation rules, rollback, and exception paths_",
        "",
        "## 产物与记录" if zh else "## Artifacts And Records",
        "",
        *markdown_table(
            ["产物", "维护方式", "存放位置"] if zh else ["Artifact", "Maintenance Rule", "Location"],
            [
                ["_源文件_", "_持续维护_", "_项目路径_"] if zh else ["_source file_", "_maintain continuously_", "_project path_"],
                ["_派生成品_", "_按需物化并登记_", "_artifact catalog_"] if zh else ["_derived deliverable_", "_materialize as needed and register_", "_artifact catalog_"],
            ],
        ),
        "",
        "## 指标与复盘" if zh else "## Metrics And Review",
        "",
        "- _定义衡量标准、复盘频率和改进责任人_"
        if zh
        else "- _define metrics, review cadence, and improvement ownership_",
        "",
    ]
    return "\n".join(lines)


def render_training_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
    bundle_name: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind=artifact_kind,
            record_date=record_date,
            slot=slot,
            document_genre="training",
            bundle_name=bundle_name,
        ),
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 受众与学习目标" if zh else "## Audience And Outcomes",
        "",
        *markdown_table(
            ["受众", "起点", "目标结果"] if zh else ["Audience", "Starting Point", "Target Outcome"],
            [
                ["_对象_", "_现状_", "_培训后应达到的结果_"] if zh else ["_audience_", "_current baseline_", "_expected outcome after training_"],
            ],
        ),
        "",
        "## 议程总览" if zh else "## Agenda Overview",
        "",
        *markdown_table(
            ["模块", "时长", "目标"] if zh else ["Module", "Duration", "Objective"],
            [
                ["_模块一_", "_30 min_", "_写本模块目标_"] if zh else ["_module one_", "_30 min_", "_define the module objective_"],
                ["_模块二_", "_45 min_", "_写本模块目标_"] if zh else ["_module two_", "_45 min_", "_define the module objective_"],
            ],
        ),
        "",
        "## 课前准备与材料" if zh else "## Preparation And Materials",
        "",
        "- _列出参训前提、材料、环境和负责人_"
        if zh
        else "- _list prerequisites, materials, environment, and owners_",
        "",
        "## 课程执行方案" if zh else "## Session Plan",
        "",
        *markdown_table(
            ["时间段", "讲授内容", "形式", "负责人"] if zh else ["Time Block", "Content", "Format", "Owner"],
            [
                ["_00:00-00:30_", "_内容_", "_讲解 / 演示 / 练习_", "_负责人_"] if zh else ["_00:00-00:30_", "_content_", "_lecture / demo / exercise_", "_owner_"],
            ],
        ),
        "",
        "## 练习与评估" if zh else "## Exercises And Assessment",
        "",
        "- _说明练习题、通过标准、评估方式和补救动作_"
        if zh
        else "- _document exercises, pass criteria, evaluation method, and remediation_",
        "",
        "## 课后跟进与留痕" if zh else "## Follow-up And Records",
        "",
        *markdown_table(
            ["事项", "负责人", "截止日期", "记录位置"] if zh else ["Item", "Owner", "Due Date", "Record Location"],
            [
                ["_课后动作_", "_负责人_", "YYYY-MM-DD", "_记录路径_"] if zh else ["_follow-up action_", "_owner_", "YYYY-MM-DD", "_record path_"],
            ],
        ),
        "",
    ]
    return "\n".join(lines)


def render_generic_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind=artifact_kind,
            record_date=record_date,
            slot=slot,
        ),
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 详情" if zh else "## Details",
        "",
        "- _补充详情_" if zh else "- _fill in details_",
        "",
    ]
    return "\n".join(lines)


def render_artifact_template(
    config: ProjectConfig,
    artifact_kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
) -> str:
    document_genre = infer_document_genre(artifact_kind, title)
    bundle_name = config.document_bundle_for_genre(document_genre) if document_genre else ""
    if document_genre == "schedule":
        return render_schedule_artifact_template(config, artifact_kind, title, summary, record_date, slot, bundle_name)
    if document_genre == "proposal":
        return render_proposal_artifact_template(config, artifact_kind, title, summary, record_date, slot, bundle_name)
    if document_genre == "report":
        return render_report_artifact_template(config, artifact_kind, title, summary, record_date, slot, bundle_name)
    if document_genre == "process":
        return render_process_artifact_template(config, artifact_kind, title, summary, record_date, slot, bundle_name)
    if document_genre == "training":
        return render_training_artifact_template(config, artifact_kind, title, summary, record_date, slot, bundle_name)
    return render_generic_artifact_template(config, artifact_kind, title, summary, record_date, slot)


def render_workflow_spec_template(
    config: ProjectConfig,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind="spec",
            record_date=record_date,
            slot=slot,
        ),
        f"- {'执行模式' if zh else 'execution mode'}: {config.workflow_execution_mode}",
        f"- {'设计门禁' if zh else 'design gate'}: {config.workflow_design_gate}",
        f"- {'计划门禁' if zh else 'plan gate'}: {config.workflow_plan_gate}",
        f"- {'评审策略' if zh else 'review policy'}: {config.workflow_review_policy}",
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 问题定义" if zh else "## Problem Statement",
        "",
        "- _说明要解决的具体问题、当前症状和触发背景_"
        if zh
        else "- _capture the concrete problem, current symptoms, and why this work exists now_",
        "",
        "## 目标与非目标" if zh else "## Goals And Non-goals",
        "",
        *markdown_table(
            ["类别", "内容"] if zh else ["Category", "Details"],
            [
                ["目标", "_写清这次必须达成的结果_"] if zh else ["Goals", "_define the required outcomes for this work_"],
                ["非目标", "_写清这次明确不做的内容_"] if zh else ["Non-goals", "_define what this work will explicitly not do_"],
            ],
        ),
        "",
        "## 约束与假设" if zh else "## Constraints And Assumptions",
        "",
        "- _列出不可违反的规则、兼容要求、时间约束和关键假设_"
        if zh
        else "- _list non-negotiable rules, compatibility constraints, timing limits, and key assumptions_",
        "",
        "## 设计方案" if zh else "## Proposed Design",
        "",
        "1. _主方案_"
        if zh
        else "1. _primary approach_",
        "2. _关键模块或接口变更_"
        if zh
        else "2. _key module or interface changes_",
        "3. _需要保留或迁移的旧行为_"
        if zh
        else "3. _legacy behavior to preserve or migrate_",
        "",
        "## 数据与接口变更" if zh else "## Data And Interface Changes",
        "",
        *markdown_table(
            ["对象", "变化", "兼容性影响"] if zh else ["Surface", "Change", "Compatibility Impact"],
            [
                ["_模块 / API / 文档_", "_写具体变化_", "_兼容 / 破坏性 / 待确认_"]
                if zh
                else ["_module / API / document_", "_describe the concrete change_", "_compatible / breaking / unknown_"],
            ],
        ),
        "",
        "## 风险与待确认问题" if zh else "## Risks And Open Questions",
        "",
        "- _列出主要风险、未知点和需要拍板的事项_"
        if zh
        else "- _list the main risks, unknowns, and decisions that still need confirmation_",
        "",
        "## 验证计划" if zh else "## Verification Plan",
        "",
        "- _说明要运行的测试、检查和完成判据_"
        if zh
        else "- _document the tests, checks, and done criteria that will verify this design_",
        "",
    ]
    return "\n".join(lines)


def render_workflow_review_template(
    config: ProjectConfig,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
) -> str:
    zh = locale_family(config.content_locale) == "zh"
    lines = [
        f"# {title}",
        "",
        *artifact_metadata_lines(
            config,
            artifact_kind="review",
            record_date=record_date,
            slot=slot,
        ),
        f"- {'评审策略' if zh else 'review policy'}: {config.workflow_review_policy}",
        f"- {'测试策略' if zh else 'testing policy'}: {config.workflow_testing_policy}",
        f"- {'收尾策略' if zh else 'closeout policy'}: {config.workflow_closeout_policy}",
        "",
        *summary_section_lines(summary, zh=zh),
        "",
        "## 审查范围" if zh else "## Reviewed Scope",
        "- _列出本次审查覆盖的代码、文档、命令和风险边界_"
        if zh
        else "- _list the code, documents, commands, and risk boundary covered by this review_",
        "",
        "## Findings" if not zh else "## 发现",
        "",
        "- _按严重级别记录问题；没有问题也要明确写无发现_"
        if zh
        else "- _record findings by severity; if none were found, say so explicitly_",
        "",
        "## 回归检查" if zh else "## Regressions Checked",
        "",
        "- _说明重点回归面、保护逻辑和未覆盖区域_"
        if zh
        else "- _document key regression surfaces, protected behaviors, and any uncovered areas_",
        "",
        "## 验证" if zh else "## Validation",
        "",
        *markdown_table(
            ["检查项", "命令 / 证据", "结果"] if zh else ["Check", "Command / Evidence", "Result"],
            [
                ["_测试或检查_", "_命令或证据_", "_通过 / 失败 / 未运行_"]
                if zh
                else ["_test or check_", "_command or evidence_", "_pass / fail / not run_"],
            ],
        ),
        "",
        "## 发布闸门" if zh else "## Release Gate",
        "",
        "- _说明可用性、主流程、外部依赖和回滚清晰度_"
        if zh
        else "- _answer availability, primary-flow, external-setup, and rollback clarity questions_",
        "",
        "## 后续动作" if zh else "## Follow-up",
        "",
        "- _列出后续动作、责任人和截止时间_"
        if zh
        else "- _list follow-up actions, owners, and due dates_",
        "",
    ]
    return "\n".join(lines)


def render_workflow_template(
    config: ProjectConfig,
    kind: str,
    title: str,
    summary: str,
    record_date: str,
    slot: str,
) -> str:
    if kind == "plan":
        return render_artifact_template(config, "plan", title, summary, record_date, slot)
    if kind == "spec":
        return render_workflow_spec_template(config, title, summary, record_date, slot)
    if kind == "review":
        return render_workflow_review_template(config, title, summary, record_date, slot)
    raise SystemExit(f"Unsupported workflow scaffold kind: {kind}")


MCP_TOOL_DEFINITIONS = [
    {"name": "sula.project.bootstrap", "permission": "read", "description": "Return project identity, status, rules, tasks, artifacts, and provider capabilities."},
    {"name": "sula.project.status", "permission": "read", "description": "Return a read-only project status summary."},
    {"name": "sula.project.check", "permission": "read", "description": "Evaluate Sula check state without recording command activity."},
    {"name": "sula.project.doctor", "permission": "read", "description": "Evaluate Sula doctor state without recording command activity."},
    {"name": "sula.project.query", "permission": "read", "description": "Query kernel objects with stable JSON output."},
    {"name": "sula.project.memory_digest", "permission": "read", "description": "Return the committed memory digest path and bounded excerpt."},
    {"name": "sula.project.rules", "permission": "read", "description": "Return the consolidated project policy view for agents."},
    {"name": "sula.artifact.locate", "permission": "read", "description": "Locate registered artifacts without refreshing providers."},
    {"name": "sula.artifact.list", "permission": "read", "description": "List registered artifacts without provider side effects."},
    {"name": "sula.workflow.assess", "permission": "read", "description": "Assess workflow rigor for a task."},
    {"name": "sula.orchestration.tasks", "permission": "read", "description": "List normalized orchestration tasks."},
    {"name": "sula.orchestration.runs", "permission": "read", "description": "List orchestration runs."},
    {"name": "sula.portfolio.list", "permission": "read", "description": "List portfolio registry entries."},
    {"name": "sula.portfolio.status", "permission": "read", "description": "Summarize portfolio state, blockers, stale surfaces, and next actions."},
    {"name": "sula.provider.capabilities", "permission": "read", "description": "Report provider adapter capabilities and gaps."},
    {"name": "sula.report.create", "permission": "record", "description": "Append a Sula report through the managed report command."},
    {"name": "sula.workflow.scaffold", "permission": "record", "description": "Create a workflow source document through Sula."},
    {"name": "sula.orchestration.intake", "permission": "record", "description": "Capture a normalized orchestration task through Sula."},
    {"name": "sula.orchestration.close", "permission": "record", "description": "Close an orchestration run through Sula evidence checks."},
    {"name": "sula.artifact.register", "permission": "generate", "description": "Register an artifact through Sula."},
    {"name": "sula.artifact.materialize", "permission": "generate", "description": "Materialize an artifact through Sula."},
    {"name": "sula.artifact.refresh", "permission": "generate", "description": "Refresh provider-backed artifact metadata through Sula."},
    {"name": "sula.sync.dry_run", "permission": "read", "description": "Return the managed sync plan without writing projections."},
]


def mcp_tools_payload() -> dict[str, object]:
    return {
        "version": VERSION,
        "tools": MCP_TOOL_DEFINITIONS,
        "write_classes": ["record", "generate", "sync", "provider-write", "destructive", "release", "runner"],
        "default_policy": "read-only",
    }


def normalize_abs_path(value: str | Path) -> str:
    return str(Path(value).expanduser().resolve())


def parse_json_object(raw: str, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {label} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a JSON object.")
    return value


def load_mcp_policy(args: argparse.Namespace, project_root: Path | None = None) -> dict[str, object]:
    policy: dict[str, object] = {
        "version": VERSION,
        "allowed_project_roots": [],
        "enabled_write_classes": [],
        "allow_read": True,
    }
    candidates: list[Path] = []
    policy_file_raw = normalize_optional_text(getattr(args, "policy_file", ""))
    if policy_file_raw:
        candidates.append(Path(policy_file_raw).expanduser())
    if project_root is not None:
        candidates.append(project_root / ".sula" / "local" / "mcp-policy.json")
    for candidate in candidates:
        if not candidate.exists():
            continue
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"MCP policy must be a JSON object: {candidate}")
        policy.update(data)
        policy["policy_file"] = str(candidate)
        break
    allowed = list(policy.get("allowed_project_roots", [])) if isinstance(policy.get("allowed_project_roots", []), list) else []
    allowed.extend(getattr(args, "allow_project_root", []) or [])
    policy["allowed_project_roots"] = sorted({normalize_abs_path(item) for item in allowed if normalize_optional_text(item)})
    enabled = list(policy.get("enabled_write_classes", [])) if isinstance(policy.get("enabled_write_classes", []), list) else []
    enabled.extend(getattr(args, "enable_write_class", []) or [])
    policy["enabled_write_classes"] = sorted({normalize_optional_text(item).strip() for item in enabled if normalize_optional_text(item).strip()})
    return policy


def mcp_tool_permission(tool_name: str) -> str:
    for item in MCP_TOOL_DEFINITIONS:
        if item["name"] == tool_name:
            return str(item["permission"])
    raise SystemExit(f"Unknown Sula MCP tool: {tool_name}")


def assert_mcp_project_allowed(policy: dict[str, object], project_root: Path, *, permission: str) -> None:
    allowed_roots = set(str(item) for item in policy.get("allowed_project_roots", []) if normalize_optional_text(item))
    resolved = normalize_abs_path(project_root)
    if allowed_roots and resolved not in allowed_roots:
        raise SystemExit(f"MCP project root is not allowlisted: {resolved}")
    if not allowed_roots and permission != "read":
        raise SystemExit("MCP write tools require an explicit project root allowlist.")
    enabled_write_classes = set(str(item) for item in policy.get("enabled_write_classes", []) if normalize_optional_text(item))
    if permission != "read" and permission not in enabled_write_classes:
        raise SystemExit(f"MCP write class `{permission}` is not enabled.")


def project_relative(config: ProjectConfig, path: Path) -> str:
    return path.relative_to(config.root).as_posix() if path.is_relative_to(config.root) else str(path)


def read_status_sections(config: ProjectConfig) -> dict[str, str]:
    status_path = config.root / config.data["paths"]["status_file"]
    text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
    return markdown_sections(text)


def mcp_project_status_payload(config: ProjectConfig) -> dict[str, object]:
    sections = read_status_sections(config)
    artifact_catalog = load_artifact_catalog(config)
    tasks, task_issues = load_orchestration_tasks(config)
    runs = read_orchestration_runs(config)
    run_counts = {status: 0 for status in ORCHESTRATION_RUN_STATUSES}
    for run in runs:
        status = normalize_optional_text(run.get("status", ""))
        if status in run_counts:
            run_counts[status] += 1
    return {
        "project": project_payload(config),
        "summary": sections.get("Summary", "_missing_"),
        "health": sections.get("Health", "_missing_"),
        "current_focus": markdown_bullet_items(sections.get("Current Focus", "")),
        "blockers": markdown_bullet_items(sections.get("Blockers", "")),
        "recent_decisions": markdown_bullet_items(sections.get("Recent Decisions", "")),
        "handoff": markdown_key_values(sections.get("Handoff", "")),
        "counts": {
            "artifacts": len([item for item in artifact_catalog.get("artifacts", []) if isinstance(item, dict)]),
            "tasks_total": len(tasks),
            "tasks_open": sum(1 for item in tasks if item.get("state") in {"open", "running"}),
            "tasks_blocked": sum(1 for item in tasks if item.get("blocked_reasons")),
            "runs_total": len(runs),
            "runs_human_review": run_counts.get("human-review", 0),
            "runs_failed": run_counts.get("failed", 0),
        },
        "task_issues": task_issues,
    }


def mcp_project_check_payload(config: ProjectConfig) -> dict[str, object]:
    report = inspect_doctor_state(config, strict=True)
    drift_errors = collect_daily_check_drift_errors(config)
    drift_errors.extend(collect_orchestration_check_errors(config))
    passed = bool(report["passed"]) and not drift_errors
    return daily_check_payload(config, report, drift_errors, passed=passed)


def mcp_project_doctor_payload(config: ProjectConfig, *, strict: bool = True) -> dict[str, object]:
    report = inspect_doctor_state(config, strict=strict)
    return doctor_payload(
        config,
        missing_files=report["missing_files"],
        drifted_files=report["drifted_files"],
        placeholder_files=report["placeholder_files"],
        memory_errors=report["memory_errors"],
        lock_issues=report["lock_issues"],
        kernel_errors=report["kernel_errors"],
        warnings=report["warnings"],
        advisories=report["advisories"],
        passed=bool(report["passed"]),
    )


def mcp_memory_digest_payload(config: ProjectConfig, *, max_chars: int = 4000) -> dict[str, object]:
    path = config.digest_file
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "path": project_relative(config, path),
        "exists": path.exists(),
        "char_count": len(text),
        "excerpt": text[: max(0, max_chars)],
        "truncated": len(text) > max_chars,
    }


def software_policy_constraints(config: ProjectConfig) -> dict[str, object]:
    manifest_paths = config.data.get("paths", {}) if isinstance(config.data.get("paths", {}), dict) else {}
    package_path = config.root / "package.json"
    package_data = load_json_file(package_path, default={}) if package_path.exists() else {}
    scripts = package_data.get("scripts", {}) if isinstance(package_data, dict) and isinstance(package_data.get("scripts", {}), dict) else {}
    return {
        "applies": config.profile == "react-frontend-erpnext" or package_path.exists(),
        "profile": config.profile,
        "source_paths": manifest_paths,
        "test_commands": [str(value) for key, value in scripts.items() if key in {"test", "typecheck", "build", "lint"}],
        "forbid_drive_by_refactors": config.agent_forbid_drive_by_refactors,
    }


def service_policy_constraints(config: ProjectConfig) -> dict[str, object]:
    return {
        "applies": config.workflow_pack in {"generic-project", "client-service", "video-production"} or config.profile == "generic-project",
        "artifact_truth": "project-owned source files and provider-native references remain business truth",
        "approval_rules": [
            "customer approval evidence belongs in project-owned records",
            "provider-native collaborative files should be refreshed before freshness-sensitive work",
            "handoff must identify next action and source of truth",
        ],
        "artifact_genres": list(FORMAL_DOCUMENT_GENRES),
    }


def mcp_project_rules_payload(config: ProjectConfig) -> dict[str, object]:
    instruction_files: list[dict[str, object]] = []
    for raw in ["AGENTS.md", "CODEX.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md", ".cursor/rules/project.mdc"]:
        path = config.root / raw
        if path.exists():
            instruction_files.append({"path": raw, "summary": source_summary(path)[:500]})
    return {
        "highest_rule": "Preserve the split between centrally managed operating-system files and project-owned business truth.",
        "profile": config.profile,
        "workflow": {
            "pack": config.workflow_pack,
            "stage": config.workflow_stage,
            "execution_mode": config.workflow_execution_mode,
            "design_gate": config.workflow_design_gate,
            "plan_gate": config.workflow_plan_gate,
            "review_policy": config.workflow_review_policy,
            "workspace_isolation": config.workflow_workspace_isolation,
            "testing_policy": config.workflow_testing_policy,
            "closeout_policy": config.workflow_closeout_policy,
        },
        "agent_behavior": agent_behavior_payload(config),
        "orchestration": {
            "approval_required_for": config.orchestration_require_human_approval_for,
            "unattended_risk_ceiling": config.orchestration_unattended_risk_ceiling,
            "verification_adapters": config.orchestration_verification_adapters,
            "remote_verification_policy": config.orchestration_remote_verification_policy,
            "forbidden_operations": [
                "arbitrary shell through MCP",
                "direct edits to Sula-managed state",
                "provider-native writes without explicit enablement",
                "destructive operations without approval",
            ],
        },
        "document_design": {
            "enabled": bool(config.data.get("document_design", {})),
            "formal_document_genres": list(FORMAL_DOCUMENT_GENRES),
        },
        "storage": {
            "provider": config.storage_provider,
            "sync_mode": config.storage_sync_mode,
            "source_of_truth_rule": "provider-native collaborative artifacts require freshness checks before latest-version answers",
        },
        "software_constraints": software_policy_constraints(config),
        "service_constraints": service_policy_constraints(config),
        "instruction_files": instruction_files,
        "required_verification_commands": [
            "python3 scripts/sula.py check --project-root .",
            "python3 scripts/sula.py doctor --project-root . --strict",
        ],
    }


def mcp_artifact_locate_payload(config: ProjectConfig, *, kind: str = "", query: str = "", limit: int = 20) -> dict[str, object]:
    catalog = load_artifact_catalog(config)
    results: list[dict[str, object]] = []
    lowered = query.strip().lower()
    for item in catalog.get("artifacts", []):
        if not isinstance(item, dict):
            continue
        if kind and normalize_optional_text(item.get("kind", "")) != kind:
            continue
        haystack = " ".join(
            str(item.get(key, ""))
            for key in ["id", "kind", "title", "slot", "path", "project_relative_path", "provider_item_id", "provider_item_kind", "provider_item_url", "summary"]
        ).lower()
        if lowered and lowered not in haystack:
            continue
        row = dict(item)
        row["display_path"] = artifact_display_path(item)
        row.update(artifact_truth_summary(config, item, catalog=catalog))
        results.append(row)
    results.sort(key=lambda item: (normalize_optional_text(item.get("date", "")), normalize_optional_text(item.get("display_path", ""))), reverse=True)
    return {"artifacts": results[: max(1, limit)], "total": len(results)}


def provider_capabilities_payload(config: ProjectConfig) -> dict[str, object]:
    provider = config.storage_provider
    capabilities: list[str] = []
    write_capabilities: list[str] = []
    gaps: list[str] = []
    if provider == "google-drive":
        capabilities = ["fetch_item", "fetch_tasks", "refresh_metadata", "normalize_google_doc", "normalize_google_sheet"]
        gaps = ["write_provider_native_item", "create_google_doc", "create_google_sheet"]
    elif provider == "local-fs":
        capabilities = ["read_workspace_files", "register_workspace_artifact", "materialize_local_artifact"]
        gaps = ["provider_refresh", "provider_task_fetch"]
    else:
        gaps = ["provider_adapter_not_available"]
    return {
        "provider": provider,
        "capabilities": capabilities,
        "write_capabilities": write_capabilities,
        "gaps": gaps,
        "oauth_store_configured": config.project_google_oauth_file.exists() if provider == "google-drive" else False,
        "fixture_env": "SULA_PROVIDER_FIXTURE_DIR" if provider == "google-drive" else "",
    }


def mcp_project_bootstrap_payload(config: ProjectConfig) -> dict[str, object]:
    status = mcp_project_status_payload(config)
    artifacts = mcp_artifact_locate_payload(config, limit=10)
    tasks, task_issues = load_orchestration_tasks(config)
    return {
        "project": project_payload(config),
        "project_status": status,
        "rules": mcp_project_rules_payload(config),
        "handoff": status.get("handoff", {}),
        "tasks": {
            "items": tasks[:20],
            "issues": task_issues,
        },
        "artifacts": artifacts,
        "provider_capabilities": provider_capabilities_payload(config),
        "allowed_operations": {
            "read": [item["name"] for item in MCP_TOOL_DEFINITIONS if item["permission"] == "read"],
            "controlled_write_classes": sorted({item["permission"] for item in MCP_TOOL_DEFINITIONS if item["permission"] != "read"}),
        },
    }


def mcp_portfolio_status_payload(portfolio_root: Path) -> dict[str, object]:
    registry = load_portfolio_registry(portfolio_root)
    rows: list[dict[str, object]] = []
    totals = {
        "projects": 0,
        "blockers": 0,
        "open_tasks": 0,
        "pending_runs": 0,
        "stale_memory": 0,
        "stale_artifacts": 0,
    }
    needs_attention: list[dict[str, object]] = []
    for item in registry.get("projects", []):
        if not isinstance(item, dict) or not isinstance(item.get("root"), str):
            continue
        root = Path(item["root"])
        manifest_path = root / MANIFEST_PATH
        if not manifest_path.exists():
            row = {"project_name": normalize_optional_text(item.get("name", "")) or str(root), "project_root": str(root), "status": "missing-manifest", "issues": [f"missing manifest: {manifest_path}"]}
            rows.append(row)
            needs_attention.append({"project_name": row["project_name"], "project_root": str(root), "reasons": ["missing manifest"]})
            continue
        config = load_manifest(root)
        status = mcp_project_status_payload(config)
        handoff = status.get("handoff", {}) if isinstance(status.get("handoff", {}), dict) else {}
        blockers = status.get("blockers", []) if isinstance(status.get("blockers", []), list) else []
        pending_runs = int(status.get("counts", {}).get("runs_human_review", 0)) + int(status.get("counts", {}).get("runs_failed", 0))
        stale_memory = normalize_optional_text(handoff.get("source freshness", "")) not in {"current", ""}
        artifact_catalog = load_artifact_catalog(config)
        stale_artifacts = 0
        for artifact in artifact_catalog.get("artifacts", []):
            if not isinstance(artifact, dict):
                continue
            summary = artifact_truth_summary(config, artifact, catalog=artifact_catalog)
            stale_artifacts += 1 if summary.get("local_copy_stale_risk") or summary.get("missing_provider_metadata") else 0
        row = {
            "project_name": config.data["project"]["name"],
            "project_slug": config.data["project"]["slug"],
            "project_root": str(config.root),
            "health": status.get("health", ""),
            "blockers": blockers,
            "handoff": handoff,
            "open_tasks": int(status.get("counts", {}).get("tasks_open", 0)),
            "pending_runs": pending_runs,
            "stale_memory": stale_memory,
            "stale_artifact_count": stale_artifacts,
            "storage_provider": config.storage_provider,
            "workflow_pack": config.workflow_pack,
        }
        rows.append(row)
        totals["projects"] += 1
        totals["blockers"] += len(blockers)
        totals["open_tasks"] += int(row["open_tasks"])
        totals["pending_runs"] += pending_runs
        totals["stale_memory"] += 1 if stale_memory else 0
        totals["stale_artifacts"] += stale_artifacts
        reasons = []
        if blockers:
            reasons.append(f"{len(blockers)} blocker(s)")
        if row["open_tasks"]:
            reasons.append(f"{row['open_tasks']} open task(s)")
        if pending_runs:
            reasons.append(f"{pending_runs} pending run(s)")
        if stale_memory:
            reasons.append("stale memory")
        if stale_artifacts:
            reasons.append(f"{stale_artifacts} stale artifact(s)")
        if reasons:
            needs_attention.append({"project_name": row["project_name"], "project_slug": row["project_slug"], "project_root": row["project_root"], "reasons": reasons})
    return {"portfolio_root": str(portfolio_root), "totals": totals, "needs_attention": needs_attention, "projects": rows}


def git_status_paths(config: ProjectConfig) -> set[str]:
    try:
        result = subprocess.run(["git", "status", "--short"], cwd=config.root, capture_output=True, text=True, check=False)
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        if raw:
            paths.add(raw)
    return paths


def capture_json_function(fn) -> tuple[dict[str, object], int]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = fn()
    output = stream.getvalue().strip()
    if not output:
        return {}, code
    candidate = output
    if "\n{" in output:
        candidate = output[output.rfind("\n{") + 1 :]
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        data = {"raw_output": output}
    return data if isinstance(data, dict) else {"result": data}, code


def mcp_audit_write(config: ProjectConfig, *, tool_name: str, intent: dict[str, object], before_paths: set[str], payload: dict[str, object], permission: str) -> dict[str, object]:
    after_paths = git_status_paths(config)
    changed_files = sorted(after_paths | before_paths)
    event = {
        "version": VERSION,
        "timestamp": current_utc_timestamp(),
        "event_type": "mcp.write",
        "tool": tool_name,
        "permission": permission,
        "project_root": str(config.root),
        "intent": intent,
        "files_changed": changed_files,
        "status": payload.get("status", "ok"),
    }
    append_jsonl_object(config.root / ".sula" / "events" / "log.jsonl", event)
    return {"event_type": "mcp.write", "files_changed": changed_files, "event_path": ".sula/events/log.jsonl"}


def mcp_call_project_tool(config: ProjectConfig, tool_name: str, tool_args: dict[str, object], *, permission: str) -> tuple[dict[str, object], int]:
    if tool_name == "sula.project.bootstrap":
        return {"command": tool_name, "status": "ok", **mcp_project_bootstrap_payload(config)}, 0
    if tool_name == "sula.project.status":
        return {"command": tool_name, "status": "ok", **mcp_project_status_payload(config)}, 0
    if tool_name == "sula.project.check":
        payload = mcp_project_check_payload(config)
        return {"command": tool_name, "status": "ok" if payload["passed"] else "failed", **payload}, 0 if payload["passed"] else 1
    if tool_name == "sula.project.doctor":
        payload = mcp_project_doctor_payload(config, strict=bool(tool_args.get("strict", True)))
        return {"command": tool_name, "status": "ok" if payload["passed"] else "failed", **payload}, 0 if payload["passed"] else 1
    if tool_name == "sula.project.query":
        query = normalize_optional_text(tool_args.get("q", ""))
        kind = normalize_optional_text(tool_args.get("kind", "")) or None
        timeline = bool(tool_args.get("timeline", False))
        results = search_kernel(
            config,
            query,
            kind=kind,
            adapter=normalize_optional_text(tool_args.get("adapter", "")) or None,
            status=normalize_optional_text(tool_args.get("status", "")) or None,
            path_prefix=normalize_optional_text(tool_args.get("path_prefix", "")) or None,
            since=normalize_optional_text(tool_args.get("since", "")) or None,
            until=normalize_optional_text(tool_args.get("until", "")) or None,
            timeline=timeline,
            limit=int(tool_args.get("limit", 10) or 10),
            route=determine_query_route(query, kind=kind, timeline=timeline, freshness_intent=False, routing_policy=normalize_optional_text(config.memory_setting("query_routing", "deterministic"))),
        )
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "results": results}, 0
    if tool_name == "sula.project.memory_digest":
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "memory_digest": mcp_memory_digest_payload(config, max_chars=int(tool_args.get("max_chars", 4000) or 4000))}, 0
    if tool_name == "sula.project.rules":
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "rules": mcp_project_rules_payload(config)}, 0
    if tool_name in {"sula.artifact.locate", "sula.artifact.list"}:
        return {"command": tool_name, "status": "ok", "project": project_payload(config), **mcp_artifact_locate_payload(config, kind=normalize_optional_text(tool_args.get("kind", "")), query=normalize_optional_text(tool_args.get("q", "")), limit=int(tool_args.get("limit", 20) or 20))}, 0
    if tool_name == "sula.workflow.assess":
        task = normalize_optional_text(tool_args.get("task", ""))
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "assessment": workflow_assessment_payload(config, task)}, 0
    if tool_name == "sula.orchestration.tasks":
        tasks, issues = load_orchestration_tasks(config)
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "tasks": tasks, "issues": issues}, 0
    if tool_name == "sula.orchestration.runs":
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "runs": read_orchestration_runs(config)}, 0
    if tool_name == "sula.provider.capabilities":
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "capability_report": provider_capabilities_payload(config)}, 0
    if tool_name == "sula.sync.dry_run":
        actions = collect_render_actions(config, include_scaffold=True)
        return {"command": tool_name, "status": "ok", "project": project_payload(config), "plan": sync_plan_payload(actions)}, 0

    before = git_status_paths(config)
    if tool_name == "sula.report.create":
        args = argparse.Namespace(summary=normalize_optional_text(tool_args.get("summary", "")), lightweight=bool(tool_args.get("lightweight", False)), json=True)
        payload, code = capture_json_function(lambda: cmd_report(config, args))
    elif tool_name == "sula.workflow.scaffold":
        args = argparse.Namespace(kind=normalize_optional_text(tool_args.get("kind", "plan")), title=normalize_optional_text(tool_args.get("title", "")), slug=normalize_optional_text(tool_args.get("slug", "")) or None, date=normalize_optional_text(tool_args.get("date", "")) or None, summary=normalize_optional_text(tool_args.get("summary", "")), json=True, project_root=str(config.root))
        payload, code = capture_json_function(lambda: workflow_scaffold(config, args))
    elif tool_name == "sula.orchestration.intake":
        args = argparse.Namespace(title=normalize_optional_text(tool_args.get("title", "")), description=normalize_optional_text(tool_args.get("description", "")), acceptance=normalize_task_string_list(tool_args.get("acceptance", [])), validation=normalize_task_string_list(tool_args.get("validation", [])), label=normalize_task_string_list(tool_args.get("label", [])), risk_hint=normalize_task_string_list(tool_args.get("risk_hint", [])), priority=normalize_optional_text(tool_args.get("priority", "normal")), identifier=normalize_optional_text(tool_args.get("identifier", "")) or None, json=True)
        payload, code = capture_json_function(lambda: orchestration_intake(config, args))
    elif tool_name == "sula.orchestration.close":
        args = argparse.Namespace(run_id=normalize_optional_text(tool_args.get("run_id", "")), evidence=normalize_task_string_list(tool_args.get("evidence", [])), touched_file=normalize_task_string_list(tool_args.get("touched_file", [])), link=normalize_task_string_list(tool_args.get("link", [])), lesson=normalize_task_string_list(tool_args.get("lesson", [])), accept=bool(tool_args.get("accept", False)), json=True)
        payload, code = capture_json_function(lambda: orchestration_close(config, args))
    elif tool_name == "sula.artifact.register":
        args = argparse.Namespace(path=normalize_optional_text(tool_args.get("path", "")) or None, kind=normalize_optional_text(tool_args.get("kind", "")), title=normalize_optional_text(tool_args.get("title", "")) or None, date=normalize_optional_text(tool_args.get("date", "")) or None, slot=normalize_optional_text(tool_args.get("slot", "")) or None, summary=normalize_optional_text(tool_args.get("summary", "")), project_relative_path=normalize_optional_text(tool_args.get("project_relative_path", "")) or None, provider_item_id=normalize_optional_text(tool_args.get("provider_item_id", "")) or None, provider_item_kind=normalize_optional_text(tool_args.get("provider_item_kind", "")) or None, provider_item_url=normalize_optional_text(tool_args.get("provider_item_url", "")) or None, source_of_truth=normalize_optional_text(tool_args.get("source_of_truth", "")) or None, collaboration_mode=normalize_optional_text(tool_args.get("collaboration_mode", "")) or None, artifact_role=normalize_optional_text(tool_args.get("artifact_role", "")) or None, last_refreshed_at=normalize_optional_text(tool_args.get("last_refreshed_at", "")) or None, last_provider_sync_at=normalize_optional_text(tool_args.get("last_provider_sync_at", "")) or None, derived_from=normalize_task_string_list(tool_args.get("derived_from", [])), json=True)
        payload, code = capture_json_function(lambda: artifact_register(config, args))
    elif tool_name == "sula.artifact.materialize":
        args = argparse.Namespace(source_path=normalize_optional_text(tool_args.get("source_path", "")), target_format=normalize_optional_text(tool_args.get("target_format", "")), kind=normalize_optional_text(tool_args.get("kind", "")) or None, title=normalize_optional_text(tool_args.get("title", "")) or None, slug=normalize_optional_text(tool_args.get("slug", "")) or None, slot=normalize_optional_text(tool_args.get("slot", "")) or None, date=normalize_optional_text(tool_args.get("date", "")) or None, summary=normalize_optional_text(tool_args.get("summary", "")), sheet_name=normalize_optional_text(tool_args.get("sheet_name", "Sheet1")), json=True)
        payload, code = capture_json_function(lambda: artifact_materialize(config, args))
    elif tool_name == "sula.artifact.refresh":
        args = argparse.Namespace(artifact_id=normalize_optional_text(tool_args.get("artifact_id", "")) or None, family_key=normalize_optional_text(tool_args.get("family_key", "")) or None, q=normalize_optional_text(tool_args.get("q", "")) or None, all_collaborative=bool(tool_args.get("all_collaborative", False)), limit=int(tool_args.get("limit", 5) or 5), force=bool(tool_args.get("force", False)), json=True)
        payload, code = capture_json_function(lambda: artifact_refresh(config, args))
    else:
        raise SystemExit(f"Unhandled Sula MCP tool: {tool_name}")
    payload["mcp_audit"] = mcp_audit_write(config, tool_name=tool_name, intent=tool_args, before_paths=before, payload=payload, permission=permission)
    return payload, code


def mcp_call_tool(tool_name: str, tool_args: dict[str, object], args: argparse.Namespace) -> tuple[dict[str, object], int]:
    permission = mcp_tool_permission(tool_name)
    if tool_name in {"sula.portfolio.list", "sula.portfolio.status"}:
        portfolio_root = resolve_portfolio_root(normalize_optional_text(tool_args.get("portfolio_root", "")) or getattr(args, "portfolio_root", None))
        if tool_name == "sula.portfolio.list":
            registry = load_portfolio_registry(portfolio_root)
            return {"command": tool_name, "status": "ok", "portfolio_root": str(portfolio_root), "projects": registry.get("projects", [])}, 0
        return {"command": tool_name, "status": "ok", **mcp_portfolio_status_payload(portfolio_root)}, 0
    project_root_raw = normalize_optional_text(tool_args.get("project_root", "")) or normalize_optional_text(getattr(args, "project_root", ""))
    if not project_root_raw:
        raise SystemExit(f"MCP tool `{tool_name}` requires a project root.")
    project_root = Path(project_root_raw).expanduser().resolve()
    policy = load_mcp_policy(args, project_root)
    assert_mcp_project_allowed(policy, project_root, permission=permission)
    config = load_manifest(project_root)
    payload, code = mcp_call_project_tool(config, tool_name, tool_args, permission=permission)
    payload["mcp"] = {"tool": tool_name, "permission": permission, "policy": {"allowed_project_roots": policy.get("allowed_project_roots", []), "enabled_write_classes": policy.get("enabled_write_classes", [])}}
    return payload, code


def handle_mcp_command(args: argparse.Namespace) -> int:
    if args.mcp_command == "tools":
        payload = {"command": "mcp.tools", "status": "ok", **mcp_tools_payload()}
        if json_output_requested(args):
            emit_json(payload)
            return 0
        for item in payload["tools"]:
            print(f"{item['name']} [{item['permission']}] - {item['description']}")
        return 0
    if args.mcp_command == "call":
        payload, code = mcp_call_tool(args.tool, parse_json_object(args.arguments_json, label="arguments"), args)
        emit_json(payload)
        return code
    if args.mcp_command == "serve":
        return mcp_serve(args)
    raise AssertionError("unreachable")


def jsonrpc_result(request_id: object, result: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def jsonrpc_error(request_id: object, code: int, message: str) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def mcp_serve(args: argparse.Namespace) -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        request_payload: dict[str, object] = {}
        try:
            parsed = json.loads(line)
            if not isinstance(parsed, dict):
                raise ValueError("JSON-RPC request must be an object")
            request_payload = parsed
            request_id = request_payload.get("id")
            method = normalize_optional_text(request_payload.get("method", ""))
            params = request_payload.get("params", {})
            if not isinstance(params, dict):
                params = {}
            if method == "initialize":
                response = jsonrpc_result(request_id, {"protocolVersion": "2024-11-05", "serverInfo": {"name": "sula", "version": VERSION}, "capabilities": {"tools": {}}})
            elif method == "tools/list":
                response = jsonrpc_result(request_id, {"tools": [{"name": item["name"], "description": item["description"], "inputSchema": {"type": "object"}} for item in MCP_TOOL_DEFINITIONS]})
            elif method == "tools/call":
                tool_args = params.get("arguments", {})
                if not isinstance(tool_args, dict):
                    tool_args = {}
                payload, _code = mcp_call_tool(normalize_optional_text(params.get("name", "")), tool_args, args)
                response = jsonrpc_result(request_id, {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=True)}], "structuredContent": payload})
            else:
                response = jsonrpc_error(request_id, -32601, f"Unknown method: {method}")
        except Exception as exc:
            response = jsonrpc_error(request_payload.get("id") if request_payload else None, -32000, str(exc))
        print(json.dumps(response, ensure_ascii=True), flush=True)
    return 0


def handle_provider_command(config: ProjectConfig, args: argparse.Namespace) -> int:
    if args.provider_command == "capabilities":
        payload = {"command": "provider.capabilities", "status": "ok", "project": project_payload(config), "capability_report": provider_capabilities_payload(config)}
        if json_output_requested(args):
            emit_json(payload)
            return 0
        report = payload["capability_report"]
        print(f"Provider capabilities for {config.data['project']['name']}: {report['provider']}")
        for item in report["capabilities"]:
            print(f"  - {item}")
        if report["gaps"]:
            print("  Gaps:")
            for item in report["gaps"]:
                print(f"    - {item}")
        return 0
    raise AssertionError("unreachable")


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
    if args.portfolio_command == "orchestration":
        registry = load_portfolio_registry(portfolio_root)
        payload = portfolio_orchestration_payload(registry, portfolio_root)
        if json_output_requested(args):
            emit_json({"command": "portfolio.orchestration", "status": "ok", **payload})
            return 0
        print(f"Portfolio orchestration for {portfolio_root}")
        print(f"  Projects: {payload['project_count']}")
        print(f"  Tasks: {payload['totals']['tasks_total']} total / {payload['totals']['tasks_blocked']} blocked")
        print(f"  Runs needing review: {payload['totals']['runs_human_review']}")
        for item in payload["needs_attention"]:
            print(f"  - {item['project_name']}: {', '.join(item['reasons'])}")
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
                route=determine_query_route(
                    args.q,
                    kind=args.kind,
                    timeline=args.timeline,
                    freshness_intent=False,
                    routing_policy=normalize_optional_text(config.memory_setting("query_routing", "deterministic")),
                ),
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


def portfolio_orchestration_payload(registry: dict[str, object], portfolio_root: Path) -> dict[str, object]:
    project_rows: list[dict[str, object]] = []
    totals = {
        "tasks_total": 0,
        "tasks_eligible": 0,
        "tasks_blocked": 0,
        "runs_total": 0,
        "runs_running": 0,
        "runs_human_review": 0,
        "runs_failed": 0,
        "runs_accepted": 0,
        "triggers_total": 0,
        "promotion_candidates_total": 0,
    }
    needs_attention: list[dict[str, object]] = []
    for item in registry.get("projects", []):
        if not isinstance(item, dict) or not isinstance(item.get("root"), str):
            continue
        project_root = Path(item["root"])
        manifest_path = project_root / MANIFEST_PATH
        if not manifest_path.exists():
            project_rows.append(
                {
                    "project_name": normalize_optional_text(item.get("name", "")) or str(project_root),
                    "project_root": str(project_root),
                    "status": "missing-manifest",
                    "issues": [f"missing manifest: {manifest_path}"],
                }
            )
            needs_attention.append(
                {
                    "project_name": normalize_optional_text(item.get("name", "")) or str(project_root),
                    "project_root": str(project_root),
                    "reasons": ["missing manifest"],
                }
            )
            continue
        config = load_manifest(project_root)
        state = orchestration_status_payload(config)
        task_state = state["tasks"]
        run_state = state["runs"]
        triggers = state.get("triggers", {})
        promotions = state.get("promotion_candidates", {})
        run_counts = run_state.get("counts", {}) if isinstance(run_state, dict) else {}
        row = {
            "project_name": config.data["project"]["name"],
            "project_slug": config.data["project"]["slug"],
            "project_root": str(config.root),
            "workspace": config.portfolio_setting("workspace", "personal"),
            "enabled": config.orchestration_enabled,
            "task_source": config.orchestration_task_source,
            "runner": config.orchestration_runner,
            "tasks": task_state,
            "runs": run_state,
            "triggers": triggers,
            "promotion_candidates": promotions,
        }
        project_rows.append(row)
        totals["tasks_total"] += int(task_state.get("total", 0))
        totals["tasks_eligible"] += int(task_state.get("eligible", 0))
        totals["tasks_blocked"] += int(task_state.get("blocked", 0))
        totals["runs_total"] += int(run_state.get("total", 0))
        totals["runs_running"] += int(run_counts.get("running", 0))
        totals["runs_human_review"] += int(run_counts.get("human-review", 0))
        totals["runs_failed"] += int(run_counts.get("failed", 0))
        totals["runs_accepted"] += int(run_counts.get("accepted", 0))
        totals["triggers_total"] += int(triggers.get("total", 0)) if isinstance(triggers, dict) else 0
        totals["promotion_candidates_total"] += int(promotions.get("total", 0)) if isinstance(promotions, dict) else 0
        reasons: list[str] = []
        if int(task_state.get("blocked", 0)):
            reasons.append(f"{task_state.get('blocked', 0)} blocked task(s)")
        if int(run_counts.get("human-review", 0)):
            reasons.append(f"{run_counts.get('human-review', 0)} run(s) need human review")
        if int(run_counts.get("failed", 0)):
            reasons.append(f"{run_counts.get('failed', 0)} failed run(s)")
        if reasons:
            needs_attention.append(
                {
                    "project_name": config.data["project"]["name"],
                    "project_slug": config.data["project"]["slug"],
                    "project_root": str(config.root),
                    "reasons": reasons,
                }
            )
    return {
        "portfolio_root": str(portfolio_root),
        "project_count": len(project_rows),
        "totals": totals,
        "needs_attention": needs_attention,
        "projects": project_rows,
    }


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


def handle_feedback_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).expanduser().resolve()
    config = load_manifest(project_root)
    if args.feedback_command == "capture":
        feedback = capture_feedback_bundle(config, args)
        if json_output_requested(args):
            emit_json({"command": "feedback.capture", "status": "ok", "project": project_payload(config), "feedback": feedback})
            return 0
        print(f"Captured feedback {feedback['id']} for {config.data['project']['name']}")
        print(f"  Title: {feedback['title']}")
        print(f"  Managed changes: {feedback['managed_change_count']}")
        print(f"  Doctor passed: {feedback['doctor_passed']}")
        print(f"  Bundle: {feedback['bundle_path']}")
        print(f"  Archive: {feedback['archive_path']}")
        return 0

    require_sula_core_project(config, f"feedback {args.feedback_command}")
    if args.feedback_command == "ingest":
        item = ingest_feedback_bundle(config, Path(args.bundle_path).expanduser().resolve())
        if json_output_requested(args):
            emit_json({"command": "feedback.ingest", "status": "ok", "project": project_payload(config), "feedback": item})
            return 0
        print(f"Ingested feedback {item['id']} into Sula Core")
        print(f"  Title: {item['title']}")
        print(f"  Status: {item['status']}")
        print(f"  Bundle: {item['bundle_path']}")
        return 0
    if args.feedback_command == "list":
        catalog = load_feedback_catalog(config)
        items = [item for item in catalog.get("items", []) if isinstance(item, dict)]
        if getattr(args, "status", None):
            items = [item for item in items if item.get("status") == args.status]
        if json_output_requested(args):
            emit_json({"command": "feedback.list", "status": "ok", "project": project_payload(config), "items": items})
            return 0
        print(f"Sula Core feedback queue for {config.data['project']['name']}")
        if not items:
            print("  No feedback items.")
            return 0
        for item in items:
            print(
                "  - "
                f"{item['id']} [{item['status']}] {item['title']} "
                f"({item['source_project_slug']} @ {item['locked_sula_version']})"
            )
        return 0
    if args.feedback_command == "show":
        item = find_feedback_catalog_item(config, args.feedback_id)
        bundle = load_feedback_bundle(config.root / str(item["bundle_path"]))
        if json_output_requested(args):
            emit_json({"command": "feedback.show", "status": "ok", "project": project_payload(config), "feedback": item, "bundle": bundle})
            return 0
        print(f"Feedback {item['id']} [{item['status']}]")
        print(f"  Title: {item['title']}")
        print(f"  Source project: {item['source_project_name']} ({item['source_project_slug']})")
        print(f"  Locked Sula version: {item['locked_sula_version']}")
        print(f"  Managed changes: {item['managed_change_count']}")
        print(f"  Summary: {bundle['feedback']['summary']}")
        if item.get("latest_decision"):
            latest = item["latest_decision"]
            print(f"  Latest decision: {latest['decision']} at {latest['decided_at']}")
        return 0
    if args.feedback_command == "decide":
        item = decide_feedback_bundle(config, args)
        if json_output_requested(args):
            emit_json({"command": "feedback.decide", "status": "ok", "project": project_payload(config), "feedback": item})
            return 0
        print(f"Updated feedback {item['id']} to {item['status']}")
        print(f"  Title: {item['title']}")
        if item.get("latest_decision"):
            latest = item["latest_decision"]
            print(f"  Note: {latest['note']}")
        return 0
    raise AssertionError("unreachable")


def require_sula_core_project(config: ProjectConfig, command: str) -> None:
    if config.profile != "sula-core":
        raise SystemExit(f"{command} requires a project adopted under the `sula-core` profile")


def feedback_outbox_bundles_root(config: ProjectConfig) -> Path:
    return config.root / ".sula" / "feedback" / "outbox" / "bundles"


def feedback_outbox_archives_root(config: ProjectConfig) -> Path:
    return config.root / ".sula" / "feedback" / "outbox" / "archives"


def feedback_registry_root(config: ProjectConfig) -> Path:
    return config.root / "registry" / "feedback"


def feedback_catalog_path(config: ProjectConfig) -> Path:
    return feedback_registry_root(config) / "catalog.json"


def feedback_inbox_root(config: ProjectConfig) -> Path:
    return feedback_registry_root(config) / "inbox"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_memory_capture_id(config: ProjectConfig, title: str, summary: str, captured_at: str) -> str:
    fingerprint = hashlib.sha1(
        f"{config.data['project']['slug']}\n{title}\n{summary}\n{captured_at}".encode("utf-8")
    ).hexdigest()[:8]
    stem = sanitize_slug(title)[:32] or "capture"
    timestamp = captured_at.replace("-", "").replace(":", "").replace("T", "-").replace("Z", "")
    return f"capture-{timestamp}-{stem}-{fingerprint}"


def ensure_session_capture_store(config: ProjectConfig) -> None:
    config.session_capture_store.parent.mkdir(parents=True, exist_ok=True)
    if not config.session_capture_store.exists():
        config.session_capture_store.write_text("", encoding="utf-8")


def ensure_memory_jobs_store(config: ProjectConfig) -> None:
    config.memory_jobs_history_path.parent.mkdir(parents=True, exist_ok=True)
    if not config.memory_jobs_history_path.exists():
        config.memory_jobs_history_path.write_text("", encoding="utf-8")
    if not config.memory_jobs_latest_path.exists():
        config.memory_jobs_latest_path.write_text("{}\n", encoding="utf-8")


def ensure_promotion_file(config: ProjectConfig) -> None:
    promotion_path = config.promotion_file
    promotion_path.parent.mkdir(parents=True, exist_ok=True)
    if promotion_path.exists():
        return
    zh = locale_family(config.content_locale) == "zh"
    text = "\n".join(
        [
            "# 会话提升记录" if zh else "# Session Promotions",
            "",
            "Sula records promoted operating insights here so they become durable project context."
            if not zh
            else "Sula 在此记录已经提升的临时操作洞察，使其成为长期项目上下文。",
            "",
            "## Rules" if not zh else "## 规则",
            "",
            "## Tasks" if not zh else "## 任务",
            "",
            "## Decisions" if not zh else "## 决策",
            "",
            "## State Updates" if not zh else "## 状态更新",
            "",
            "## Workflow Artifacts" if not zh else "## 工作流文档",
            "",
            "## Risks" if not zh else "## 风险",
            "",
        ]
    ).rstrip() + "\n"
    promotion_path.write_text(text, encoding="utf-8")


def memory_state_summary(config: ProjectConfig) -> dict[str, object]:
    captures = read_session_captures(config)
    jobs = read_memory_jobs(config)
    counts = {
        "staged": sum(1 for item in captures if item.get("status") == "staged"),
        "promoted": sum(1 for item in captures if item.get("status") == "promoted"),
        "discarded": sum(1 for item in captures if item.get("status") == "discarded"),
    }
    promotions = [
        item
        for item in captures
        if item.get("status") == "promoted" and normalize_optional_text(item.get("promoted_to", "")).strip()
    ]
    promotions.sort(key=lambda item: normalize_optional_timestamp(item.get("updated_at", "")) or "", reverse=True)
    last_success = next((item for item in jobs if item.get("status") == "ok"), None)
    last_failed = next((item for item in jobs if item.get("status") not in {"ok", "recorded"}), None)
    return {
        "capture_policy": normalize_optional_text(config.memory_setting("capture_policy", "explicit")),
        "promotion_policy": normalize_optional_text(config.memory_setting("promotion_policy", "review-required")),
        "query_routing": normalize_optional_text(config.memory_setting("query_routing", "deterministic")),
        "semantic_cache": normalize_optional_text(config.memory_setting("semantic_cache", "off")),
        "promotion_file": config.promotion_file.relative_to(config.root).as_posix(),
        "session_capture_store": config.session_capture_store.relative_to(config.root).as_posix(),
        "session_retention_days": config.session_retention_days,
        "counts": counts,
        "recent_promotions": promotions[:3],
        "recent_jobs": jobs[:5],
        "last_job": jobs[0] if jobs else None,
        "last_successful_job": last_success,
        "last_failed_job": last_failed,
    }


def read_session_captures(config: ProjectConfig) -> list[dict[str, object]]:
    ensure_session_capture_store(config)
    captures: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(config.session_capture_store.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            item["_line_number"] = line_number
            captures.append(item)
    captures.sort(key=lambda item: normalize_optional_timestamp(item.get("captured_at", "")) or "", reverse=True)
    return captures


def write_session_captures(config: ProjectConfig, captures: list[dict[str, object]]) -> None:
    ensure_session_capture_store(config)
    lines = []
    for item in captures:
        cleaned = {key: value for key, value in item.items() if key != "_line_number"}
        lines.append(json.dumps(cleaned, ensure_ascii=True))
    config.session_capture_store.write_text(("\n".join(lines) + ("\n" if lines else "")), encoding="utf-8")


def find_session_capture(config: ProjectConfig, capture_id: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    captures = read_session_captures(config)
    for item in captures:
        if item.get("id") == capture_id:
            return captures, item
    raise SystemExit(f"Unknown memory capture: {capture_id}")


def capture_status_sort_key(item: dict[str, object]) -> tuple[int, str]:
    priority = {"staged": 0, "promoted": 1, "discarded": 2}
    return (priority.get(str(item.get("status", "")), 99), normalize_optional_timestamp(item.get("captured_at", "")) or "")


def build_memory_job_id(job_type: str, started_at: str) -> str:
    return f"job:{job_type}:{started_at.replace(':', '').replace('-', '').replace('T', '-').replace('Z', '')}"


def record_memory_job(
    config: ProjectConfig,
    *,
    job_type: str,
    status: str,
    summary: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    if not bool(config.memory_setting("job_tracking", True)):
        return {}
    ensure_memory_jobs_store(config)
    started_at = current_utc_timestamp()
    item = {
        "id": build_memory_job_id(job_type, started_at),
        "job_type": job_type,
        "status": status,
        "summary": summary,
        "details": details or {},
        "started_at": started_at,
        "finished_at": started_at,
    }
    with config.memory_jobs_history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=True) + "\n")
    config.memory_jobs_latest_path.write_text(json.dumps(item, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return item


def read_memory_jobs(config: ProjectConfig) -> list[dict[str, object]]:
    ensure_memory_jobs_store(config)
    jobs: list[dict[str, object]] = []
    for raw_line in config.memory_jobs_history_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            jobs.append(item)
    jobs.sort(key=lambda item: normalize_optional_timestamp(item.get("started_at", "")) or "", reverse=True)
    return jobs


def promoted_section_name(target: str, locale: str) -> str:
    zh = locale_family(locale) == "zh"
    mapping = {
        "rule": "规则" if zh else "Rules",
        "task": "任务" if zh else "Tasks",
        "decision": "决策" if zh else "Decisions",
        "risk": "风险" if zh else "Risks",
        "state": "状态更新" if zh else "State Updates",
        "workflow-artifact": "工作流文档" if zh else "Workflow Artifacts",
    }
    return mapping[target]


def promoted_bullet_text(capture: dict[str, object]) -> str:
    title = normalize_optional_text(capture.get("title", "")).strip()
    summary = normalize_optional_text(capture.get("summary", "")).strip()
    captured_at = normalize_optional_text(capture.get("captured_at", "")).strip()
    date_prefix = captured_at[:10] if MEMORY_DATE_PATTERN.fullmatch(captured_at[:10]) else ""
    parts = [part for part in [date_prefix + ":" if date_prefix else "", title, summary] if part]
    if not parts:
        return "Promoted capture"
    text = " ".join(parts).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def append_markdown_section_bullet(path: Path, section_name: str, bullet_text: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if not text.strip():
        text = f"# Session Promotions\n\n## {section_name}\n\n"
    sections = markdown_sections(text)
    existing = markdown_bullet_items(sections.get(section_name, ""))
    if bullet_text in existing:
        return
    lines = text.splitlines()
    heading = f"## {section_name}"
    for index, line in enumerate(lines):
        if line.strip() != heading:
            continue
        insert_at = index + 1
        while insert_at < len(lines) and lines[insert_at].strip():
            insert_at += 1
        insertion = ["", f"- {bullet_text}"]
        lines[insert_at:insert_at] = insertion
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return
    text = text.rstrip() + f"\n\n## {section_name}\n\n- {bullet_text}\n"
    path.write_text(text, encoding="utf-8")


def handle_memory_command(config: ProjectConfig, args: argparse.Namespace) -> int:
    if args.memory_command == "digest":
        return generate_memory_digest(config, args)
    if args.memory_command == "capture":
        captured_at = current_utc_timestamp()
        item = {
            "id": build_memory_capture_id(config, args.title, args.summary, captured_at),
            "title": args.title.strip(),
            "summary": args.summary.strip(),
            "category": args.category,
            "status": "staged",
            "captured_at": captured_at,
            "updated_at": captured_at,
            "source_path": normalize_optional_text(getattr(args, "source_path", "")).strip(),
            "confidence": int(getattr(args, "confidence", 3)),
            "session_id": normalize_optional_text(getattr(args, "session_id", "")).strip(),
        }
        captures = read_session_captures(config)
        captures.append(item)
        write_session_captures(config, captures)
        job = record_memory_job(
            config,
            job_type="memory.capture",
            status="ok",
            summary=f"Captured staged memory `{item['id']}`.",
            details={"capture_id": item["id"], "category": item["category"]},
        )
        refresh_kernel_state(config, event_type="memory.capture", summary=f"Captured staged memory `{item['id']}`.")
        if json_output_requested(args):
            emit_json({"command": "memory.capture", "status": "ok", "project": project_payload(config), "capture": item, "job": job})
            return 0
        print(f"Captured staged memory {item['id']}")
        print(f"  Category: {item['category']}")
        print(f"  Title: {item['title']}")
        return 0
    if args.memory_command == "review":
        captures = read_session_captures(config)
        if getattr(args, "status", None):
            captures = [item for item in captures if item.get("status") == args.status]
        captures.sort(key=capture_status_sort_key)
        captures = captures[: max(1, int(args.limit))]
        if json_output_requested(args):
            emit_json({"command": "memory.review", "status": "ok", "project": project_payload(config), "captures": captures})
            return 0
        print(f"Memory captures for {config.data['project']['name']}")
        if not captures:
            print("  No captures.")
            return 0
        for item in captures:
            print(
                "  - "
                f"{item['id']} [{item.get('status', 'unknown')}] ({item.get('category', 'note')}) "
                f"{item.get('captured_at', '')} {item.get('title', '')}"
            )
            if item.get("source_path"):
                print(f"      source={item.get('source_path')}")
            if item.get("promoted_to"):
                print(f"      promoted_to={item.get('promoted_to')} path={item.get('promotion_path', '')}")
        return 0
    if args.memory_command == "promote":
        captures, capture = find_session_capture(config, args.capture_id)
        if capture.get("status") != "staged":
            raise SystemExit(f"Memory capture `{args.capture_id}` is already {capture.get('status')}")
        ensure_promotion_file(config)
        section_name = promoted_section_name(args.to, config.content_locale)
        bullet_text = promoted_bullet_text(capture)
        append_markdown_section_bullet(config.promotion_file, section_name, bullet_text)
        promoted_at = current_utc_timestamp()
        capture["status"] = "promoted"
        capture["updated_at"] = promoted_at
        capture["promoted_to"] = args.to
        capture["promotion_path"] = config.promotion_file.relative_to(config.root).as_posix()
        capture["promotion_summary"] = bullet_text
        write_session_captures(config, captures)
        job = record_memory_job(
            config,
            job_type="memory.promote",
            status="ok",
            summary=f"Promoted capture `{args.capture_id}` to `{args.to}`.",
            details={"capture_id": args.capture_id, "target": args.to},
        )
        refresh_kernel_state(config, event_type="memory.promote", summary=f"Promoted capture `{args.capture_id}` to `{args.to}`.")
        if json_output_requested(args):
            emit_json({"command": "memory.promote", "status": "ok", "project": project_payload(config), "capture": capture, "job": job})
            return 0
        print(f"Promoted {args.capture_id} to {args.to}")
        print(f"  Path: {capture['promotion_path']}")
        return 0
    if args.memory_command == "clear":
        cleared_paths: list[str] = []
        if args.derived:
            for path in [
                config.root / ".sula" / "cache" / "kernel.db",
                config.root / ".sula" / "cache" / "query-index.json",
                config.root / ".sula" / "cache" / "semantic",
            ]:
                if not path.exists():
                    continue
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                cleared_paths.append(path.relative_to(config.root).as_posix())
        else:
            captures = read_session_captures(config)
            if args.reviewed_captures:
                captures = [item for item in captures if item.get("status") == "staged"]
            elif args.all_captures:
                captures = []
            write_session_captures(config, captures)
            cleared_paths.append(config.session_capture_store.relative_to(config.root).as_posix())
        job = record_memory_job(
            config,
            job_type="memory.clear",
            status="ok",
            summary="Cleared disposable memory state.",
            details={"paths": cleared_paths},
        )
        if args.derived:
            event_log_path = config.root / ".sula" / "events" / "log.jsonl"
            event_log_path.parent.mkdir(parents=True, exist_ok=True)
            if not event_log_path.exists():
                event_log_path.write_text("", encoding="utf-8")
            append_kernel_event(config, event_log_path, "memory.clear", "Cleared disposable memory state.")
        else:
            refresh_kernel_state(config, event_type="memory.clear", summary="Cleared disposable memory state.")
        if json_output_requested(args):
            emit_json({"command": "memory.clear", "status": "ok", "project": project_payload(config), "cleared_paths": cleared_paths, "job": job})
            return 0
        print("Cleared memory state:")
        for item in cleared_paths:
            print(f"  - {item}")
        return 0
    if args.memory_command == "jobs":
        jobs = read_memory_jobs(config)[: max(1, int(args.limit))]
        if json_output_requested(args):
            emit_json({"command": "memory.jobs", "status": "ok", "project": project_payload(config), "jobs": jobs})
            return 0
        print(f"Memory jobs for {config.data['project']['name']}")
        if not jobs:
            print("  No jobs.")
            return 0
        last_success = next((item for item in jobs if item.get("status") == "ok"), None)
        last_failed = next((item for item in jobs if item.get("status") not in {"ok", "recorded"}), None)
        if last_success:
            print(f"  Last successful job: {last_success.get('started_at', '')} {last_success.get('job_type', '')}")
        if last_failed:
            print(f"  Last failed job: {last_failed.get('started_at', '')} {last_failed.get('job_type', '')}")
        for item in jobs:
            print(f"  - {item.get('started_at', '')} [{item.get('job_type', '')}] {item.get('status', '')} :: {item.get('summary', '')}")
        return 0
    raise AssertionError("unreachable")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_feedback_id(config: ProjectConfig, title: str, summary: str, captured_at: str) -> str:
    timestamp = captured_at.replace("-", "").replace(":", "").replace(".", "").replace("Z", "").replace("T", "T")
    slug = sanitize_slug(title)[:40]
    fingerprint = hashlib.sha256(
        f"{config.data['project']['slug']}\n{title}\n{summary}\n{captured_at}".encode("utf-8")
    ).hexdigest()[:8]
    return f"feedback-{timestamp}-{slug}-{fingerprint}"


def write_feedback_text(bundle_root: Path, relative_path: Path, text: str) -> None:
    output_path = bundle_root / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def diff_patch_relative_path(relative_path: Path) -> Path:
    patch_path = Path("diffs") / relative_path
    return patch_path.parent / f"{patch_path.name}.patch"


def diff_line_counts(diff_lines: list[str]) -> tuple[int, int]:
    added = 0
    removed = 0
    for line in diff_lines:
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def create_feedback_archive(bundle_root: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_resolved = archive_path.resolve()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle_root.rglob("*")):
            if path.is_dir():
                continue
            if path.resolve() == archive_resolved:
                continue
            archive.write(path, arcname=f"{bundle_root.name}/{path.relative_to(bundle_root).as_posix()}")


def load_feedback_bundle(bundle_root: Path) -> dict[str, object]:
    bundle_path = bundle_root / "bundle.json"
    if not bundle_path.exists():
        raise SystemExit(f"Missing feedback bundle manifest: {bundle_path}")
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid feedback bundle JSON: {bundle_path} ({exc})")
    if not isinstance(bundle, dict):
        raise SystemExit(f"Malformed feedback bundle: {bundle_path}")
    feedback = bundle.get("feedback")
    if not isinstance(feedback, dict) or not isinstance(feedback.get("id"), str) or not feedback["id"].strip():
        raise SystemExit(f"Malformed feedback bundle metadata: {bundle_path}")
    return bundle


def resolve_feedback_bundle_source(bundle_path: Path) -> tuple[Path, object | None]:
    if bundle_path.is_dir():
        return bundle_path, None
    if bundle_path.is_file() and zipfile.is_zipfile(bundle_path):
        tempdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(bundle_path) as archive:
            archive.extractall(tempdir.name)
        candidates = [path.parent for path in Path(tempdir.name).rglob("bundle.json")]
        if len(candidates) != 1:
            tempdir.cleanup()
            raise SystemExit(f"Expected exactly one feedback bundle in archive: {bundle_path}")
        return candidates[0], tempdir
    raise SystemExit(f"Feedback bundle path must be a directory or zip archive: {bundle_path}")


def default_feedback_catalog() -> dict[str, object]:
    return {"version": VERSION, "updated_at": "", "items": []}


def ensure_feedback_catalog(config: ProjectConfig) -> None:
    registry_root = feedback_registry_root(config)
    registry_root.mkdir(parents=True, exist_ok=True)
    feedback_inbox_root(config).mkdir(parents=True, exist_ok=True)
    catalog_path = feedback_catalog_path(config)
    if catalog_path.exists():
        return
    catalog_path.write_text(json.dumps(default_feedback_catalog(), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_feedback_catalog(config: ProjectConfig) -> dict[str, object]:
    ensure_feedback_catalog(config)
    path = feedback_catalog_path(config)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid feedback catalog JSON: {path} ({exc})")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise SystemExit(f"Malformed feedback catalog: {path}")
    return data


def write_feedback_catalog(config: ProjectConfig, catalog: dict[str, object]) -> None:
    ensure_feedback_catalog(config)
    path = feedback_catalog_path(config)
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def capture_feedback_bundle(config: ProjectConfig, args: argparse.Namespace) -> dict[str, object]:
    captured_at = utc_timestamp()
    feedback_id = build_feedback_id(config, args.title, args.summary, captured_at)
    bundle_root = feedback_outbox_bundles_root(config) / feedback_id
    archive_path = feedback_outbox_archives_root(config) / f"{feedback_id}.zip"
    if bundle_root.exists() or archive_path.exists():
        raise SystemExit(f"Feedback bundle already exists: {feedback_id}")

    bundle_root.mkdir(parents=True, exist_ok=True)
    feedback_outbox_archives_root(config).mkdir(parents=True, exist_ok=True)

    actions = collect_render_actions(config, include_scaffold=False)
    drifted_actions = [action for action in actions if action.status == "update"]
    doctor_state = inspect_doctor_state(config, strict=False)
    managed_changes: list[dict[str, object]] = []
    combined_diff_parts: list[str] = []

    for action in drifted_actions:
        current_text = action.output_path.read_text(encoding="utf-8")
        diff_lines = list(
            difflib.unified_diff(
                action.rendered_text.splitlines(keepends=True),
                current_text.splitlines(keepends=True),
                fromfile=f"rendered/{action.relative_path.as_posix()}",
                tofile=f"local/{action.relative_path.as_posix()}",
            )
        )
        diff_text = "".join(diff_lines)
        local_relative_path = Path("files") / "local" / action.relative_path
        rendered_relative_path = Path("files") / "rendered" / action.relative_path
        patch_relative_path = diff_patch_relative_path(action.relative_path)
        write_feedback_text(bundle_root, local_relative_path, current_text)
        write_feedback_text(bundle_root, rendered_relative_path, action.rendered_text)
        write_feedback_text(bundle_root, patch_relative_path, diff_text)
        added_lines, removed_lines = diff_line_counts(diff_lines)
        if diff_text:
            combined_diff_parts.append(diff_text)
        managed_changes.append(
            {
                "path": action.relative_path.as_posix(),
                "origin": action.origin,
                "impact_level": action.impact_level,
                "impact_scope": action.impact_scope,
                "local_sha256": sha256_text(current_text),
                "rendered_sha256": sha256_text(action.rendered_text),
                "added_lines": added_lines,
                "removed_lines": removed_lines,
                "local_path": local_relative_path.as_posix(),
                "rendered_path": rendered_relative_path.as_posix(),
                "patch_path": patch_relative_path.as_posix(),
            }
        )

    combined_patch_text = "".join(combined_diff_parts)
    write_feedback_text(bundle_root, Path("changes.patch"), combined_patch_text)
    write_feedback_text(bundle_root, Path("doctor.json"), json.dumps(doctor_state, indent=2, ensure_ascii=True) + "\n")
    write_feedback_text(
        bundle_root,
        Path("sync-plan.json"),
        json.dumps(sync_plan_payload(actions), indent=2, ensure_ascii=True) + "\n",
    )
    write_feedback_text(bundle_root, Path("snapshots") / "project.toml", (config.root / MANIFEST_PATH).read_text(encoding="utf-8"))
    write_feedback_text(bundle_root, Path("snapshots") / "version.lock", (config.root / LOCK_PATH).read_text(encoding="utf-8"))

    bundle = {
        "schema_version": FEEDBACK_BUNDLE_SCHEMA_VERSION,
        "captured_at": captured_at,
        "feedback": {
            "id": feedback_id,
            "title": args.title,
            "summary": args.summary,
            "kind": args.kind,
            "severity": args.severity,
            "shared_rationale": args.shared_rationale,
            "local_fix_summary": args.local_fix_summary.strip(),
            "requested_outcome": args.requested_outcome.strip(),
        },
        "source_project": {
            "project": config.data["project"],
            "repository": config.data["repository"],
            "workflow": config.data.get("workflow", {}),
            "storage": config.data.get("storage", {}),
            "portfolio": config.data.get("portfolio", {}),
            "language": config.data.get("language", {}),
            "root": str(config.root),
        },
        "source_sula": {
            "captured_with_version": VERSION,
            "locked_version": parse_flat_kv_toml((config.root / LOCK_PATH).read_text(encoding="utf-8")).get("sula_version", ""),
            "profile": config.profile,
        },
        "doctor": doctor_state,
        "sync_plan": sync_plan_payload(actions),
        "managed_changes": managed_changes,
        "artifacts": {
            "doctor_report": "doctor.json",
            "sync_plan": "sync-plan.json",
            "combined_patch": "changes.patch",
            "manifest_snapshot": "snapshots/project.toml",
            "lockfile_snapshot": "snapshots/version.lock",
        },
    }
    write_feedback_text(bundle_root, Path("bundle.json"), json.dumps(bundle, indent=2, ensure_ascii=True) + "\n")
    create_feedback_archive(bundle_root, archive_path)
    refresh_kernel_state(config, event_type="feedback.captured", summary=f"Captured reusable feedback `{args.title}`.")
    return {
        "id": feedback_id,
        "title": args.title,
        "kind": args.kind,
        "severity": args.severity,
        "bundle_path": bundle_root.relative_to(config.root).as_posix(),
        "archive_path": archive_path.relative_to(config.root).as_posix(),
        "captured_at": captured_at,
        "managed_change_count": len(managed_changes),
        "doctor_passed": bool(doctor_state["passed"]),
        "locked_sula_version": bundle["source_sula"]["locked_version"],
    }


def feedback_catalog_entry(
    config: ProjectConfig,
    bundle: dict[str, object],
    *,
    bundle_path: Path,
    archive_path: Path,
    ingested_at: str,
) -> dict[str, object]:
    feedback = bundle["feedback"]
    source_project = bundle["source_project"]
    source_sula = bundle["source_sula"]
    doctor_report = bundle["doctor"]
    return {
        "id": feedback["id"],
        "title": feedback["title"],
        "kind": feedback["kind"],
        "severity": feedback["severity"],
        "status": "open",
        "captured_at": bundle["captured_at"],
        "ingested_at": ingested_at,
        "updated_at": ingested_at,
        "source_project_name": source_project["project"]["name"],
        "source_project_slug": source_project["project"]["slug"],
        "source_profile": source_project["project"]["profile"],
        "locked_sula_version": source_sula["locked_version"],
        "captured_with_version": source_sula["captured_with_version"],
        "managed_change_count": len(bundle.get("managed_changes", [])),
        "doctor_passed": bool(doctor_report.get("passed")),
        "bundle_path": bundle_path.relative_to(config.root).as_posix(),
        "archive_path": archive_path.relative_to(config.root).as_posix(),
        "shared_rationale": feedback["shared_rationale"],
        "requested_outcome": feedback.get("requested_outcome", ""),
        "latest_decision": None,
        "decision_history": [],
    }


def ingest_feedback_bundle(config: ProjectConfig, source_path: Path) -> dict[str, object]:
    source_bundle_root, tempdir = resolve_feedback_bundle_source(source_path)
    try:
        bundle = load_feedback_bundle(source_bundle_root)
        catalog = load_feedback_catalog(config)
        feedback_id = str(bundle["feedback"]["id"])
        existing_ids = {str(item.get("id")) for item in catalog.get("items", []) if isinstance(item, dict)}
        if feedback_id in existing_ids:
            raise SystemExit(f"Feedback already exists in Sula Core: {feedback_id}")
        inbox_root = feedback_inbox_root(config)
        target_root = inbox_root / feedback_id
        if target_root.exists():
            raise SystemExit(f"Feedback inbox path already exists: {target_root}")
        shutil.copytree(source_bundle_root, target_root)
        target_archive = target_root / "bundle.zip"
        if source_path.is_file() and zipfile.is_zipfile(source_path):
            shutil.copyfile(source_path, target_archive)
        else:
            create_feedback_archive(target_root, target_archive)
        ingested_at = utc_timestamp()
        entry = feedback_catalog_entry(
            config,
            bundle,
            bundle_path=target_root,
            archive_path=target_archive,
            ingested_at=ingested_at,
        )
        items = [item for item in catalog.get("items", []) if isinstance(item, dict)]
        items.append(entry)
        items.sort(key=lambda item: (str(item.get("status", "")) != "open", str(item.get("captured_at", "")), str(item.get("id", ""))))
        catalog["version"] = VERSION
        catalog["updated_at"] = ingested_at
        catalog["items"] = items
        write_feedback_catalog(config, catalog)
        refresh_kernel_state(
            config,
            event_type="feedback.ingested",
            summary=f"Ingested feedback `{feedback_id}` from `{entry['source_project_slug']}`.",
        )
        return entry
    finally:
        if tempdir is not None:
            tempdir.cleanup()


def find_feedback_catalog_item(config: ProjectConfig, feedback_id: str) -> dict[str, object]:
    catalog = load_feedback_catalog(config)
    for item in catalog.get("items", []):
        if isinstance(item, dict) and item.get("id") == feedback_id:
            return item
    raise SystemExit(f"Unknown feedback id: {feedback_id}")


def decide_feedback_bundle(config: ProjectConfig, args: argparse.Namespace) -> dict[str, object]:
    catalog = load_feedback_catalog(config)
    items = [item for item in catalog.get("items", []) if isinstance(item, dict)]
    match_index = next((index for index, item in enumerate(items) if item.get("id") == args.feedback_id), None)
    if match_index is None:
        raise SystemExit(f"Unknown feedback id: {args.feedback_id}")
    decided_at = utc_timestamp()
    decision_record = {
        "decision": args.decision,
        "note": args.note,
        "decided_at": decided_at,
        "target_version": args.target_version or "",
        "linked_change_record": args.linked_change_record or "",
        "linked_release": args.linked_release or "",
    }
    item = dict(items[match_index])
    raw_history = item.get("decision_history", [])
    decision_history = list(raw_history) if isinstance(raw_history, list) else []
    decision_history.append(decision_record)
    item["status"] = args.decision
    item["updated_at"] = decided_at
    item["latest_decision"] = decision_record
    item["decision_history"] = decision_history
    items[match_index] = item
    catalog["version"] = VERSION
    catalog["updated_at"] = decided_at
    catalog["items"] = items
    write_feedback_catalog(config, catalog)

    bundle_root = config.root / str(item["bundle_path"])
    write_feedback_text(bundle_root, Path("decision.json"), json.dumps(decision_record, indent=2, ensure_ascii=True) + "\n")
    refresh_kernel_state(
        config,
        event_type="feedback.decided",
        summary=f"Marked feedback `{args.feedback_id}` as `{args.decision}`.",
    )
    return item


def load_json_file(path: Path, *, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def render_export_catalog(config: ProjectConfig) -> str:
    export_items = [
        {"path": config.data["paths"]["status_file"], "kind": "status", "project_owned": True},
        {"path": config.data["paths"]["change_records_file"], "kind": "change-index", "project_owned": True},
        {"path": config.memory_setting("digest_file", ".sula/memory-digest.md"), "kind": "memory-digest", "project_owned": False},
        {"path": ".sula/exports/provider-imports", "kind": "provider-import-plans", "project_owned": False},
        {"path": ".sula/cache/provider-snapshots", "kind": "provider-snapshots", "project_owned": False},
        {"path": ".sula/feedback/outbox/archives", "kind": "feedback-outbox", "project_owned": False},
    ]
    if config.profile == "sula-core":
        export_items.extend(
            [
                {"path": "registry/feedback/catalog.json", "kind": "feedback-catalog", "project_owned": True},
                {"path": "registry/feedback/inbox", "kind": "feedback-inbox", "project_owned": True},
            ]
        )
    exports = {
        "version": VERSION,
        "exports": export_items,
    }
    return json.dumps(exports, indent=2, ensure_ascii=True) + "\n"


def normalize_manifest_projection_data(data: dict) -> dict[str, object]:
    profile = str(data.get("project", {}).get("profile", "generic-project"))
    section = data.setdefault("projection", {})
    assert isinstance(section, dict)
    default_mode = default_projection_mode_for_existing_consumer(profile)
    mode = normalize_projection_mode(str(section.get("mode", default_mode)), default_mode)
    raw_packs = section.get("enabled_packs", [])
    packs = normalize_projection_packs(profile, raw_packs if isinstance(raw_packs, list) else [])
    if not packs:
        packs = default_projection_packs(profile, mode)
    section["mode"] = mode
    section["enabled_packs"] = packs
    document_design = data.setdefault("document_design", default_document_design_config(projection_mode=mode))
    assert isinstance(document_design, dict)
    principles_default = "docs/ops/document-design-principles.md"
    current_principles = str(document_design.get("principles_path", "") or "").strip()
    if "document-design" in packs:
        if current_principles.lower() in NON_PATH_SENTINELS or not current_principles:
            document_design["principles_path"] = principles_default
    elif current_principles == principles_default:
        document_design["principles_path"] = "n/a"
    return section


def write_manifest_data(project_root: Path, data: dict) -> ProjectConfig:
    normalize_manifest_projection_data(data)
    manifest_path = project_root / MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(render_manifest(data), encoding="utf-8")
    return load_manifest(project_root)


def projection_pack_state_payload(config: ProjectConfig) -> dict[str, object]:
    enabled = set(config.enabled_projection_packs)
    defaults = set(default_projection_packs(config.profile, config.projection_mode))
    descriptions = projection_pack_descriptions()
    return {
        "mode": config.projection_mode,
        "enabled_packs": config.enabled_projection_packs,
        "available_packs": [
            {
                "id": pack,
                "enabled": pack in enabled,
                "default_for_mode": pack in defaults,
                "description": descriptions.get(pack, "Sula projection pack."),
            }
            for pack in profile_available_projection_packs(config.profile)
        ],
    }


def handle_projection_command(project_root: Path, args: argparse.Namespace) -> int:
    config = load_manifest(project_root)
    if args.projection_command == "list":
        payload = {"command": "projection.list", "status": "ok", "project": project_payload(config), "projection": projection_pack_state_payload(config)}
        if json_output_requested(args):
            emit_json(payload)
            return 0
        print(f"Sula projections for {config.data['project']['name']}:")
        print(f"  mode: {config.projection_mode}")
        for item in payload["projection"]["available_packs"]:
            state = "enabled" if item["enabled"] else "disabled"
            default_suffix = " [default]" if item["default_for_mode"] else ""
            print(f"  - {item['id']}: {state}{default_suffix} :: {item['description']}")
        return 0

    data = json.loads(json.dumps(config.data))
    projection_data = normalize_manifest_projection_data(data)
    packs = list(projection_data["enabled_packs"])

    if args.projection_command == "mode":
        projection_data["mode"] = args.mode
        projection_data["enabled_packs"] = default_projection_packs(config.profile, args.mode)
    elif args.projection_command == "enable":
        if args.pack not in profile_available_projection_packs(config.profile):
            raise SystemExit(f"Unknown projection pack for profile `{config.profile}`: {args.pack}")
        if args.pack not in packs:
            packs.append(args.pack)
        projection_data["enabled_packs"] = normalize_projection_packs(config.profile, packs)
    elif args.projection_command == "disable":
        if args.pack not in profile_available_projection_packs(config.profile):
            raise SystemExit(f"Unknown projection pack for profile `{config.profile}`: {args.pack}")
        dependent_packs = [pack for pack in packs if pack != args.pack and args.pack in projection_pack_dependencies(pack)]
        if dependent_packs:
            raise SystemExit(
                f"Cannot disable projection pack `{args.pack}` while dependent packs remain enabled: {', '.join(dependent_packs)}"
            )
        projection_data["enabled_packs"] = [pack for pack in packs if pack != args.pack]
    else:
        raise AssertionError("unreachable")

    updated_config = write_manifest_data(project_root, data)
    actions = collect_render_actions(updated_config, include_scaffold=True)
    apply_projection_state(updated_config, actions)
    write_lockfile(updated_config)
    refresh_kernel_state(
        updated_config,
        event_type="projection.updated",
        summary=f"Updated Sula projection settings via `{args.projection_command}`.",
    )
    payload = {
        "command": f"projection.{args.projection_command}",
        "status": "ok",
        "project": project_payload(updated_config),
        "projection": projection_pack_state_payload(updated_config),
        "plan": sync_plan_payload(actions),
    }
    if json_output_requested(args):
        emit_json(payload)
        return 0
    print(f"Updated Sula projection state for {updated_config.data['project']['name']}")
    print(f"  mode: {updated_config.projection_mode}")
    print(f"  enabled packs: {', '.join(updated_config.enabled_projection_packs) or 'none'}")
    return 0


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
    registry_path = projection_registry_path(config)
    if registry_path.exists():
        registry = load_projection_registry(config)
        managed_paths = sorted(
            {
                project_root / str(item.get("path", ""))
                for items in registry.get("packs", {}).values()
                if isinstance(items, list)
                for item in items
                if isinstance(item, dict) and bool(item.get("managed")) and str(item.get("path", ""))
            },
            key=lambda path: path.as_posix(),
        )
        scaffold_paths = sorted(
            {
                project_root / str(item.get("path", ""))
                for items in registry.get("packs", {}).values()
                if isinstance(items, list)
                for item in items
                if isinstance(item, dict) and not bool(item.get("managed")) and str(item.get("path", ""))
            },
            key=lambda path: path.as_posix(),
        )
    else:
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
    promotion_path = config.promotion_file
    if promotion_path.exists() and promotion_path.is_relative_to(project_root):
        managed_paths = sorted({*managed_paths, promotion_path}, key=lambda path: path.as_posix())
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
