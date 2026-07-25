# Refine the public bootstrap contract for existing Sula consumers

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): working tree refinement after real bootstrap-site usage
- status: completed

## Background

The first real-world use of the public bootstrap prompt exposed two protocol gaps. Already-adopted repositories were still being narrated as if they were first-time adoption targets, and agents that could not find a local `scripts/sula.py` stopped at “CLI missing” instead of resolving the canonical Sula source.

## Analysis

- The inspect-report-approve flow itself behaved correctly because it inspected the target repository and paused for approval.
- The hosted contract and `sula.json` did not yet define how an agent should branch into existing-consumer review versus first-time adoption.
- The public site and root repository docs still described the custom domain as pending, even after DNS and TLS were active.

## Chosen Plan

- extend the public bootstrap page with explicit rules for existing consumers and tool resolution
- expand `site/sula.json` so machine-readable protocol consumers get the same guidance
- align repository documentation and status tracking with the live domain state

## Execution

- updated `site/bootstrap/index.html` to add explicit sections for existing Sula consumers and canonical tool resolution
- expanded `site/sula.json` with `source_repository_url`, existing-consumer behavior, tool-resolution guidance, and existing-consumer CLI entrypoints
- updated `docs/reference/adoption-agent.md`, `README.md`, `STATUS.md`, and `CHANGE-RECORDS.md` to match the hosted protocol
- redeployed the updated static assets to the active Fly machine serving `sula.fly.dev` and `sula.1stp.monster`

## Verification

- `curl -I https://sula.1stp.monster/`
- `curl -I https://sula.1stp.monster/bootstrap/`
- `curl https://sula.1stp.monster/sula.json`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`

## Rollback

- revert the protocol and documentation changes in this record
- redeploy the previous static bootstrap assets to the active Fly machine

## Data Side-effects

- no project data side-effects
- public bootstrap behavior now more accurately reflects how Sula should treat existing consumers and missing local tooling

## Follow-up

- validate the refined protocol against the first external repository that does not vendor Sula locally
- revisit `source_repository_url` when the canonical public repository strategy is finalized

## Architecture Boundary Check

- highest rule impact: preserved; this change only clarifies the public bootstrap contract and does not alter managed versus project-owned behavior inside adopted repositories
