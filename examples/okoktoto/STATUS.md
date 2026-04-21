# STATUS

- last updated: 2026-04-22

## Summary

- Sula now treats this example as the canary for single-project memory support.
- The goal is to prove that managed guidance, scaffold records, doctor checks, and generated memory digests work together.

## Health

- status: green
- reason: core memory scaffolding, records, and digest generation are in place for this example.

## Current Focus

- verify that the canary passes `sula doctor --strict`
- keep the example aligned with the latest memory-aware templates

## Blockers

- none

## Recent Decisions

- 2026-04-11: adopted the memory canary release note [Prepare Sula memory canary rollout](docs/releases/2026-04-11-prepare-sula-memory-canary-rollout.md)
- 2026-04-11: added [Adopt Sula memory model](docs/change-records/2026-04-11-adopt-sula-memory-model.md)
- 2026-04-11: documented the canary incident context [Capture canary documentation gaps](docs/incidents/2026-04-11-capture-canary-documentation-gaps.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-18
- trigger: review again after the next managed-template or doctor-contract change

## Handoff

- ready: yes
- start here: `docs/change-records/2026-04-11-adopt-sula-memory-model.md`; `STATUS.md`
- latest record: `docs/change-records/2026-04-11-adopt-sula-memory-model.md`
- next action: review `docs/change-records/2026-04-11-adopt-sula-memory-model.md`; run `python3 scripts/sula.py sync --project-root . --dry-run`
- next owner: Sula Core maintainers
- next due: 2026-04-22
- done when: result `sync dry run reviewed`; artifact `STATUS.md`
- blockers: none
- source of truth: `STATUS.md`; `docs/change-records/2026-04-11-adopt-sula-memory-model.md`
- source freshness: n/a
- verification command: `python3 scripts/sula.py check --project-root .`
- verification result: n/a
- verification date: 2026-04-22
- git branch: main
- git commit: fae5174
- git working tree: dirty
