# Sula

Sula is a reusable project operating system for AI-native software teams.

It standardizes how projects define rules, accept requests, execute work, verify changes, ship releases, and keep durable traceability across repositories.

Sula is not a product template for one stack. It is a coordination layer with:

- a reusable documentation and operations core
- profile-specific templates for project families
- a project manifest that captures each repository's facts
- a guided zero-memory onboarding flow for first-time setup
- a site-launch contract with a canonical URL and downloadable bootstrap launcher
- machine-readable CLI outputs for external tools and adapters
- an inspect-report-approve adoption flow for one-sentence onboarding
- scripts to initialize, sync, and audit project adoption
- a governed rollout path for sync impact and release discipline
- a single-project memory model for durable status, decisions, releases, and incidents
- workflow packs, artifact routing, and portfolio registration for non-code client projects

Long-term direction:

- a `generic-project` kernel that can attach to unknown project types first and specialize later through adapter bundles
- removable, namespaced machine state so portability also means easy detachment
- structured indexing and recall that stay reproducible instead of depending on prior chat context
- explicit adapter contracts so kernel sources can be mapped to stable operating capabilities
- rebuildable local SQLite cache layers so query quality can improve without turning the cache into project truth

## What Sula Solves

Without a system, every repository drifts:

- AI tools each get slightly different instructions
- release checks live in people's heads
- architecture rules are implicit until they are violated
- status and change records become inconsistent
- improvements made in one project do not reach the others

Sula makes those concerns portable.

## User Experience Contract

Sula should trend toward a zero-memory user model:

- the user should not need to remember commands, paths, file slots, or project-state rules
- onboarding should ask the missing questions, not expect the user to preload Sula's internal model
- once onboarding answers are captured, Sula should tell the user what it will manage, where files will go, and which commands or automations become available

This means adapters, workflow packs, and portfolio registration are not just technical metadata. They are the basis for a guided setup flow that turns a live project into an understandable operating system.

## Core Concepts

### 1. Sula Core

Reusable docs and tool adapters that should evolve once and benefit many projects:

- `CODEX.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/project.mdc`
- `docs/README.md`
- `docs/ops/*`

### 2. Profile

A profile is a reusable project-family layer.

Current profiles:

- `generic-project`
- `react-frontend-erpnext`
- `sula-core`

Profiles provide:

- managed architecture docs
- managed runbooks
- scaffold starters for project-owned files

### 3. Project Manifest

Each adopted project keeps a local `.sula/project.toml` that defines:

- project identity
- branch model
- highest architecture rule
- build and verification commands
- key source paths
- deploy expectations
- auth/session semantics
- workflow pack, storage adapter, and portfolio registration metadata

### 4. Managed vs Scaffold Files

Sula distinguishes two classes of files:

- managed files: overwritten by `sync`
- scaffold files: generated once if missing, then owned by the project

This avoids centralizing project truth that should remain local.

## Repository Layout

```text
docs/
  philosophy.md
  adoption-playbook.md
  versioning.md
  reference/
schema/
registry/
scripts/
tests/
templates/
  core/
    managed/
    scaffold/
  profiles/
    generic-project/
      managed/
      scaffold/
    react-frontend-erpnext/
      managed/
      scaffold/
    sula-core/
      managed/
      scaffold/
examples/
```

## Quick Start

### Onboard A Project With Questions

For first-time setup, prefer the guided onboarding flow:

```bash
python3 scripts/sula.py onboard --project-root /path/to/project
python3 scripts/sula.py onboard --project-root /path/to/project --accept-suggested --approve
```

`onboard` asks the missing questions, including the default language for generated docs and records, proposes workflow/storage/portfolio answers, explains what Sula will manage, and can apply adoption immediately after confirmation.

### Launch From The Site Contract

The final startup direction is a URL-first launch flow:

```text
请按 https://sula.1stp.monster/launch/ 的启动协议接管当前项目。
```

or

```text
Please take over the current project using the launch contract at https://sula.1stp.monster/launch/.
```

The site now exposes:

- `/launch/` as the human-readable launch contract
- `/sula.json` as the machine-readable launcher descriptor
- `/launch/bootstrap.py` as the canonical bootstrap shim when local Sula tooling is missing

### Low-Level Adoption Report

In a live agent session, the target request should be as short as:

```text
Please take over this repository using the Sula bootstrap protocol: first read https://sula.1stp.monster/, inspect the repo and produce an adoption report, wait for my approval, then adopt it and report the changes, risks, and how to use it.
```

