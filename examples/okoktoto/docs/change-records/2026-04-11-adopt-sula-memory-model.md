# Adopt Sula memory model

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): 901c67f
- status: completed

## Background

Promoted the example project into a canary for Sula single-project memory.

## Analysis

- The example project previously proved manifest extraction, but it did not prove memory-aware scaffolds.
- A canary inside the Sula repo lets maintainers validate `init`, `record`, `memory digest`, and `doctor --strict` without depending on an external repository.
- The memory model needs one concrete consumer so future sync changes can be reviewed against actual generated files.

## Chosen Plan

- render the latest managed and scaffold files into the example
- create one change record, one release record, and one incident record
- add minimal placeholder source and workflow files so strict doctor checks have valid targets
- generate a memory digest from project sources

## Execution

- ran `sula init` for `examples/okoktoto`
- generated memory-aware scaffold directories under `docs/change-records/`, `docs/releases/`, and `docs/incidents/`
- recorded the canary rollout history and updated `STATUS.md`
- prepared the example for strict memory validation

## Verification

- `python3 scripts/sula.py init --project-root examples/okoktoto`
- `python3 scripts/sula.py record new --project-root examples/okoktoto --title "Adopt Sula memory model" --summary "Promoted the example project into a canary for Sula single-project memory." --date 2026-04-11`
- `python3 scripts/sula.py memory digest --project-root examples/okoktoto`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`

## Rollback

- remove the generated example files if the canary stops representing a valid consumer
- keep the memory model in Sula Core but stop treating this example as the strict doctor target

## Data Side-effects

- no production data side-effects
- repository-only example files added for memory validation

## Follow-up

- keep future Sula memory changes compatible with this example
- update the canary digest after material example memory changes

## Architecture Boundary Check

- highest rule impact: none for the business system; this change only upgrades the reusable operating system around the example
