---
id: 2026-05-05T00-00-00Z--decision-implement-sula-0-17-0-agent-native-control-surface
time: 2026-05-05T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-05-implement-sula-0-17-0-agent-native-control-surface.md
---
# Implement Sula 0.17.0 agent-native control surface

## Metadata

- date: 2026-05-05
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Implemented the optional MCP-compatible Sula control surface, controlled write tooling, project policy view, portfolio status summary, provider capability report, PR closeout structured evidence, and 0.17.0 release metadata.

## Analysis

- Sula already exposed machine-readable CLI payloads, but external agents still needed to know which commands and files to use.
- 0.17.0 needed an optional agent-native access layer without turning MCP into the only entrypoint or giving agents arbitrary shell/file writes.
- Read-only project and portfolio tools could be implemented as a thin layer over existing state files and payload helpers.
- Controlled writes needed explicit write-class enablement, project-root allowlisting, and audit events.

## Chosen Plan

- Add a dependency-light `mcp` command family with `tools`, `call`, and minimal stdio `serve`.
- Keep default behavior read-only.
- Route write tools through existing Sula commands and functions.
- Add explicit provider capability and project policy payloads.
- Strengthen PR closeout evidence with CI/review summary fields.
- Version the release as 0.17.0 after the control surface is implemented.

## Execution

- Added MCP tool definitions for project, artifact, workflow, orchestration, portfolio, provider, report, sync, and controlled artifact operations.
- Added `mcp call` and stdio `mcp serve` entrypoints.
- Added local MCP policy handling for allowlisted project roots and enabled write classes.
- Added project bootstrap, project rules, read-only status, artifact locate/list, provider capabilities, and portfolio status payloads.
- Added controlled write wrappers for report, workflow scaffold, orchestration intake/close, artifact register/materialize/refresh, and sync dry-run.
- Added audit events for MCP write tools.
- Added provider capability CLI surface.
- Extended PR verification results with `checks_summary`, `review_summary`, `ci_state`, unresolved review-thread count, review comments requiring action, and `closeout_state`.
- Added MCP and PR closeout regression tests.
- Made registry canary verification rebuild memory digest after its own sync/doctor activity and before the final check, so `canary verify` does not make committed canary state stale during the same run.
- Updated `VERSION`, `site/sula.json`, `CHANGELOG.md`, the Sula overview, and release docs for 0.17.0.
- Restored `site/launch/bootstrap.py` for public release readiness and aligned its default source ref with `v0.17.0`.
- Published the clean public export to `https://github.com/irihiyahnj/sula-public.git` on `main` with tag `v0.17.0`.

## Verification

- Task package closeout:
  - `mcp-readonly-surface`: implemented `mcp tools`, `mcp call`, stdio `mcp serve`, read-only project/artifact/workflow/orchestration/portfolio/provider tools; verified by no-write MCP bootstrap/rules tests and stdio tools-list test; rollback by removing the `mcp` command family and tool definitions.
  - `project-policy-view`: implemented `sula.project.bootstrap` and `sula.project.rules` consolidated payloads; verified across software and service project fixtures through MCP portfolio/provider tests; rollback by removing the bootstrap/rules payload helpers.
  - `controlled-record-tools`: implemented policy-gated report, workflow, orchestration, artifact, refresh, and sync dry-run wrappers; verified by controlled report policy/audit test; rollback by removing controlled write dispatch and audit hooks.
  - `portfolio-control-surface`: implemented `sula.portfolio.list` and `sula.portfolio.status`; verified by multi-project portfolio status test; rollback by removing portfolio MCP payload helpers.
  - `provider-capability-report`: implemented `provider capabilities --json` and `sula.provider.capabilities`; verified by Google Drive/local-fs fixture expectations; rollback by removing provider capability payload and command routing.
  - `pr-closeout-structured-checks`: added CI/review summary fields, unresolved review-thread counts, review comments requiring action, and closeout state; verified by remote PR fixture closeout test; rollback by reverting PR verification summary helpers.
  - `non-software-canary`: kept field-ops and client-service Google Drive canaries aligned with 0.17.0 and fixed canary verification ordering; verified by `canary verify --all`; rollback by reverting canary fixture state and the `memory_digest` canary check step.
  - `release-docs-and-rollout`: updated version metadata, launch descriptor, README, manifest reference, agent instructions, changelog, release record, workflow review, STATUS, and memory digest; verified by final `check`, `doctor --strict`, full unittest, and canary verification.
- Targeted tests passed:
  - `python3 -m unittest tests.test_sula.SulaCliTests.test_mcp_readonly_bootstrap_and_rules_do_not_write_project_files tests.test_sula.SulaCliTests.test_mcp_controlled_report_requires_policy_and_writes_audit tests.test_sula.SulaCliTests.test_mcp_portfolio_status_and_provider_capabilities_cover_service_projects tests.test_sula.SulaCliTests.test_mcp_stdio_serves_tools_list tests.test_sula.SulaCliTests.test_orchestration_closeout_requires_remote_pr_verification_when_configured -v`
- Final release verification passed:
  - `python3 scripts/sula.py check --project-root .`
  - `python3 scripts/sula.py doctor --project-root . --strict`
  - `python3 -m unittest discover -s tests -v` (116 tests)
  - `python3 -m unittest tests.test_sula.SulaCliTests.test_canary_verify_runs_local_registry_canaries -v`
  - `python3 scripts/sula.py canary verify --project-root . --all`

## Rollback

- Revert MCP command registration and helper payloads in `scripts/sula.py`.
- Revert PR verification summary additions if structured closeout fields need to be postponed.
- Restore `VERSION`, `site/sula.json`, changelog, release docs, and tests to the previous 0.16.0 baseline.

## Data Side-effects

- Controlled MCP writes append audit events to `.sula/events/log.jsonl`.
- Read-only MCP calls are designed not to mutate project files.
- No provider-native writes, arbitrary shell commands, or destructive project operations were introduced.

## Follow-up

- Add host-specific examples for Hermes or other MCP clients after the minimal stdio surface is validated.
- Add richer authenticated provider capability reports when real provider write targets are selected.

## Architecture Boundary Check

- highest rule impact: preserved. Sula-managed writes are routed through Sula, project-owned business truth remains outside centrally managed operating files, and MCP is optional rather than a replacement for the CLI.
