---
id: 2026-05-01T00-00-00Z--decision-sula-karpathy-inspired-agent-quality-policy
time: 2026-05-01T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-01-sula-karpathy-inspired-agent-quality-policy.md
---
# Sula Karpathy-Inspired Agent Quality Policy

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Sula evaluated `forrestchang/andrej-karpathy-skills` as a possible capability upgrade. The upstream repository is a compact instruction package for agent coding behavior: think before coding, simplify, make surgical changes, work toward explicit goals, and verify results.

## Analysis

- The upstream value is behavioral policy, not runtime implementation.
- Vendoring the Claude/Cursor-oriented plugin would couple Sula to one assistant ecosystem and duplicate policy that should live in Sula manifests.
- The highest-value absorption is to make this behavior machine-readable for all future Sula runners and visible in closeout evidence.
- Policy must remain subordinate to Sula's highest rule, workflow gates, tests, and project-owned business truth.

## Chosen Plan

- Add optional `[agent_behavior]` manifest policy with strict defaults.
- Surface resolved agent behavior through project/status JSON payloads.
- Add agent behavior and a quality checklist to orchestration run records.
- Require verification and acceptance/success-criteria evidence during accepted closeout when policy requires it.
- Document the boundary so Sula absorbs reusable guidance without importing editor-specific plugin mechanics.

## Execution

- Added manifest constants, defaults, schema validation, example manifest fields, and root manifest fields for `[agent_behavior]`.
- Added `agent_behavior` payloads to project status and orchestration config surfaces.
- Added run-record quality checklists for assumptions, simplicity, diff scope, success criteria, verification, and drive-by refactor control.
- Strengthened `orchestration close --accept` so accepted runs require policy-aligned evidence.
- Added reference documentation and unit coverage for status/run behavior.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m json.tool schema/project.schema.json`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_intake_and_closeout_require_evidence -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_agent_behavior_policy_surfaces_in_status_and_orchestration_runs -v`
- `python3 -m unittest discover -s tests -v` passed 101 tests.
- `python3 scripts/sula.py doctor --project-root . --strict --json` passed.
- `python3 scripts/sula.py check --project-root . --json` passed.
- `python3 scripts/sula.py orchestration doctor --project-root . --json` passed with expected disabled-orchestration warnings.

## Rollback

- Remove `[agent_behavior]` from manifest defaults, schema, root/example manifests, JSON payloads, and docs.
- Remove run-record `agent_behavior` and `quality_checklist` fields from new records.
- Remove the closeout checks for verification and acceptance/success-criteria evidence.
- Preserve historical run records as audit history unless explicit cleanup is approved.

## Data Side-effects

- New and rewritten manifests can include an optional `[agent_behavior]` section.
- New orchestration run records include `agent_behavior` and `quality_checklist` fields under `.sula/state/orchestration/`.
- Accepted closeout may now be blocked until evidence mentions verification and acceptance/success criteria.

## Follow-up

- Connect this policy to future real runner adapters before enabling any non-dry-run orchestration execution.
- Consider adding provider-specific prompt adapters that read `agent_behavior` without changing the manifest contract.

## Architecture Boundary Check

- highest rule impact: preserved. Sula absorbs portable execution behavior as operating-system policy while keeping project-owned task intent, acceptance criteria, and business truth outside managed templates.
