是# AGENTS.md

This file is the primary instruction source for AI coding agents working in the Sula repository.

## Repository Identity

- Repository root is `Sula`.
- Sula is a reusable project operating system, not a single application product.
- Sula manages reusable ops structure, profiles, manifests, and sync tooling.

## Highest Rule

- Preserve the split between centrally managed operating-system files and project-owned business truth.
- Do not turn Sula into a one-project template repository.

## Working Rules

- Keep Sula improvements portable across adopted projects.
- Prefer profile-level abstractions over project-specific wording.
- Keep bootstrap scripts dependency-light.
- Do not make Python 3.11+ or third-party packages mandatory without a strong reason.
- When changing managed templates, consider sync impact on existing projects.
- When changing scaffold templates, keep them as starters, not as centrally enforced truth.
- Update Sula docs when introducing new profiles, manifest fields, or sync behavior.

## Session Lifecycle

Every AI session in a Sula-adopted project follows this flow:

1. **Start**: Read `.sula/memory-digest.md` first — it contains the current project state, recent activity, and handoff instructions. Then run `python3 scripts/sula.py session start --project-root .` so every CLI sees the same active task, stage, role, and model-routing status.
2. **Work**: Perform the tasks described in STATUS.md Handoff section or as directed by the user.
   If the user gives a natural-language project-maintenance or fleet-maintenance goal, route it through Sula before doing the mechanical work yourself:
   ```bash
   python3 scripts/sula.py auto --project-root . \
     --intent "User goal in their words"
   ```
   If Sula classifies the goal as executor-required, do not perform that work in the host chat model. Let the configured executor route handle it, then review the status and evidence.
3. **Report before each commit**: Before every `git commit`, record what changed:
   ```bash
   python3 scripts/sula.py report --project-root . \
     --summary "What was done in this work unit."
   ```
   The `report` command appends to today's Date group in Summary, archives old groups, regenerates `.sula/memory-digest.md`, and updates Handoff verification date.
4. **Check before each commit**: After reporting, verify consistency:
   ```bash
   python3 scripts/sula.py check --project-root .
   ```
   If check fails (e.g. Summary still stale), fix the issue before committing.
5. **Commit**: Commit STATUS.md, `.sula/memory-digest.md`, and any change records. The next window then has the full truth immediately.

## Current Scope

- Core managed files
- `generic-project` profile
- `react-frontend-erpnext` profile
- `sula-core` profile
- project manifest schema and example
- machine-readable CLI outputs for local software integration
- optional MCP-compatible agent-native control surface for project, portfolio, artifact, provider, workflow, orchestration, and controlled record tools
- `onboard`, `adopt`, `init`, `sync`, `doctor`, `check`, `auto`, `fleet`, `remove`, `query`, `status`, `session`, `agent-routing`, `artifact`, `portfolio`, `feedback`, `record`, `memory digest`, and `report` commands
- static launch-site assets under `site/`, including the canonical launch contract and bootstrap shim

## Current Capabilities

