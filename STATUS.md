# STATUS

- last updated: 2026-04-16
## Summary

- Sula now manages itself as a first-class `sula-core` consumer while still acting as the source repository for reusable operating-system assets.
- The repository has memory-aware governance, an in-repo canary, a root self-adoption path, and an approval-based adoption agent for bringing new repositories under Sula.
- Public-release governance is now in place, and the remaining blocker is historical lineage cleanup rather than working-tree quality.
- The future `sula.1stp.monster` landing page is now represented by real static site assets with canonical long-form bootstrap prompts and protocol pages.
- The bootstrap site is now live on both `https://sula.fly.dev/` and `https://sula.1stp.monster/`, with the public bootstrap contract explicitly handling existing Sula consumers and canonical tool-source resolution.
- Sula now has a recorded vNext architecture target for a `generic-project` kernel, adapter bundles, scientific retrieval, and first-class removal semantics.
- The first milestone of that direction is now implemented: unknown and non-Git projects can adopt through `generic-project`, `.sula/` holds kernel artifacts, and removal has a report-first command.
- The second milestone is now implemented as well: local retrieval can rebuild from SQLite, kernel objects cover task/decision/risk/person/agreement/milestone shapes, and query supports stronger filters plus timeline output.
- The next operating milestone is now implemented too: machine-readable CLI responses, workflow/storage/portfolio manifest sections, artifact routing, and portfolio registration are available for non-code client projects.
- Drive-synced projects can now describe `google-drive` as an adapter instead of pretending that storage provider is a project type, which keeps the kernel portable for future providers.
- Collaborative provider-backed artifact families can now declare their truth source, refresh state, and stale-local-copy risk, so Sula can prefer shared Google-native facts when users ask for the latest version in natural language.
- Sula now has a real read-only provider refresh path for Google Docs and Google Sheets, plus `artifact refresh` and cached provider snapshots, so freshness intent can trigger an actual provider metadata refresh instead of only local re-ranking.
- Sula now has a first-class daily `check` workflow, so state-sync work can fail fast when `.sula/state/current.md` or `.sula/memory-digest.md` drift away from the current status and change records.
- Formal document design is now a first-class Sula capability: adopted projects can carry reusable source-first structure bundles for schedule, proposal, report, process, and training documents instead of relying on one-off prompt instructions.
- Sula now has a documented proposal for absorbing long-term value from workflow systems like `obra/superpowers` through manifest-driven capability contracts instead of platform-specific skill lock-in.
- Sula now implements the first workflow-capability slice from that proposal: manifest-level workflow rigor policy plus source-first `spec`, `plan`, and `review` scaffolds under `docs/workflows/`.
- Sula now completes that workflow slice with first-class `workflow branch` and `workflow close` commands, so complex work can move from policy assessment to explicit closeout readiness.
- The next UX milestone is now implemented too: `onboard` provides a zero-memory interview flow that asks setup questions, explains what Sula will manage, and then applies adoption through the same kernel contract.
- The next launch milestone is now implemented too: the public site exposes `/launch/`, a machine-readable launcher descriptor, and a downloadable `bootstrap.py` shim so startup no longer depends on guessing local commands.
- The feedback-bundle lifecycle is now released in the Git-backed Sula 0.11.0 source state: adopted projects can capture reusable local Sula fixes as feedback bundles, and Sula Core can ingest, review, and release them through a central queue.
- Sula now has registry-backed in-repo canary verification across `sula-core`, `software-delivery`, `generic-project`, and `client-service`-style examples, plus public-release readiness and export commands that isolate remaining publication risk to git history rather than content drift.
- Sula now has a chosen default public-release path: keep this repository as the private pre-public lineage, publish a fresh public repository from `release export-public`, and only then point the site descriptor at the public source.
- The fresh public source now exists at `irihiyahnj/sula-public`, so `https://sula.1stp.monster/launch/` can resolve a real canonical clone source instead of depending on a local checkout.

## Health

- status: yellow
- reason: the canonical public source now exists, but the hosted site still needs redeployment and the optional DigitalOcean migration is not complete yet.

## Current Focus

