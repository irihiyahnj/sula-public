# Changelog

All notable changes to Sula Core should be recorded here with explicit sync impact.

## Unreleased

- no entries yet

## 0.14.0 - 2026-04-22

### Added

- a structured `## Handoff` contract in `STATUS.md`, including machine-checkable ownership, due date, next action, acceptance criteria, source freshness, verification, and git-runtime fields
- published Git release upgrade assets, including a dedicated runbook and model-facing prompt set for one-project and fleet rollout
- status-archive spillover support for current-state sections so long-lived projects can keep a compact dashboard without deleting historical context

### Changed

- `doctor --strict` and `check` now require `STATUS.md` to stay aligned with the latest durable record, enforce the structured handoff contract, and gate closeout on a current-state page instead of a loose status note
- `done when` validation now prefers standard result values while still allowing custom result text through advisories instead of hard failure
- `record new`, workflow closeout flows, and memory-digest normalization now keep handoff runtime fields and generated state aligned with the current repository state

### Sync Impact

- adopted projects syncing to `0.14.0` must refresh `STATUS.md` so it contains a valid `## Handoff` section and stays within the configured current-state limits before `doctor --strict` and `check` will pass
- teams can now upgrade from the published Git release source and reuse one-line model prompts instead of depending on one mutable local Sula checkout
- projects that already manage their own status narrative remain compatible, but closeout now requires a machine-checkable handoff contract before downstream operators should treat the project as ready to continue
## 0.13.0 - 2026-04-18

### Added

- staged session memory under `.sula/state/session/captures.jsonl` with `memory capture`, `memory review`, `memory promote`, `memory clear`, and `memory jobs`
- first-class kernel objects for rules, staged session captures, promotions, and memory-maintenance jobs
- deterministic query-route reporting plus rule-aware routing for `query` and portfolio query surfaces
- default durable promotion file `docs/ops/session-promotions.md` with reusable sections for rules, tasks, decisions, state updates, workflow artifacts, and risks

### Changed

- `status`, `onboard`, and `adopt` now expose the staged-memory lifecycle, recent promotions, last memory job, and the configured promotion file
- `doctor --strict` and `check` now validate staged-capture age, memory-job state, and promotion-file structure as part of the normal release bar
- `memory promote` now supports `state` and `workflow-artifact` targets in addition to rules, tasks, decisions, and risks
- the project-memory guidance now documents the stable operator loop as capture, review, promote, query, clear

### Sync Impact

- existing adopted projects remain backward-compatible and gain the new memory command surface, rule indexing, and query-route reporting on next sync
- projects syncing to this release can keep semantic help disabled while still getting a stronger cross-session operating-memory loop through staged capture and explicit promotion
- adopted projects that use `check` or `doctor --strict` will now be held to stale-capture and promotion-file integrity checks, so rollout should review old temporary memory before treating the upgrade as a no-op
- newly adopted projects and projects using memory promotion will now create or extend `docs/ops/session-promotions.md` as a project-owned durable source instead of leaving promoted operating insight implicit

## 0.12.0 - 2026-04-16

### Added

- truth-source and freshness metadata for collaborative artifact families, including `family_key`, `artifact_role`, `source_of_truth`, `collaboration_mode`, `last_refreshed_at`, and `last_provider_sync_at`
- `artifact refresh` plus read-only Google Docs / Google Sheets provider adapters and `.sula/cache/provider-snapshots/` normalized provider snapshot caching
- project-local Google OAuth storage under `.sula/local/google-oauth.json` when a Sula project root is known
- `check` as a first-class daily state-sync verification command that fails when generated `.sula/state/current.md` or `.sula/memory-digest.md` drift away from current source documents

### Changed

- `query`, `artifact locate`, and `status` now surface fact-source summaries, local-copy staleness risk, and provider-metadata gaps for collaborative provider-backed artifacts
- natural-language freshness phrases such as "先看最新版本再继续" or "共享文档为准" now trigger truth-source-aware retrieval instead of blindly trusting old local context
- freshness-intent `query` and `artifact locate` now attempt a real provider refresh before returning results when provider metadata and access are available
- provider-native registration and import planning now default Google Docs or Sheets target paths from workflow slots like `delivery/...` instead of treating the provider root as the implicit destination
- state-sync workflows now expect `SULA CHECK OK` before completion, with generated `.sula/*` state rebuilt through Sula commands instead of hand edits
- discovered source registry ids now preserve Unicode path distinctions, and `doctor --strict` fails fast when duplicate source ids are already present instead of letting sqlite rebuild crash later

