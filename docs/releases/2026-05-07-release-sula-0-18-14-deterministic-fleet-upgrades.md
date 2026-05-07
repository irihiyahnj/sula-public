# Release Sula 0.18.14 Deterministic Fleet Upgrades

## Metadata

- date: 2026-05-07
- executor: Codex host with local Sula validation
- branch: main
- status: ready

## Scope

Sula 0.18.14 makes Sula fleet upgrades completion-oriented and cheaper by using
a deterministic zero-model executor for Sula maintenance upgrades. Projects no
longer need their own DeepSeek/ClaudeCode wrapper just to sync Sula managed
files to a new release.

## Risks

- The deterministic executor can still leave a project in human review if
  `doctor` or `check` fails after sync.
- This release does not make code-changing tasks deterministic; those still need
  model-backed executor routes.

## Verification

- Python compile check passed.
- Site descriptor JSON validation passed.
- Targeted autopilot executor tests passed, including the no-runner
  deterministic upgrade path.

## Rollback

Revert the 0.18.14 commit and tag, then restore version metadata to 0.18.13.

## Follow-up

- Run a real machine-wide fleet upgrade after publishing and review status,
  token, cost, and any validation failures.
