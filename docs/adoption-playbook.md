# Sula Adoption Playbook

This playbook describes how to roll Sula into a repository cleanly.

## Fast Path

The default onboarding flow is inspect, report, approve:

```bash
python3 scripts/sula.py adopt --project-root /path/to/project
python3 scripts/sula.py adopt --project-root /path/to/project --approve
```

Use `adopt` by default. Drop down to `init` only when you need manual control over fields that the adoption report cannot infer safely.

## Adopt A New Project

1. Run `sula adopt --project-root /path/to/project`.
2. Review the adoption report:
   - recommended profile
   - detected project facts
   - managed files that will be created or overwritten
   - scaffold files that will be created or preserved
   - blockers and warnings
3. Re-run with `--approve`.
4. Review scaffold files:
   - `AGENTS.md`
   - `README.md`
   - `CHANGE-RECORDS.md`
   - `STATUS.md`
   - `docs/change-records/_template.md`
   - `docs/releases/_template.md`
   - `docs/incidents/_template.md`
5. Review managed files:
   - `CODEX.md`
   - `CLAUDE.md`
   - `GEMINI.md`
   - `.github/copilot-instructions.md`
   - `.cursor/rules/project.mdc`
   - `docs/README.md`
   - `docs/ops/*`
   - profile-managed docs
6. Adjust project-specific facts in scaffold files.
7. Create or migrate the first change record if useful for project onboarding history.
8. Generate the first project memory digest if the team wants a fast recall layer.
9. Run `sula doctor --strict` if the apply phase did not already leave the repository clean.
10. Commit the adoption in the target repository.

## Adopt An Existing Project

1. Run `sula adopt --project-root /path/to/project` in a working branch, not directly in the deployment branch.
2. Read the current project rules before approval.
3. Compare the reported operating-system diff against existing docs and project habits.
4. Preserve project truth where it is already stronger than the scaffold.
5. Approve only after the managed/scaffold boundary is clear.
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
7. Commit as a discrete "Sula sync" batch.

## When Not To Adopt Immediately

Pause adoption if:

- the project has no stable branch model
- its architecture is still unknown
- the profile is a poor fit
- the team is not ready to accept managed operational files
