# STATUS

- last updated: 2026-05-02
## Summary
### 2026-05-05

- Aligned the field-ops generic canary with Sula 0.17.0 release verification.
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
- verification date: 2026-05-05
- git branch: main
- git commit: any
- git working tree: dirty
