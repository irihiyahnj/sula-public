# Add adoption-agent flow for one-sentence onboarding

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): bbc39aa
- status: completed

## Background

Sula onboarding still required the maintainer to remember a manual `init` workflow and explain the steps in session. That contradicted the intended user experience: a repository owner should be able to say one sentence, review an approval-ready report, approve the rollout, and get a complete adoption summary.

## Analysis

- The underlying rendering and doctor mechanics were already strong enough to support automation, but the user-facing entrypoint still behaved like a toolkit instead of an adoption agent.
- The highest risk in simplifying onboarding is hiding managed/scaffold boundaries or silently overwriting project-owned truth, so the new flow must preserve an explicit inspect-report-approve split.
- The Sula root repository also needs durable traceability for this change, otherwise the source repository would ship a new operating model without recording its own reasoning and rollout impact.

## Chosen Plan

- add an `adopt` command that inspects a target repository, detects a profile, builds a proposed manifest, and reports the planned managed/scaffold impact
- require an explicit `--approve` rerun before applying the adoption
- create initial status and change-record traceability automatically after approval
- update the Sula docs so the default onboarding story becomes one-sentence and approval-based

## Execution

- implemented `sula adopt` with auto-detection for `react-frontend-erpnext` and `sula-core`
- added adoption reporting, approval gating, post-apply validation, and usage guidance
- added CLI tests that cover inspect, apply, and unknown-profile blocker behavior
- added the `scripts/sula-adopt` wrapper and updated Sula docs to describe the new default flow

## Verification

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`

## Rollback

- revert the adoption-agent commit if the flow proves too brittle for real repositories
- fall back to the lower-level `init` and `sync` commands while retaining the same managed/scaffold contracts

## Data Side-effects

- no runtime or production data side-effects
- repository docs, lockfiles, and generated operating-system files move to `0.4.0`

## Follow-up

- validate the flow against the first external non-example repository
- expand profile detection only after a real project demands it
- keep the approval report clear enough that maintainers can trust what will be overwritten versus preserved

## Architecture Boundary Check

- highest rule impact: preserved; adoption gets easier, but Sula still manages only the operating-system layer and does not absorb project-owned business truth
