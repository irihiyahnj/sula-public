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

- 2026-04-16 - [Publish the fresh public Sula source](docs/change-records/2026-04-16-publish-the-fresh-public-sula-source.md) - Created the fresh public repository, switched the launch contract to a real canonical public source, and prepared the export-first public lineage.
- 2026-04-16 - [Choose fresh public repository as the default release path](docs/change-records/2026-04-16-choose-fresh-public-repository-as-the-default-release-path.md) - Promoted `fresh-public-repo` from fallback to default strategy, made the launch descriptor honest about the unpublished public source, and tightened release guidance around export-first publication.
- 2026-04-16 - [Complete workflow close, canary verification, and release readiness](docs/change-records/2026-04-16-complete-workflow-close-canary-and-release-readiness.md) - Completed the first workflow execution loop, added repeatable in-repo canary verification, and turned public-release governance into an explicit readiness audit with a non-destructive export path.
- 2026-04-16 - [Add workflow policy and source-first workflow scaffolds](docs/change-records/2026-04-16-add-workflow-policy-and-source-first-workflow-scaffolds.md) - Added manifest-level workflow rigor policy, a first-class `workflow` command family, and durable `spec` / `plan` / `review` source-document scaffolds under `docs/workflows/`.
- 2026-04-16 - [Document Superpowers capability absorption plan](docs/change-records/2026-04-16-document-superpowers-capability-absorption-plan.md) - Recorded which `obra/superpowers` workflow capabilities should be absorbed into Sula Core, which should remain optional, and how a manifest-driven rollout should work.
- 2026-04-15 - [Add daily Sula check workflow for state-sync verification](docs/change-records/2026-04-15-add-daily-sula-check-workflow-for-state-sync-verification.md) - Added a first-class `check` command, generated-state drift detection, and template rules that make `SULA CHECK OK` the daily gate for status-sync work.
- 2026-04-12 - [Add project-local Google OAuth storage and provider target-path routing](docs/change-records/2026-04-12-add-project-local-google-oauth-and-provider-target-path-routing.md) - Standardized project-local Google OAuth storage, default provider-native target paths, and provider parent-folder routing under the provider root.
- 2026-04-12 - [Add provider-native read-only refresh and artifact refresh command](docs/change-records/2026-04-12-add-provider-native-read-only-refresh-and-artifact-refresh-command.md) - Added provider adapters, `artifact refresh`, automatic provider refresh on freshness intent, and cached provider snapshots for Google-native collaborative artifacts.
- 2026-04-12 - [Add truth-source and freshness checks for collaborative provider-backed artifacts](docs/change-records/2026-04-12-add-truth-source-and-freshness-checks-for-collaborative-provider-artifacts.md) - Added artifact-family truth-source metadata, natural-language freshness intent handling, stale-local-copy detection, and provider-metadata gap reporting for collaborative provider-backed files.
- 2026-04-12 - [Add formal document design bundles](docs/change-records/2026-04-12-add-formal-document-design-bundles.md) - Added a first-class document design manifest section, a managed formal-document rulebook, and genre-aware source bundles for schedule, proposal, report, process, and training artifacts.
- 2026-04-12 - [Add feedback bundles and Sula Core review workflow](docs/change-records/2026-04-12-add-feedback-bundles-and-core-review-workflow.md) - Added a governed upstream-feedback lifecycle so adopted projects can package reusable local Sula fixes, Sula Core can review them centrally, and approved changes can still roll out later through versioned sync.
- 2026-04-12 - [Add artifact materialization for docs and sheets](docs/change-records/2026-04-12-add-artifact-materialization-for-docs-and-sheets.md) - Added a local bridge from project-owned source files to `.html`, `.docx`, and `.xlsx` artifact outputs so teams can import deliverables into Google Docs or Google Sheets without waiting for direct provider adapters.
- 2026-04-12 - [Add project language policy for generated docs and records](docs/change-records/2026-04-12-add-project-language-policy-for-generated-docs.md) - Added project-level language settings so generated docs, records, and summaries can use Chinese or English without changing stable file paths.
- 2026-04-12 - [Add provider-backed artifact registration identity](docs/change-records/2026-04-12-add-provider-backed-artifact-registration-identity.md) - Extended artifact registration and indexing so Google Drive and future provider-backed deliverables can carry stable identity fields without depending on one machine's local path.
- 2026-04-12 - [Document provider-backed artifact identity for cross-device project workspaces](docs/change-records/2026-04-12-document-provider-backed-artifact-identity.md) - Added the cross-device identity contract for Drive-synced and future provider-backed artifacts, clarifying that project ownership is stable even when local access paths differ.
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