The CLI equivalent is:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project
python3 scripts/sula.py adopt --project-root /path/to/project --approve
```

The first command inspects the repository, detects the likely profile, and prints an approval-ready report. Unknown project types now fall back to the safe `generic-project` baseline instead of blocking adoption. The second command applies the adoption, validates the result with `doctor --strict`, creates initial traceability, and prints the follow-up usage commands.

Use `init` only when you need low-level manual control over manifest values before the approval-based adoption flow can infer them safely.

### Bootstrap site assets

The public bootstrap site lives in this repository under `site/`:

- `site/index.html`: landing page with the canonical copyable bootstrap lines
- `site/bootstrap/index.html`: behavioral contract for inspect, report, approve, adopt
- `site/sula.json`: machine-readable bootstrap descriptor

These assets are designed for eventual hosting at `https://sula.1stp.monster/`.

Current deployment state:

- live Fly preview: `https://sula.fly.dev/`
- live custom domain: `https://sula.1stp.monster/`
- machine-readable descriptor: `https://sula.1stp.monster/sula.json`
- custom domain routing: active through Fly-managed DNS targets

### Sync improvements into an existing project

```bash
python3 scripts/sula.py sync --project-root /path/to/project --dry-run
python3 scripts/sula.py sync --project-root /path/to/project
python3 scripts/sula.py doctor --project-root /path/to/project
python3 scripts/sula.py doctor --project-root /path/to/project --strict
```

Use `--dry-run` before every real sync so you can review which managed files would change and how risky they are.

### Remove Sula from a project

```bash
python3 scripts/sula.py remove --project-root /path/to/project
python3 scripts/sula.py remove --project-root /path/to/project --approve
```

The report shows which namespaced kernel files and managed docs will be removed, and which scaffold files will stay project-owned.

### Create durable project memory

```bash
python3 scripts/sula.py record new \
  --project-root /path/to/project \
  --title "Explain the non-trivial change"

python3 scripts/sula.py memory digest --project-root /path/to/project
```

This creates durable project memory without mixing managed operating-system files with project-owned history.

### Read machine-usable project state

```bash
python3 scripts/sula.py status --project-root /path/to/project
python3 scripts/sula.py status --project-root /path/to/project --json
python3 scripts/sula.py doctor --project-root /path/to/project --strict --json
```

These commands expose the same project kernel to humans and to external software. When `--json` is used, Sula becomes a local machine protocol instead of a text-only CLI.

### Create and track project artifacts

```bash
python3 scripts/sula.py artifact create \
  --project-root /path/to/project \
  --kind agreement \
  --title "Hospital Service Contract"

python3 scripts/sula.py artifact register \
  --project-root /path/to/project \
  --kind report \
  --title "Hospital Intake Report" \
  --project-relative-path delivery/2026-04-12-hospital-intake-report-v1 \
  --provider-item-id doc-abc123 \
  --provider-item-kind google-doc \
  --provider-item-url https://docs.google.com/document/d/doc-abc123/edit

python3 scripts/sula.py artifact materialize \
  --project-root /path/to/project \
  --source-path drafts/hospital-intake.md \
  --target-format docx \
  --kind report \
  --title "Hospital Intake Report"

python3 scripts/sula.py artifact materialize \
  --project-root /path/to/project \
  --source-path planning/shoot-schedule.csv \
  --target-format xlsx \
  --kind schedule \
  --title "Shoot Schedule Export"

python3 scripts/sula.py artifact import-plan \
  --project-root /path/to/project \
  --source-path drafts/hospital-intake.md \
  --provider-item-kind google-doc \
  --json

python3 scripts/sula.py artifact import-plan \
  --project-root /path/to/project \
  --artifact-id artifact:path-planning-shoot-schedule-csv \
  --provider-item-kind google-sheet \
  --json

python3 scripts/sula.py artifact locate \
  --project-root /path/to/project \
  --kind agreement --json
```

Artifacts are routed through the active workflow pack and stored under the project's artifacts root, then registered in `.sula/artifacts/catalog.json`.

Provider-backed artifacts can also be registered without a local materialized file path by supplying a stable project-relative path and provider item metadata. This lets Drive-synced and provider-native deliverables survive device-specific local path differences.

`artifact materialize` lets a project-owned source file produce import-friendly deliverables without requiring Google OAuth first:

- `.md` / `.txt` / `.html` -> `.html`
- `.md` / `.txt` / `.html` -> `.docx` on macOS via `textutil`
- `.csv` / `.tsv` / `.json` -> `.xlsx`

