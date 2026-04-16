# Sula

Sula is a reusable project operating system for AI-native software teams.

It standardizes how projects define rules, accept requests, execute work, verify changes, ship releases, and keep durable traceability across repositories.

Sula is not a product template for one stack. It is a coordination layer with:

- a reusable documentation and operations core
- a namespaced `.sula/` kernel with detached-first visible projection packs
- profile-specific templates for project families
- a project manifest that captures each repository's facts
- a guided zero-memory onboarding flow for first-time setup
- a site-launch contract with a canonical URL and downloadable bootstrap launcher
- machine-readable CLI outputs for external tools and adapters
- an inspect-report-approve adoption flow for one-sentence onboarding
- scripts to initialize, sync, and audit project adoption
- a governed rollout path for sync impact and release discipline
- a feedback-bundle workflow so reusable fixes can move upstream into Sula Core and then back downstream through versioned sync
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

Reusable kernel state and orchestration that should evolve once and benefit many projects:

- `.sula/project.toml`
- `.sula/version.lock`
- `.sula/state/*`
- `.sula/indexes/*`
- `.sula/objects/*`
- `.sula/cache/*`
- `scripts/sula.py`

### 2. Projection Packs

Optional repo-visible surfaces rendered from the same kernel:

- `CODEX.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/project.mdc`
- `docs/README.md`
- `docs/ops/*`
- `docs/architecture/*`
- `docs/runbooks/*`
- `README.md`
- `AGENTS.md`
- `STATUS.md`
- `CHANGE-RECORDS.md`
- `docs/change-records/*`
- `docs/releases/*`
- `docs/incidents/*`

New `generic-project` and `react-frontend-erpnext` adoptions default to the lowest visible footprint first: `detached`. `sula-core` defaults to `governed`.

### 3. Profile

A profile is a reusable project-family layer.

Current profiles:

- `generic-project`
- `react-frontend-erpnext`
- `sula-core`

Profiles provide:

- optional architecture projections
- optional runbook projections
- scaffold starters for project-owned files

### 4. Project Manifest

Each adopted project keeps a local `.sula/project.toml` that defines:

- project identity
- branch model
- highest architecture rule
- build and verification commands
- key source paths
- deploy expectations
- auth/session semantics
- projection mode and enabled visible packs
- workflow pack, storage adapter, and portfolio registration metadata

### 5. Kernel, Projections, And Project-Owned Files

Sula distinguishes three surfaces:

- kernel files: namespaced state under `.sula/`
- projection files: visible docs and tool instructions rendered only for enabled packs
- scaffold files: generated once if missing, then owned by the project

This keeps the core system portable while avoiding accidental ownership grabs over project truth.

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

`onboard` asks the missing questions, including the default language for generated docs and records, proposes workflow/storage/portfolio answers, explains the initial projection depth, and can apply adoption immediately after confirmation.

