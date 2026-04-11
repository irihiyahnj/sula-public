# STATUS

- last updated: 2026-04-11

## Summary

- Sula now manages itself as a first-class `sula-core` consumer while still acting as the source repository for reusable operating-system assets.
- The repository has memory-aware governance, an in-repo canary, a root self-adoption path, and an approval-based adoption agent for bringing new repositories under Sula.

## Health

- status: green
- reason: root self-adoption, canary validation, adoption automation, and repository tests are all in place; the remaining work is external rollout.

## Current Focus

- validate the new `adopt` flow against the first external repository
- keep `sula-core` and `react-frontend-erpnext` profiles aligned with real usage
- maintain clear approval reporting so managed/scaffold boundaries remain obvious during onboarding

## Blockers

- none

## Recent Decisions

- 2026-04-11: promoted `examples/okoktoto` into the in-repo memory canary
- 2026-04-11: introduced durable project memory, strict memory doctor checks, and generated memory digests
- 2026-04-11: added [Add adoption-agent flow for one-sentence onboarding](docs/change-records/2026-04-11-add-adoption-agent-flow-for-one-sentence-onboarding.md)
- 2026-04-11: added [Self-adopt Sula root under sula-core profile](docs/change-records/2026-04-11-self-adopt-sula-root-under-sula-core-profile.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-18
- trigger: review again before onboarding the first external repository or changing managed/scaffold onboarding contracts
