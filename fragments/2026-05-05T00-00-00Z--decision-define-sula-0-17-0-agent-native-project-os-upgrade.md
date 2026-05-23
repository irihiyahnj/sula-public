---
id: 2026-05-05T00-00-00Z--decision-define-sula-0-17-0-agent-native-project-os-upgrade
time: 2026-05-05T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-05-define-sula-0-17-0-agent-native-project-os-upgrade.md
---
# Define Sula 0.17.0 agent-native project OS upgrade

## Metadata

- date: 2026-05-05
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Added the 0.17.0 agent-native project operating system whitepaper, overview link, executable workflow spec/plan/review, and task intake for phased MCP-compatible control-surface implementation.

## Analysis

- Sula 0.16.0 already has durable memory, workflow scaffolds, orchestration, automation, provider-backed artifact identity, and machine-readable CLI output.
- The next upgrade should not add another project template or platform-specific agent plugin. It should expose Sula's existing operating-system layer through a stable, policy-gated agent access surface.
- MCP-compatible access is useful for Hermes, Codex, Claude, Cursor, and future agents, but it must stay optional so the CLI remains the portable core.
- The design must cover both software projects and real-world service projects without forcing software-only rules onto non-software work.

## Chosen Plan

- Define 0.17.0 as an agent-native project OS control-surface upgrade.
- Keep read-only access first, controlled Sula-managed writes second, and strongly approved operations out of the default surface.
- Treat provider capability reporting and PR closeout structured checks as bounded verification upgrades.
- Formalize the implementation as an open workflow task with spec, plan, and review documents.

## Execution

- Added `docs/reference/sula-0-17-0-agent-native-project-os-whitepaper.md`.
- Added `docs/sula-overview.md` as a concise product overview and linked it to the 0.17.0 whitepaper.
- Added README reference links for the overview and whitepaper.
- Created workflow task intake in `docs/workflows/tasks.json`.
- Created and filled workflow spec, plan, and review records for the 0.17.0 execution task.
- Added executable task-package breakdown inside the whitepaper for phased implementation.

## Verification

- Pending final session verification:
  - `python3 scripts/sula.py check --project-root .`
  - `python3 scripts/sula.py doctor --project-root . --strict`
  - `python3 -m unittest discover -s tests -v`

## Rollback

- Remove the new whitepaper and overview documents.
- Remove README reference links.
- Remove the 0.17.0 workflow task and generated workflow spec/plan/review documents.
- Regenerate Sula state with `python3 scripts/sula.py check --project-root .` if operating indexes need to be refreshed.

## Data Side-effects

- Sula operating indexes, source registry, artifact catalog, event log, and workflow task state were updated by Sula commands.
- No provider-native documents, external services, production systems, or project-owned business truth were changed.

## Follow-up

- Start implementation with the `mcp-readonly-surface` task package from the whitepaper.
- Decide the MCP transport/dependency strategy while preserving dependency-light CLI behavior.
- Add non-software service canary coverage before 0.17.0 release readiness.

## Architecture Boundary Check

- highest rule impact: preserved. The whitepaper explicitly keeps Sula-managed operating files under Sula control and keeps project-owned business truth outside centrally managed templates.
