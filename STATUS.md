# STATUS

- last updated: 2026-04-11

## Summary

- Sula now manages itself as a first-class `sula-core` consumer while still acting as the source repository for reusable operating-system assets.
- The repository has memory-aware governance, an in-repo canary, a root self-adoption path, and an approval-based adoption agent for bringing new repositories under Sula.
- Public-release governance is now in place, and the remaining blocker is historical lineage cleanup rather than working-tree quality.
- The future `sula.1stp.monster` landing page is now represented by real static site assets with canonical long-form bootstrap prompts and protocol pages.
- The bootstrap site is now live on both `https://sula.fly.dev/` and `https://sula.1stp.monster/`, with the public bootstrap contract explicitly handling existing Sula consumers and canonical tool-source resolution.

## Health

- status: yellow
- reason: the bootstrap site and custom domain are live, but the repository history still needs a clean public-release strategy before this exact repository should be opened.

## Current Focus

- choose the public release path: sanitized history rewrite or fresh public repository
- validate the new `adopt` flow against the first external repository
- keep `sula-core` and `react-frontend-erpnext` profiles aligned with real usage
- maintain clear approval reporting so managed/scaffold boundaries remain obvious during onboarding
- keep the public bootstrap contract aligned with real consumer behavior and protocol failures seen in live use

## Blockers

- none

## Recent Decisions

- 2026-04-11: added [Refine the public bootstrap contract for existing Sula consumers](docs/change-records/2026-04-11-refine-the-public-bootstrap-contract-for-existing-sula-consumers.md)
- 2026-04-11: added [Deploy the Sula bootstrap site to Fly and prepare the custom domain](docs/change-records/2026-04-11-deploy-the-sula-bootstrap-site-to-fly-and-prepare-the-custom-domain.md)
- 2026-04-11: added [Add bootstrap site assets for the public Sula protocol](docs/change-records/2026-04-11-add-bootstrap-site-assets-for-the-public-sula-protocol.md)
- 2026-04-11: added [Prepare Sula for public release](docs/change-records/2026-04-11-prepare-sula-for-public-release.md)
- 2026-04-11: promoted `examples/okoktoto` into the in-repo memory canary
- 2026-04-11: introduced durable project memory, strict memory doctor checks, and generated memory digests
- 2026-04-11: added [Add adoption-agent flow for one-sentence onboarding](docs/change-records/2026-04-11-add-adoption-agent-flow-for-one-sentence-onboarding.md)
- 2026-04-11: added [Self-adopt Sula root under sula-core profile](docs/change-records/2026-04-11-self-adopt-sula-root-under-sula-core-profile.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-18
- trigger: review again before changing the public bootstrap contract or changing managed/scaffold onboarding contracts
