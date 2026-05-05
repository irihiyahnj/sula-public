# Release Sula 0.11.0 formal document workflows and feedback bundles

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- status: released

## Scope

Released Sula 0.11.0 on the canonical Git branch so the repository now carries the formal document design contract and the feedback-bundle workflow in one synchronized source state.

## Risks

- adopted projects will receive more managed operating guidance and a broader manifest contract on next sync, so teams need to review the new document-design and feedback guidance before treating the rollout as routine
- project teams can still ignore the new feedback capture path and keep one-off local managed drift, so operator behavior remains part of rollout quality

## Verification

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- validated the repository self-sync so managed root files match the current templates and kernel state

## Rollback

- revert the `0.11.0` batch from Git if the combined document-design and feedback lifecycle should not be the canonical source state
- resync affected adopted projects back to the previous Sula release if downstream rollout must be withdrawn

## Follow-up

- validate the first external adopted project that uses the formal document design contract in production work
- validate the first external adopted project that captures a real reusable managed-file fix through the feedback bundle flow
