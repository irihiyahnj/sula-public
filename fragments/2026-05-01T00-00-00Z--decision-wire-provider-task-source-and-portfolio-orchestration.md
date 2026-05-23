---
id: 2026-05-01T00-00-00Z--decision-wire-provider-task-source-and-portfolio-orchestration
time: 2026-05-01T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-01-wire-provider-task-source-and-portfolio-orchestration.md
---
# Wire Provider Task Source And Portfolio Orchestration

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

The completed orchestration design requires more than local task files and single-project status. Sula needs at least one external task-source adapter and a portfolio-level orchestration view so users can see blocked, running, failed, and review-needed work across adopted projects.

## Analysis

- Sula Core should not depend on network SDKs or a specific tracker to prove the external task-source contract.
- Provider-backed and external task systems can safely enter Core through project-local mirror files under `orchestration.tasks_path`.
- Portfolio orchestration should summarize project-local state without replacing project-local policy as the authority.
- Cross-project attention should focus on blocked tasks, human-review runs, failed runs, triggers, and promotion candidates.

## Chosen Plan

- Add `task_source = "provider-task-document"` as the first external/provider task adapter.
- Support Markdown checklist task mirrors and JSON task mirrors under the existing normalized task model.
- Add `portfolio orchestration --json` to aggregate orchestration state across registered projects.
- Keep all writes inside `.sula/state/orchestration/` operational records and project-owned task mirror files.

## Execution

- Added `provider-task-document` to the manifest task-source enum and schema.
- Added Markdown checklist parsing for provider task documents with metadata such as `id`, `acceptance`, `validation`, `labels`, `priority`, and `risk`.
- Added JSON mirror support for provider task documents.
- Added portfolio orchestration aggregation with totals for tasks, runs, triggers, and promotion candidates.
- Added `needs_attention` rows for blocked tasks, human-review runs, failed runs, and missing manifests.
- Updated README, manifest reference, orchestration reference, execution plan, and tests.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m json.tool schema/project.schema.json`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_provider_task_document_source_and_portfolio_orchestration_summary -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_portfolio_register_list_and_query_json -v`
- `python3 -m unittest discover -s tests -v` passed 103 tests.
- `python3 scripts/sula.py doctor --project-root . --strict --json` passed.
- `python3 scripts/sula.py check --project-root . --json` passed.
- `python3 scripts/sula.py orchestration doctor --project-root . --json` passed with expected disabled-orchestration warnings.
- `python3 scripts/sula.py portfolio orchestration --portfolio-root /tmp/sula-empty-portfolio --json` passed.

## Rollback

- Remove `provider-task-document` from task-source choices, schema, docs, and loader dispatch.
- Remove `portfolio orchestration` command and aggregation helper.
- Preserve existing project-local provider task mirror files because they are project-owned task truth.

## Data Side-effects

- Projects may set `orchestration.task_source = "provider-task-document"` and point `tasks_path` at a Markdown or JSON task mirror.
- `portfolio orchestration` reads registered projects and writes normal per-project orchestration snapshots through existing status helpers.

## Follow-up

- Add direct provider refresh/import integration for provider-native task documents when provider write/read adapters are enabled.
- Add Codex SDK/app-server runner adapters behind optional adapter boundaries.
- Add richer PR/artifact verification to closeout evaluator.

## Architecture Boundary Check

- highest rule impact: preserved. Provider task mirrors remain project-owned task truth, while Sula only normalizes them for dispatch and portfolio observability.