- Sula can encode formal document design policy in a first-class `[document_design]` manifest section, including source-first rules and reusable structure bundles for schedule, proposal, report, process, and training documents.
- Sula can capture reusable managed-file fixes from adopted projects as portable feedback bundles, then ingest, review, and decide them in Sula Core before later rollout through normal versioned sync.
- Sula can register provider-backed artifacts for Google Drive style workspaces, including stable fields such as `project_relative_path`, `provider_item_id`, `provider_item_kind`, `provider_item_url`, `derived_from`, and `identity_key`.
- Sula can now track artifact-family truth sources and freshness for collaborative provider-backed files through fields such as `family_key`, `artifact_role`, `source_of_truth`, `collaboration_mode`, `last_refreshed_at`, and `last_provider_sync_at`.
- Sula can now refresh provider-native Google Docs and Google Sheets in read-only mode through `artifact refresh`, cache normalized provider snapshots under `.sula/cache/provider-snapshots/`, and auto-trigger that refresh when freshness intent is detected.
- Sula can now run a first-class daily `check` workflow that verifies status-memory structure, kernel health, and whether `.sula/state/current.md` plus `.sula/memory-digest.md` are still synchronized with current source documents.
- Sula can materialize project-owned source files into import-friendly deliverables through `artifact materialize`.
- Sula can prepare machine-readable provider import plans through `artifact import-plan`, including auto-generated `.docx` or `.xlsx` bridge artifacts when a Google Docs or Google Sheets import still needs a local handoff file.
- Sula can expose a dependency-light MCP-compatible control surface through `mcp tools`, `mcp call`, and `mcp serve`, with read-only project/portfolio tools by default and controlled write tools gated by local allowlists and write classes.
- Sula can now expose a CLI-owned session status banner and role-based agent routing policy so every coding CLI can see the active task, stage, model/provider role assignments, and local provider readiness without relying on client-native task UI.
- Sula can now route natural-language maintenance goals through `auto`, including executor-required fleet Sula upgrades that hand mechanical project work to configured local executor routes and leave the host model in supervisor/reviewer mode.
- Sula can return a consolidated project policy view for agents, including highest rule, workflow policy, agent behavior, approval categories, verification adapters, software constraints, service constraints, and instruction-file summaries.
- Sula can report provider adapter capabilities and structured PR closeout evidence, including CI state, unresolved review-thread count, comments requiring action, and closeout state when fixture or remote metadata is available.
- `artifact create` can now render formal source-document bundles for `schedule`, `proposal` / `plan`, `report`, `process`, and `training` artifacts instead of falling back to a single generic shell.
- Current materialization formats:
  - `.md` / `.txt` / `.html` -> `.html`
  - `.md` / `.txt` / `.html` -> `.docx` on macOS through `textutil`
  - `.csv` / `.tsv` / `.json` -> `.xlsx`
- Treat these features as the preferred bridge when a project needs Google Docs or Google Sheets outputs before direct provider-side document creation is available.
- When a new session needs details, read:
  - `docs/reference/feedback-bundle-lifecycle.md`
  - `README.md` artifact section
  - `docs/reference/provider-backed-artifact-identity.md`
  - `docs/change-records/2026-04-12-add-provider-backed-artifact-registration-identity.md`
  - `docs/change-records/2026-04-12-add-artifact-materialization-for-docs-and-sheets.md`
  - `docs/change-records/2026-04-12-add-provider-import-plans-for-google-docs-and-sheets.md`
  - `docs/change-records/2026-04-12-add-truth-source-and-freshness-checks-for-collaborative-provider-artifacts.md`
  - `docs/change-records/2026-04-12-add-provider-native-read-only-refresh-and-artifact-refresh-command.md`

## Out Of Scope For Now

- automatic GitHub app integration
- remote sync service
- stack profiles not yet backed by real project use

---

<!-- sula-vector -->
# Sula Vector — Host Operating Protocol

This project has migrated to the Sula Vector convention. The full
template lives at `tools/sula_vector/AGENTS.md`. Any LLM operating
in this project must follow the protocol below.

## At session start

1. Note the current ISO-8601 UTC time as your `session_start`.
2. Run `python3 tools/sula_vector/render.py . --for-agent` and read the output.
3. Treat that output as authoritative project context (Tier A–E principles + recent activity + open goals).

## Throughout the turn

- Append new fragments under `fragments/` for any decision, intent, goal, fact, artifact, annotation, or turn worth preserving (Tier B8).
- Filename: `<ISO-8601-time-Z>--<short-slug>.md`. Required frontmatter: `id`, `time`, `kind`.
- Append, never edit (Tier B1). To revise a previous decision or principle, append a new `kind: decision` whose `refs` includes the old fragment's id.
- Do not append if nothing meaningful changed (Tier C7).

## At end of turn

If you appended any fragments this turn, end your reply with the
output of:

```
python3 tools/sula_vector/render.py . --view changes-summary --since <session_start>
```

Display the full multi-line `[sula] +N this turn:` block to the
user. If the output is `[sula] no changes`, do not display it.
