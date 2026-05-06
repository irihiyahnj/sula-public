# Current State Snapshot

- generated on: 2026-05-06
- project: Sula
- profile: `sula-core`
- source priority: STATUS.md and project records override this generated snapshot

## Summary

### 2026-05-06

- Added Sula Core compact execution visibility: `orchestration status --compact` now prints one English tool line with run state, task count, risk, main model/depth, context placeholder, executor model/depth/runner effort, workspace, elapsed, cost, last event, and next action. `agent-routing configure` now accepts executor `--reasoning-effort`; shell and Codex runners receive runner effort hints, mapping Sula `xhigh` to Claude-style `max`.
- Prepared Sula 0.18.0 remembered agent routing release with agent-routing configure, release metadata, launch descriptor version bump, and verification docs.
- Verified and finalized the Sula 0.18.0 remembered agent routing release for downstream project sync.
- Prepared Sula 0.18.1 with descriptor-based Git release upgrade prompts for downstream project upgrades.
- Verified Sula 0.18.1 descriptor-based Git upgrade docs and prepared patch release publication.
- Prepared Sula 0.18.2 to use the public GitHub descriptor as the live upgrade source instead of the stale hosted descriptor.
- Prepared Sula 0.18.2 to use the public GitHub descriptor as the live Git upgrade source.
- Prepared Sula 0.18.3 to use GitHub raw refs descriptor URL after raw.githubusercontent main returned a cached previous descriptor.
- Prepared Sula 0.18.3 to use the noncached GitHub raw refs descriptor for model-driven Git upgrades.
- Prepared Sula 0.18.4 so upgrade automation reads the live descriptor through a shallow Git clone instead of HTTP raw endpoints.
- Prepared Sula 0.18.4 so Git upgrade automation discovers source_ref from a shallow public repo clone.
- Added compact orchestration status and executor effort routing to Sula Core.
- Prepared Sula 0.18.5 so compact orchestration status and executor effort routing can roll out through the normal versioned upgrade path.
- Finalize Sula 0.18.5 compact orchestration status release metadata and canary verification.
- Adjusted orchestration visible-active semantics so terminal runs stay in history and no longer appear as active execution; added regression coverage and a change record.
- Released Sula 0.18.6 terminal active display patch; bumped version metadata, launch descriptor, and bootstrap default ref.
- Released Sula 0.18.7 check automation self-lock fix; DeepSeek Flash executor supplied the initial patch, reviewer corrected it, validation passed, and runner cost/token metrics were recorded.
- Completed Sula 0.18.7 check automation self-lock release cleanup; added required follow-up section and regenerated memory.
- Implemented Sula 0.18.8 bounded executor contract and budget visibility: executor routes now carry bounded contract and execution packet data, compact status shows executor budget, local Sula executor route was adjusted from xhigh to high, and target tests passed.
- Completed Sula 0.18.8 validation cleanup: full unittest discover ran 124 tests with one stale site descriptor version assertion, the assertion now follows VERSION, targeted rerun passed, py_compile and JSON validation passed.
- Prepared Sula 0.18.9 executor default adjustment: executor reasoning now defaults to xhigh, reported cost is open by default instead of a hard cap, local Sula route uses deepseek-v4-flash xhigh, and targeted validation passed.
- Updated the local DeepSeek Flash executor wrapper to consume Sula executor contracts and return structured runner JSON; documented the reusable local executor wrapper contract for downstream projects in Sula 0.18.10.
- Completed Sula 0.18.10 wrapper contract cleanup by updating the managed docs README template after check caught docs-map drift; Sula check now passes.
- Implemented Sula 0.18.11 supervised executor retry: reviewer feedback can be recorded with orchestration review, retries can inherit feedback with orchestration run --from-run-id, runners receive review feedback in execution packets, and run records now include failure classification, execution summaries, runner scores, and runner health status.

### 2026-05-05

- Defined the Sula 0.17.0 agent-native project OS upgrade package: added the whitepaper, overview link, workflow spec/plan/review, task intake, and change record; verified with check, doctor strict, and full unittest suite.
- Completed the Sula 0.17.0 agent-native project OS upgrade, including MCP-compatible control surface, controlled write policy, provider and portfolio reports, PR closeout evidence, canary verification repair, release metadata, tests, canary rollout checks, and final verification docs.
- Closed the Sula 0.17.0 task package records after final verification, including the eight task package closeout table and completed workflow task state.
- Prepared Sula 0.17.0 for official release: restored the public bootstrap shim, rechecked release readiness, and moved the release batch to commit/tag/export closeout.
- Recorded the official Sula 0.17.0 public publication to sula-public main and tag v0.17.0 after clean export release.

### 2026-05-04

- Bump status limits 10→100, add sula report --lightweight for instant team sync, update workflow_auto_loop with per-completion sync rule
- Bump status limits 10→100, add sula report --lightweight, update workflow_auto_loop protocol

### 2026-05-02

