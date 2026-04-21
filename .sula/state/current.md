# Current State Snapshot

- generated on: 2026-04-22
- project: Sula
- profile: `sula-core`
- source priority: STATUS.md and project records override this generated snapshot

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
- Sula now has a documented proposal for absorbing long-term value from reusable workflow-governance patterns through manifest-driven capability contracts instead of platform-specific skill lock-in.
- Sula now implements the first workflow-capability slice from that proposal: manifest-level workflow rigor policy plus source-first `spec`, `plan`, and `review` scaffolds under `docs/workflows/`.
- Sula now completes that workflow slice with first-class `workflow branch` and `workflow close` commands, so complex work can move from policy assessment to explicit closeout readiness.
- The next UX milestone is now implemented too: `onboard` provides a zero-memory interview flow that asks setup questions, explains what Sula will manage, and then applies adoption through the same kernel contract.
- The next launch milestone is now implemented too: the public site exposes `/launch/`, a machine-readable launcher descriptor, and a downloadable `bootstrap.py` shim so startup no longer depends on guessing local commands.
- The feedback-bundle lifecycle is now released in the Git-backed Sula 0.11.0 source state: adopted projects can capture reusable local Sula fixes as feedback bundles, and Sula Core can ingest, review, and release them through a central queue.
- Sula 0.12.0 is now released in source form, bundling truth-source freshness checks, the daily `check` workflow, stronger workflow/release governance, and Unicode-safe discovered source ids into one downstream sync target.
- Sula 0.13.0 is now released in source form, bundling staged session captures, durable memory promotion, rule-aware retrieval routing, memory-job inspection, and stable operator-facing memory workflows into one downstream sync target.
- Sula now has registry-backed in-repo canary verification across `sula-core`, `software-delivery`, `generic-project`, and `client-service`-style examples, plus public-release readiness and export commands that isolate remaining publication risk to git history rather than content drift.
- Sula now has a chosen default public-release path: keep this repository as the private pre-public lineage, publish a fresh public repository from `release export-public`, and only then point the site descriptor at the public source.
- The fresh public source now exists at `irihiyahnj/sula-public`, so `https://sula.1stp.monster/launch/` can resolve a real canonical clone source instead of depending on a local checkout.

## Health

- status: green
- reason: Sula 0.13.0 release-grade verification now passes, and the staged-memory kernel plus product-facing memory workflow are stable for downstream sync.

## Current Focus

- turn the recorded vNext architecture into stronger adapter composition and better result quality over the new SQLite-backed retrieval path
- maintain clear approval reporting so managed/scaffold boundaries remain obvious during onboarding
- keep the public bootstrap contract aligned with real consumer behavior and protocol failures seen in live use
- switch `site/sula.json` and `site/launch/bootstrap.py` to the published public source after that repository exists
- decide whether to keep the hosted site on Fly or migrate it onto the existing DigitalOcean infrastructure once server write access is available

## Blockers

- none

## Recent Decisions

- 2026-04-12: released [Sula 0.11.0 formal document workflows and feedback bundles](docs/releases/2026-04-12-release-sula-0-11-0-formal-document-workflows-and-feedback-bundles.md)
- 2026-04-16: added release record [Release Sula 0.12.0 freshness, workflow, and Unicode source-id fixes](docs/releases/2026-04-16-release-sula-0-12-0-freshness-workflow-and-unicode-source-id-fixes.md)
- 2026-04-18: added release record [Release Sula 0.13.0 stable memory kernel and operator workflow](docs/releases/2026-04-18-release-sula-0-13-0-stable-memory-kernel-and-operator-workflow.md)
- 2026-04-12: added release record [Release Sula 0.11.0 formal document workflows and feedback bundles](docs/releases/2026-04-12-release-sula-0-11-0-formal-document-workflows-and-feedback-bundles.md)
- 2026-04-22: added release record [Release Sula 0.14.0 handoff contract and Git release upgrade flow](docs/releases/2026-04-22-release-sula-0-14-0-handoff-contract-and-git-release-upgrade-flow.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-04-21
- trigger: review again before broad 0.13.0 rollout, changing the public bootstrap contract, or expanding memory beyond the current stable promotion loop

## Handoff

- ready: yes
- start here: `docs/releases/2026-04-22-release-sula-0-14-0-handoff-contract-and-git-release-upgrade-flow.md`; `STATUS.md`
- latest record: `docs/releases/2026-04-22-release-sula-0-14-0-handoff-contract-and-git-release-upgrade-flow.md`
- next action: review `docs/change-records/2026-04-18-document-memory-capability-implementation-plan.md`; run `python3 scripts/sula.py canary verify --project-root . --all`
- next owner: Sula Core maintainers
- next due: 2026-04-22
- done when: result `SULA CHECK OK`; result `doctor strict passed`; artifact `STATUS.md`
- blockers: none
- source of truth: `STATUS.md`; `docs/releases/2026-04-22-release-sula-0-14-0-handoff-contract-and-git-release-upgrade-flow.md`
- source freshness: n/a
- verification command: `python3 scripts/sula.py canary verify --project-root . --all`
- verification result: n/a
- verification date: 2026-04-22
- git branch: main
- git commit: fae517499091
- git working tree: dirty
