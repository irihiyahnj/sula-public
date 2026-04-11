# Sula Adoption Playbook

This playbook describes how to roll Sula into a repository cleanly.

## Adopt A New Project

1. Confirm the project family matches an existing profile.
2. Create `.sula/project.toml`, or let `sula init` generate it.
3. Run `sula init`.
4. Review scaffold files:
   - `AGENTS.md`
   - `README.md`
   - `CHANGE-RECORDS.md`
   - `STATUS.md`
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
7. Run `sula doctor`.
8. Commit the adoption in the target repository.

## Adopt An Existing Project

1. Read the current project rules before generating anything.
2. Map current project facts into `.sula/project.toml`.
3. Generate into a working branch, not directly into the deployment branch.
4. Compare the generated operating system with existing docs.
5. Preserve project truth where it is already stronger than the scaffold.
6. Sync only the files that should become centrally managed.

## Upgrade An Adopted Project

1. Pull the latest Sula changes.
2. Run `sula sync`.
3. Run `sula doctor`.
4. Review diff carefully, especially:
   - release checklist changes
   - architecture exception rules
   - tool adapter changes
5. Commit as a discrete "Sula sync" batch.

## When Not To Adopt Immediately

Pause adoption if:

- the project has no stable branch model
- its architecture is still unknown
- the profile is a poor fit
- the team is not ready to accept managed operational files
