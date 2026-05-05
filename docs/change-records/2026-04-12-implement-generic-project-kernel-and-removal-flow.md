# Implement generic-project kernel and removal flow

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

The recorded vNext direction was clear: Sula should attach to any in-progress project through a safe baseline kernel, support projects without Git, and remain easy to remove later. The repository still behaved like a profile-gated adoption tool, so the first implementation milestone was to make that baseline real.

## Analysis

- Unknown project types previously blocked during `adopt`.
- The manifest and docs still centered stack-specific repo assumptions too strongly.
- `.sula/` did not yet contain the structured kernel artifacts promised by the vNext direction.
- Removal still depended on manual cleanup or Git history instead of an explicit report-first flow.

## Chosen Plan

- add a `generic-project` profile as the safe baseline
- make `adopt` fall back to that profile automatically
- write kernel state under `.sula/` during init, adopt, sync, record, and memory-digest flows
- add a report-first `remove` command
- update docs, schema examples, and tests together

## Execution

- added the `generic-project` managed and scaffold template set
- updated `scripts/sula.py` to:
  - auto-fallback to `generic-project`
  - support non-Git projects
  - generate `.sula/kernel.toml`, adapter catalog, discovered source registry, state snapshot, event log, index catalog, and export catalog
  - add `remove` inspect/apply flow
- updated README, adoption docs, manifest reference, schema example, and changelog
- added automated tests for generic adoption and Sula removal
- bumped the repository version to `0.5.0`

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest discover -s tests -v`

## Rollback

- revert this change batch
- remove the `generic-project` profile templates
- revert the CLI fallback and removal flow changes
- drop the added `.sula/` kernel artifacts from canaries if the design is reconsidered

## Data Side-effects

- adopted projects now gain additional namespaced `.sula/` kernel files
- removal is now explicit and reviewable instead of relying on manual cleanup alone

## Follow-up

- add canaries for Git and non-Git generic projects
- define adapter composition more explicitly beyond the current kernel metadata
- decide which exported human-readable views should eventually become generated from kernel state by default

## Architecture Boundary Check

- highest rule impact: preserved; the new baseline broadens adoption while keeping project-owned truth local and Sula-owned state namespaced and removable
