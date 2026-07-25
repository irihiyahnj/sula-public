# Default full Sula surface and activity feedback

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): uncommitted working-tree change
- status: draft

## Background

Changed new adoptions to governed projection mode, enabled dry-run orchestration by default, and added human-readable activity feedback for Sula automation events.

## Analysis

- Previous new-adoption defaults favored a lower visible footprint: generic and React/EPRNext projects started with detached projection and orchestration disabled.
- That was safe, but it meant many Sula capabilities were installed but not visible or active until the user manually promoted the project.
- The target behavior is a complete Sula operating surface by default, while preserving the highest rule: project-owned truth and real execution remain under explicit project policy.
- The safe boundary is to open the control plane and projection surface, but keep mutating runner execution gated behind dry-run defaults and explicit real-runner configuration.

## Chosen Plan

- Make governed projection the default for all new manifests.
- Enable orchestration by default with `runner = "dry-run"`, so task normalization, run records, closeout checks, and automation-planned work are available without automatic mutation.
- Keep automation enabled in execute mode with automatic intake/planning/dispatch, while keeping default dispatch inside the non-mutating dry-run runner unless a project explicitly configures a real runner.
- Add concise human-readable feedback when Sula records automation activity, creates or resolves an intent, or attempts dispatch.
- Keep JSON output stable for software integrations.

## Execution

- Updated manifest defaults and examples so new adoptions expose the full governed Sula surface by default.
- Updated Sula Core's own `.sula/project.toml` to keep orchestration enabled.
- Updated documentation to describe governed-by-default projection, dry-run orchestration, and visible Sula activity feedback.
- Added Sula activity feedback to human-readable command paths for sync, doctor, check, query, status, artifact locate, and artifact refresh.
- Changed missing local orchestration task files to mean zero local tasks instead of a warning, because the default local task source should not require an empty starter task file.
- Updated tests to expect governed projection and dry-run orchestration defaults.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- Targeted unit tests for adoption defaults, orchestration defaults, automation intake, and memory overflow behavior were updated for the new baseline.
- Full validation must pass through `sula doctor --strict`, `sula check`, and `sula orchestration doctor` before release.

## Rollback

- Revert `default_projection_mode_for_new_manifest` to profile-specific detached behavior for non-core profiles.
- Revert default orchestration enablement to disabled in `default_orchestration_config` and `ProjectConfig`.
- Remove the human-readable activity feedback hook if command output noise becomes unacceptable.
- Existing projects can locally reduce capability surface by setting `[projection].mode`, disabling projection packs, or setting `[orchestration].enabled = false`.

## Data Side-effects

- Human-readable Sula commands may now print one additional activity line when automation state changes.
- JSON outputs are intentionally unchanged in shape for downstream integrations.
- Automation and orchestration ledgers remain under `.sula/state/`; real runner execution is still not automatic under the default dry-run runner policy.
- Governed projection writes more visible managed files during new adoption than detached mode.

## Follow-up

- Consider a first-class retention or compaction command for append-only automation and orchestration ledgers if high-volume projects start generating excessive state history.
- Continue to treat real external runners and provider-write automation as explicit opt-in policy, not default behavior.

## Architecture Boundary Check

- highest rule impact: preserved. The change opens Sula's reusable operating surface by default, but does not move project-owned business truth into Sula-managed templates and does not enable mutating automation without explicit project policy.
