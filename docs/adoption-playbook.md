# Sula Adoption Playbook

This playbook describes how to roll Sula into a repository cleanly.

## Fast Path

The outermost startup path is now the site launch contract:

```text
请按 https://sula.1stp.monster/launch/ 的启动协议接管当前项目。
```

or

```text
Please take over the current project using the launch contract at https://sula.1stp.monster/launch/.
```

The default onboarding flow is guided onboarding first, low-level adoption second when needed:

```bash
python3 scripts/sula.py onboard --project-root /path/to/project
python3 scripts/sula.py onboard --project-root /path/to/project --accept-suggested --approve
```

`onboard` asks the missing questions, explains which kernel and visible projections Sula will manage, and then applies adoption through the same manifest and kernel contract.

The lower-level inspect, report, approve flow remains:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project
python3 scripts/sula.py adopt --project-root /path/to/project --approve
```

Use `onboard` by default. Drop down to `adopt` when you already know the exact fields or need the raw approval report without the interview flow. Drop down to `init` only when you need manual control over fields that the adoption report cannot infer safely.

Software integrations should prefer the same commands with `--json` so they can consume stable envelopes instead of scraping human text.

## Zero-Memory Onboarding Rule

Users should not have to remember Sula internals.

The target experience is:

1. connect a project
2. answer the minimum missing questions
3. review what Sula will manage, where files will go, and how the project will be queried later

If an adoption flow requires the user to remember internal paths, slot names, or command sequences before the project is configured, the UX contract is still incomplete.

## Adopt A New Project

1. Run `sula adopt --project-root /path/to/project`.
2. Review the adoption report:
   - recommended profile
   - whether the report defaulted to `generic-project`
   - detected project facts
   - selected projection mode
   - visible projection files that will be created or overwritten
   - scaffold files that will be created or preserved
   - kernel files that will be created under `.sula/`
   - blockers and warnings
3. Re-run with `--approve`.
4. Review the default detached surface:
   - `AGENTS.md`
   - `README.md`
   - `CHANGE-RECORDS.md`
   - `STATUS.md`
   - `docs/change-records/_template.md`
   - `docs/releases/_template.md`
   - `docs/incidents/_template.md`
5. If the project needs a deeper visible operating surface, promote it intentionally with `projection mode` or `projection enable`.
6. Review collaborative or governed projection packs when they are enabled:
   - `CODEX.md`
   - `CLAUDE.md`
   - `GEMINI.md`
   - `.github/copilot-instructions.md`
   - `.cursor/rules/project.mdc`
   - `docs/README.md`
   - `docs/ops/*`
   - `docs/ops/document-design-principles.md`
   - profile-managed docs
7. Adjust project-specific facts in scaffold files.
8. Create or migrate the first change record if useful for project onboarding history.
9. Generate the first project memory digest if the team wants a fast recall layer.
10. Run `sula doctor --strict` if the apply phase did not already leave the repository clean.
11. Commit the adoption in the target repository.

If the project does not match a narrower profile safely, adopt it under `generic-project` first and refine later only when a more truthful reusable profile exists.

## Adopt A Drive-Synced Client Project

When the project lives in a Google Drive local-sync folder or another non-Git workspace, keep the project type and the storage provider separate:

```bash
python3 scripts/sula.py adopt \
  --project-root /path/to/project \
  --workflow-pack client-service \
  --storage-provider google-drive \
  --storage-sync-mode local-sync \
  --portfolio-workspace external-clients
```

Then approve, register the project in a portfolio, and create artifacts through the workflow pack:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project --approve
python3 scripts/sula.py portfolio register --project-root /path/to/project --portfolio-root /path/to/portfolio
python3 scripts/sula.py artifact create --project-root /path/to/project --kind agreement --title "Service Contract"
```

This keeps Google Drive in the storage adapter layer while letting the workflow pack route contracts, reports, invoices, and schedules into the right project folders.

## Adopt An Existing Project

1. Run `sula adopt --project-root /path/to/project` in a working branch, not directly in the deployment branch.
2. Read the current project rules before approval.
3. Compare the reported operating-system diff against existing docs and project habits.
4. Preserve project truth where it is already stronger than the scaffold.
5. Approve only after the kernel, visible projection, and project-owned scaffold boundaries are clear.
6. Migrate existing status, change history, release notes, and incident notes into the new memory layout only when that improves clarity.
7. Commit adoption as a distinct batch so future rollback stays simple.

## Upgrade An Adopted Project

1. Pull the latest Sula changes.
2. Run `sula sync --dry-run`.
3. Review the planned managed-file changes and their impact levels.
4. Run `sula sync`.
5. Run `sula doctor --strict`.
6. Review diff carefully, especially:
   - release checklist changes
   - architecture exception rules
   - tool adapter changes
   - new workflow, storage, or portfolio metadata if the project now participates in a broader workspace
7. Commit as a discrete "Sula sync" batch.

## Machine Consumers

External tools should treat Sula as a local control protocol:

1. call `adopt`, `sync`, `doctor`, `status`, `artifact`, `portfolio`, and `remove` with `--json`
2. read `.sula/` kernel files only as supporting state, not as a replacement for project truth
3. keep provider-specific details in storage adapter metadata instead of hard-coding them into prompts or workflows

## When Not To Adopt Immediately

Pause adoption if:

- the project has no stable branch model
- its architecture is still unknown
- the profile is a poor fit
- the team is not ready to accept managed operational files

## Remove A Project Cleanly

1. Run `sula remove --project-root /path/to/project`.
2. Review the report:
   - `.sula/` kernel paths that will be removed
   - registered visible projection files that will be removed
   - scaffold files that will remain project-owned
3. Re-run with `--approve`.
4. Review the resulting diff before committing the removal.
