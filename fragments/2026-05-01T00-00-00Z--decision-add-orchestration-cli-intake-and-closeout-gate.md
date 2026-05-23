---
id: 2026-05-01T00-00-00Z--decision-add-orchestration-cli-intake-and-closeout-gate
time: 2026-05-01T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-01-add-orchestration-cli-intake-and-closeout-gate.md
---
# Add Orchestration CLI Intake And Closeout Gate

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: unknown
- related commit(s): none
- status: completed

## Background

The first orchestration slice gave Sula a disabled-by-default manifest contract, local task normalization, dry-run records, and safety gates. The next gap was user perception: a user should be able to express intent through the CLI and have Sula capture it as auditable task intent, while still preventing dry-run scheduling from being treated as accepted work.

## Analysis

- CLI/user conversation should be a task-source entry path, but not a reason to bypass task normalization, risk classification, or evidence gates.
- Dry-run runner output proves scheduling and policy behavior only; it must not satisfy accepted closeout by itself.
- Closeout needs an explicit evidence surface before real runner adapters are introduced.

## Chosen Plan

- Add `orchestration intake` to capture CLI/user intent into the local task file with `source_kind = "cli-intent"`.
- Add `orchestration close` to evaluate closeout evidence and optionally mark a run accepted.
- Require validation evidence beyond dry-run scheduling before accepted closeout.
- Keep all writes inside project-owned task files or `.sula/state/orchestration/` operational state.

## Execution

- Added `orchestration intake` arguments for title, description, acceptance criteria, validation requirements, labels, risk hints, priority, and identifier.
- Added local task-file read/write helpers that preserve a JSON object with a `tasks` array.
- Added `orchestration close` with evidence, touched-file, link, lesson, and `--accept` fields.
- Updated tests to cover CLI intent intake and evidence-required accepted closeout.
- Updated README and orchestration reference docs.

## Verification

- `python3 -m py_compile scripts/sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_intake_and_closeout_require_evidence -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_defaults_to_disabled_and_supports_dry_run_records -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py doctor --project-root . --strict --json`
- `python3 scripts/sula.py check --project-root . --json`
- `python3 scripts/sula.py orchestration doctor --project-root . --json`

## Rollback

- Remove the `orchestration intake` and `orchestration close` command handlers.
- Revert the tests and docs added for CLI intent intake and closeout evidence.
- Preserve any existing `.sula/state/orchestration/` records as audit history unless explicitly approved for cleanup.

## Data Side-effects

- `orchestration intake` writes project-owned task intent to `orchestration.tasks_path`.
- `orchestration close` rewrites `.sula/state/orchestration/runs.jsonl` and updates `.sula/state/orchestration/latest.json`.

## Follow-up

- Add memory/feedback promotion proposal records for reusable lessons captured during closeout.
- Add real runner adapters only after accepted closeout semantics remain stable under local/dry-run use.

## Architecture Boundary Check

- highest rule impact: preserved. User intent becomes project-owned task truth, while run and closeout state remains Sula-managed operational state under `.sula/`.
