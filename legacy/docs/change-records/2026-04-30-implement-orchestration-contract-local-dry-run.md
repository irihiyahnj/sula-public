# Add Orchestration Contract Local Dry Run

## Metadata

- date: 2026-04-30
- executor: Codex
- branch: unknown
- related commit(s): none
- status: completed

## Background

Sula had a durable Symphony-style orchestration absorption plan, but no executable Core surface yet. The plan requires starting with dependency-light contracts, local task ingestion, dry-run execution, records, and safety gates before any real remote runner or tracker integration.

## Analysis

- Orchestration must be optional and disabled by default so existing adopted projects are not forced into unattended execution.
- The first implementation slice should prove the control-plane contract without mutating project files or requiring network services.
- Task intent remains project-owned truth; Sula should normalize it and record operational state under `.sula/state/orchestration/`.

## Chosen Plan

- Add optional `[orchestration]` manifest fields and schema coverage.
- Add a local JSON task source and dry-run runner path.
- Add CLI commands for status, task listing, run recording, cancellation, stop-all, and orchestration doctor checks.
- Surface orchestration state in `status --json`.

## Execution

- Updated `scripts/sula.py` with orchestration config accessors, validation, local task normalization, risk/approval/budget gates, and state records.
- Added `orchestration status`, `tasks`, `run`, `cancel`, `stop-all`, and `doctor` commands.
- Updated `schema/project.schema.json`, `schema/project.example.toml`, `.sula/project.toml`, and reference docs.
- Added tests for disabled default behavior and enabled dry-run record creation.
- Aligned the public site descriptor test with the already-published `v0.14.0` source reference.

## Verification

- `python3 -m py_compile scripts/sula.py`
- `python3 scripts/sula.py orchestration status --project-root . --json`
- Full repository verification should run after docs and generated state settle: `python3 -m unittest discover -s tests -v`, `python3 scripts/sula.py doctor --project-root . --strict --json`, and `python3 scripts/sula.py check --project-root . --json`.

## Rollback

- Remove the `[orchestration]` section from manifests.
- Revert orchestration CLI additions and schema/docs updates.
- Keep `.sula/state/orchestration/` records as audit history unless a maintainer explicitly approves cleanup.

## Data Side-effects

- Running orchestration status/tasks/run writes operational records under `.sula/state/orchestration/`.
- The dry-run runner does not mutate project business files.

## Follow-up

- Add a real runner adapter only after closeout evidence, safety gates, and rollback semantics are reviewed.
- Add one external task-source adapter after the local adapter contract is stable.
- Add portfolio summaries after per-project state is stable.

## Architecture Boundary Check

- highest rule impact: preserved. The implementation keeps orchestration as optional OS policy and stores run state in `.sula/`, while task intent and acceptance criteria stay project-owned.
