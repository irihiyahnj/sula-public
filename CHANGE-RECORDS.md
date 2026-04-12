# Sula Change Records

This file is the index for non-trivial Sula Core changes.

## Purpose

Track why Sula changed, how sync impact was evaluated, what was verified, and how rollback should work.

## Rules

- keep this file short and index-oriented
- put detailed records in `docs/change-records/`
- mention sync impact explicitly in non-trivial records
- use release records when the rollout itself needs durable history

## Index

- 2026-04-12 - [Add site launch contract and canonical bootstrap shim](docs/change-records/2026-04-12-add-site-launch-contract-and-canonical-bootstrap-shim.md) - Added a URL-first launch contract, upgraded `site/sula.json`, and introduced `site/launch/bootstrap.py` so agents can start Sula from the site without guessing local commands.
- 2026-04-12 - [Add guided onboarding and zero-memory setup flow](docs/change-records/2026-04-12-add-guided-onboarding-and-zero-memory-setup-flow.md) - Added the `onboard` interview flow, onboarding summaries, and a single-envelope JSON apply path so users do not need to remember Sula internals before adopting a project.
- 2026-04-12 - [Add machine JSON interfaces, artifact routing, portfolio registry, and Google Drive local-sync contracts](docs/change-records/2026-04-12-add-machine-json-interfaces-artifact-routing-portfolio-registry-and-google-drive-local-sync-contracts.md) - Added machine-readable CLI envelopes, first-class artifacts, portfolio registry commands, and storage/workflow/portfolio manifest contracts for Drive-synced client projects.
- 2026-04-12 - [Add SQLite kernel cache, richer object extraction, and timeline query filters](docs/change-records/2026-04-12-add-sqlite-kernel-cache-richer-object-extraction-and-timeline-query-filters.md) - Added a rebuildable SQLite retrieval cache, richer project object kinds, and stronger local query filters and timeline behavior.
- 2026-04-12 - [Implement generic-project kernel and removal flow](docs/change-records/2026-04-12-implement-generic-project-kernel-and-removal-flow.md) - Added the safe baseline profile, `.sula/` kernel artifacts, non-Git adoption support, and an explicit remove command.
- 2026-04-12 - [Define Sula vNext project kernel](docs/change-records/2026-04-12-define-sula-vnext-project-kernel.md) - Recorded the target architecture for a generic project kernel with adapter bundles, scientific indexing, and first-class removal semantics.
- 2026-04-11 - [Refine the public bootstrap contract for existing Sula consumers](docs/change-records/2026-04-11-refine-the-public-bootstrap-contract-for-existing-sula-consumers.md) - Clarified that already-adopted repositories should be treated as existing consumers, not fresh adoption targets, and that missing local tooling must resolve to the canonical Sula source.
- 2026-04-11 - [Deploy the Sula bootstrap site to Fly and prepare the custom domain](docs/change-records/2026-04-11-deploy-the-sula-bootstrap-site-to-fly-and-prepare-the-custom-domain.md) - Published the static bootstrap site to `sula.fly.dev`, added Fly deployment configuration to the repository, and queued `sula.1stp.monster` on Fly with one remaining DNS CNAME step.
- 2026-04-11 - [Add bootstrap site assets for the public Sula protocol](docs/change-records/2026-04-11-add-bootstrap-site-assets-for-the-public-sula-protocol.md) - Added a deployable static site with canonical Chinese and English bootstrap lines, the public behavioral contract page, and a machine-readable `sula.json` descriptor.
- 2026-04-11 - [Prepare Sula for public release](docs/change-records/2026-04-11-prepare-sula-for-public-release.md) - Added public-project governance files, documented launch-readiness checks, and recorded the current git-history blocker for publishing this repository safely.
- 2026-04-11 - [Add adoption-agent flow for one-sentence onboarding](docs/change-records/2026-04-11-add-adoption-agent-flow-for-one-sentence-onboarding.md) - Added an inspect-report-approve onboarding flow so new repositories can adopt Sula through a single approval-based entrypoint.
- 2026-04-11 - [Self-adopt Sula root under sula-core profile](docs/change-records/2026-04-11-self-adopt-sula-root-under-sula-core-profile.md) - Promoted the Sula repository itself into a managed consumer so root governance, memory, and rollout checks use the same operating-system model.

- 2026-04-12 - [Add kernel object, query, and bundle contracts](docs/change-records/2026-04-12-add-kernel-object-query-and-bundle-contracts.md) - Added object catalogs, relation indexes, local query retrieval, bundle metadata, and rebuildable query cache to the Sula kernel.
## Detailed Records

- directory: `docs/change-records/`
- template: [docs/change-records/_template.md](docs/change-records/_template.md)