### Sync Impact

- existing adopted projects remain compatible and gain richer artifact catalog metadata plus truth-source/freshness summaries on next artifact registration or kernel refresh
- collaborative Drive-based projects can now distinguish provider-native truth from local sync copies and exported derivatives without relying on one project-specific prompt ritual
- projects that want live provider refresh can now supply a read-only Google access token through `SULA_GOOGLE_ACCESS_TOKEN` without introducing a mandatory third-party dependency
- adopted projects that sync to this version gain a reusable daily close-out gate for status and memory updates instead of relying on project-local scripts
- adopted projects with Unicode-named source files now rebuild `.sula/sources/registry.json` and sqlite cache safely on next sync or kernel refresh instead of risking duplicate `source:` ids

## 0.11.0 - 2026-04-12

### Added

- formal document design bundles with a first-class `[document_design]` manifest section, a managed design rulebook, and genre-aware source templates for schedule, proposal, report, process, and training artifacts
- `feedback capture` so adopted projects can package reusable local managed-file fixes as portable feedback bundles with doctor state, sync plan, diffs, and snapshot files
- `feedback ingest`, `feedback list`, `feedback show`, and `feedback decide` so Sula Core can run a governed intake and decision workflow over those bundles
- `.sula/feedback/outbox/archives/` as the machine-readable export surface for project-side feedback bundles
- `registry/feedback/catalog.json` and `registry/feedback/inbox/` as Sula Core's central feedback review queue
- [docs/reference/feedback-bundle-lifecycle.md](docs/reference/feedback-bundle-lifecycle.md) as the formal contract for upstream feedback and downstream rollout

### Changed

- managed AI instructions, docs, schemas, and artifact generation now carry the formal document design contract consistently across adoption, sync, and artifact creation
- managed AI instruction files and team-operating docs now tell adopted projects to capture reusable Sula issues instead of leaving them as undocumented local drift
- the Sula Core release runbook and release-process docs now require feedback queue review as part of release discipline
- export catalogs now expose feedback outbox paths for every project, and expose the central feedback catalog when the active profile is `sula-core`

### Sync Impact

- existing adopted projects remain compatible and gain the formal document design policy plus an extra feedback export path under `.sula/exports/catalog.json` on next sync
- teams can now standardize source-first planning, proposal, report, process, and training documents through managed Sula guidance instead of per-project prompt drift
- projects can now keep working with local managed-file fixes while still sending a reviewable upstream bundle back to Sula Core
- Sula Core maintainers now have an explicit inbox and decision trail before reusable fixes are absorbed into templates, docs, scripts, and later releases

## 0.10.0 - 2026-04-12

### Added

- `artifact import-plan` as a machine-readable bridge from project-owned sources to provider-native Google Docs and Google Sheets imports
- `.sula/exports/provider-imports/*.json` as stable import-plan outputs for external software and future adapters
- automatic bridge artifact generation during import planning when a source file still needs `.docx` or `.xlsx` materialization

### Changed

- README and provider-backed artifact docs now describe provider import planning as the next step after local materialization, not as a future-only idea
- export catalog now exposes the provider import plan directory under `.sula/exports/provider-imports`

### Sync Impact

- existing adopted projects remain compatible and only gain an extra export path in `.sula/exports/catalog.json` on next sync
- external software can now ask Sula for an explicit Google Docs or Google Sheets import plan instead of reverse-engineering bridge files from artifact metadata
- provider-backed artifact workflows now have a formal handoff layer between local project truth and future direct provider adapters

## 0.9.0 - 2026-04-12

### Added

- `/launch/` as the canonical site-launch contract for URL-first startup
- `site/launch/bootstrap.py` as a canonical bootstrap shim that can resolve Sula source and route onboarding or existing-consumer review
- launcher metadata in `site/sula.json`, including source ref, launcher URL, and no-global-lookup rules

