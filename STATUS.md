# STATUS

- last updated: 2026-04-11

## Summary

- Sula now manages itself as a first-class `sula-core` consumer while still acting as the source repository for reusable operating-system assets.
- The repository has memory-aware governance, an in-repo canary, a root self-adoption path, and an approval-based adoption agent for bringing new repositories under Sula.
- Public-release governance is now in place, and the remaining blocker is historical lineage cleanup rather than working-tree quality.

## Health

- status: yellow
- reason: working-tree quality is at public-project standard, but the current git history still needs a clean public-release strategy before this exact repository should be opened.

## Current Focus

- choose the public release path: sanitized history rewrite or fresh public repository
- validate the new `adopt` flow against the first external repository
- keep `sula-core` and `react-frontend-erpnext` profiles aligned with real usage
- maintain clear approval reporting so managed/scaffold boundaries remain obvious during onboarding

## Blockers

- none

## Recent Decisions

- 2026-04-11: added [Prepare Sula for public release](docs/change-records/2026-04-11-prepare-sula-for-public-release.md)
- 2026-04-11: promoted `examples/okoktoto` into the in-repo memory canary
- 2026-04-11: introduced durable project memory, strict memory doctor checks, and generated memory digests
- 2026-04-11: added [Add adoption-agent flow for one-sentence onboarding](docs/change-records/2026-04-11-add-adoption-agent-flow-for-one-sentence-onboarding.md)
- 2026-04-11: added [Self-adopt Sula root under sula-core profile](docs/change-records/2026-04-11-self-adopt-sula-root-under-sula-core-profile.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-18
- trigger: review again before opening the repository publicly or changing managed/scaffold onboarding contracts
