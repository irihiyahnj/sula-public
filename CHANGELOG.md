# Changelog

All notable changes to Sula Core should be recorded here with explicit sync impact.

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