### Changed

- homepage and bootstrap-site prompts now point to the shorter launch URL instead of relying on the older long-form bootstrap copy
- the public site now defines startup as `read launch URL -> resolve launcher -> onboard or review`, not `guess local CLI`

### Sync Impact

- existing adopted projects remain compatible and only receive routine version-lock and kernel refresh updates
- external sessions can now start from the site contract even when no local `sula` command or vendored source exists
- the canonical startup path now has a stable site URL, a machine descriptor, and a bootstrap shim instead of a documentation-only contract

## 0.8.0 - 2026-04-12

### Added

- `onboard` as a guided, zero-memory onboarding entrypoint for first-time project setup
- onboarding question payloads and operating summaries that explain what Sula will manage before adoption
- interactive confirmation flow for human users and `--accept-suggested` for machine or fast-path callers

### Changed

- `adopt --approve --json` and `onboard --approve --json` now emit a single machine envelope instead of leaking helper output
- onboarding defaults now follow the selected storage provider, so `google-drive` suggestions no longer inherit `local-only` storage settings
- README and adoption docs now treat guided onboarding as the preferred first-time entrypoint

### Sync Impact

- existing adopted projects remain compatible and only receive the normal version-lock and kernel-state refresh on next sync
- external tools can now drive a first-time setup conversation without requiring users to memorize Sula flags or artifact-routing details
- human operators can connect a project through questions first and inspect the resulting operating promise before or during adoption

## 0.7.0 - 2026-04-12

### Added

- `status --json` as a machine-readable project state summary
- `artifact create/register/locate` for workflow-routed project files
- `portfolio register/list/status/query` for multi-project workspaces
- optional manifest sections for `workflow`, `storage`, and `portfolio`
- `google-drive` local-sync adapter metadata alongside existing `repo` and `local-fs` behavior
- a formal portfolio/adapter/workflow contract in [docs/reference/portfolio-adapter-workflow-contract.md](docs/reference/portfolio-adapter-workflow-contract.md)

### Changed

- `init`, `adopt`, `sync`, `doctor`, `remove`, `record new`, and `memory digest` now support machine-readable `--json` output
- kernel state now persists a first-class artifact catalog under `.sula/artifacts/catalog.json`
- generic projects can now describe workflow packs and storage adapters without pretending those concepts are profiles

### Sync Impact

- Existing adopted projects gain optional workflow/storage/portfolio metadata and artifact catalog support on the next sync or state refresh
- External tools can now integrate with Sula without scraping human CLI output
- Drive-synced non-Git client projects now have a first-class path toward artifact routing and portfolio-wide visibility

## 0.6.0 - 2026-04-12

### Added

- `.sula/cache/kernel.db` as a rebuildable local SQLite cache for kernel retrieval
- richer kernel object extraction for `task`, `decision`, `risk`, `person`, `agreement`, and `milestone`
- structured query filters for adapter, status, path prefix, and date range
- timeline query mode over dated objects and kernel events

### Changed

- `query` now prefers SQLite-backed local retrieval when the cache exists and falls back to JSON catalogs when needed
- kernel doctor checks now validate the rebuildable SQLite cache structure
- generated object catalogs now carry date metadata so timeline and date filters can work without reparsing project files on every query

### Sync Impact

- Existing adopted projects will gain `.sula/cache/kernel.db` on the next sync or adoption-related write
- Query output can now recover richer project structure from existing status files, records, and markdown sources without changing project-owned truth
- Teams can use local filters and timeline queries immediately after resyncing, even on non-Git projects

## 0.5.0 - 2026-04-12

### Added

- `generic-project` as the safe baseline profile for unknown or in-progress projects
- namespaced `.sula/` kernel artifacts for source registry, current-state snapshot, event log, index catalog, and export catalog
- automatic text-source discovery for project files so the source registry reflects real project content
- `.sula/adapters/catalog.json` as the explicit adapter contract for each adopted project
- `.sula/adapters/bundles.json` as the profile bundle contract for each adopted project
- `.sula/objects/catalog.json`, `.sula/indexes/relations.json`, and `query` for local object/source retrieval
- `.sula/cache/query-index.json` as a rebuildable local retrieval cache
- non-Git adoption support for projects that should not be blocked on repository metadata
- `remove` as an inspect-report-approve exit path for detaching Sula cleanly from a project
- automated CLI coverage for generic adoption and removal behavior

