# Complete workflow close, canary verification, and release readiness

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

Sula had already gained manifest-level workflow policy plus `workflow assess` and `workflow scaffold`, but the remaining roadmap gaps were still real: complex work could not close through a first-class workflow contract, in-repo canaries were not centrally verifiable, and public-release governance still depended on manual judgment instead of a repeatable audit.

## Analysis

- the next step should complete the existing workflow model instead of introducing a new subsystem
- canary validation should reflect the same `sync` / `doctor --strict` / `check` bar used by real managed projects
- public-release readiness should distinguish code-quality gaps from repository-history exposure so the remaining blocker is explicit

## Chosen Plan

- add `workflow branch` and `workflow close` to complete the workflow execution loop
- add registry-backed `canary list` and `canary verify` commands plus broader in-repo canary coverage
- add `release readiness` and `release export-public` so public governance has an auditable, non-destructive path forward

## Execution

- added workflow execution commands that model branch/worktree isolation decisions and explicit closeout readiness
- added canary registry parsing, local-root resolution, coverage validation, and repeatable canary verification reports
- promoted `examples/field-ops-generic` and `examples/client-service-gdrive` into real in-repo canaries and refreshed `examples/okoktoto`
- added release-governance auditing plus a clean-tree export path for fresh public repository creation
- scrubbed tracked adapter and documentation surfaces so provider-backed examples no longer leak machine-specific local paths

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_canary_verify_runs_local_registry_canaries -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py canary verify --project-root . --all --json`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py check --project-root .`
- `python3 scripts/sula.py release readiness --project-root . --json`

## Rollback

- remove the new workflow close, canary, and release command paths from `scripts/sula.py`
- remove the new in-repo canary registry entries and example projects
- revert the governance and generated-state updates that assume the new audit surface

## Data Side-effects

- the adoption registry now carries resolvable `local_root` metadata for in-repo canaries
- Sula root status can now be audited against registry canaries instead of relying on ad hoc manual checks
- public-release readiness reports can separate clean-content issues from immutable git-history concerns

## Follow-up

- run the first external non-example canaries through the new verification contract
- choose the public release path: sanitized history rewrite or fresh public repository seeded from `release export-public`
- decide whether release readiness should eventually require external canary evidence in addition to local in-repo coverage

## Architecture Boundary Check

- highest rule impact: preserved; workflow, canary, and public-release rigor all remain project-visible contracts and auditable repository artifacts rather than hidden agent-only behavior
