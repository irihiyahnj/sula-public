# STATUS

- last updated: 2026-05-02
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
- Sula now has a durable Symphony-style orchestration absorption plan and execution culture, so future AI sessions can implement the upgrade from repository truth instead of chat history.
- Sula now has the first executable Symphony-style orchestration slice: optional disabled-by-default manifest policy, local task normalization, dry-run run records, safety gates, and JSON orchestration commands.
- Sula now captures CLI/user intent as auditable orchestration tasks and requires closeout evidence beyond dry-run scheduling before a run can be accepted.
- Sula now absorbs Karpathy-inspired coding guidance as a portable `[agent_behavior]` policy with run-record quality checklists and verification/success-criteria closeout gates.
- Sula orchestration now has a generic trigger surface, a dependency-light `shell-command` real runner with isolated copy-workspace evidence, machine closeout evaluation, and review-required promotion candidates.
- Sula orchestration now reads provider task document mirrors and exposes portfolio-level orchestration summaries across registered projects.
- Sula orchestration closeout now validates task requirements, touched files, links, and requested `sula check` evidence before accepting a run.
- Sula orchestration closeout now emits typed verification checks for local files, artifact catalog entries, provider metadata, PR URLs, and ordinary URLs through manifest-controlled verification adapters.
- Sula orchestration now has a `provider-api` task source contract with provider task item identity, provider adapter task fetching, and fixture-backed Google Drive task ingestion.
- Sula orchestration now has policy-controlled remote verification for PR/provider closeout references plus `codex-sdk` and `codex-app-server` runner adapters behind explicit project settings.
- Sula now has a first-class automation kernel above orchestration: normal `check`, `doctor`, `status`, `query`, `sync`, and artifact freshness entrypoints can create events and intents automatically, so users do not need to remember a manual trigger command before Sula can plan follow-up work.

## Health

- status: green
- reason: Sula 0.15.0 is now published to `https://github.com/irihiyahnj/sula-public.git` with tag `v0.15.0`; source-release verification, canaries, and clean public export all pass, while readiness still reports the expected private-lineage constraints.

## Current Focus


- keep the public bootstrap contract aligned with real consumer behavior and protocol failures seen in live use
- run credentialed real-project canaries for GitHub PR verification, provider-backed artifact verification, and Codex runner endpoints before broad orchestration rollout
- add authenticated provider task adapters beyond the current Google Drive document/checklist contract when a real provider task API target is selected
- harden long-running remote runner cancellation and streamed event capture after the first real app-server canary
- expand automation classifiers after real projects reveal recurring provider, status, and workflow failure patterns
## Blockers

- none

## Recent Decisions


- 2026-05-01: added [Add Closeout Verification Adapters](docs/change-records/2026-05-01-zz-add-closeout-verification-adapters.md)
- 2026-05-01: added [Strengthen Orchestration Closeout Evaluator](docs/change-records/2026-05-01-z-strengthen-orchestration-closeout-evaluator.md)
- 2026-05-01: added [Wire Provider Task Source And Portfolio Orchestration](docs/change-records/2026-05-01-wire-provider-task-source-and-portfolio-orchestration.md)
- 2026-05-01: added [Add Automation Kernel For Event Driven Orchestration](docs/change-records/2026-05-01-zzzzz-add-automation-kernel-for-event-driven-orchestration.md)
- 2026-05-01: added [Default full Sula surface and activity feedback](docs/change-records/2026-05-01-default-full-sula-surface-and-activity-feedback.md)
## Next Review

- owner: Sula Core maintainers
- date: 2026-05-08
- trigger: review again before broad orchestration rollout, long-running runner streaming/cancellation, or changing agent behavior policy gates

## Handoff


- ready: yes
- start here: `docs/change-records/2026-05-01-zzzzz-add-automation-kernel-for-event-driven-orchestration.md`; `STATUS.md`
- latest record: `docs/change-records/2026-05-01-zzzzz-add-automation-kernel-for-event-driven-orchestration.md`
- next action: review `docs/releases/2026-05-01-release-sula-0-15-0-orchestration-control-plane-and-runner-boundaries.md`; run `python3 scripts/sula.py release readiness --project-root . --json`
- next owner: Sula Core maintainers
- next due: 2026-05-08
- done when: result `SULA CHECK OK`; result `doctor strict passed`; artifact `STATUS.md`
- blockers: none
- source of truth: `STATUS.md`; `docs/change-records/2026-05-01-zzzzz-add-automation-kernel-for-event-driven-orchestration.md`
- source freshness: n/a
- verification command: `python3 scripts/sula.py check --project-root . --json`; `python3 scripts/sula.py doctor --project-root . --strict --json`
- verification result: pass
- verification date: 2026-05-02
- git branch: main
- git commit: 56fd6d899fd2
- git working tree: clean