- Committed the full 0.15.0 release that previously existed only in the working tree (118 files, +9742/-1038 lines): orchestration control plane, automation kernel, closeout verification adapters, shell-command/codex-sdk/codex-app-server runner boundaries, and `[agent_behavior]` policy surface are now in git history.
- Added `**/.sula/state/automation/*` and `**/.sula/state/orchestration/*` to `.gitignore` so that runtime events, intents, tasks, budgets, and run records — generated on every command execution — no longer dirty the working tree or get committed.
- Added `git commit: any` sentinel to doctor handoff validation in `scripts/sula.py`, permanently breaking the self-reference cycle where updating STATUS.md's commit field requires a commit that moves HEAD.
- Verified all 4 in-repo canaries (`sula-root`, `okoktoto-v5-example`, `field-ops-generic-canary`, `client-service-drive-canary`) pass `release readiness` with 0 issues; `sync --dry-run`, `doctor --strict`, and `check` all pass for every canary.
- Regenerated `.sula/state/current.md` and `.sula/memory-digest.md` for root and all 3 example projects so generated state matches committed source documents.
- Identified a design gap: Sula lacks a `report` command to write session summaries back into STATUS.md after work completes. Planned for 0.15.1.
- Implemented the sula report command: adds date-grouped session summaries to STATUS.md, auto-archives old groups, regenerates memory-digest without timestamp.
- Added Session Lifecycle section to AGENTS.md and CLAUDE.md.tmpl so all adopted projects know to start with memory-digest.md, work, end with sula report.
- Released 0.15.2: session lifecycle discipline (start with memory-digest, end with report+check+commit), sula report command with Summary archiving, git commit: any sentinel preserved through sync, Summary staleness check in sula check, projected AI-tool templates updated across all profiles.
- Finalize 0.15.2 release: commit, tag, push to public repo.
- Implement auto-loop: workflow start, orchestration check in sula check, orchestration in status/digest, closeout next-action suggestions.
- Implemented auto-loop: workflow start composite command, orchestration check in sula check, orchestration status in status/digest, next-action suggestions in closeout. Simplified closeout validation (removed fragile token matching). Bumped status section limits from 5 to 10. Updated sula.json protocol with cross-agent workflow rules. Released 0.16.0.
- Implemented auto-loop: workflow start, orchestration check in sula check, orchestration status in status/digest, next-action suggestions in closeout. Simplified closeout validation. Bumped status section limits to 10. Updated sula.json protocol with cross-agent workflow rules.
- Deprecate Fly.io hosting: move to Git-only delivery. Remove fly.toml, Fly deployment change record, and all static site assets. Keep site/sula.json as the machine-readable protocol descriptor. Update all URLs from sula.fly.dev/1stp.monster to GitHub. Repository now serves as the sole distribution channel.
- Fix STATUS.md handoff and CHANGE-RECORDS.md Fly retirement entry for v0.16.0 release readiness
- Unify to single public repo: change origin to sula-public, retire private sula.git. All project records, change records, and release history now live in one public repository.

### 0.15.0 and earlier

- Sula now manages itself as a first-class `sula-core` consumer while still acting as the source repository for reusable operating-system assets.
- The repository has memory-aware governance, an in-repo canary, a root self-adoption path, and an approval-based adoption agent for bringing new repositories under Sula.
- Public-release governance is now in place, and the remaining blocker is historical lineage cleanup rather than working-tree quality.
- The public source at `irihiyahnj/sula-public` serves as the canonical clone source for bootstrap.
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
- The fresh public source now exists at `irihiyahnj/sula-public`, serving as the canonical clone source.
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
- 2026-05-05: added [Define Sula 0.17.0 agent-native project OS upgrade](docs/change-records/2026-05-05-define-sula-0-17-0-agent-native-project-os-upgrade.md)
- 2026-05-05: added [Implement Sula 0.17.0 agent-native control surface](docs/change-records/2026-05-05-implement-sula-0-17-0-agent-native-control-surface.md)
- 2026-05-06: added release record [Release Sula 0.18.0 remembered agent routing](docs/releases/2026-05-06-release-sula-0-18-0-remembered-agent-routing.md)
- 2026-05-06: added release record [Release Sula 0.18.1 current upgrade descriptor](docs/releases/2026-05-06-release-sula-0-18-1-current-upgrade-descriptor.md)
- 2026-05-06: added release record [Release Sula 0.18.2 GitHub upgrade descriptor](docs/releases/2026-05-06-release-sula-0-18-2-github-upgrade-descriptor.md)
- 2026-05-06: added release record [Release Sula 0.18.3 noncached GitHub upgrade descriptor](docs/releases/2026-05-06-release-sula-0-18-3-noncached-github-upgrade-descriptor.md)
- 2026-05-06: added release record [Release Sula 0.18.4 Git-cloned upgrade descriptor](docs/releases/2026-05-06-release-sula-0-18-4-git-cloned-upgrade-descriptor.md)
- 2026-05-06: added release record [Release Sula 0.18.5 compact orchestration status](docs/releases/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md)

## Next Review

- owner: Sula Core maintainers
- date: 2026-05-08
- trigger: review again before broad orchestration rollout, long-running runner streaming/cancellation, or changing agent behavior policy gates

## Handoff

- ready: yes
- start here: `docs/change-records/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md`; `STATUS.md`
- latest record: `docs/change-records/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md`
- next action: review `docs/change-records/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md`; run `python3 scripts/sula.py check --project-root .`; run `python3 -m unittest tests.test_sula -v`
- next owner: Sula Core maintainers
- next due: 2026-05-08
- done when: result `SULA CHECK OK`; result `doctor strict passed`
- blockers: none
- source of truth: `STATUS.md`; `docs/change-records/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md`
- source freshness: current
- verification command: `python3 scripts/sula.py check --project-root . --json`; `python3 scripts/sula.py doctor --project-root . --strict --json`; `python3 -m unittest discover -s tests -v`
- verification result: pass
- verification date: 2026-05-06
- git branch: main
- git commit: any
- git working tree: dirty
