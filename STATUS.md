# STATUS

- last updated: 2026-04-11

## Summary

- Sula now manages itself as a first-class `sula-core` consumer while still acting as the source repository for reusable operating-system assets.
- The repository has memory-aware governance, an in-repo canary, and a root self-adoption path that can be checked with `doctor --strict`.

## Health

- status: green
- reason: root self-adoption, canary validation, and repository tests are all in place; the remaining work is release and rollout.

## Current Focus

- tag and release the current governed Sula version
- onboard the first external canary project beyond `examples/okoktoto`
- keep `sula-core` and `react-frontend-erpnext` profiles aligned with real usage

## Blockers

- none

## Recent Decisions

- 2026-04-11: promoted `examples/okoktoto` into the in-repo memory canary
- 2026-04-11: introduced durable project memory, strict memory doctor checks, and generated memory digests
- 2026-04-11: added [Self-adopt Sula root under sula-core profile](docs/change-records/2026-04-11-self-adopt-sula-root-under-sula-core-profile.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-18
- trigger: review again before tagging the next Sula release or changing managed/scaffold memory contracts
