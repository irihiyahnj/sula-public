# Current State Snapshot

- generated on: 2026-04-22
- project: Field Ops Generic Canary
- profile: `generic-project`
- source priority: STATUS.md and project records override this generated snapshot

## Summary

- This in-repo generic-project canary exists to validate detached-safe adoption, sync, doctor, and check behavior for repositories that are not tied to the React profile.

## Health

- status: green
- reason: the canary is intentionally small and currently passes the baseline Sula verification path.

## Current Focus

- keep the generic-project canary aligned with current managed templates
- use it as a local rollout target before broader generic-project sync changes

## Blockers

- none

## Recent Decisions

- 2026-04-16: promoted this example into a generic-project rollout canary for local Sula verification

- 2026-04-16: added [Promote field ops example into generic-project canary](docs/change-records/2026-04-16-promote-field-ops-example-into-generic-project-canary.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-23
- trigger: review again before changing generic-project managed templates or detached-mode defaults

## Handoff

- ready: yes
- start here: `docs/change-records/2026-04-16-promote-field-ops-example-into-generic-project-canary.md`; `STATUS.md`
- latest record: `docs/change-records/2026-04-16-promote-field-ops-example-into-generic-project-canary.md`
- next action: review `docs/change-records/2026-04-16-promote-field-ops-example-into-generic-project-canary.md`; run `python3 scripts/sula.py check --project-root .`
- next owner: Sula Core maintainers
- next due: 2026-04-22
- done when: result `SULA CHECK OK`; artifact `STATUS.md`
- blockers: none
- source of truth: `STATUS.md`; `docs/change-records/2026-04-16-promote-field-ops-example-into-generic-project-canary.md`
- source freshness: n/a
- verification command: `python3 scripts/sula.py check --project-root .`
- verification result: n/a
- verification date: 2026-04-22
- git branch: main
- git commit: fae5174
- git working tree: dirty