### Changed

- `adopt` now falls back to `generic-project` instead of treating unknown projects as an immediate blocker
- generated project state now includes kernel metadata and append-only event tracking under `.sula/`
- kernel doctor checks now validate source registry content and event log structure
- source registry entries now declare which adapters own or interpret them
- kernel doctor checks now validate object and relation catalogs as well
- public docs now describe `generic-project` as the safe baseline and document the removal flow

### Sync Impact

- Existing adopted projects remain compatible but will gain new `.sula/` kernel artifacts on the next sync or adoption-related write
- Teams can now adopt in-progress or non-Git projects without inventing a stack-specific profile first
- Projects that later choose to leave Sula can use the new removal report before deleting managed files manually

## 0.4.0 - 2026-04-11

### Added

- `adopt` as the inspect-report-approve onboarding command for repositories that have not yet adopted Sula
- automatic profile detection, manifest proposal, and planned managed/scaffold impact reporting during adoption
- post-approval adoption traceability that creates the initial status and change record automatically
- [docs/reference/adoption-agent.md](docs/reference/adoption-agent.md) to describe the one-sentence onboarding model
- `scripts/sula-adopt` as a thin wrapper over the main CLI

### Changed

- README and adoption guidance now treat `adopt` as the default onboarding path instead of the manual `init` flow
- root Sula traceability now records the adoption-agent model as a durable project decision
- `sula-core` module documentation now includes the adoption wrapper in the CLI surface

### Sync Impact

- Existing adopted projects do not need to change anything to remain compatible
- Repositories onboarding into Sula can now use a simpler approval-based flow without changing the underlying managed/scaffold contract
- Canary projects and root self-adoption should be resynced to move lockfiles and managed docs to `0.4.0`

## 0.3.0 - 2026-04-11

### Added

- single-project memory model documentation and project-memory operating guide
- core scaffold assets for detailed change records, release records, and incident records
- `record new` command for creating durable project records
- `memory digest` command for generating a project recall layer from source documents
- memory-aware doctor checks for status freshness, change-record structure, and exception references
- an in-repo OKOKTOTO canary that exercises the memory contract end to end
- a `sula-core` profile for operating-system repositories and root self-adoption

### Changed

- scaffold `STATUS.md` now uses explicit summary, health, focus, blockers, recent decisions, and next review sections
- scaffold `CHANGE-RECORDS.md` now acts as a short index instead of a long rules dump
- project manifests can now optionally define memory paths and freshness expectations
- release and adoption docs now require memory-aware rollout review
- the Sula root repository now manages itself through `.sula/project.toml` and strict doctor checks

### Sync Impact

- New projects will receive richer memory scaffolds automatically during `init`
- Existing adopted projects can accept managed memory-guide updates safely, but they should review whether to generate the new scaffold directories locally
- `doctor --strict` now fails if project memory structure is incomplete or malformed
- Teams should migrate important history into the new layout before treating strict doctor as a release gate

## 0.2.0 - 2026-04-11

### Added

- `sync --dry-run` to preview managed-file changes before writing them into an adopted project
- per-file sync impact classification for managed files
- stronger `doctor` checks for managed-file drift and lockfile mismatches
- an automated CLI test suite for `init`, `sync`, and `doctor`
- a GitHub Actions CI workflow for repository-level verification
- release governance, sync impact, and adoption registry docs
- `registry/adopted-projects.toml` as the central rollout tracking file

### Changed

- manifest validation now rejects unexpected sections, unexpected keys, and invalid value types
- `doctor` now compares managed files against the current rendered Sula output instead of checking only for file presence
- Sula Core now treats itself as a governed project with release and rollout discipline

### Sync Impact

- Existing adopted projects remain backward-compatible at the file contract level
- Repositories with locally drifted managed files or stale `.sula/version.lock` entries will now fail `doctor` until they resync or resolve drift intentionally
- Teams should run `sync --dry-run` before the first `0.2.0` rollout into any adopted project