- push the fresh export-first lineage to `irihiyahnj/sula-public` and redeploy the hosted site descriptor
- validate the new `adopt` flow against the first external repository
- run the first external canaries through the new `canary verify` contract
- keep `sula-core` and `react-frontend-erpnext` profiles aligned with real usage
- validate the new `generic-project` and `remove` flows against external canaries
- validate portfolio registration, artifact routing, and `google-drive` local-sync behavior against the first real client-service workspace
- validate the new formal-document bundles against the first real planning-heavy client workspace and confirm where Google Docs import needs richer tabular bridge defaults
- validate the released feedback-bundle lifecycle through the first external adopted project and the first real Sula Core feedback item that flows through the queue end to end
- validate the now-complete workflow policy, scaffold, branch, and close loop against the first external software-delivery canary
- turn the recorded vNext architecture into stronger adapter composition and better result quality over the new SQLite-backed retrieval path
- maintain clear approval reporting so managed/scaffold boundaries remain obvious during onboarding
- keep the public bootstrap contract aligned with real consumer behavior and protocol failures seen in live use
- switch `site/sula.json` and `site/launch/bootstrap.py` to the published public source after that repository exists
- decide whether to keep the hosted site on Fly or migrate it onto the existing DigitalOcean infrastructure once server write access is available

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
- 2026-04-12: added [Define Sula vNext project kernel](docs/change-records/2026-04-12-define-sula-vnext-project-kernel.md)
- 2026-04-12: added [Implement generic-project kernel and removal flow](docs/change-records/2026-04-12-implement-generic-project-kernel-and-removal-flow.md)
- 2026-04-12: added [Add kernel object, query, and bundle contracts](docs/change-records/2026-04-12-add-kernel-object-query-and-bundle-contracts.md)
- 2026-04-12: added [Add SQLite kernel cache, richer object extraction, and timeline query filters](docs/change-records/2026-04-12-add-sqlite-kernel-cache-richer-object-extraction-and-timeline-query-filters.md)
- 2026-04-12: added [Add machine JSON interfaces, artifact routing, portfolio registry, and Google Drive local-sync contracts](docs/change-records/2026-04-12-add-machine-json-interfaces-artifact-routing-portfolio-registry-and-google-drive-local-sync-contracts.md)
- 2026-04-12: added [Add formal document design bundles](docs/change-records/2026-04-12-add-formal-document-design-bundles.md)
- 2026-04-12: added [Add truth-source and freshness checks for collaborative provider-backed artifacts](docs/change-records/2026-04-12-add-truth-source-and-freshness-checks-for-collaborative-provider-artifacts.md)
- 2026-04-12: added [Add provider-native read-only refresh and artifact refresh command](docs/change-records/2026-04-12-add-provider-native-read-only-refresh-and-artifact-refresh-command.md)
- 2026-04-15: added [Add daily Sula check workflow for state-sync verification](docs/change-records/2026-04-15-add-daily-sula-check-workflow-for-state-sync-verification.md)
- 2026-04-16: added [Document Superpowers capability absorption plan](docs/change-records/2026-04-16-document-superpowers-capability-absorption-plan.md)
- 2026-04-16: added [Add workflow policy and source-first workflow scaffolds](docs/change-records/2026-04-16-add-workflow-policy-and-source-first-workflow-scaffolds.md)
- 2026-04-16: added [Complete workflow close, canary verification, and release readiness](docs/change-records/2026-04-16-complete-workflow-close-canary-and-release-readiness.md)
- 2026-04-16: added [Choose fresh public repository as the default release path](docs/change-records/2026-04-16-choose-fresh-public-repository-as-the-default-release-path.md)
- 2026-04-16: added [Publish the fresh public Sula source](docs/change-records/2026-04-16-publish-the-fresh-public-sula-source.md)
- 2026-04-12: added [Add guided onboarding and zero-memory setup flow](docs/change-records/2026-04-12-add-guided-onboarding-and-zero-memory-setup-flow.md)
- 2026-04-12: added [Add site launch contract and canonical bootstrap shim](docs/change-records/2026-04-12-add-site-launch-contract-and-canonical-bootstrap-shim.md)
- 2026-04-12: added [Add feedback bundles and Sula Core review workflow](docs/change-records/2026-04-12-add-feedback-bundles-and-core-review-workflow.md)
- 2026-04-12: released [Sula 0.11.0 formal document workflows and feedback bundles](docs/releases/2026-04-12-release-sula-0-11-0-formal-document-workflows-and-feedback-bundles.md)

- 2026-04-12: added release record [Release Sula 0.11.0 formal document workflows and feedback bundles](docs/releases/2026-04-12-release-sula-0-11-0-formal-document-workflows-and-feedback-bundles.md)
## Next Review

- owner: Sula Core maintainers
- date: 2026-04-18
- trigger: review again before changing the public bootstrap contract, the managed/scaffold onboarding contract, or the planned vNext kernel contract