That supports a practical workflow where Sula keeps Markdown and tabular files as project truth, then Google Docs or Google Sheets import the generated `.docx` or `.xlsx` when a native Google file is needed.

`artifact import-plan` is the next bridge layer for external software:

- it accepts a project source file or an existing artifact id
- it reuses an import-ready `.docx`, `.html`, or `.xlsx` when one already exists
- otherwise it materializes the required bridge file automatically
- it writes a machine-readable plan to `.sula/exports/provider-imports/*.json`
- it returns the follow-up `artifact register` shape that should be used after the real provider item id and URL exist

### Register projects in a portfolio

```bash
python3 scripts/sula.py portfolio register \
  --project-root /path/to/project \
  --portfolio-root /path/to/portfolio

python3 scripts/sula.py portfolio list --portfolio-root /path/to/portfolio --json
python3 scripts/sula.py portfolio query --portfolio-root /path/to/portfolio --q "contract" --json
```

The portfolio registry lets one Sula workspace track many adopted projects, including non-Git client-service projects stored in Google Drive local-sync folders.

### Query the project kernel

```bash
python3 scripts/sula.py query --project-root /path/to/project --q "contract"
python3 scripts/sula.py query --project-root /path/to/project --q "deploy" --kind change
python3 scripts/sula.py query --project-root /path/to/project --q "review" --kind task --adapter memory
python3 scripts/sula.py query --project-root /path/to/project --q "" --timeline --since 2026-04-01 --limit 20
```

This searches the local kernel object catalog, source registry, and event timeline using exact, structured, and lexical matching. Query now prefers the rebuildable `.sula/cache/kernel.db` cache when present, prefers richer object hits over lower-signal duplicate source/document hits, and by default compacts same-path family results into one primary hit plus `related_kinds`. If you pass `--kind`, that family compaction is skipped so the query stays literal to the requested kind.

## Current Version

Sula version: `0.9.0`

Versioning rules are in [docs/versioning.md](docs/versioning.md).

## Operating Sula Core

Sula itself is a maintained project. Before releasing changes that will later sync into adopted repositories:

1. Run `python3 -m unittest discover -s tests -v`
2. Review [CHANGELOG.md](CHANGELOG.md) and capture sync impact
3. Review [registry/adopted-projects.toml](registry/adopted-projects.toml)
4. Dry-run sync against canary projects before broad rollout
5. Regenerate committed canary memory digests if the project policy uses them

Release discipline and impact rules live in:

- [docs/README.md](docs/README.md)
- [docs/release-process.md](docs/release-process.md)
- [docs/reference/project-memory-model.md](docs/reference/project-memory-model.md)
- [docs/reference/sync-impact-model.md](docs/reference/sync-impact-model.md)
- [docs/reference/adoption-registry.md](docs/reference/adoption-registry.md)

## Recommended Adoption Order

1. Adopt Sula Core
2. Run `adopt` to inspect and report
3. Approve the adoption and review scaffold files
4. Commit the generated operating system to the project
5. Use `sync --dry-run` for future shared improvements

## References

- [docs/philosophy.md](docs/philosophy.md)
- [docs/README.md](docs/README.md)
- [docs/reference/sula-vnext-project-kernel.md](docs/reference/sula-vnext-project-kernel.md)
- [docs/reference/portfolio-adapter-workflow-contract.md](docs/reference/portfolio-adapter-workflow-contract.md)
- [docs/adoption-playbook.md](docs/adoption-playbook.md)
- [docs/reference/adoption-agent.md](docs/reference/adoption-agent.md)
- [docs/reference/public-release-readiness.md](docs/reference/public-release-readiness.md)
- [docs/release-process.md](docs/release-process.md)
- [docs/versioning.md](docs/versioning.md)
- [docs/reference/project-memory-model.md](docs/reference/project-memory-model.md)
- [docs/reference/sync-impact-model.md](docs/reference/sync-impact-model.md)
- [docs/reference/adoption-registry.md](docs/reference/adoption-registry.md)
- [docs/reference/project-manifest.md](docs/reference/project-manifest.md)
- [schema/project.schema.json](schema/project.schema.json)
- [schema/project.example.toml](schema/project.example.toml)
- [registry/adopted-projects.toml](registry/adopted-projects.toml)
- [site/index.html](site/index.html)
- [site/bootstrap/index.html](site/bootstrap/index.html)
- [site/sula.json](site/sula.json)

## Project Governance

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