New `generic-project` and `react-frontend-erpnext` repositories start in `detached` mode by default, so the `.sula/` kernel lands first and deeper visible governance can be enabled later. `sula-core` starts in `governed` mode because it is the source repository.

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
python3 scripts/sula.py check --project-root /path/to/project
```

Use `--dry-run` before every real sync so you can review which managed files would change and how risky they are.
Use `check` as the daily close-out gate after changing `STATUS.md`, `CHANGE-RECORDS.md`, `docs/change-records/*`, or generated `.sula/*` state; only `SULA CHECK OK` counts as a finished state-sync update.

### Control Visible Projections

```bash
python3 scripts/sula.py projection list --project-root /path/to/project
python3 scripts/sula.py projection mode --project-root /path/to/project --set collaborative
python3 scripts/sula.py projection mode --project-root /path/to/project --set governed
python3 scripts/sula.py projection enable --project-root /path/to/project --pack ai-tooling
python3 scripts/sula.py projection disable --project-root /path/to/project --pack ai-tooling
```

Projection modes describe how much repo-visible governance Sula should materialize, not which kernel abilities exist:

- `detached`: keep the kernel plus minimal project-facing memory files and record templates
- `collaborative`: add reusable operating docs, document-design rules, architecture maps, and runbooks
- `governed`: add AI tool instruction projections and the deepest visible governance surface

All modes keep the same kernel-level capabilities such as `doctor`, `check`, `query`, `artifact`, `portfolio`, `feedback`, and `remove`.

### Remove Sula from a project

```bash
python3 scripts/sula.py remove --project-root /path/to/project
python3 scripts/sula.py remove --project-root /path/to/project --approve
```

The report shows which namespaced kernel files and registered visible projections will be removed, and which scaffold files will stay project-owned.

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
python3 scripts/sula.py check --project-root /path/to/project --json
```

These commands expose the same project kernel to humans and to external software. When `--json` is used, Sula becomes a local machine protocol instead of a text-only CLI.

### Capture reusable feedback from adopted projects

```bash
python3 scripts/sula.py feedback capture \
  --project-root /path/to/project \
  --title "Route reusable managed fix upstream" \
  --summary "Captured a reusable fix from local Sula drift." \
  --shared-rationale "This issue affects more than one adopted project." \
  --json

python3 scripts/sula.py feedback ingest \
  --project-root /path/to/sula-core \
  --bundle-path /path/to/project/.sula/feedback/outbox/archives/<feedback-id>.zip \
  --json

python3 scripts/sula.py feedback decide \
  --project-root /path/to/sula-core \
  --feedback-id <feedback-id> \
  --decision accepted \
  --note "Absorb this into the shared release path." \
  --target-version 0.11.0 \
  --json
```

This keeps project-owned truth local while still giving Sula Core a governed intake path for reusable fixes. Projects may patch their local managed files to stay productive, but upstream adoption happens only after Sula Core review and a later versioned rollout.

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
  --provider-item-url https://docs.google.com/document/d/doc-abc123/edit \
  --source-of-truth provider-native \
  --collaboration-mode multi-editor \
  --last-provider-sync-at 2026-04-12T10:00:00Z

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

python3 scripts/sula.py artifact refresh \
  --project-root /path/to/project \
  --artifact-id artifact-provider-google-drive-hospital-root-google-doc-doc-abc123 \
  --json
```

Artifacts are routed through the active workflow pack and stored under the project's artifacts root, then registered in `.sula/artifacts/catalog.json`.

Workflow policy is now also a first-class manifest surface:

- `.sula/project.toml` can record `execution_mode`, `design_gate`, `plan_gate`, `review_policy`, `workspace_isolation`, `testing_policy`, and `closeout_policy` under `[workflow]`
- durable source-first workflow documents now live under `workflow.docs_root`, which defaults to `docs/workflows`
- `python3 scripts/sula.py workflow assess --project-root /path/to/project --task "Refactor auth and rollout provider sync"` reports whether the task should carry a `spec`, `plan`, or `review`
- `python3 scripts/sula.py workflow scaffold --project-root /path/to/project --kind spec --title "Auth Sync Spec"` creates a durable workflow source document and registers it in the artifact catalog

Provider-backed artifacts can also be registered without a local materialized file path by supplying a stable project-relative path and provider item metadata. This lets Drive-synced and provider-native deliverables survive device-specific local path differences.

Collaborative provider-backed artifacts can now also carry truth-source and freshness metadata:

- `artifact register` accepts `--source-of-truth`, `--collaboration-mode`, `--artifact-role`, `--last-refreshed-at`, and `--last-provider-sync-at`
- artifact families keep `workspace-source`, `provider-native-source`, and `exported-derivative` entries traceable under one `family_key`
- when a multi-editor artifact points at a Google Doc or Google Sheet, Sula treats the provider-native item as the default fact source instead of silently trusting a local copy
- if provider metadata is incomplete, Sula reports the missing `provider_root_url`, `provider_root_id`, `provider_item_id`, `provider_item_kind`, and `provider_item_url` fields instead of assuming that the local file is current

Formal planning, proposal, report, process, and training documents now have a first-class design contract:

- projects can declare that contract in `[document_design]` inside `.sula/project.toml`
- managed projects receive `docs/ops/document-design-principles.md` as the reusable rulebook
- `artifact create` renders genre-specific source-document bundles for `schedule`, `proposal` / `plan`, `report`, `process`, and `training`
- source files remain the editable truth; `.docx`, `.html`, `.xlsx`, and provider-native outputs stay derived artifacts with traceable lineage

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
- it treats `project_relative_path` as the provider-native target path under the recorded `provider_root_id`
- it now also emits `provider_parent_relative_path` so external Google import or create steps know which folder path to use instead of defaulting to the provider root folder

Natural-language freshness checks are now part of the retrieval contract:

- `python3 scripts/sula.py query --project-root /path/to/project --q "先看最新版本再继续" --json`
- `python3 scripts/sula.py artifact locate --project-root /path/to/project --q "共享文档为准" --json`
- `python3 scripts/sula.py status --project-root /path/to/project --json`

Those outputs now expose the current `truth_source_type`, `last_refreshed_at`, `last_provider_sync_at`, `local_copy_stale_risk`, and any missing provider metadata for collaborative artifact families.

When provider metadata is complete and read-only Google access is available, freshness intent now triggers a real provider refresh before results are returned:

- set `SULA_GOOGLE_ACCESS_TOKEN` to a read-only Google API bearer token
- or, for local testing, point `SULA_PROVIDER_FIXTURE_DIR` at JSON fixtures consumed by the Google provider adapter

For a durable local setup, you can do one browser-based consent and let Sula refresh access tokens from a stored refresh token afterward:

```bash
python3 scripts/sula_google_auth.py \
  --project-root /path/to/project \
  --client-secrets-file /path/to/client_secret_desktop.json \
  --print-shell
```

When `--project-root` is present, the OAuth store defaults to `PROJECT/.sula/local/google-oauth.json`. Without it, the fallback remains `~/.config/sula/google-oauth.json`. During provider refresh, Sula now tries the project-local OAuth store first and then falls back to the global store, so other sessions only need the project root to find the right token file.

For provider-native Docs or Sheets, Sula now treats the saved location as:

- `provider_root_id` or `provider_root_url`: the project container in Drive
- `project_relative_path`: the provider-native target path inside that container
- `provider_parent_relative_path`: the folder path that should contain the native item

If you do not set `--project-relative-path` explicitly, Sula defaults it from the workflow slot, record date, and title slug, for example `delivery/2026-04-12-hospital-intake-draft`. That avoids ambiguous “save it at the root” behavior.

`artifact refresh` is the explicit operational surface for the same workflow:

- `--artifact-id` refreshes one registered family
- `--family-key` refreshes one whole artifact family
- `--q` refreshes matching provider-native families before a focused operation
- `--all-collaborative` refreshes every collaborative provider-native family in the project

Successful refreshes persist read-only provider metadata such as revision id, modified time, fetch status, and a cached normalized provider snapshot under `.sula/cache/provider-snapshots/`.

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

Sula version: `0.11.0`

Versioning rules are in [docs/versioning.md](docs/versioning.md).

## Operating Sula Core

Sula itself is a maintained project. Before releasing changes that will later sync into adopted repositories:

1. Run `python3 -m unittest discover -s tests -v`
2. Review [CHANGELOG.md](CHANGELOG.md) and capture sync impact
3. Review [registry/adopted-projects.toml](registry/adopted-projects.toml)
4. Review [registry/feedback/catalog.json](registry/feedback/catalog.json)
5. Dry-run sync against canary projects before broad rollout
6. Regenerate committed canary memory digests if the project policy uses them

Release discipline and impact rules live in:

- [docs/README.md](docs/README.md)
- [docs/release-process.md](docs/release-process.md)
- [docs/reference/feedback-bundle-lifecycle.md](docs/reference/feedback-bundle-lifecycle.md)
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
- [docs/reference/feedback-bundle-lifecycle.md](docs/reference/feedback-bundle-lifecycle.md)
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
