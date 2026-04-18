# Current State Snapshot

- generated on: 2026-04-18
- project: OKOKTOTO v5
- profile: `react-frontend-erpnext`
- source priority: STATUS.md and project records override this generated snapshot

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
